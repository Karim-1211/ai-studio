import os

from flask import (
    Blueprint,
    current_app,
    request,
    send_file
)
from PIL import Image, UnidentifiedImageError

from database.crud import (
    create_message_attachment,
    create_message_attachment_chunks,
    get_chat_by_id,
    get_message_attachment_by_id,
    get_pending_message_attachments,
    update_message_attachment_status
)
from services.api_utils import error_response
from services.deletion_service import delete_attachment_with_file
from services.document_service import (
    DocumentProcessingError,
    extract_text_from_file,
    is_allowed_file,
    save_uploaded_file,
    split_text_into_chunks
)
from services.embedding_service import (
    EmbeddingServiceError,
    generate_embeddings
)


attachment_routes = Blueprint("attachment_routes", __name__)

IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def attachment_to_dict(attachment):
    is_image = attachment.attachment_kind == "image"

    return {
        "id": attachment.id,
        "chat_id": attachment.chat_id,
        "message_id": attachment.message_id,
        "original_filename": attachment.original_filename,
        "file_type": attachment.file_type,
        "mime_type": attachment.mime_type,
        "file_size": attachment.file_size,
        "attachment_kind": attachment.attachment_kind,
        "status": attachment.status,
        "error_message": attachment.error_message,
        "chunk_count": attachment.chunk_count,
        "text_length": attachment.text_length,
        "extraction_method": attachment.extraction_method,
        "page_count": attachment.page_count,
        "preview_url": (
            f"/api/attachments/{attachment.id}/preview"
            if is_image and attachment.status == "ready"
            else None
        ),
        "created_at": attachment.created_at.isoformat()
        if attachment.created_at
        else None
    }


@attachment_routes.route(
    "/api/chats/<int:chat_id>/attachments",
    methods=["POST"]
)
def upload_message_attachment(chat_id):
    chat = get_chat_by_id(chat_id)

    if not chat:
        return error_response("Chat not found.", 404, "chat_not_found")

    pending_attachments = get_pending_message_attachments(chat_id)
    maximum_files = int(current_app.config.get("ATTACHMENT_MAX_FILES", 5))

    if len(pending_attachments) >= maximum_files:
        return error_response(
            f"A message can contain no more than {maximum_files} attachments.",
            409,
            "attachment_count_limit"
        )

    uploaded_file = request.files.get("file")

    if uploaded_file is None:
        return error_response("No file was provided.", 400, "missing_file")

    if not uploaded_file.filename:
        return error_response("No file was selected.", 400, "empty_filename")

    allowed_extensions = current_app.config["ATTACHMENT_ALLOWED_EXTENSIONS"]

    if not is_allowed_file(uploaded_file.filename, allowed_extensions):
        return error_response(
            "Unsupported attachment. Use PDF, DOCX, TXT, PNG, JPG, JPEG, or WebP.",
            400,
            "unsupported_attachment_type"
        )

    saved_file = None
    attachment = None

    try:
        saved_file = save_uploaded_file(
            uploaded_file,
            current_app.config["UPLOAD_FOLDER"]
        )

        maximum_bytes = int(
            current_app.config.get("ATTACHMENT_MAX_FILE_BYTES", 20 * 1024 * 1024)
        )

        if saved_file["file_size"] > maximum_bytes:
            raise AttachmentLimitError(
                f"Attachment exceeds the {maximum_bytes // (1024 * 1024)} MB file limit."
            )

        maximum_total_bytes = int(
            current_app.config.get(
                "ATTACHMENT_MAX_TOTAL_BYTES",
                40 * 1024 * 1024
            )
        )

        pending_total_bytes = sum(
            item.file_size for item in pending_attachments
        )

        if pending_total_bytes + saved_file["file_size"] > maximum_total_bytes:
            raise AttachmentLimitError(
                "The pending attachments exceed the configured total size limit."
            )

        extension = saved_file["extension"]
        attachment_kind = "image" if extension in IMAGE_EXTENSIONS else "document"

        if attachment_kind == "image":
            validate_image_attachment(
                saved_file["file_path"],
                int(current_app.config.get("OCR_MAX_IMAGE_PIXELS", 25_000_000))
            )

        attachment = create_message_attachment(
            chat_id=chat_id,
            original_filename=saved_file["original_filename"],
            stored_filename=saved_file["stored_filename"],
            file_type=extension,
            mime_type=uploaded_file.mimetype,
            file_size=saved_file["file_size"],
            attachment_kind=attachment_kind
        )

        extraction_result = None
        extracted_text = ""

        try:
            extraction_result = extract_text_from_file(
                saved_file["file_path"],
                extension,
                ocr_settings=current_app.config
            )

            extracted_text = extraction_result.get("text", "")

        except DocumentProcessingError:
            if attachment_kind != "image":
                raise

            extraction_result = {
                "method": "vision",
                "pages_processed": 1,
                "ocr_used": False
            }

        chunks = []

        if extracted_text:
            chunks = split_text_into_chunks(
                extracted_text,
                chunk_size=current_app.config["RAG_CHUNK_SIZE"],
                overlap=current_app.config["RAG_CHUNK_OVERLAP"]
            )

        if chunks:
            try:
                embeddings = generate_embeddings(chunks)

                create_message_attachment_chunks(
                    attachment_id=attachment.id,
                    chunks=chunks,
                    embeddings=embeddings
                )

            except EmbeddingServiceError as error:
                current_app.logger.warning(
                    "attachment_embedding_skipped",
                    extra={
                        "attachment_id": getattr(attachment, "id", None),
                        "reason": str(error),
                    },
                )

                chunks = []

        attachment = update_message_attachment_status(
            attachment_id=attachment.id,
            status="ready",
            error_message=None,
            chunk_count=len(chunks),
            text_length=len(extracted_text),
            extraction_method=extraction_result.get("method", "native"),
            page_count=int(extraction_result.get("pages_processed", 1))
        )

        message = "Attachment is ready."

        if extracted_text and not chunks:
            message = (
                "Attachment uploaded. Text was extracted, but knowledge search "
                "is unavailable because local embeddings are not configured."
            )

        return {
            "message": message,
            "attachment": attachment_to_dict(attachment)
        }, 201

    except AttachmentLimitError as error:
        return handle_attachment_failure(
            error,
            attachment,
            saved_file,
            413,
            "attachment_too_large"
        )

    except DocumentProcessingError as error:
        return handle_attachment_failure(
            error,
            attachment,
            saved_file,
            getattr(error, "status_code", 422),
            "attachment_processing_failed"
        )

    except Exception as error:
        current_app.logger.exception("attachment_upload_failed")

        return handle_attachment_failure(
            error,
            attachment,
            saved_file,
            500,
            "attachment_upload_failed"
        )


@attachment_routes.route(
    "/api/attachments/<int:attachment_id>/preview",
    methods=["GET"]
)
def preview_attachment(attachment_id):
    attachment = get_message_attachment_by_id(attachment_id)

    if not attachment:
        return error_response("Attachment not found.", 404, "attachment_not_found")

    if attachment.attachment_kind != "image" or attachment.status != "ready":
        return error_response(
            "Only ready image attachments can be previewed.",
            415,
            "attachment_preview_not_available"
        )

    path = safe_attachment_path(attachment.stored_filename)

    if not os.path.isfile(path):
        return error_response(
            "Attachment file is missing.",
            404,
            "attachment_file_missing"
        )

    return send_file(
        path,
        mimetype=attachment.mime_type or "application/octet-stream",
        download_name=attachment.original_filename,
        conditional=True,
        max_age=3600
    )


@attachment_routes.route(
    "/api/attachments/<int:attachment_id>",
    methods=["DELETE"]
)
def remove_message_attachment(attachment_id):
    attachment = get_message_attachment_by_id(attachment_id)

    if not attachment:
        return error_response("Attachment not found.", 404, "attachment_not_found")

    if attachment.message_id is not None:
        return error_response(
            "An attachment already saved with a message cannot be removed separately.",
            409,
            "attachment_already_sent"
        )

    delete_attachment_with_file(attachment)

    return {"message": "Attachment removed."}


def validate_image_attachment(path, maximum_pixels):
    try:
        with Image.open(path) as image:
            width, height = image.size

            if width <= 0 or height <= 0:
                raise DocumentProcessingError("The image dimensions are invalid.")

            if width * height > maximum_pixels:
                raise AttachmentLimitError(
                    "The image dimensions exceed the configured safety limit."
                )

            image.verify()

    except UnidentifiedImageError as error:
        raise DocumentProcessingError(
            "The attachment is not a readable image."
        ) from error


def safe_attachment_path(stored_filename):
    upload_folder = os.path.abspath(current_app.config["UPLOAD_FOLDER"])
    path = os.path.abspath(os.path.join(upload_folder, stored_filename))

    if os.path.commonpath([path, upload_folder]) != upload_folder:
        raise ValueError("Unsafe attachment filename.")

    return path


def handle_attachment_failure(
    error,
    attachment,
    saved_file,
    status_code,
    error_code
):
    if attachment:
        try:
            update_message_attachment_status(
                attachment_id=attachment.id,
                status="failed",
                error_message=str(error)
            )

        except Exception:
            current_app.logger.exception("attachment_status_update_failed")

    if saved_file and os.path.exists(saved_file["file_path"]):
        try:
            os.remove(saved_file["file_path"])

        except OSError:
            current_app.logger.exception("attachment_cleanup_failed")

    return error_response(
        "Attachment processing failed.",
        status_code,
        error_code,
        str(error)
    )


class AttachmentLimitError(DocumentProcessingError):
    status_code = 413