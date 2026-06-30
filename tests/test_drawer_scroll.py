from pathlib import Path


def test_knowledge_drawer_has_independent_scroll_container():
    css = Path("static/style.css").read_text(encoding="utf-8")
    assert ".knowledge-drawer-content" in css
    assert "overflow-y: auto" in css
    assert "overscroll-behavior-y: contain" in css
    assert "scrollbar-gutter: stable" in css


def test_authentication_assets_are_present():
    assert Path("templates/auth.html").exists()
    assert Path("templates/account.html").exists()
    assert Path("templates/admin_users.html").exists()
    assert Path("static/auth.css").exists()
