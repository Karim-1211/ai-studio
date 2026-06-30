import base64
import json
import re
import time

from flask import (
    Blueprint,
    Response,
    current_app,
    g,
    request,
    stream_with_context
)

from flask_login import current_user

from database.crud import (
    get_chat_by_id,
    get_message_attachments_by_ids
)

from services.ollama_service import (
    OllamaVisionError,
    find_vision_model,
    generate_vision_analysis,
    model_supports_vision
)

from services.ai_provider_service import (
    get_ai_provider,
    provider_supports_direct_images,
    stream_ai_response
)

from services.rag_service import (
    build_rag_prompt,
    retrieve_attachment_context,
    retrieve_relevant_context
)

from services.telemetry_service import record_model_usage


chat_routes = Blueprint(
    "chat_routes",
    __name__
)


VALID_MODES = {
    "single",
    "options",
    "detailed",
    "creative",
    "precise",
    "fast"
}


@chat_routes.route(
    "/chat",
    methods=["POST"]
)
def chat():
    data = request.get_json(
        silent=True
    )

    if not isinstance(
        data,
        dict
    ):
        return text_error(
            "A JSON object is required.",
            400
        )

    prompt = str(
        data.get(
            "prompt",
            ""
        )
    ).strip()

    model = str(
        data.get(
            "model",
            ""
        )
    ).strip()

    mode = str(
        data.get(
            "mode",
            "single"
        )
    ).strip()

    option_number = data.get(
        "option_number"
    )

    chat_id = data.get(
        "chat_id"
    )

    system_prompt = str(
        data.get(
            "system_prompt",
            ""
        )
    ).strip()

    if not prompt:
        return text_error(
            "Prompt is required.",
            400
        )

    if len(prompt) > 50_000:
        return text_error(
            "Prompt cannot exceed 50,000 characters.",
            413
        )

    if not model:
        return text_error(
            "Model is required.",
            400
        )

    if len(model) > 200:
        return text_error(
            "Model name is too long.",
            400
        )

    if mode not in VALID_MODES:
        return text_error(
            "Invalid response mode.",
            400
        )

    if mode == "options":
        try:
            option_number = int(
                option_number
            )
        except (
            TypeError,
            ValueError
        ):
            return text_error(
                "Option number is required for 3 Options mode.",
                400
            )

        if option_number not in {
            1,
            2,
            3
        }:
            return text_error(
                "Option number must be 1, 2, or 3.",
                400
            )

    if len(system_prompt) > 4000:
        return text_error(
            "System prompt cannot exceed 4000 characters.",
            400
        )

    try:
        temperature = parse_float_setting(
            data.get("temperature"),
            "temperature",
            0.0,
            2.0,
            0.7
        )

        max_tokens = parse_int_setting(
            data.get("max_tokens"),
            "max_tokens",
            50,
            8192,
            1000
        )

        top_p = parse_float_setting(
            data.get("top_p"),
            "top_p",
            0.05,
            1.0,
            0.9
        )

        top_k = parse_int_setting(
            data.get("top_k"),
            "top_k",
            0,
            100,
            40
        )

        repeat_penalty = parse_float_setting(
            data.get("repeat_penalty"),
            "repeat_penalty",
            0.5,
            2.0,
            1.1
        )

        context_length = parse_int_setting(
            data.get("context_length"),
            "context_length",
            512,
            32768,
            4096
        )

        document_ids = normalize_document_ids(
            data.get("document_ids")
        )

        global_document_ids = normalize_document_ids(
            data.get(
                "global_document_ids"
            )
        )

        website_source_ids = normalize_document_ids(
            data.get(
                "website_source_ids"
            )
        )

        social_source_ids = normalize_document_ids(
            data.get("social_source_ids")
        )

        attachment_ids = normalize_attachment_ids(
            data.get("attachment_ids"),
            maximum=current_app.config.get("ATTACHMENT_MAX_FILES", 5)
        )

    except ValueError as error:
        return text_error(
            str(error),
            400
        )

    use_documents = parse_boolean(
        data.get("use_documents"),
        default=True
    )

    strict_documents = parse_boolean(
        data.get("strict_documents"),
        default=True
    )

    use_global_documents = parse_boolean(
        data.get(
            "use_global_documents"
        ),
        default=True
    )

    use_website_sources = parse_boolean(
        data.get(
            "use_website_sources"
        ),
        default=True
    )

    use_social_sources = parse_boolean(
        data.get("use_social_sources"),
        default=True
    )

    final_prompt = prompt
    context_items = []
    attachment_context_items = []
    attachments = []
    image_paths = []
    direct_image_input = False

    parsed_chat_id = None

    if chat_id is not None:
        try:
            parsed_chat_id = int(
                chat_id
            )
        except (
            TypeError,
            ValueError
        ):
            return text_error(
                "Invalid chat ID.",
                400
            )

        if parsed_chat_id <= 0:
            return text_error(
                "Invalid chat ID.",
                400
            )

        if not get_chat_by_id(
            parsed_chat_id
        ):
            return text_error(
                "Chat not found.",
                404
            )

    if attachment_ids:
        if parsed_chat_id is None:
            return text_error(
                "A chat ID is required when attachments are included.",
                400
            )

        attachments = get_message_attachments_by_ids(
            parsed_chat_id,
            attachment_ids
        )

        if len(attachments) != len(attachment_ids):
            return text_error(
                "One or more attachments do not belong to this chat.",
                400
            )

        unavailable = [
            item.original_filename
            for item in attachments
            if item.status != "ready"
        ]

        if unavailable:
            return text_error(
                "These attachments are not ready: " + ", ".join(unavailable),
                409
            )

        total_bytes = sum(item.file_size for item in attachments)
        maximum_total = int(
            current_app.config.get(
                "ATTACHMENT_MAX_TOTAL_BYTES",
                40 * 1024 * 1024
            )
        )
        if total_bytes > maximum_total:
            return text_error(
                "The selected attachments exceed the total size limit.",
                413
            )

        try:
            attachment_context_items = retrieve_attachment_context(
                chat_id=parsed_chat_id,
                query=prompt,
                attachment_ids=attachment_ids
            )
        except Exception:
            current_app.logger.exception(
                "attachment_context_retrieval_failed"
            )
            return text_error(
                "Attachment text could not be retrieved.",
                502
            )

        image_attachments = [
            item for item in attachments
            if item.attachment_kind == "image"
        ]

        if image_attachments:
            try:
                candidate_paths = [
                    attachment_file_path(item.stored_filename)
                    for item in image_attachments
                ]

                if provider_supports_direct_images(get_ai_provider()):
                    image_paths = candidate_paths
                    direct_image_input = True
                    vision_model = None
                else:
                    vision_model = find_vision_model(
                        selected_model=model,
                        preferred_model=current_app.config.get("VISION_MODEL")
                    )

                if vision_model == model and model_supports_vision(model):
                    image_paths = candidate_paths
                    direct_image_input = True
                elif vision_model:
                    vision_text = generate_vision_analysis(
                        model=vision_model,
                        prompt=prompt,
                        image_paths=candidate_paths
                    )
                    context_items.append({
                        "chunk_id": None,
                        "document_id": image_attachments[0].id,
                        "source_scope": "vision",
                        "filename": (
                            image_attachments[0].original_filename
                            if len(image_attachments) == 1
                            else f"{len(image_attachments)} attached images"
                        ),
                        "chunk_index": 0,
                        "content": vision_text,
                        "score": 1.0
                    })
                elif not attachment_context_items:
                    return text_error(
                        "No installed Ollama model supports vision and no readable OCR text was found. Install a vision model such as gemma3 or configure VISION_MODEL.",
                        422
                    )
            except OllamaVisionError as error:
                return text_error(str(error), 502)
            except (OSError, ValueError) as error:
                current_app.logger.exception("attachment_image_prepare_failed")
                return text_error(
                    f"The image attachment could not be prepared: {error}",
                    422
                )

    context_items.extend(attachment_context_items)

    if use_documents:
        if parsed_chat_id is None:
            return text_error(
                (
                    "A chat ID is required when "
                    "document mode is enabled."
                ),
                400
            )

        try:
            knowledge_context_items = (
                retrieve_relevant_context(
                    chat_id=parsed_chat_id,
                    query=prompt,
                    document_ids=document_ids,
                    global_document_ids=(
                        global_document_ids
                    ),
                    website_source_ids=(
                        website_source_ids
                    ),
                    social_source_ids=(
                        social_source_ids
                    ),
                    include_global_documents=(
                        use_global_documents
                    ),
                    include_website_sources=(
                        use_website_sources
                    ),
                    include_social_sources=(
                        use_social_sources
                    )
                )
            )
            context_items.extend(knowledge_context_items)

        except Exception:
            current_app.logger.exception(
                "rag_context_retrieval_failed"
            )

            return text_error(
                (
                    "Document context could not "
                    "be retrieved."
                ),
                502
            )

        if (
            strict_documents
            and not context_items
            and not direct_image_input
        ):
            selected_chat_count = len(
                document_ids or []
            )

            selected_global_count = (
                len(
                    global_document_ids
                    or []
                )
                if use_global_documents
                else 0
            )

            selected_website_count = (
                len(website_source_ids or [])
                if use_website_sources
                else 0
            )

            selected_social_count = (
                len(social_source_ids or [])
                if use_social_sources
                else 0
            )

            if (
                selected_chat_count == 0
                and selected_global_count == 0
                and selected_website_count == 0
                and selected_social_count == 0
                and not attachment_ids
            ):
                message = (
                    "No ready knowledge sources are selected. "
                    "Select a chat document, global file, website page, or social source, "
                    "add a relevant source, or turn off Strict answers."
                )
            else:
                message = (
                    "I could not find enough relevant information in the "
                    "selected knowledge sources to answer this question. "
                    "Try another source, add a more relevant file, website, or social source, "
                    "or turn off Strict answers."
                )

            return Response(
                message,
                mimetype="text/plain",
                headers={
                    "X-RAG-Used": "false",
                    "X-RAG-Status": "no-context"
                }
            )

    if (
        attachment_ids
        and strict_documents
        and not context_items
        and not direct_image_input
    ):
        return Response(
            "I could not find enough readable information in the attached file to answer this question. Try a clearer image, another file, a different question, or turn off Strict answers.",
            mimetype="text/plain",
            headers={
                "X-RAG-Used": "false",
                "X-RAG-Status": "no-attachment-context"
            }
        )

    if context_items:
        final_prompt = build_rag_prompt(
            user_prompt=prompt,
            context_items=context_items,
            strict_mode=strict_documents
        )
    elif direct_image_input:
        final_prompt = (
            "Analyze the attached image or images and answer the user request accurately. "
            "Do not invent details that are not visible.\n\n"
            f"USER REQUEST:\n{prompt}"
        )

    response_headers = {
        "X-RAG-Used": (
            "true"
            if context_items
            else "false"
        )
    }

    if context_items:
        response_headers[
            "X-RAG-Sources"
        ] = encode_sources_header(
            context_items
        )

    request_id = getattr(g, "request_id", None)
    user_id = int(current_user.id) if current_user.is_authenticated else None
    generation_started_at = time.perf_counter()

    @stream_with_context
    def monitored_stream():
        success = False
        error_message = None
        try:
            for chunk in stream_ai_response(
                model=model,
                prompt=final_prompt,
                mode=mode,
                option_number=option_number,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                context_length=context_length,
                image_paths=image_paths
            ):
                yield chunk
            success = True
        except GeneratorExit:
            error_message = "Client disconnected before generation completed."
            raise
        except Exception as error:
            error_message = str(error)
            raise
        finally:
            duration_ms = (time.perf_counter() - generation_started_at) * 1000
            record_model_usage(
                model=model,
                mode=mode,
                duration_ms=duration_ms,
                success=success,
                used_rag=bool(context_items),
                source_count=len(context_items),
                error_message=error_message,
                request_id=request_id,
                chat_id=parsed_chat_id,
                user_id=user_id,
            )

    return Response(
        monitored_stream(),
        mimetype="text/plain",
        headers=response_headers
    )


def text_error(
    message,
    status_code
):
    return Response(
        f"Error: {message}",
        status=status_code,
        mimetype="text/plain"
    )


def parse_float_setting(
    value,
    field_name,
    minimum,
    maximum,
    default
):
    if value in (
        None,
        ""
    ):
        return default

    try:
        parsed = float(
            value
        )

    except (
        TypeError,
        ValueError
    ) as error:
        raise ValueError(
            f"{field_name} must be a number."
        ) from error

    if (
        parsed < minimum
        or parsed > maximum
    ):
        raise ValueError(
            (
                f"{field_name} must be between "
                f"{minimum} and {maximum}."
            )
        )

    return parsed


def parse_int_setting(
    value,
    field_name,
    minimum,
    maximum,
    default
):
    if value in (
        None,
        ""
    ):
        return default

    try:
        parsed = int(
            value
        )

    except (
        TypeError,
        ValueError
    ) as error:
        raise ValueError(
            (
                f"{field_name} must be "
                "a whole number."
            )
        ) from error

    if (
        parsed < minimum
        or parsed > maximum
    ):
        raise ValueError(
            (
                f"{field_name} must be between "
                f"{minimum} and {maximum}."
            )
        )

    return parsed


def normalize_document_ids(
    value
):
    if value is None:
        return None

    if not isinstance(
        value,
        list
    ):
        raise ValueError(
            (
                "Document IDs must be "
                "provided as a list."
            )
        )

    if len(value) > 100:
        raise ValueError(
            (
                "No more than 100 document "
                "IDs may be selected."
            )
        )

    normalized = []

    for document_id in value:
        try:
            parsed_id = int(
                document_id
            )

        except (
            TypeError,
            ValueError
        ) as error:
            raise ValueError(
                (
                    "Every document ID must "
                    "be an integer."
                )
            ) from error

        if parsed_id <= 0:
            raise ValueError(
                (
                    "Every document ID must "
                    "be positive."
                )
            )

        if parsed_id not in normalized:
            normalized.append(
                parsed_id
            )

    return normalized


def parse_boolean(
    value,
    default=False
):
    if value is None:
        return default

    if isinstance(
        value,
        bool
    ):
        return value

    if isinstance(
        value,
        str
    ):
        normalized = (
            value
            .strip()
            .lower()
        )

        if normalized in {
            "1",
            "true",
            "yes",
            "on"
        }:
            return True

        if normalized in {
            "0",
            "false",
            "no",
            "off"
        }:
            return False

    return bool(
        value
    )



def normalize_attachment_ids(value, maximum=5):
    normalized = normalize_document_ids(value)
    if normalized is None:
        return []
    if len(normalized) > int(maximum):
        raise ValueError(
            f"No more than {int(maximum)} attachments may be used in one message."
        )
    return normalized


def attachment_file_path(stored_filename):
    import os

    upload_folder = os.path.abspath(
        current_app.config["UPLOAD_FOLDER"]
    )
    path = os.path.abspath(
        os.path.join(upload_folder, stored_filename)
    )
    if os.path.commonpath([path, upload_folder]) != upload_folder:
        raise ValueError("Unsafe attachment filename.")
    if not os.path.isfile(path):
        raise OSError("Attachment file is missing.")
    return path

def encode_sources_header(
    context_items
):
    sources = []

    for item in context_items:
        excerpt = re.sub(
            r"\s+",
            " ",
            item["content"]
        ).strip()

        if len(excerpt) > 320:
            excerpt = (
                excerpt[:317].rstrip()
                + "..."
            )

        sources.append({
            "document_id": item.get("document_id"),
            "source_scope": item.get(
                "source_scope",
                "chat"
            ),
            "filename": item[
                "filename"
            ],
            "source_url": item.get(
                "source_url"
            ),
            "platform": item.get("platform"),
            "chunk_index": item.get("chunk_index", 0),
            "score": round(
                float(
                    item["score"]
                ),
                4
            ),
            "excerpt": excerpt
        })

    raw_json = json.dumps(
        sources,
        ensure_ascii=False,
        separators=(
            ",",
            ":"
        )
    ).encode(
        "utf-8"
    )

    return (
        base64
        .urlsafe_b64encode(
            raw_json
        )
        .decode(
            "ascii"
        )
        .rstrip(
            "="
        )
    )
