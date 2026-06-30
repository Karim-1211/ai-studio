import re
from urllib.parse import urlsplit

from flask import Blueprint, current_app, request
from sqlalchemy.exc import IntegrityError

from database import db
from database.crud import (
    delete_website_sources_by_domain,
    get_website_source_by_url,
    get_website_sources_by_domain,
)
from routes.website_routes import (
    index_website_url,
    refresh_website_source_record,
    website_source_to_dict,
)
from services.api_utils import error_response
from services.crawler_service import discover_website_pages
from services.embedding_service import EmbeddingServiceError
from services.website_service import (
    WebsiteSourceError,
    normalize_website_url,
)


crawler_routes = Blueprint(
    "crawler_routes",
    __name__,
)


@crawler_routes.route(
    "/api/website-crawler/discover",
    methods=["POST"],
)
def discover_website():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return error_response(
            "A JSON object is required.",
            400,
            "invalid_json_body",
        )

    try:
        result = discover_website_pages(
            raw_url=data.get("url"),
            settings=current_app.config,
            max_pages=data.get("max_pages"),
            max_depth=data.get("max_depth"),
            use_sitemap=data.get("use_sitemap", True) is not False,
        )

        for page in result["pages"]:
            existing = get_website_source_by_url(page["url"])
            page["already_indexed"] = existing is not None
            page["website_source_id"] = (
                existing.id if existing else None
            )

        return result

    except WebsiteSourceError as error:
        return crawler_error_response(error)

    except Exception as error:
        current_app.logger.exception(
            "website_crawler_discovery_failed"
        )
        return error_response(
            "The website pages could not be discovered.",
            500,
            "website_crawler_discovery_failed",
            str(error),
        )


@crawler_routes.route(
    "/api/website-crawler/index",
    methods=["POST"],
)
def index_discovered_pages():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return error_response(
            "A JSON object is required.",
            400,
            "invalid_json_body",
        )

    urls = data.get("urls")

    if not isinstance(urls, list) or not urls:
        return error_response(
            "Select at least one discovered page to index.",
            400,
            "website_crawler_urls_required",
        )

    maximum_pages = int(
        current_app.config.get(
            "WEBSITE_CRAWLER_MAX_PAGES",
            100,
        )
    )

    if len(urls) > maximum_pages:
        return error_response(
            f"A maximum of {maximum_pages} pages can be indexed at once.",
            400,
            "website_crawler_page_limit",
        )

    normalized_urls = []
    hostnames = set()

    try:
        for raw_url in urls:
            normalized = normalize_website_url(raw_url)
            normalized_urls.append(normalized)
            hostnames.add(
                (urlsplit(normalized).hostname or "").lower()
            )
    except WebsiteSourceError as error:
        return crawler_error_response(error)

    if len(hostnames) != 1:
        return error_response(
            "All selected pages must belong to the same website domain.",
            400,
            "website_crawler_mixed_domains",
        )

    created_sources = []
    existing_sources = []
    failures = []

    for page_url in dict.fromkeys(normalized_urls):
        try:
            source, created = index_website_url(page_url)

            if created:
                created_sources.append(
                    website_source_to_dict(source)
                )
            else:
                existing_sources.append(
                    website_source_to_dict(source)
                )

        except WebsiteSourceError as error:
            failures.append({
                "url": page_url,
                "error": str(error),
                "code": error.error_code,
            })
        except EmbeddingServiceError as error:
            failures.append({
                "url": page_url,
                "error": str(error),
                "code": "website_embedding_failed",
            })
        except IntegrityError:
            db.session.rollback()
            existing = get_website_source_by_url(page_url)
            if existing:
                existing_sources.append(
                    website_source_to_dict(existing)
                )
            else:
                failures.append({
                    "url": page_url,
                    "error": "The page conflicts with an existing website source.",
                    "code": "website_source_exists",
                })
        except Exception as error:
            db.session.rollback()
            current_app.logger.exception(
                "website_crawler_index_page_failed",
                extra={"page_url": page_url},
            )
            failures.append({
                "url": page_url,
                "error": str(error),
                "code": "website_crawler_index_failed",
            })

    if not created_sources and not existing_sources:
        return error_response(
            "None of the selected pages could be indexed.",
            422,
            "website_crawler_index_failed",
            failures,
        )

    return {
        "message": _batch_index_message(
            len(created_sources),
            len(existing_sources),
            len(failures),
        ),
        "created": created_sources,
        "existing": existing_sources,
        "failures": failures,
        "created_count": len(created_sources),
        "existing_count": len(existing_sources),
        "failed_count": len(failures),
    }


@crawler_routes.route(
    "/api/website-crawler/sites/<domain>/refresh",
    methods=["POST"],
)
def refresh_website_domain(domain):
    normalized_domain = normalize_domain(domain)
    if not normalized_domain:
        return error_response(
            "A valid website domain is required.",
            400,
            "invalid_website_domain",
        )

    sources = get_website_sources_by_domain(
        normalized_domain
    )

    if not sources:
        return error_response(
            "No indexed website pages were found for this domain.",
            404,
            "website_domain_not_found",
        )

    refreshed = []
    failures = []

    for source in sources:
        try:
            refreshed_source = refresh_website_source_record(source)
            refreshed.append(
                website_source_to_dict(refreshed_source)
            )
        except Exception as error:
            db.session.rollback()
            failures.append({
                "id": source.id,
                "url": source.canonical_url or source.url,
                "error": str(error),
            })

    if not refreshed:
        return error_response(
            "The website pages could not be refreshed.",
            422,
            "website_domain_refresh_failed",
            failures,
        )

    return {
        "message": (
            f"Refreshed {len(refreshed)} page"
            f"{'s' if len(refreshed) != 1 else ''}."
        ),
        "refreshed": refreshed,
        "failures": failures,
    }


@crawler_routes.route(
    "/api/website-crawler/sites/<domain>",
    methods=["DELETE"],
)
def delete_website_domain(domain):
    normalized_domain = normalize_domain(domain)
    if not normalized_domain:
        return error_response(
            "A valid website domain is required.",
            400,
            "invalid_website_domain",
        )

    deleted_ids = delete_website_sources_by_domain(
        normalized_domain
    )

    if not deleted_ids:
        return error_response(
            "No indexed website pages were found for this domain.",
            404,
            "website_domain_not_found",
        )

    return {
        "message": (
            f"Deleted {len(deleted_ids)} indexed page"
            f"{'s' if len(deleted_ids) != 1 else ''} from {normalized_domain}."
        ),
        "deleted_ids": deleted_ids,
    }


def normalize_domain(value):
    normalized = str(value or "").strip().lower().rstrip(".")

    if not normalized or len(normalized) > 255:
        return None

    if not re.fullmatch(r"[a-z0-9.-]+", normalized):
        return None

    if normalized.startswith(".") or ".." in normalized:
        return None

    return normalized


def crawler_error_response(error):
    return error_response(
        str(error),
        getattr(error, "status_code", 422),
        getattr(
            error,
            "error_code",
            "website_crawler_error",
        ),
    )


def _batch_index_message(created, existing, failed):
    parts = []

    if created:
        parts.append(
            f"{created} page{'s' if created != 1 else ''} indexed"
        )
    if existing:
        parts.append(
            f"{existing} already indexed"
        )
    if failed:
        parts.append(
            f"{failed} failed"
        )

    return ", ".join(parts).capitalize() + "."
