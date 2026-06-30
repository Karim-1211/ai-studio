from pathlib import Path

from services.google_business_service import prepare_google_business_content
from services.social_service import detect_social_platform, normalize_social_url


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.ok = 200 <= status_code < 300

    def json(self):
        return self._payload


def test_google_business_profile_url_is_supported_and_tracking_is_removed():
    url = "https://www.google.com/maps/place/DeepTechArt/@46.2,6.1,15z?utm_source=test"
    normalized, platform = normalize_social_url(url)

    assert platform == "Google Business Profile"
    assert "utm_source" not in normalized
    assert detect_social_platform("https://maps.app.goo.gl/example") == "Google Business Profile"


def test_google_places_content_is_converted_to_searchable_text(monkeypatch):
    search_payload = {
        "places": [
            {
                "id": "places/example",
                "displayName": {"text": "DeepTechArt"},
                "formattedAddress": "Geneva, Switzerland",
                "googleMapsUri": "https://maps.google.com/?cid=123",
            }
        ]
    }
    details_payload = {
        "id": "places/example",
        "displayName": {"text": "DeepTechArt"},
        "formattedAddress": "Geneva, Switzerland",
        "internationalPhoneNumber": "+41 22 000 00 00",
        "websiteUri": "https://www.deeptechart.com",
        "googleMapsUri": "https://maps.google.com/?cid=123",
        "rating": 4.9,
        "userRatingCount": 25,
        "businessStatus": "OPERATIONAL",
        "types": ["marketing_agency"],
        "regularOpeningHours": {
            "weekdayDescriptions": ["Monday: 9:00 AM – 5:00 PM"]
        },
        "editorialSummary": {"text": "Digital marketing agency in Geneva."},
        "reviews": [
            {
                "rating": 5,
                "text": {"text": "Excellent local SEO support."},
                "authorAttribution": {"displayName": "Example reviewer"},
            }
        ],
    }

    monkeypatch.setattr(
        "services.google_business_service.requests.post",
        lambda *args, **kwargs: FakeResponse(search_payload),
    )
    monkeypatch.setattr(
        "services.google_business_service.requests.get",
        lambda *args, **kwargs: FakeResponse(details_payload),
    )

    result = prepare_google_business_content(
        raw_url="https://www.google.com/maps/place/DeepTechArt/",
        settings={
            "GOOGLE_MAPS_API_KEY": "test-key",
            "GOOGLE_PLACES_LANGUAGE_CODE": "en",
            "GOOGLE_PLACES_MAX_REVIEWS": 5,
            "WEBSITE_CONNECT_TIMEOUT": 1,
            "WEBSITE_READ_TIMEOUT": 1,
            "SOCIAL_MIN_TEXT_CHARACTERS": 40,
        },
    )

    assert result["platform"] == "Google Business Profile"
    assert result["extraction_method"] == "google_places_api"
    assert "DeepTechArt" in result["text"]
    assert "Geneva, Switzerland" in result["text"]
    assert "Excellent local SEO support" in result["text"]


def test_google_business_route_returns_manual_fallback_without_api_key(client):
    response = client.post(
        "/api/social-sources",
        json={
            "url": "https://www.google.com/maps/place/DeepTechArt/",
            "import_mode": "public",
        },
    )

    assert response.status_code == 202
    payload = response.get_json()
    assert payload["manual_required"] is True
    assert payload["reason_code"] == "google_places_api_key_required"
    assert payload["platform"] == "Google Business Profile"


def test_social_manual_workflow_and_dark_drawer_have_accessible_controls(client):
    page = client.get("/").get_data(as_text=True)
    css = (PROJECT_ROOT / "static" / "style.css").read_text(encoding="utf-8")
    documents_js = (
        PROJECT_ROOT / "static" / "js" / "documents.js"
    ).read_text(encoding="utf-8")

    assert 'id="socialOpenSourceButton"' in page
    assert 'id="socialPasteClipboardButton"' in page
    assert "Google Business Profile" in page
    assert "pasteSocialClipboard" in documents_js
    assert '"google business profile": "GBP"' in documents_js
    assert 'html:not([data-theme="light"]) .document-panel-body.knowledge-drawer' in css
    assert ".social-manual-tools" in css
    assert "grid-template-columns: repeat(2, minmax(0, 1fr));" in css
