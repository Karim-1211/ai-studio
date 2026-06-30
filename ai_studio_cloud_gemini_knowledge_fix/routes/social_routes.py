from flask import Blueprint, current_app, request
from sqlalchemy.exc import IntegrityError

from database import db
from database.crud import (
    add_social_source_to_user,
    create_social_source,
    create_social_source_chunks,
    delete_social_source,
    get_all_social_sources,
    get_social_source_by_id,
    get_social_source_by_url,
    get_shared_social_source_by_url,
    replace_social_source_content,
    update_social_source_status
)
from services.api_utils import error_response
from services.document_service import split_text_into_chunks
from services.embedding_service import (
    EmbeddingServiceError,
    generate_embeddings
)
from services.social_service import (
    SocialSourceError,
    normalize_social_url,
    prepare_social_content,
    suggested_social_title
)


social_routes = Blueprint("social_routes", __name__)


def social_source_to_dict(source):
    return {
        "id": source.id,
        "scope": "social",
        "url": source.url,
        "canonical_url": source.canonical_url,
        "title": source.title,
        "platform": source.platform,
        "domain": source.domain,
        "extraction_method": source.extraction_method,
        "status": source.status,
        "error_message": source.error_message,
        "chunk_count": source.chunk_count,
        "text_length": source.text_length,
        "http_status": source.http_status,
        "content_type": source.content_type,
        "fetched_at": source.fetched_at.isoformat() if source.fetched_at else None,
        "created_at": source.created_at.isoformat() if source.created_at else None,
        "updated_at": source.updated_at.isoformat() if source.updated_at else None
    }


@social_routes.route("/api/social-sources", methods=["GET"])
def list_social_sources():
    return [
        social_source_to_dict(source)
        for source in get_all_social_sources()
    ]


@social_routes.route("/api/social-sources", methods=["POST"])
def add_social_source():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return error_response(
            "A JSON object is required.",
            400,
            "invalid_json_body"
        )

    manual_text = str(data.get("manual_text") or "")
    requested_mode = data.get("import_mode")
    import_mode = str(
        requested_mode
        or ("manual" if manual_text.strip() else "public")
    ).strip().lower()
    if import_mode not in {"public", "manual"}:
        return error_response(
            "import_mode must be public or manual.",
            400,
            "invalid_social_import_mode"
        )

    try:
        normalized_url, platform = normalize_social_url(data.get("url"))
    except SocialSourceError as error:
        return social_error_response(error)

    supplied_title = str(data.get("title") or "")
    existing = get_social_source_by_url(normalized_url)

    if import_mode == "public" and existing and existing.status == "ready":
        return {
            "message": "This social source is already available.",
            "social_source": social_source_to_dict(existing),
            "already_exists": True,
        }, 200

    try:
        result = prepare_social_content(
            raw_url=normalized_url,
            settings=current_app.config,
            manual_text=manual_text if import_mode == "manual" else "",
            supplied_title=supplied_title
        )
    except SocialSourceError as error:
        manual_required_codes = {
            "social_public_fetch_failed",
            "facebook_share_link_manual_required",
            "google_places_api_key_required",
            "google_business_query_missing",
            "google_business_not_found",
            "google_business_redirect_failed",
            "google_business_redirect_invalid",
            "google_business_text_too_short",
        }
        if (
            import_mode == "public"
            and getattr(error, "error_code", "") in manual_required_codes
        ):
            return {
                "message": str(error),
                "code": "social_manual_required",
                "reason_code": getattr(error, "error_code", ""),
                "manual_required": True,
                "url": normalized_url,
                "platform": platform,
                "suggested_title": suggested_social_title(
                    platform,
                    normalized_url,
                ),
                "minimum_characters": int(
                    current_app.config.get("SOCIAL_MIN_TEXT_CHARACTERS", 40)
                ),
                "details": str(error),
            }, 202
        return social_error_response(error)

    source = None

    try:
        duplicate = get_social_source_by_url(result["canonical_url"])
        if duplicate:
            existing = duplicate

        chunks = split_text_into_chunks(
            result["text"],
            chunk_size=current_app.config["RAG_CHUNK_SIZE"],
            overlap=current_app.config["RAG_CHUNK_OVERLAP"]
        )

        if not chunks:
            raise SocialSourceError(
                "The social source did not produce searchable content.",
                422,
                "social_chunks_empty"
            )

        embeddings = generate_embeddings(chunks)

        if existing:
            source = replace_social_source_content(
                source_id=existing.id,
                chunks=chunks,
                embeddings=embeddings,
                title=result["title"],
                canonical_url=result["canonical_url"],
                domain=result["domain"],
                text_length=len(result["text"]),
                extraction_method=result["extraction_method"],
                http_status=result["http_status"],
                content_type=result["content_type"],
                fetched_at=result["fetched_at"]
            )
            return {
                "message": "Social source updated and selected successfully.",
                "social_source": social_source_to_dict(source),
                "updated": True,
            }, 200

        shared = get_shared_social_source_by_url(result["canonical_url"])
        if shared:
            add_social_source_to_user(shared)
            return {
                "message": "Social source added to this workspace.",
                "social_source": social_source_to_dict(shared)
            }, 201

        source = create_social_source(
            url=result["url"],
            canonical_url=result["canonical_url"],
            title=result["title"],
            platform=result["platform"],
            domain=result["domain"],
            extraction_method=result["extraction_method"],
            status="processing",
            http_status=result["http_status"],
            content_type=result["content_type"],
            fetched_at=result["fetched_at"]
        )

        create_social_source_chunks(
            source_id=source.id,
            chunks=chunks,
            embeddings=embeddings
        )

        source = update_social_source_status(
            source_id=source.id,
            status="ready",
            error_message=None,
            chunk_count=len(chunks),
            text_length=len(result["text"]),
            title=result["title"],
            canonical_url=result["canonical_url"],
            domain=result["domain"],
            extraction_method=result["extraction_method"],
            http_status=result["http_status"],
            content_type=result["content_type"],
            fetched_at=result["fetched_at"]
        )

        return {
            "message": "Social source indexed and selected successfully.",
            "social_source": social_source_to_dict(source)
        }, 201

    except SocialSourceError as error:
        return social_error_response(error)
    except EmbeddingServiceError as error:
        return error_response(
            "Social source embeddings could not be generated.",
            502,
            "social_embedding_failed",
            str(error)
        )
    except IntegrityError:
        db.session.rollback()
        return error_response(
            "This social link already exists. Refresh the source list and try again.",
            409,
            "social_source_exists"
        )
    except Exception as error:
        db.session.rollback()
        if source is not None:
            try:
                update_social_source_status(
                    source_id=source.id,
                    status="failed",
                    error_message=str(error)
                )
            except Exception:
                db.session.rollback()
        current_app.logger.exception("social_source_create_failed")
        return error_response(
            "The social source could not be indexed.",
            500,
            "social_source_create_failed",
            str(error)
        )


@social_routes.route(
    "/api/social-sources/<int:source_id>/refresh",
    methods=["POST"]
)
def refresh_social_source(source_id):
    source = get_social_source_by_id(source_id)

    if not source:
        return error_response(
            "Social source not found.",
            404,
            "social_source_not_found"
        )

    if source.extraction_method == "manual":
        return error_response(
            "Manually pasted social content cannot be refreshed automatically. Delete it and add the updated text again.",
            409,
            "manual_social_refresh_not_supported"
        )

    try:
        refresh_title = source.title or ""
        if refresh_title.startswith("Google Business Profile · "):
            refresh_title = refresh_title.split(" · ", 1)[1]

        result = prepare_social_content(
            raw_url=source.canonical_url or source.url,
            settings=current_app.config,
            supplied_title=refresh_title
        )

        duplicate = get_social_source_by_url(result["canonical_url"])
        if duplicate and duplicate.id != source.id:
            return error_response(
                "The refreshed social link already exists as another source.",
                409,
                "social_source_exists"
            )

        chunks = split_text_into_chunks(
            result["text"],
            chunk_size=current_app.config["RAG_CHUNK_SIZE"],
            overlap=current_app.config["RAG_CHUNK_OVERLAP"]
        )
        if not chunks:
            raise SocialSourceError(
                "The social source did not produce searchable content.",
                422,
                "social_chunks_empty"
            )

        embeddings = generate_embeddings(chunks)
        source = replace_social_source_content(
            source_id=source.id,
            chunks=chunks,
            embeddings=embeddings,
            title=result["title"],
            canonical_url=result["canonical_url"],
            domain=result["domain"],
            text_length=len(result["text"]),
            extraction_method=result["extraction_method"],
            http_status=result["http_status"],
            content_type=result["content_type"],
            fetched_at=result["fetched_at"]
        )

        return {
            "message": "Social source refreshed successfully.",
            "social_source": social_source_to_dict(source)
        }
    except SocialSourceError as error:
        return social_error_response(error)
    except EmbeddingServiceError as error:
        return error_response(
            "Social source embeddings could not be regenerated.",
            502,
            "social_embedding_failed",
            str(error)
        )
    except Exception as error:
        db.session.rollback()
        current_app.logger.exception("social_source_refresh_failed")
        return error_response(
            "The social source could not be refreshed.",
            500,
            "social_source_refresh_failed",
            str(error)
        )


@social_routes.route("/api/social-sources/<int:source_id>", methods=["DELETE"])
def remove_social_source(source_id):
    source = get_social_source_by_id(source_id)
    if not source:
        return error_response(
            "Social source not found.",
            404,
            "social_source_not_found"
        )

    delete_social_source(source_id)
    return {"message": "Social source deleted successfully."}


def social_error_response(error):
    return error_response(
        str(error),
        getattr(error, "status_code", 422),
        getattr(error, "error_code", "social_source_error")
    )
