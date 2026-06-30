from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_workspace_uses_icon_send_button(client):
    page = client.get("/").get_data(as_text=True)

    assert 'id="sendButton"' in page
    assert 'class="send-button"' in page
    assert 'aria-label="Send message"' in page
    assert 'class="send-button-icon send-icon"' in page
    assert 'class="send-button-icon stop-icon"' in page


def test_markdown_renderer_marks_formatted_messages():
    markdown_module = (
        PROJECT_ROOT / "static" / "js" / "markdown.js"
    ).read_text(encoding="utf-8")

    assert 'message.classList.add("is-formatted")' in markdown_module


def test_send_state_preserves_svg_icon():
    app_module = (
        PROJECT_ROOT / "static" / "js" / "app.js"
    ).read_text(encoding="utf-8")

    assert "setSendButtonState" in app_module
    assert 'classList.toggle(\n    "is-generating"' in app_module
    assert 'innerText = "Send"' not in app_module
    assert 'innerText = "Stop"' not in app_module


def test_microphone_permission_allows_same_origin(client):
    response = client.get("/")

    assert "microphone=(self)" in response.headers["Permissions-Policy"]


def test_advanced_panel_closes_on_outside_click(client):
    page = client.get("/").get_data(as_text=True)
    settings_module = (
        PROJECT_ROOT / "static" / "js" / "settings.js"
    ).read_text(encoding="utf-8")

    assert 'id="advancedBox"' in page
    assert '"pointerdown"' in settings_module
    assert "!advancedBox.contains(event.target)" in settings_module
    assert "advancedBox.open = false" in settings_module


def test_pinned_chat_uses_modern_down_left_pin():
    sidebar_module = (
        PROJECT_ROOT / "static" / "js" / "sidebar.js"
    ).read_text(encoding="utf-8")
    stylesheet = (
        PROJECT_ROOT / "static" / "style.css"
    ).read_text(encoding="utf-8")

    assert 'aria-pressed' in sidebar_module
    assert 'M9 3h6v5l2 3v2l2 2v2H5v-2l2-2v-2l2-3V3Z' in sidebar_module
    assert "transform: rotate(38deg);" in stylesheet
    assert "transform: rotate(-38deg);" not in stylesheet
