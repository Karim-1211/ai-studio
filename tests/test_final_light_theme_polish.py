from pathlib import Path


def test_final_light_theme_polish_contract():
    css = Path("static/style.css").read_text(encoding="utf-8")

    required_selectors = (
        'html[data-theme="light"] .new-chat',
        'html[data-theme="light"] .chat-tag-badge.tag-violet',
        'html[data-theme="light"] .chat-tag-badge.tag-blue',
        'html[data-theme="light"] .chat-tag-badge.tag-cyan',
        'html[data-theme="light"] .chat-tag-badge.tag-green',
        'html[data-theme="light"] .chat-tag-badge.tag-amber',
        'html[data-theme="light"] .chat-tag-badge.tag-rose',
        'html[data-theme="light"] .attachment-preview-icon',
        'html[data-theme="light"] .attachment-preview-name',
        'html[data-theme="light"] #prompt:focus',
    )

    for selector in required_selectors:
        assert selector in css


def test_light_theme_tag_text_uses_dark_foreground():
    css = Path("static/style.css").read_text(encoding="utf-8")
    assert "color: #5b21b6 !important;" in css
    assert "color: #1e40af !important;" in css
    assert "color: #155e75 !important;" in css
    assert "color: #166534 !important;" in css
    assert "color: #92400e !important;" in css
    assert "color: #9f1239 !important;" in css
