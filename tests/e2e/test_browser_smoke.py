import os
from pathlib import Path

import pytest


if os.getenv("RUN_E2E") != "1":
    pytest.skip(
        "Set RUN_E2E=1 to run browser tests against a live AI Studio instance.",
        allow_module_level=True,
    )

sync_api = pytest.importorskip("playwright.sync_api")


BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
EMAIL = os.getenv("E2E_EMAIL")
PASSWORD = os.getenv("E2E_PASSWORD")


def _login(page):
    page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
    if "/login" not in page.url:
        return
    if not EMAIL or not PASSWORD:
        pytest.fail("Set E2E_EMAIL and E2E_PASSWORD for the browser test account.")
    page.locator('input[name="email"]').fill(EMAIL)
    page.locator('input[name="password"]').fill(PASSWORD)
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_url(f"{BASE_URL}/")


@pytest.fixture()
def page():
    with sync_api.sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        _login(page)
        page.locator("#prompt").wait_for()
        yield page
        context.close()
        browser.close()


def test_workspace_responsive_drawer_and_keyboard(page):
    page.get_by_role("heading", name="AI Assistant").wait_for()
    page.locator("#documentToggle").click()
    page.locator("#documentPanel").wait_for(state="visible")

    for width, height in [(1024, 768), (768, 900), (390, 844)]:
        page.set_viewport_size({"width": width, "height": height})
        assert page.locator("#prompt").is_visible()
        assert page.locator("#documentPanel").is_visible()

    page.keyboard.press("Escape")
    page.locator("#documentPanel").wait_for(state="hidden")

    page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
    page.keyboard.press("Tab")
    focused_class = page.evaluate("document.activeElement.className")
    assert "skip-link" in str(focused_class)


def test_accessible_voice_and_source_controls_exist(page):
    assert page.locator("#voiceInputButton").get_attribute("aria-label")
    assert page.locator("#voiceOutputButton").get_attribute("aria-label")
    assert page.locator("#sendButton").get_attribute("aria-label")
    assert page.evaluate("typeof window.speechSynthesis !== 'undefined'") is True


def test_live_chat_round_trip(page):
    if os.getenv("E2E_RUN_AI") != "1":
        pytest.skip("Set E2E_RUN_AI=1 when Ollama is available for live chat testing.")

    page.locator("#prompt").fill("Reply with exactly: browser test passed")
    page.locator("#sendButton").click()
    page.locator(".bot:not(.loading)").last.wait_for(timeout=120_000)
    assert page.locator(".bot").last.inner_text().strip()


def test_attachment_upload_and_rag(page, tmp_path):
    if os.getenv("E2E_RUN_AI") != "1":
        pytest.skip("Set E2E_RUN_AI=1 when embeddings and Ollama are available.")

    sample = tmp_path / "browser-rag.txt"
    sample.write_text("The browser test project code is ORBIT-4729.", encoding="utf-8")
    page.locator("#attachmentInput").set_input_files(str(sample))
    page.locator("#attachmentPreviewList").locator(".attachment-preview-item").wait_for(
        timeout=120_000
    )
    page.locator("#prompt").fill("What is the project code in the attached file?")
    page.locator("#sendButton").click()
    page.locator(".bot:not(.loading)").last.wait_for(timeout=120_000)
    assert "ORBIT-4729" in page.locator(".bot").last.inner_text()


def test_workspace_backup_download(page):
    if os.getenv("E2E_RUN_BACKUP") != "1":
        pytest.skip("Set E2E_RUN_BACKUP=1 to exercise workspace backup download.")

    page.locator(".sidebar-account-menu > summary").click()
    with page.expect_download(timeout=120_000) as download_info:
        page.locator("#workspaceBackupButton").click()
    download = download_info.value
    assert download.suggested_filename.endswith(".zip")
