from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_folder_tag_and_chat_organization_crud(client):
    folder_response = client.post(
        "/api/chat-folders",
        json={"name": "Client work"},
    )
    assert folder_response.status_code == 201
    folder = folder_response.get_json()

    tag_response = client.post(
        "/api/chat-tags",
        json={"name": "Urgent", "color": "rose"},
    )
    assert tag_response.status_code == 201
    tag = tag_response.get_json()

    chat_response = client.post(
        "/api/chats",
        json={"title": "Campaign plan", "folder_id": folder["id"]},
    )
    assert chat_response.status_code == 201
    chat_id = chat_response.get_json()["id"]

    update = client.patch(
        f"/api/chats/{chat_id}",
        json={
            "is_favorite": True,
            "tag_ids": [tag["id"]],
        },
    )
    assert update.status_code == 200
    payload = update.get_json()
    assert payload["is_favorite"] is True
    assert payload["folder"]["name"] == "Client work"
    assert payload["tags"][0]["name"] == "Urgent"

    favorites = client.get("/api/chats?view=favorites")
    assert favorites.status_code == 200
    assert [item["id"] for item in favorites.get_json()] == [chat_id]

    archive = client.patch(
        f"/api/chats/{chat_id}",
        json={"is_archived": True},
    )
    assert archive.status_code == 200
    assert archive.get_json()["is_archived"] is True

    active = client.get("/api/chats")
    assert active.get_json() == []
    archived = client.get("/api/chats?view=archived")
    assert [item["id"] for item in archived.get_json()] == [chat_id]


def test_bulk_chat_actions(client):
    folder = client.post(
        "/api/chat-folders",
        json={"name": "Research"},
    ).get_json()
    tag = client.post(
        "/api/chat-tags",
        json={"name": "Reference", "color": "cyan"},
    ).get_json()
    first = client.post("/api/chats", json={"title": "One"}).get_json()
    second = client.post("/api/chats", json={"title": "Two"}).get_json()
    ids = [first["id"], second["id"]]

    moved = client.post(
        "/api/chats/bulk",
        json={"chat_ids": ids, "action": "move", "folder_id": folder["id"]},
    )
    assert moved.status_code == 200
    assert moved.get_json()["affected"] == 2

    tagged = client.post(
        "/api/chats/bulk",
        json={"chat_ids": ids, "action": "add_tag", "tag_id": tag["id"]},
    )
    assert tagged.status_code == 200

    archived = client.post(
        "/api/chats/bulk",
        json={"chat_ids": ids, "action": "archive"},
    )
    assert archived.status_code == 200

    listing = client.get(
        f"/api/chats?view=archived&folder_id={folder['id']}&tag_id={tag['id']}"
    )
    assert len(listing.get_json()) == 2


def test_chat_organization_interface_is_present(client):
    page = client.get("/").get_data(as_text=True)
    template = (PROJECT_ROOT / "templates" / "index.html").read_text(
        encoding="utf-8"
    )
    sidebar = (PROJECT_ROOT / "static" / "js" / "sidebar.js").read_text(
        encoding="utf-8"
    )

    assert 'id="chatOrganizerToggle"' in page
    assert 'id="chatFolderList"' in page
    assert 'id="chatBulkToolbar"' in page
    assert 'id="workspaceBackupButton"' in template
    assert 'id="workspaceRestoreButton"' in template
    assert "dragstart" in sidebar
    assert "bulkUpdateChats" in sidebar
