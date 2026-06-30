from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_social_source_manual_fallback_is_actionable(client):
    page = client.get("/").get_data(as_text=True)
    documents_module = (
        PROJECT_ROOT / "static" / "js" / "documents.js"
    ).read_text(encoding="utf-8")
    api_module = (
        PROJECT_ROOT / "static" / "js" / "api.js"
    ).read_text(encoding="utf-8")

    assert 'id="socialManualDetails"' in page
    assert 'id="socialManualAddButton"' in page
    assert 'id="socialFallbackHint"' in page
    assert "Index pasted content" in page
    assert 'error.code = data.code || "request_error"' in api_module
    assert '"social_public_fetch_failed", "social_manual_required"' in documents_module
    assert "result?.manual_required" in documents_module
    assert "elements.socialManualDetails.open = true" in documents_module
    assert "elements.socialManualText.focus()" in documents_module


def test_light_theme_has_high_contrast_controls():
    stylesheet = (
        PROJECT_ROOT / "static" / "style.css"
    ).read_text(encoding="utf-8")

    assert 'html[data-theme="light"] .document-upload-button' in stylesheet
    assert 'html[data-theme="light"] .social-add-button' in stylesheet
    assert 'html[data-theme="light"] .social-manual-add-button' in stylesheet
    assert 'html[data-theme="light"] .document-upload-button:disabled' in stylesheet
    assert 'html[data-theme="light"] .knowledge-tab.is-active' in stylesheet
    assert 'html[data-theme="light"] .document-upload-status.is-error' in stylesheet


def test_ai_assistant_title_uses_neon_branding():
    stylesheet = (
        PROJECT_ROOT / "static" / "style.css"
    ).read_text(encoding="utf-8")

    assert ".header-title h1" in stylesheet
    assert "-webkit-text-fill-color: transparent" in stylesheet
    assert "#67e8f9" in stylesheet
    assert "#c084fc" in stylesheet
    assert 'html[data-theme="light"] .header-title h1' in stylesheet


def test_blocked_social_import_returns_machine_readable_fallback_code(
    client,
    monkeypatch
):
    from services.social_service import SocialSourceError

    def blocked_import(**_kwargs):
        raise SocialSourceError(
            "The platform blocked automatic reading.",
            403,
            "social_public_fetch_failed"
        )

    monkeypatch.setattr(
        "routes.social_routes.prepare_social_content",
        blocked_import
    )

    response = client.post(
        "/api/social-sources",
        json={
            "url": "https://www.linkedin.com/company/example",
            "title": "Example company",
            "manual_text": ""
        }
    )

    assert response.status_code == 202
    payload = response.get_json()
    assert payload["code"] == "social_manual_required"
    assert payload["manual_required"] is True
