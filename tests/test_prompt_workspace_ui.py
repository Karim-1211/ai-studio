from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_prompt_library_and_branch_controls_are_present(client):
    page = client.get("/").get_data(as_text=True)
    prompts = (PROJECT_ROOT / "static" / "js" / "prompts.js").read_text(
        encoding="utf-8"
    )
    conversation = (
        PROJECT_ROOT / "static" / "js" / "conversation.js"
    ).read_text(encoding="utf-8")

    assert 'id="promptLibraryButton"' in page
    assert 'id="promptLibraryDrawer"' in page
    assert 'id="promptTemplateForm"' in page
    assert "Insert into message" in prompts
    assert "include_target" in conversation
    assert "Edit in branch" in conversation


def test_wide_conversation_rail_and_compact_sidebar_actions():
    styles = (PROJECT_ROOT / "static" / "style.css").read_text(
        encoding="utf-8"
    )
    sidebar = (PROJECT_ROOT / "static" / "js" / "sidebar.js").read_text(
        encoding="utf-8"
    )

    assert "@media (min-width: 1180px)" in styles
    assert "padding-left: clamp(42px, 5.2vw, 96px)" in styles
    assert ".chat-state-badges" in styles
    assert "actions.appendChild(menuWrapper)" in sidebar
    assert "actions.appendChild(favoriteBtn)" not in sidebar
    assert "const pinItem = createMenuItem" in sidebar
