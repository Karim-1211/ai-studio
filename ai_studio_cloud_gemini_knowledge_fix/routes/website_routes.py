from flask import Blueprint, current_app, request
from sqlalchemy.exc import IntegrityError

from database import db
from database.crud import (
    add_website_source_to_user,
    create_website_source,
    create_website_source_chunks,
    delete_website_source,
    get_all_website_sources,
    get_website_source_by_id,
    get_website_source_by_url,
    get_shared_website_source_by_url,
    replace_website_source_content,
    update_website_source_status,
)
from services.api_utils import error_response
from services.document_service import split_text_into_chunks
from services.embedding_service import (
    EmbeddingServiceError,
    generate_embeddings,
)
from services.website_service import (
    WebsiteSourceError,
    fetch_website_content,
    normalize_website_url,
)


website_routes = Blueprint(
    "website_routes",
    __name__,
)


def website_source_to_dict(source):
    return {
        "id": source.id,
        "scope": "website",
        "url": source.url,
        "canonical_url": source.canonical_url,
        "title": source.title,
        "domain": source.domain,
        "status": source.status,
        "error_message": source.error_message,
        "chunk_count": source.chunk_count,
        "text_length": source.text_length,
        "http_status": source.http_status,
        "content_type": source.content_type,
        "fetched_at": (
            source.fetched_at.isoformat()
            if source.fetched_at
            else None
        ),
        "created_at": (
            source.created_at.isoformat()
            if source.created_at
            else None
        ),
        "updated_at": (
            source.updated_at.isoformat()
            if source.updated_at
            else None
        ),
    }


def build_website_chunks(result):
    chunks = split_text_into_chunks(
        result["text"],
        chunk_size=current_app.config["RAG_CHUNK_SIZE"],
        overlap=current_app.config["RAG_CHUNK_OVERLAP"],
    )

    if not chunks:
        raise WebsiteSourceError(
            "The webpage did not produce any searchable text chunks.",
            422,
            "website_chunks_empty",
        )

    embeddings = generate_embeddings(chunks)
    return chunks, embeddings


def index_website_url(raw_url):
    normalized_url = normalize_website_url(raw_url)

    existing = get_website_source_by_url(normalized_url)
    if existing:
        return existing, False

    shared = get_shared_website_source_by_url(normalized_url)
    if shared:
        add_website_source_to_user(shared)
        return shared, True

    result = fetch_website_content(
        normalized_url,
        current_app.config,
    )

    duplicate = get_website_source_by_url(
        result["canonical_url"]
    )
    if duplicate:
        return duplicate, False

    shared = get_shared_website_source_by_url(
        result["canonical_url"]
    )
    if shared:
        add_website_source_to_user(shared)
        return shared, True

    chunks, embeddings = build_website_chunks(result)
    source = None

    try:
        source = create_website_source(
            url=result["url"],
            canonical_url=result["canonical_url"],
            title=result["title"],
            domain=result["domain"],
            status="processing",
            http_status=result["http_status"],
            content_type=result["content_type"],
            fetched_at=result["fetched_at"],
        )

        create_website_source_chunks(
            website_source_id=source.id,
            chunks=chunks,
            embeddings=embeddings,
        )

        source = update_website_source_status(
            website_source_id=source.id,
            status="ready",
            error_message=None,
            chunk_count=len(chunks),
            text_length=len(result["text"]),
            title=result["title"],
            canonical_url=result["canonical_url"],
            domain=result["domain"],
            http_status=result["http_status"],
            content_type=result["content_type"],
            fetched_at=result["fetched_at"],
        )

        return source, True

    except Exception as error:
        db.session.rollback()

        if source is not None:
            try:
                update_website_source_status(
                    website_source_id=source.id,
                    status="failed",
                    error_message=str(error),
                )
            except Exception:
                db.session.rollback()

        raise


def refresh_website_source_record(source):
    result = fetch_website_content(
        source.canonical_url or source.url,
        current_app.config,
    )

    duplicate = get_website_source_by_url(
        result["canonical_url"]
    )

    if duplicate and duplicate.id != source.id:
        raise WebsiteSourceError(
            "The refreshed page redirects to a website source that already exists.",
            409,
            "website_source_exists",
        )

    chunks, embeddings = build_website_chunks(result)

    return replace_website_source_content(
        website_source_id=source.id,
        chunks=chunks,
        embeddings=embeddings,
        title=result["title"],
        canonical_url=result["canonical_url"],
        domain=result["domain"],
        text_length=len(result["text"]),
        http_status=result["http_status"],
        content_type=result["content_type"],
        fetched_at=result["fetched_at"],
    )


@website_routes.route(
    "/api/website-sources",
    methods=["GET"],
)
def list_website_sources():
    return [
        website_source_to_dict(source)
        for source in get_all_website_sources()
    ]


@website_routes.route(
    "/api/website-sources",
    methods=["POST"],
)
def add_website_source():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return error_response(
            "A JSON object is required.",
            400,
            "invalid_json_body",
        )

    try:
        source, created = index_website_url(
            data.get("url")
        )

        if not created:
            return error_response(
                "This website page is already in the global library.",
                409,
                "website_source_exists",
            )

        return {
            "message": "Website page indexed and selected successfully.",
            "website": website_source_to_dict(source),
        }, 201

    except WebsiteSourceError as error:
        return website_error_response(error)

    except EmbeddingServiceError as error:
        return error_response(
            "Website embeddings could not be generated.",
            502,
            "website_embedding_failed",
            str(error),
        )

    except IntegrityError:
        db.session.rollback()
        return error_response(
            "This website page is already in the global library.",
            409,
            "website_source_exists",
        )

    except Exception as error:
        db.session.rollback()
        current_app.logger.exception(
            "website_source_create_failed"
        )
        return error_response(
            "The website page could not be indexed.",
            500,
            "website_source_create_failed",
            str(error),
        )


@website_routes.route(
    "/api/website-sources/<int:website_source_id>/refresh",
    methods=["POST"],
)
def refresh_website_source(website_source_id):
    source = get_website_source_by_id(
        website_source_id
    )

    if not source:
        return error_response(
            "Website source not found.",
            404,
            "website_source_not_found",
        )

    try:
        source = refresh_website_source_record(source)
        return {
            "message": "Website page refreshed successfully.",
            "website": website_source_to_dict(source),
        }

    except WebsiteSourceError as error:
        return website_error_response(error)

    except EmbeddingServiceError as error:
        return error_response(
            "Website embeddings could not be regenerated.",
            502,
            "website_embedding_failed",
            str(error),
        )

    except IntegrityError:
        db.session.rollback()
        return error_response(
            "The refreshed page conflicts with another website source.",
            409,
            "website_source_exists",
        )

    except Exception as error:
        db.session.rollback()
        current_app.logger.exception(
            "website_source_refresh_failed"
        )
        return error_response(
            "The website page could not be refreshed.",
            500,
            "website_source_refresh_failed",
            str(error),
        )


@website_routes.route(
    "/api/website-sources/<int:website_source_id>",
    methods=["DELETE"],
)
def remove_website_source(website_source_id):
    source = get_website_source_by_id(
        website_source_id
    )

    if not source:
        return error_response(
            "Website source not found.",
            404,
            "website_source_not_found",
        )

    delete_website_source(website_source_id)

    return {
        "message": "Website source deleted successfully."
    }


def website_error_response(error):
    return error_response(
        str(error),
        getattr(error, "status_code", 422),
        getattr(
            error,
            "error_code",
            "website_source_error",
        ),
    )
