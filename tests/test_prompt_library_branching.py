from database import db
from database.models import Chat, Message, PromptTemplate


def test_prompt_template_crud_and_usage(client, app):
    created = client.post(
        "/api/prompt-templates",
        json={
            "title": "Professional rewrite",
            "content": "Rewrite the following text in a professional tone.",
            "category": "Writing",
            "is_favorite": True,
        },
    )
    assert created.status_code == 201
    prompt = created.get_json()
    assert prompt["title"] == "Professional rewrite"
    assert prompt["is_favorite"] is True
    assert prompt["usage_count"] == 0

    listing = client.get("/api/prompt-templates?category=Writing")
    assert listing.status_code == 200
    assert [item["id"] for item in listing.get_json()] == [prompt["id"]]

    used = client.post(f"/api/prompt-templates/{prompt['id']}/use")
    assert used.status_code == 200
    assert used.get_json()["usage_count"] == 1

    updated = client.patch(
        f"/api/prompt-templates/{prompt['id']}",
        json={"title": "Client-ready rewrite", "is_favorite": False},
    )
    assert updated.status_code == 200
    assert updated.get_json()["title"] == "Client-ready rewrite"
    assert updated.get_json()["is_favorite"] is False

    deleted = client.delete(f"/api/prompt-templates/{prompt['id']}")
    assert deleted.status_code == 200

    with app.app_context():
        assert PromptTemplate.query.count() == 0


def test_branch_chat_copies_messages_through_target(client, app):
    chat = client.post("/api/chats", json={"title": "Original"}).get_json()
    first = client.post(
        f"/api/chats/{chat['id']}/messages",
        json={"role": "user", "content": "Question one"},
    ).get_json()
    second = client.post(
        f"/api/chats/{chat['id']}/messages",
        json={"role": "bot", "content": "Answer one"},
    ).get_json()
    client.post(
        f"/api/chats/{chat['id']}/messages",
        json={"role": "user", "content": "Question two"},
    )

    response = client.post(
        f"/api/chats/{chat['id']}/branch",
        json={
            "message_id": second["id"],
            "include_target": True,
            "title": "Alternative direction",
        },
    )
    assert response.status_code == 201
    branch = response.get_json()
    assert branch["parent_chat_id"] == chat["id"]
    assert branch["branched_from_message_id"] == second["id"]

    messages = client.get(
        f"/api/chats/{branch['id']}/messages"
    ).get_json()
    assert [item["content"] for item in messages] == [
        "Question one",
        "Answer one",
    ]

    with app.app_context():
        stored = db.session.get(Chat, branch["id"])
        assert stored.parent_chat_id == chat["id"]
        assert Message.query.filter_by(chat_id=stored.id).count() == 2


def test_edit_branch_excludes_target_message(client):
    chat = client.post("/api/chats", json={"title": "Editing"}).get_json()
    first = client.post(
        f"/api/chats/{chat['id']}/messages",
        json={"role": "user", "content": "First prompt"},
    ).get_json()
    client.post(
        f"/api/chats/{chat['id']}/messages",
        json={"role": "bot", "content": "First answer"},
    )
    third = client.post(
        f"/api/chats/{chat['id']}/messages",
        json={"role": "user", "content": "Original follow-up"},
    ).get_json()

    response = client.post(
        f"/api/chats/{chat['id']}/branch",
        json={"message_id": third["id"], "include_target": False},
    )
    assert response.status_code == 201
    branch = response.get_json()
    messages = client.get(f"/api/chats/{branch['id']}/messages").get_json()
    assert [item["content"] for item in messages] == [
        "First prompt",
        "First answer",
    ]
    assert branch["branched_from_message_id"] == third["id"]
    assert first["id"] != third["id"]
