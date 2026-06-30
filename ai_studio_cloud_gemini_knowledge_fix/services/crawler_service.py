from collections import deque
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup

from services.website_service import (
    ALLOWED_CONTENT_TYPES,
    WebsiteSourceError,
    extract_page_title,
    normalize_website_url,
    read_limited_response,
    request_with_safe_redirects,
    validate_website_url_for_fetch,
)


EXCLUDED_PATH_PARTS = {
    "admin",
    "wp-admin",
    "login",
    "logout",
    "signin",
    "sign-in",
    "signup",
    "sign-up",
    "register",
    "account",
    "my-account",
    "checkout",
    "cart",
    "basket",
    "search",
    "feed",
    "preview",
}

EXCLUDED_EXTENSIONS = {
    ".7z",
    ".avi",
    ".css",
    ".csv",
    ".doc",
    ".docx",
    ".exe",
    ".gif",
    ".gz",
    ".ico",
    ".jpeg",
    ".jpg",
    ".js",
    ".json",
    ".m4a",
    ".mov",
    ".mp3",
    ".mp4",
    ".pdf",
    ".png",
    ".ppt",
    ".pptx",
    ".rar",
    ".rss",
    ".svg",
    ".tar",
    ".webm",
    ".webp",
    ".xml",
    ".zip",
}

TRACKING_QUERY_PREFIXES = (
    "utm_",
    "fbclid",
    "gclid",
    "mc_",
)


def discover_website_pages(
    raw_url,
    settings,
    max_pages=None,
    max_depth=None,
    use_sitemap=True,
):
    start_url = validate_website_url_for_fetch(raw_url)
    start_parts = urlsplit(start_url)
    root_hostname = (start_parts.hostname or "").lower()

    configured_max_pages = int(
        settings.get("WEBSITE_CRAWLER_MAX_PAGES", 100)
    )
    configured_default_pages = int(
        settings.get("WEBSITE_CRAWLER_DEFAULT_MAX_PAGES", 25)
    )
    configured_max_depth = int(
        settings.get("WEBSITE_CRAWLER_MAX_DEPTH", 5)
    )
    configured_default_depth = int(
        settings.get("WEBSITE_CRAWLER_DEFAULT_DEPTH", 2)
    )

    page_limit = _bounded_integer(
        max_pages,
        configured_default_pages,
        1,
        configured_max_pages,
    )
    depth_limit = _bounded_integer(
        max_depth,
        configured_default_depth,
        0,
        configured_max_depth,
    )

    session = requests.Session()
    user_agent = str(
        settings.get(
            "WEBSITE_USER_AGENT",
            "AI-Studio-KnowledgeIndexer/1.0",
        )
    )
    session.headers.update({
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.1",
    })

    timeout = (
        float(settings.get("WEBSITE_CONNECT_TIMEOUT", 5.0)),
        float(settings.get("WEBSITE_READ_TIMEOUT", 15.0)),
    )
    maximum_redirects = int(
        settings.get("WEBSITE_MAX_REDIRECTS", 3)
    )
    discovery_bytes = int(
        settings.get("WEBSITE_CRAWLER_DISCOVERY_BYTES", 750_000)
    )
    sitemap_bytes = int(
        settings.get("WEBSITE_CRAWLER_SITEMAP_BYTES", 1_000_000)
    )
    sitemap_limit = int(
        settings.get("WEBSITE_CRAWLER_MAX_SITEMAPS", 8)
    )

    robots_parser, sitemap_hints = _load_robots_rules(
        session=session,
        start_url=start_url,
        timeout=timeout,
        maximum_redirects=maximum_redirects,
        maximum_bytes=min(sitemap_bytes, 300_000),
        user_agent=user_agent,
    )

    sitemap_urls = []
    used_sitemap = False

    if use_sitemap:
        sitemap_candidates = list(sitemap_hints)
        default_sitemap = urlunsplit((
            start_parts.scheme,
            start_parts.netloc,
            "/sitemap.xml",
            "",
            "",
        ))

        if default_sitemap not in sitemap_candidates:
            sitemap_candidates.append(default_sitemap)

        sitemap_urls = _discover_sitemap_page_urls(
            session=session,
            sitemap_urls=sitemap_candidates,
            root_hostname=root_hostname,
            timeout=timeout,
            maximum_redirects=maximum_redirects,
            maximum_bytes=sitemap_bytes,
            maximum_sitemaps=sitemap_limit,
            maximum_pages=page_limit,
        )
        used_sitemap = bool(sitemap_urls)

    ordered_candidates = []
    seen_candidates = set()

    def queue_candidate(candidate_url, depth, source):
        normalized = normalize_crawl_candidate(
            candidate_url,
            root_hostname,
        )

        if not normalized or normalized in seen_candidates:
            return

        seen_candidates.add(normalized)
        ordered_candidates.append({
            "url": normalized,
            "depth": depth,
            "source": source,
        })

    queue_candidate(start_url, 0, "start")

    for sitemap_url in sitemap_urls:
        queue_candidate(sitemap_url, 0, "sitemap")
        if len(ordered_candidates) >= page_limit:
            break

    crawl_queue = deque(ordered_candidates)
    queued_urls = {item["url"] for item in ordered_candidates}
    visited = set()
    emitted_urls = set()
    pages = []
    skipped_count = 0

    while crawl_queue and len(pages) < page_limit:
        item = crawl_queue.popleft()
        page_url = item["url"]
        depth = int(item["depth"])

        if page_url in visited:
            continue
        visited.add(page_url)

        if robots_parser and not robots_parser.can_fetch(
            user_agent,
            page_url,
        ):
            skipped_count += 1
            continue

        try:
            page = _fetch_discovery_page(
                session=session,
                url=page_url,
                timeout=timeout,
                maximum_redirects=maximum_redirects,
                maximum_bytes=discovery_bytes,
                root_hostname=root_hostname,
            )
        except WebsiteSourceError:
            skipped_count += 1
            continue

        if page["url"] in emitted_urls:
            continue

        emitted_urls.add(page["url"])
        pages.append({
            "url": page["url"],
            "title": page["title"],
            "path": urlsplit(page["url"]).path or "/",
            "depth": depth,
            "source": item["source"],
        })

        if depth >= depth_limit:
            continue

        for link in page["links"]:
            normalized = normalize_crawl_candidate(
                link,
                root_hostname,
            )

            if (
                not normalized
                or normalized in visited
                or normalized in queued_urls
            ):
                continue

            queued_urls.add(normalized)
            crawl_queue.append({
                "url": normalized,
                "depth": depth + 1,
                "source": "crawl",
            })

    if not pages:
        raise WebsiteSourceError(
            "No readable internal pages were discovered.",
            422,
            "website_crawler_no_pages",
        )

    return {
        "root_url": start_url,
        "domain": root_hostname,
        "max_pages": page_limit,
        "max_depth": depth_limit,
        "used_sitemap": used_sitemap,
        "skipped_count": skipped_count,
        "pages": pages,
    }


def normalize_crawl_candidate(raw_url, root_hostname):
    try:
        normalized = normalize_website_url(raw_url)
    except WebsiteSourceError:
        return None

    parsed = urlsplit(normalized)
    hostname = (parsed.hostname or "").lower()

    if not _same_crawl_hostname(hostname, root_hostname):
        return None

    path = parsed.path or "/"
    lowered_path = path.lower()

    if any(lowered_path.endswith(extension) for extension in EXCLUDED_EXTENSIONS):
        return None

    path_parts = {
        part.lower()
        for part in path.split("/")
        if part
    }

    if path_parts.intersection(EXCLUDED_PATH_PARTS):
        return None

    query_parts = []
    if parsed.query:
        for pair in parsed.query.split("&"):
            key = pair.split("=", 1)[0].lower()
            if not key.startswith(TRACKING_QUERY_PREFIXES):
                query_parts.append(pair)

    query = "&".join(query_parts)

    return urlunsplit((
        parsed.scheme,
        parsed.netloc,
        path,
        query,
        "",
    ))


def _fetch_discovery_page(
    session,
    url,
    timeout,
    maximum_redirects,
    maximum_bytes,
    root_hostname,
):
    response, final_url = request_with_safe_redirects(
        session=session,
        url=url,
        timeout=timeout,
        maximum_redirects=maximum_redirects,
    )

    try:
        response.raise_for_status()
    except requests.HTTPError as error:
        response.close()
        raise WebsiteSourceError(
            f"Website returned HTTP {response.status_code}.",
            422,
            "website_http_error",
        ) from error

    content_type = (
        response.headers.get("Content-Type", "")
        .split(";", 1)[0]
        .strip()
        .lower()
    )

    if content_type not in ALLOWED_CONTENT_TYPES:
        response.close()
        raise WebsiteSourceError(
            "The discovered URL is not a readable webpage.",
            415,
            "unsupported_website_content_type",
        )

    raw = read_limited_response(response, maximum_bytes)
    encoding = response.encoding or "utf-8"

    try:
        content = raw.decode(encoding, errors="replace")
    except LookupError:
        content = raw.decode("utf-8", errors="replace")

    canonical = normalize_crawl_candidate(
        final_url,
        root_hostname,
    )

    if not canonical:
        raise WebsiteSourceError(
            "The page redirected outside the selected website.",
            422,
            "website_crawler_external_redirect",
        )

    if content_type == "text/plain":
        return {
            "url": canonical,
            "title": urlsplit(canonical).hostname or "Website",
            "links": [],
        }

    soup = BeautifulSoup(content, "html.parser")
    links = []

    for anchor in soup.find_all("a", href=True):
        href = str(anchor.get("href") or "").strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        links.append(urljoin(canonical, href))

    return {
        "url": canonical,
        "title": extract_page_title(soup, canonical)[:500],
        "links": links,
    }


def _load_robots_rules(
    session,
    start_url,
    timeout,
    maximum_redirects,
    maximum_bytes,
    user_agent,
):
    parsed = urlsplit(start_url)
    robots_url = urlunsplit((
        parsed.scheme,
        parsed.netloc,
        "/robots.txt",
        "",
        "",
    ))

    try:
        response, final_url = request_with_safe_redirects(
            session=session,
            url=robots_url,
            timeout=timeout,
            maximum_redirects=maximum_redirects,
        )

        if response.status_code >= 400:
            response.close()
            return None, []

        raw = read_limited_response(response, maximum_bytes)
        text = raw.decode(
            response.encoding or "utf-8",
            errors="replace",
        )

        parser = RobotFileParser()
        parser.set_url(final_url)
        parser.parse(text.splitlines())

        sitemaps = []
        for line in text.splitlines():
            if line.lower().startswith("sitemap:"):
                value = line.split(":", 1)[1].strip()
                if value:
                    sitemaps.append(urljoin(final_url, value))

        return parser, sitemaps

    except WebsiteSourceError as error:
        if error.error_code == "private_website_not_allowed":
            raise
        return None, []
    except Exception:
        return None, []


def _discover_sitemap_page_urls(
    session,
    sitemap_urls,
    root_hostname,
    timeout,
    maximum_redirects,
    maximum_bytes,
    maximum_sitemaps,
    maximum_pages,
):
    queue = deque(sitemap_urls)
    seen_sitemaps = set()
    page_urls = []
    seen_pages = set()

    while (
        queue
        and len(seen_sitemaps) < maximum_sitemaps
        and len(page_urls) < maximum_pages
    ):
        sitemap_url = queue.popleft()

        try:
            normalized_sitemap = validate_website_url_for_fetch(
                sitemap_url
            )
        except WebsiteSourceError:
            continue

        parsed_sitemap = urlsplit(normalized_sitemap)
        if not _same_crawl_hostname(
            (parsed_sitemap.hostname or "").lower(),
            root_hostname,
        ):
            continue

        if normalized_sitemap in seen_sitemaps:
            continue
        seen_sitemaps.add(normalized_sitemap)

        try:
            response, _final_url = request_with_safe_redirects(
                session=session,
                url=normalized_sitemap,
                timeout=timeout,
                maximum_redirects=maximum_redirects,
            )

            if response.status_code >= 400:
                response.close()
                continue

            raw = read_limited_response(response, maximum_bytes)

            lowered_raw = raw.lower()
            if b"<!doctype" in lowered_raw or b"<!entity" in lowered_raw:
                continue

            root = ElementTree.fromstring(raw)
        except (WebsiteSourceError, ElementTree.ParseError):
            continue
        except Exception:
            continue

        root_name = _xml_local_name(root.tag)
        locations = [
            (element.text or "").strip()
            for element in root.iter()
            if _xml_local_name(element.tag) == "loc"
            and (element.text or "").strip()
        ]

        if root_name == "sitemapindex":
            for location in locations:
                if len(seen_sitemaps) + len(queue) >= maximum_sitemaps:
                    break
                queue.append(location)
            continue

        if root_name != "urlset":
            continue

        for location in locations:
            normalized = normalize_crawl_candidate(
                location,
                root_hostname,
            )

            if not normalized or normalized in seen_pages:
                continue

            seen_pages.add(normalized)
            page_urls.append(normalized)

            if len(page_urls) >= maximum_pages:
                break

    return page_urls


def _same_crawl_hostname(candidate, root_hostname):
    candidate = str(candidate or "").lower().rstrip(".")
    root = str(root_hostname or "").lower().rstrip(".")

    if candidate == root:
        return True

    return candidate.removeprefix("www.") == root.removeprefix("www.")



def _xml_local_name(tag):
    return str(tag).rsplit("}", 1)[-1].lower()


def _bounded_integer(value, fallback, minimum, maximum):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = int(fallback)

    return max(minimum, min(maximum, parsed))
