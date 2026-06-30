import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, unquote_plus, urlsplit

import requests

from services.website_service import (
    WebsiteSourceError,
    normalize_website_url,
    request_with_safe_redirects,
    validate_website_url_for_fetch,
)


GOOGLE_BUSINESS_PLATFORM = "Google Business Profile"
GOOGLE_BUSINESS_HOSTS = {
    "google.com",
    "maps.google.com",
    "maps.app.goo.gl",
    "goo.gl",
    "g.page",
}


class GoogleBusinessSourceError(Exception):
    def __init__(
        self,
        message,
        status_code=422,
        error_code="google_business_source_error",
    ):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


def is_google_business_profile_url(raw_url):
    try:
        parsed = urlsplit(str(raw_url or ""))
    except ValueError:
        return False

    hostname = (parsed.hostname or "").lower().rstrip(".")
    path = parsed.path or "/"

    if hostname.startswith("www."):
        hostname = hostname[4:]

    if hostname in {"maps.app.goo.gl", "goo.gl", "g.page", "maps.google.com"}:
        return True

    return (
        hostname == "google.com"
        or hostname.endswith(".google.com")
    ) and (
        path.startswith("/maps")
        or path.startswith("/local")
        or "maps" in parsed.query.lower()
    )


def prepare_google_business_content(
    raw_url,
    settings,
    supplied_title="",
):
    normalized_url = _normalize_google_business_url(raw_url)
    api_key = str(settings.get("GOOGLE_MAPS_API_KEY") or "").strip()

    if not api_key:
        raise GoogleBusinessSourceError(
            "Automatic Google Business Profile import requires a Google Maps Platform API key with Places API enabled. You can still paste the visible business details below and index them manually.",
            422,
            "google_places_api_key_required",
        )

    resolved_url = _resolve_google_maps_url(normalized_url, settings)
    query = _extract_business_query(resolved_url, supplied_title)

    if not query:
        raise GoogleBusinessSourceError(
            "The business name could not be read from this Google Maps link. Enter the business name in Source title, then try again, or paste the visible business details below.",
            422,
            "google_business_query_missing",
        )

    place = _search_place(query, api_key, settings)
    details = _fetch_place_details(place["id"], api_key, settings)
    text = _build_business_text(details, settings)

    if len(text) < int(settings.get("SOCIAL_MIN_TEXT_CHARACTERS", 40)):
        raise GoogleBusinessSourceError(
            "Google Places returned too little readable business information to index.",
            422,
            "google_business_text_too_short",
        )

    display_name = _localized_text(details.get("displayName")) or query
    canonical_url = (
        str(details.get("googleMapsUri") or "").strip()
        or resolved_url
        or normalized_url
    )

    return {
        "url": normalized_url,
        "canonical_url": canonical_url,
        "title": f"Google Business Profile · {display_name}"[:500],
        "platform": GOOGLE_BUSINESS_PLATFORM,
        "domain": urlsplit(canonical_url).hostname or "google.com",
        "text": text,
        "extraction_method": "google_places_api",
        "http_status": 200,
        "content_type": "application/json",
        "fetched_at": datetime.now(timezone.utc).replace(tzinfo=None),
    }


def _normalize_google_business_url(raw_url):
    try:
        normalized = normalize_website_url(raw_url)
    except WebsiteSourceError as error:
        raise GoogleBusinessSourceError(
            str(error),
            getattr(error, "status_code", 400),
            getattr(error, "error_code", "invalid_google_business_url"),
        ) from error

    if not is_google_business_profile_url(normalized):
        raise GoogleBusinessSourceError(
            "Use a Google Maps or Google Business Profile link.",
            400,
            "invalid_google_business_url",
        )

    return normalized


def _resolve_google_maps_url(url, settings):
    parsed = urlsplit(url)
    hostname = (parsed.hostname or "").lower().rstrip(".")

    if hostname.startswith("www."):
        hostname = hostname[4:]

    if hostname not in {"maps.app.goo.gl", "goo.gl", "g.page"}:
        return url

    timeout = (
        float(settings.get("WEBSITE_CONNECT_TIMEOUT", 5.0)),
        float(settings.get("WEBSITE_READ_TIMEOUT", 15.0)),
    )
    maximum_redirects = int(settings.get("WEBSITE_MAX_REDIRECTS", 3))

    session = requests.Session()
    session.headers.update({
        "User-Agent": str(
            settings.get(
                "WEBSITE_USER_AGENT",
                "AI-Studio-KnowledgeIndexer/1.0",
            )
        ),
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
    })

    try:
        response, final_url = request_with_safe_redirects(
            session=session,
            url=validate_website_url_for_fetch(url),
            timeout=timeout,
            maximum_redirects=maximum_redirects,
        )
    except WebsiteSourceError as error:
        raise GoogleBusinessSourceError(
            "The Google Maps share link could not be resolved.",
            getattr(error, "status_code", 422),
            "google_business_redirect_failed",
        ) from error

    response.close()

    if not is_google_business_profile_url(final_url):
        raise GoogleBusinessSourceError(
            "The Google Maps share link redirected outside Google Maps.",
            422,
            "google_business_redirect_invalid",
        )

    return final_url


def _extract_business_query(url, supplied_title=""):
    title = re.sub(r"\s+", " ", str(supplied_title or "")).strip()
    if title:
        return title[:250]

    parsed = urlsplit(url)
    query_values = parse_qs(parsed.query)

    for key in ("query", "q"):
        values = query_values.get(key)
        if values:
            candidate = re.sub(r"\s+", " ", unquote_plus(values[0])).strip()
            if candidate:
                return candidate[:250]

    path_parts = [part for part in parsed.path.split("/") if part]

    for marker in ("place", "search"):
        if marker in path_parts:
            index = path_parts.index(marker)
            if index + 1 < len(path_parts):
                candidate = unquote_plus(path_parts[index + 1])
                candidate = re.sub(r"\s+", " ", candidate).strip()
                if candidate and not candidate.startswith("@"): 
                    return candidate[:250]

    return ""


def _search_place(query, api_key, settings):
    endpoint = "https://places.googleapis.com/v1/places:searchText"
    timeout = (
        float(settings.get("WEBSITE_CONNECT_TIMEOUT", 5.0)),
        float(settings.get("WEBSITE_READ_TIMEOUT", 15.0)),
    )
    language_code = str(settings.get("GOOGLE_PLACES_LANGUAGE_CODE") or "en").strip()

    payload = {"textQuery": query}
    if language_code:
        payload["languageCode"] = language_code

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.formattedAddress,"
            "places.googleMapsUri"
        ),
    }

    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=timeout,
        )
    except requests.Timeout as error:
        raise GoogleBusinessSourceError(
            "Google Places took too long to respond.",
            504,
            "google_places_timeout",
        ) from error
    except requests.RequestException as error:
        raise GoogleBusinessSourceError(
            "Google Places could not be contacted.",
            502,
            "google_places_request_failed",
        ) from error

    data = _read_google_json(response)
    places = data.get("places") or []

    if not places:
        raise GoogleBusinessSourceError(
            "Google Places could not find a business matching this link or title.",
            404,
            "google_business_not_found",
        )

    return places[0]


def _fetch_place_details(place_id, api_key, settings):
    endpoint = f"https://places.googleapis.com/v1/places/{place_id}"
    timeout = (
        float(settings.get("WEBSITE_CONNECT_TIMEOUT", 5.0)),
        float(settings.get("WEBSITE_READ_TIMEOUT", 15.0)),
    )
    language_code = str(settings.get("GOOGLE_PLACES_LANGUAGE_CODE") or "en").strip()

    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "id,displayName,formattedAddress,nationalPhoneNumber,"
            "internationalPhoneNumber,websiteUri,googleMapsUri,rating,"
            "userRatingCount,businessStatus,types,regularOpeningHours,"
            "editorialSummary,reviews"
        ),
    }
    params = {}
    if language_code:
        params["languageCode"] = language_code

    try:
        response = requests.get(
            endpoint,
            params=params,
            headers=headers,
            timeout=timeout,
        )
    except requests.Timeout as error:
        raise GoogleBusinessSourceError(
            "Google Places took too long to return business details.",
            504,
            "google_places_timeout",
        ) from error
    except requests.RequestException as error:
        raise GoogleBusinessSourceError(
            "Google Places business details could not be downloaded.",
            502,
            "google_places_request_failed",
        ) from error

    return _read_google_json(response)


def _read_google_json(response):
    try:
        data = response.json()
    except ValueError as error:
        raise GoogleBusinessSourceError(
            "Google Places returned an unreadable response.",
            502,
            "google_places_invalid_response",
        ) from error

    if response.ok:
        return data

    error_payload = data.get("error") or {}
    message = str(error_payload.get("message") or "").strip()
    status = str(error_payload.get("status") or "").strip()

    if response.status_code in {401, 403}:
        friendly = (
            "Google Places rejected the API request. Confirm that GOOGLE_MAPS_API_KEY is correct, Places API is enabled, billing is active, and the key restrictions allow Places API."
        )
    else:
        friendly = "Google Places could not import this business profile."

    details = ": ".join(item for item in (status, message) if item)
    if details:
        friendly = f"{friendly} {details}"

    raise GoogleBusinessSourceError(
        friendly,
        response.status_code if response.status_code >= 400 else 502,
        "google_places_api_error",
    )


def _build_business_text(details, settings):
    lines = ["Google Business Profile"]
    name = _localized_text(details.get("displayName"))
    summary = _localized_text(details.get("editorialSummary"))

    _append_field(lines, "Business name", name)
    _append_field(lines, "Address", details.get("formattedAddress"))
    _append_field(
        lines,
        "Phone",
        details.get("internationalPhoneNumber")
        or details.get("nationalPhoneNumber"),
    )
    _append_field(lines, "Website", details.get("websiteUri"))
    _append_field(lines, "Google Maps", details.get("googleMapsUri"))
    _append_field(lines, "Business status", details.get("businessStatus"))

    types = details.get("types") or []
    if types:
        cleaned_types = [str(item).replace("_", " ") for item in types]
        _append_field(lines, "Categories", ", ".join(cleaned_types))

    rating = details.get("rating")
    rating_count = details.get("userRatingCount")
    if rating is not None:
        rating_text = f"{rating} out of 5"
        if rating_count is not None:
            rating_text += f" from {rating_count} ratings"
        _append_field(lines, "Rating", rating_text)

    _append_field(lines, "Business summary", summary)

    opening_hours = details.get("regularOpeningHours") or {}
    weekday_descriptions = opening_hours.get("weekdayDescriptions") or []
    if weekday_descriptions:
        lines.append("Opening hours:")
        lines.extend(f"- {item}" for item in weekday_descriptions)

    reviews = details.get("reviews") or []
    maximum_reviews = int(settings.get("GOOGLE_PLACES_MAX_REVIEWS", 5))
    selected_reviews = reviews[:maximum_reviews]

    if selected_reviews:
        lines.append("Selected public reviews:")
        for review in selected_reviews:
            text = _localized_text(review.get("text"))
            if not text:
                continue
            rating_value = review.get("rating")
            author = (
                (review.get("authorAttribution") or {}).get("displayName")
                or "Google user"
            )
            prefix = f"- {author}"
            if rating_value is not None:
                prefix += f" ({rating_value}/5)"
            lines.append(f"{prefix}: {text}")

    return "\n".join(str(line).strip() for line in lines if str(line).strip())


def _append_field(lines, label, value):
    cleaned = str(value or "").strip()
    if cleaned:
        lines.append(f"{label}: {cleaned}")


def _localized_text(value):
    if isinstance(value, dict):
        return str(value.get("text") or "").strip()
    return str(value or "").strip()
