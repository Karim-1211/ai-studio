import os

from flask import (
    Blueprint,
    current_app,
    request
)

from database.crud import (
    create_global_document,
    create_global_document_chunks,
    get_all_global_documents,
    get_global_document_by_id,
    update_global_document_status
)

from services.api_utils import (
    error_response
)

from services.deletion_service import (
    delete_global_document_with_file
)

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


global_document_routes = Blueprint(
    "global_document_routes",
    __name__
)


def global_document_to_dict(document):
    return {
        "id": document.id,
        "scope": "global",
        "original_filename": (
            document.original_filename
        ),
        "file_type": document.file_type,
        "file_size": document.file_size,
        "status": document.status,
        "error_message": document.error_message,
        "chunk_count": document.chunk_count,
        "text_length": document.text_length,
        "created_at": (
            document.created_at.isoformat()
            if document.created_at
            else None
        ),
        "updated_at": (
            document.updated_at.isoformat()
            if document.updated_at
            else None
        )
    }


def extraction_to_dict(result):
    return {
        "method": result.get(
            "method",
            "native"
        ),
        "ocr_used": bool(
            result.get(
                "ocr_used",
                False
            )
        ),
        "pages_processed": int(
            result.get(
                "pages_processed",
                1
            )
        ),
        "native_pages": int(
            result.get(
                "native_pages",
                0
            )
        ),
        "ocr_pages": int(
            result.get(
                "ocr_pages",
                0
            )
        )
    }


def build_success_message(
    extraction_result
):
    method = extraction_result.get(
        "method"
    )

    if method == "ocr":
        return (
            "Global document read with OCR, indexed, "
            "and selected successfully."
        )

    if method == "hybrid":
        return (
            "Global document read with native extraction "
            "and OCR, then indexed successfully."
        )

    return (
        "Global document uploaded and indexed successfully."
    )


@global_document_routes.route(
    "/api/global-documents",
    methods=["GET"]
)
def list_global_documents():
    return [
        global_document_to_dict(
            document
        )
        for document in (
            get_all_global_documents()
        )
    ]


@global_document_routes.route(
    "/api/global-documents",
    methods=["POST"]
)
def upload_global_document():
    uploaded_file = request.files.get(
        "file"
    )

    if uploaded_file is None:
        return error_response(
            "No file was provided.",
            400,
            "missing_file"
        )

    if not uploaded_file.filename:
        return error_response(
            "No file was selected.",
            400,
            "empty_filename"
        )

    if not is_allowed_file(
        uploaded_file.filename,
        current_app.config[
            "ALLOWED_EXTENSIONS"
        ]
    ):
        return error_response(
            (
                "Unsupported file type. "
                "Upload PDF, DOCX, TXT, PNG, JPG, or JPEG."
            ),
            400,
            "unsupported_file_type"
        )

    saved_file = None
    document = None

    try:
        saved_file = save_uploaded_file(
            uploaded_file,
            current_app.config[
                "UPLOAD_FOLDER"
            ]
        )

        document = create_global_document(
            original_filename=saved_file[
                "original_filename"
            ],
            stored_filename=saved_file[
                "stored_filename"
            ],
            file_type=saved_file[
                "extension"
            ],
            file_size=saved_file[
                "file_size"
            ]
        )

        extraction_result = (
            extract_text_from_file(
                saved_file["file_path"],
                saved_file["extension"],
                ocr_settings=current_app.config
            )
        )

        extracted_text = extraction_result[
            "text"
        ]

        chunks = split_text_into_chunks(
            extracted_text,
            chunk_size=current_app.config[
                "RAG_CHUNK_SIZE"
            ],
            overlap=current_app.config[
                "RAG_CHUNK_OVERLAP"
            ]
        )

        if not chunks:
            raise DocumentProcessingError(
                "The document did not produce any searchable text chunks."
            )

        embeddings = generate_embeddings(
            chunks
        )

        create_global_document_chunks(
            global_document_id=document.id,
            chunks=chunks,
            embeddings=embeddings
        )

        document = update_global_document_status(
            document_id=document.id,
            status="ready",
            error_message=None,
            chunk_count=len(chunks),
            text_length=len(extracted_text)
        )

        return {
            "message": build_success_message(
                extraction_result
            ),
            "document": global_document_to_dict(
                document
            ),
            "extraction": extraction_to_dict(
                extraction_result
            )
        }, 201

    except DocumentProcessingError as error:
        return handle_processing_failure(
            error=error,
            document=document,
            saved_file=saved_file,
            status_code=getattr(
                error,
                "status_code",
                422
            ),
            error_code="document_processing_failed"
        )

    except EmbeddingServiceError as error:
        return handle_processing_failure(
            error=error,
            document=document,
            saved_file=saved_file,
            status_code=502,
            error_code="embedding_service_failed"
        )

    except Exception as error:
        current_app.logger.exception(
            "global_document_upload_failed"
        )

        return handle_processing_failure(
            error=error,
            document=document,
            saved_file=saved_file,
            status_code=500,
            error_code="global_document_upload_failed"
        )


def handle_processing_failure(
    error,
    document,
    saved_file,
    status_code,
    error_code
):
    error_message = str(
        error
    )

    if document:
        update_global_document_status(
            document_id=document.id,
            status="failed",
            error_message=error_message
        )

    if (
        saved_file
        and os.path.exists(
            saved_file["file_path"]
        )
    ):
        try:
            os.remove(
                saved_file["file_path"]
            )
        except OSError as cleanup_error:
            current_app.logger.warning(
                "failed_global_upload_cleanup_error: %s",
                cleanup_error
            )

    return error_response(
        "Global document processing failed.",
        status_code,
        error_code,
        error_message
    )


@global_document_routes.route(
    "/api/global-documents/<int:document_id>",
    methods=["DELETE"]
)
def remove_global_document(
    document_id
):
    document = get_global_document_by_id(
        document_id
    )

    if not document:
        return error_response(
            "Global document not found.",
            404,
            "global_document_not_found"
        )

    delete_global_document_with_file(
        document
    )

    return {
        "message": (
            "Global document deleted successfully."
        )
    }
