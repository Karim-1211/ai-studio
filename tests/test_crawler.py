from datetime import datetime
from pathlib import Path

from database import db
from database.models import WebsiteSource
from services.crawler_service import (
    discover_website_pages,
    normalize_crawl_candidate,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_normalize_crawl_candidate_filters_unsafe_or_unwanted_pages():
    assert (
        normalize_crawl_candidate(
            "https://example.com/about?utm_source=test#team",
            "example.com",
        )
        == "https://example.com/about"
    )

    assert normalize_crawl_candidate(
        "https://www.example.com/services",
        "example.com",
    ) == "https://www.example.com/services"

    assert normalize_crawl_candidate(
        "https://other.example.org/about",
        "example.com",
    ) is None

    assert normalize_crawl_candidate(
        "https://example.com/login",
        "example.com",
    ) is None

    assert normalize_crawl_candidate(
        "https://example.com/brochure.pdf",
        "example.com",
    ) is None


def test_discovery_combines_sitemap_and_internal_links(monkeypatch):
    monkeypatch.setattr(
        "services.crawler_service.validate_website_url_for_fetch",
        lambda url: url,
    )
    monkeypatch.setattr(
        "services.crawler_service._load_robots_rules",
        lambda **_kwargs: (None, ["https://example.com/sitemap.xml"]),
    )
    monkeypatch.setattr(
        "services.crawler_service._discover_sitemap_page_urls",
        lambda **_kwargs: ["https://example.com/about"],
    )

    pages = {
        "https://example.com/": {
            "url": "https://example.com/",
            "title": "Home",
            "links": ["https://example.com/services"],
        },
        "https://example.com/about": {
            "url": "https://example.com/about",
            "title": "About",
            "links": [],
        },
        "https://example.com/services": {
            "url": "https://example.com/services",
            "title": "Services",
            "links": [],
        },
    }

    monkeypatch.setattr(
        "services.crawler_service._fetch_discovery_page",
        lambda **kwargs: pages[kwargs["url"]],
    )

    result = discover_website_pages(
        "https://example.com/",
        {
            "WEBSITE_CRAWLER_MAX_PAGES": 10,
            "WEBSITE_CRAWLER_DEFAULT_MAX_PAGES": 10,
            "WEBSITE_CRAWLER_MAX_DEPTH": 3,
            "WEBSITE_CRAWLER_DEFAULT_DEPTH": 2,
        },
        max_pages=10,
        max_depth=2,
        use_sitemap=True,
    )

    assert result["used_sitemap"] is True
    assert [page["title"] for page in result["pages"]] == [
        "Home",
        "About",
        "Services",
    ]


def test_crawler_discovery_route(client, monkeypatch):
    monkeypatch.setattr(
        "routes.crawler_routes.discover_website_pages",
        lambda **_kwargs: {
            "root_url": "https://example.com/",
            "domain": "example.com",
            "max_pages": 25,
            "max_depth": 2,
            "used_sitemap": True,
            "skipped_count": 0,
            "pages": [
                {
                    "url": "https://example.com/",
                    "title": "Example Home",
                    "path": "/",
                    "depth": 0,
                    "source": "start",
                }
            ],
        },
    )

    response = client.post(
        "/api/website-crawler/discover",
        json={
            "url": "https://example.com/",
            "max_pages": 25,
            "max_depth": 2,
            "use_sitemap": True,
        },
    )

    assert response.status_code == 200
    page = response.get_json()["pages"][0]
    assert page["title"] == "Example Home"
    assert page["already_indexed"] is False


def test_crawler_batch_index_and_domain_delete(app, client, monkeypatch):
    def fake_index(url):
        source = WebsiteSource(
            url=url,
            canonical_url=url,
            title=url.rsplit("/", 1)[-1] or "Home",
            domain="example.com",
            status="ready",
            chunk_count=1,
            text_length=100,
            fetched_at=datetime(2026, 6, 28, 12, 0, 0),
        )
        db.session.add(source)
        db.session.commit()
        return source, True

    monkeypatch.setattr(
        "routes.crawler_routes.index_website_url",
        fake_index,
    )

    response = client.post(
        "/api/website-crawler/index",
        json={
            "urls": [
                "https://example.com/",
                "https://example.com/about",
            ]
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["created_count"] == 2
    assert payload["failed_count"] == 0

    deleted = client.delete(
        "/api/website-crawler/sites/example.com"
    )
    assert deleted.status_code == 200
    assert len(deleted.get_json()["deleted_ids"]) == 2

    with app.app_context():
        assert WebsiteSource.query.count() == 0


def test_crawler_rejects_mixed_domains(client):
    response = client.post(
        "/api/website-crawler/index",
        json={
            "urls": [
                "https://example.com/",
                "https://example.org/",
            ]
        },
    )

    assert response.status_code == 400
    assert response.get_json()["code"] == "website_crawler_mixed_domains"


def test_workspace_contains_crawler_controls(client):
    page = client.get("/").get_data(as_text=True)

    assert 'id="websiteDiscoverButton"' in page
    assert 'id="websiteCrawlerMaxPages"' in page
    assert 'id="websiteCrawlerMaxDepth"' in page
    assert 'id="websiteCrawlerUseSitemap"' in page
    assert 'id="websiteDiscoveryPanel"' in page
    assert 'id="websiteIndexSelectedButton"' in page

    app_module = (
        PROJECT_ROOT / "static" / "js" / "documents.js"
    ).read_text(encoding="utf-8")

    assert "discoverWebsiteFromInput" in app_module
    assert "createWebsiteDomainGroup" in app_module
