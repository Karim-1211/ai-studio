import re
from datetime import datetime, timezone
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

from services.google_business_service import (
    GOOGLE_BUSINESS_PLATFORM,
    GoogleBusinessSourceError,
    is_google_business_profile_url,
    prepare_google_business_content,
)
from services.website_service import (
    WebsiteSourceError,
    fetch_website_content,
    normalize_website_url,
)


SOCIAL_PLATFORM_DOMAINS = {
    "Facebook": {
        "facebook.com",
        "fb.com",
    },
    "Instagram": {
        "instagram.com",
    },
    "X": {
        "x.com",
        "twitter.com",
    },
    "TikTok": {
        "tiktok.com",
    },
    "LinkedIn": {
        "linkedin.com",
    },
    "YouTube": {
        "youtube.com",
        "youtu.be",
    },
    "Threads": {
        "threads.net",
    },
    "Bluesky": {
        "bsky.app",
    },
}

TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "igsh",
    "igshid",
    "li_fat_id",
    "mibextid",
    "si",
    "trk",
}


class SocialSourceError(Exception):
    def __init__(
        self,
        message,
        status_code=422,
        error_code="social_source_error",
    ):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


def normalize_social_url(raw_url):
    try:
        normalized = normalize_website_url(raw_url)
    except WebsiteSourceError as error:
        raise SocialSourceError(
            str(error),
            getattr(error, "status_code", 400),
            getattr(error, "error_code", "invalid_social_url"),
        ) from error

    platform = detect_social_platform(normalized)

    if not platform:
        raise SocialSourceError(
            "Use a supported Facebook, Instagram, X, TikTok, LinkedIn, YouTube, Threads, Bluesky, or Google Business Profile link.",
            400,
            "unsupported_social_platform",
        )

    return canonicalize_social_url(normalized, platform), platform


def detect_social_platform(url):
    if is_google_business_profile_url(url):
        return GOOGLE_BUSINESS_PLATFORM

    hostname = (
        urlsplit(str(url or "")).hostname
        or ""
    ).lower().rstrip(".")

    if hostname.startswith("www."):
        hostname = hostname[4:]

    for platform, domains in SOCIAL_PLATFORM_DOMAINS.items():
        for domain in domains:
            if hostname == domain or hostname.endswith(f".{domain}"):
                return platform

    return None


def canonicalize_social_url(url, platform):
    parsed = urlsplit(url)
    path = parsed.path or "/"

    if platform == "Instagram":
        path = re.sub(r"/+", "/", path)
        if not path.endswith("/"):
            path += "/"

    filtered_query = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered in TRACKING_QUERY_KEYS or lowered.startswith("utm_"):
            continue
        filtered_query.append((key, value))

    return urlunsplit((
        parsed.scheme,
        parsed.netloc,
        path,
        urlencode(filtered_query, doseq=True),
        "",
    ))


def prepare_social_content(
    raw_url,
    settings,
    manual_text="",
    supplied_title="",
):
    normalized_url, platform = normalize_social_url(raw_url)
    cleaned_manual_text = clean_manual_text(manual_text)

    maximum_manual_characters = int(
        settings.get("SOCIAL_MAX_MANUAL_CHARACTERS", 200_000)
    )

    if len(cleaned_manual_text) > maximum_manual_characters:
        raise SocialSourceError(
            "The pasted social content is too large.",
            413,
            "social_manual_text_too_large",
        )

    minimum_characters = int(
        settings.get("SOCIAL_MIN_TEXT_CHARACTERS", 40)
    )

    if cleaned_manual_text:
        if len(cleaned_manual_text) < minimum_characters:
            raise SocialSourceError(
                f"Paste at least {minimum_characters} readable characters from the social page, post, or business profile.",
                422,
                "social_manual_text_too_short",
            )

        parsed = urlsplit(normalized_url)

        return {
            "url": normalized_url,
            "canonical_url": normalized_url,
            "title": normalize_social_title(
                supplied_title,
                platform,
                normalized_url,
            ),
            "platform": platform,
            "domain": parsed.hostname or "",
            "text": cleaned_manual_text,
            "extraction_method": "manual",
            "http_status": None,
            "content_type": "text/plain",
            "fetched_at": datetime.now(timezone.utc).replace(tzinfo=None),
        }

    if platform == GOOGLE_BUSINESS_PLATFORM:
        try:
            return prepare_google_business_content(
                raw_url=normalized_url,
                settings=settings,
                supplied_title=supplied_title,
            )
        except GoogleBusinessSourceError as error:
            raise SocialSourceError(
                str(error),
                getattr(error, "status_code", 422),
                getattr(error, "error_code", "google_business_import_failed"),
            ) from error

    if _is_facebook_share_link(normalized_url):
        raise SocialSourceError(
            "Facebook share links are redirect links and are not reliable knowledge-source URLs. Open the link, copy the visible page or post text, paste it below, and keep this link as the citation. A direct Facebook Page or post URL may also work better.",
            422,
            "facebook_share_link_manual_required",
        )

    social_settings = dict(settings)
    social_settings["WEBSITE_MIN_TEXT_CHARACTERS"] = minimum_characters

    try:
        result = fetch_website_content(
            normalized_url,
            social_settings,
        )
    except WebsiteSourceError as error:
        raise SocialSourceError(
            _public_import_failure_message(platform, error),
            getattr(error, "status_code", 422),
            "social_public_fetch_failed",
        ) from error

    result["platform"] = platform
    result["extraction_method"] = "public_page"
    result["title"] = normalize_social_title(
        supplied_title or result.get("title"),
        platform,
        result.get("canonical_url") or normalized_url,
    )
    return result


def clean_manual_text(value):
    text = str(value or "").replace("\x00", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_social_title(value, platform, url):
    title = re.sub(r"\s+", " ", str(value or "")).strip()

    if title:
        return title[:500]

    parsed = urlsplit(url)
    path_parts = [
        unquote(item)
        for item in parsed.path.split("/")
        if item
    ]

    if path_parts:
        label = path_parts[-1].replace("-", " ").replace("_", " ")
        label = re.sub(r"\s+", " ", label).strip()
        if label:
            return f"{platform} · {label}"[:500]

    return f"{platform} source"


def suggested_social_title(platform, url):
    return normalize_social_title("", platform, url)


def _is_facebook_share_link(url):
    parsed = urlsplit(url)
    hostname = (parsed.hostname or "").lower()
    return (
        "facebook.com" in hostname
        and parsed.path.lower().startswith("/share/")
    )


def _public_import_failure_message(platform, error):
    reason = str(error).strip()
    platform_name = platform or "This platform"

    return (
        f"{platform_name} did not provide readable public HTML to AI Studio. "
        "The page may require login, use JavaScript-only content, or block automated requests. "
        "Open the source, copy the visible About text, caption, description, post text, or business details, then paste and index it below. "
        f"Technical reason: {reason}"
    )
