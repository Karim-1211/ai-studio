import ipaddress
import re
import socket
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup


class WebsiteSourceError(Exception):
    def __init__(
        self,
        message,
        status_code=422,
        error_code="website_source_error"
    ):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain"
}

ALLOWED_CONTENT_TYPES = {
    "text/html",
    "application/xhtml+xml",
    "text/plain"
}

REMOVABLE_TAGS = {
    "script",
    "style",
    "noscript",
    "template",
    "svg",
    "canvas",
    "iframe",
    "form",
    "button",
    "nav",
    "footer",
    "aside"
}


class NoRedirectSession(requests.Session):
    def rebuild_auth(self, prepared_request, response):
        return super().rebuild_auth(prepared_request, response)


def normalize_website_url(raw_url):
    value = str(raw_url or "").strip()

    if not value:
        raise WebsiteSourceError(
            "Website URL is required.",
            400,
            "missing_website_url"
        )

    if len(value) > 2048:
        raise WebsiteSourceError(
            "Website URL cannot exceed 2,048 characters.",
            400,
            "website_url_too_long"
        )

    parsed = urlsplit(value)

    if parsed.scheme.lower() not in {"http", "https"}:
        raise WebsiteSourceError(
            "Only http:// and https:// website URLs are supported.",
            400,
            "unsupported_website_scheme"
        )

    if not parsed.hostname:
        raise WebsiteSourceError(
            "Website URL must include a valid hostname.",
            400,
            "invalid_website_hostname"
        )

    if parsed.username or parsed.password:
        raise WebsiteSourceError(
            "Website URLs containing usernames or passwords are not allowed.",
            400,
            "website_credentials_not_allowed"
        )

    hostname = parsed.hostname.rstrip(".").lower()

    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(".localhost"):
        raise WebsiteSourceError(
            "Localhost and private network websites are not allowed.",
            400,
            "private_website_not_allowed"
        )

    try:
        port = parsed.port
    except ValueError as error:
        raise WebsiteSourceError(
            "Website URL contains an invalid port.",
            400,
            "invalid_website_port"
        ) from error

    netloc = hostname

    if ":" in hostname and not hostname.startswith("["):
        netloc = f"[{hostname}]"

    if port:
        netloc = f"{netloc}:{port}"

    path = parsed.path or "/"

    return urlunsplit((
        parsed.scheme.lower(),
        netloc,
        path,
        parsed.query,
        ""
    ))


def validate_public_hostname(hostname):
    normalized = str(hostname or "").rstrip(".").lower()

    if not normalized:
        raise WebsiteSourceError(
            "Website hostname is missing.",
            400,
            "invalid_website_hostname"
        )

    if normalized in BLOCKED_HOSTNAMES or normalized.endswith(".localhost"):
        raise WebsiteSourceError(
            "Localhost and private network websites are not allowed.",
            400,
            "private_website_not_allowed"
        )

    try:
        literal_ip = ipaddress.ip_address(normalized)
    except ValueError:
        literal_ip = None

    addresses = []

    if literal_ip is not None:
        addresses = [literal_ip]
    else:
        try:
            records = socket.getaddrinfo(
                normalized,
                None,
                type=socket.SOCK_STREAM
            )
        except socket.gaierror as error:
            raise WebsiteSourceError(
                "The website hostname could not be resolved.",
                422,
                "website_dns_failed"
            ) from error

        for record in records:
            try:
                addresses.append(
                    ipaddress.ip_address(record[4][0])
                )
            except ValueError:
                continue

    if not addresses:
        raise WebsiteSourceError(
            "The website hostname did not resolve to an address.",
            422,
            "website_dns_failed"
        )

    for address in addresses:
        if (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_reserved
            or address.is_unspecified
        ):
            raise WebsiteSourceError(
                "Local, private, reserved, and link-local websites are not allowed.",
                400,
                "private_website_not_allowed"
            )

    return [str(address) for address in addresses]


def validate_website_url_for_fetch(raw_url):
    normalized_url = normalize_website_url(raw_url)
    parsed = urlsplit(normalized_url)
    validate_public_hostname(parsed.hostname)
    return normalized_url


def fetch_website_content(raw_url, settings):
    normalized_url = validate_website_url_for_fetch(raw_url)

    timeout = (
        float(settings.get("WEBSITE_CONNECT_TIMEOUT", 5.0)),
        float(settings.get("WEBSITE_READ_TIMEOUT", 15.0))
    )

    maximum_bytes = int(
        settings.get("WEBSITE_MAX_RESPONSE_BYTES", 2_000_000)
    )

    maximum_redirects = int(
        settings.get("WEBSITE_MAX_REDIRECTS", 3)
    )

    user_agent = str(
        settings.get(
            "WEBSITE_USER_AGENT",
            "AI-Studio-KnowledgeIndexer/1.0"
        )
    )

    respect_robots = bool(
        settings.get("WEBSITE_RESPECT_ROBOTS", True)
    )

    session = requests.Session()
    session.headers.update({
        "User-Agent": user_agent,
        "Accept": (
            "text/html,application/xhtml+xml,text/plain;"
            "q=0.9,*/*;q=0.1"
        )
    })

    if respect_robots and not is_allowed_by_robots(
        session=session,
        url=normalized_url,
        timeout=timeout,
        maximum_bytes=min(maximum_bytes, 250_000),
        maximum_redirects=maximum_redirects,
        user_agent=user_agent
    ):
        raise WebsiteSourceError(
            "This website does not allow this page to be indexed according to robots.txt.",
            403,
            "website_robots_denied"
        )

    response, final_url = request_with_safe_redirects(
        session=session,
        url=normalized_url,
        timeout=timeout,
        maximum_redirects=maximum_redirects
    )

    try:
        response.raise_for_status()
    except requests.HTTPError as error:
        raise WebsiteSourceError(
            f"Website returned HTTP {response.status_code}.",
            422,
            "website_http_error"
        ) from error

    content_type = (
        response.headers.get("Content-Type", "")
        .split(";", 1)[0]
        .strip()
        .lower()
    )

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise WebsiteSourceError(
            "The URL did not return a readable HTML or text webpage.",
            415,
            "unsupported_website_content_type"
        )

    content = read_limited_response(
        response,
        maximum_bytes
    )

    encoding = response.encoding or "utf-8"

    try:
        decoded = content.decode(encoding, errors="replace")
    except LookupError:
        decoded = content.decode("utf-8", errors="replace")

    extraction = extract_readable_web_text(
        decoded,
        content_type,
        final_url,
        maximum_characters=int(
            settings.get(
                "WEBSITE_MAX_TEXT_CHARACTERS",
                500_000
            )
        ),
        minimum_characters=int(
            settings.get(
                "WEBSITE_MIN_TEXT_CHARACTERS",
                120
            )
        )
    )

    return {
        "url": normalized_url,
        "canonical_url": final_url,
        "title": extraction["title"],
        "domain": urlsplit(final_url).hostname or "",
        "text": extraction["text"],
        "http_status": response.status_code,
        "content_type": content_type,
        "fetched_at": datetime.now(timezone.utc).replace(tzinfo=None)
    }


def request_with_safe_redirects(
    session,
    url,
    timeout,
    maximum_redirects
):
    current_url = validate_website_url_for_fetch(url)

    for redirect_index in range(maximum_redirects + 1):
        try:
            response = session.get(
                current_url,
                stream=True,
                timeout=timeout,
                allow_redirects=False
            )
        except requests.Timeout as error:
            raise WebsiteSourceError(
                "The website took too long to respond.",
                504,
                "website_timeout"
            ) from error
        except requests.RequestException as error:
            raise WebsiteSourceError(
                "The website could not be downloaded.",
                502,
                "website_request_failed"
            ) from error

        if response.status_code not in {301, 302, 303, 307, 308}:
            return response, current_url

        location = response.headers.get("Location")
        response.close()

        if not location:
            raise WebsiteSourceError(
                "The website returned an invalid redirect.",
                422,
                "invalid_website_redirect"
            )

        if redirect_index >= maximum_redirects:
            raise WebsiteSourceError(
                "The website redirected too many times.",
                422,
                "website_redirect_limit"
            )

        current_url = validate_website_url_for_fetch(
            urljoin(current_url, location)
        )

    raise WebsiteSourceError(
        "The website redirected too many times.",
        422,
        "website_redirect_limit"
    )


def is_allowed_by_robots(
    session,
    url,
    timeout,
    maximum_bytes,
    maximum_redirects,
    user_agent
):
    parsed = urlsplit(url)
    robots_url = urlunsplit((
        parsed.scheme,
        parsed.netloc,
        "/robots.txt",
        "",
        ""
    ))

    try:
        response, final_url = request_with_safe_redirects(
            session=session,
            url=robots_url,
            timeout=timeout,
            maximum_redirects=maximum_redirects
        )

        if response.status_code >= 400:
            response.close()
            return True

        content_type = (
            response.headers.get("Content-Type", "")
            .split(";", 1)[0]
            .strip()
            .lower()
        )

        if content_type and not (
            content_type.startswith("text/")
            or content_type == "application/octet-stream"
        ):
            response.close()
            return True

        raw = read_limited_response(
            response,
            maximum_bytes
        )

        text = raw.decode(
            response.encoding or "utf-8",
            errors="replace"
        )

        parser = RobotFileParser()
        parser.set_url(final_url)
        parser.parse(text.splitlines())

        return parser.can_fetch(
            user_agent,
            url
        )

    except WebsiteSourceError as error:
        if error.error_code == "private_website_not_allowed":
            raise
        return True
    except Exception:
        return True


def read_limited_response(response, maximum_bytes):
    content_length = response.headers.get("Content-Length")

    if content_length:
        try:
            if int(content_length) > maximum_bytes:
                response.close()
                raise WebsiteSourceError(
                    "The webpage is too large to index.",
                    413,
                    "website_too_large"
                )
        except ValueError:
            pass

    chunks = []
    total = 0

    try:
        for chunk in response.iter_content(chunk_size=65_536):
            if not chunk:
                continue

            total += len(chunk)

            if total > maximum_bytes:
                raise WebsiteSourceError(
                    "The webpage is too large to index.",
                    413,
                    "website_too_large"
                )

            chunks.append(chunk)
    finally:
        response.close()

    return b"".join(chunks)


def extract_readable_web_text(
    content,
    content_type,
    source_url,
    maximum_characters,
    minimum_characters
):
    if content_type == "text/plain":
        text = clean_web_text(content)
        title = urlsplit(source_url).hostname or "Website"
    else:
        soup = BeautifulSoup(content, "html.parser")

        title = extract_page_title(
            soup,
            source_url
        )

        for tag_name in REMOVABLE_TAGS:
            for element in soup.find_all(tag_name):
                element.decompose()

        root = (
            soup.find("main")
            or soup.find("article")
            or soup.body
            or soup
        )

        text = clean_web_text(
            root.get_text("\n", strip=True)
        )

    if len(text) < minimum_characters:
        raise WebsiteSourceError(
            "The webpage did not contain enough readable text to index.",
            422,
            "website_text_too_short"
        )

    if len(text) > maximum_characters:
        text = text[:maximum_characters].rstrip()

    return {
        "title": title[:500],
        "text": text
    }


def extract_page_title(soup, source_url):
    if soup.title:
        title = clean_web_text(
            soup.title.get_text(" ", strip=True)
        )

        if title:
            return title

    heading = soup.find("h1")

    if heading:
        title = clean_web_text(
            heading.get_text(" ", strip=True)
        )

        if title:
            return title

    return urlsplit(source_url).hostname or "Website"


def clean_web_text(value):
    text = str(value or "")
    text = text.replace("\x00", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = []

    for line in text.split("\n"):
        cleaned = re.sub(r"[ \t\f\v]+", " ", line).strip()

        if cleaned:
            lines.append(cleaned)

    cleaned_text = "\n".join(lines)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

    return cleaned_text.strip()
