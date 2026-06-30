from pathlib import Path


def test_workspace_has_skip_link_and_main_landmark(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'class="skip-link"' in html
    assert 'id="mainContent"' in html
    assert 'aria-label="Search chats"' in html


def test_rag_sources_are_collapsible_and_session_persistent():
    source = Path("static/js/ui.js").read_text(encoding="utf-8")
    assert 'document.createElement("details")' in source
    assert 'document.createElement("summary")' in source
    assert "aiStudioRagSourcesOpen" in source
    assert "Toggle source details" in source


def test_light_theme_has_explicit_contrast_overrides():
    css = Path("static/style.css").read_text(encoding="utf-8")
    assert "--light-text-strong: #0f172a" in css
    assert 'html[data-theme="light"] .rag-source-score' in css
    assert "prefers-reduced-motion" in css


def test_admin_dashboard_assets_exist():
    assert Path("templates/admin_dashboard.html").is_file()
    assert Path("static/admin.css").is_file()
    assert Path("static/js/admin_dashboard.js").is_file()
