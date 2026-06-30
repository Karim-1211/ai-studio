from pathlib import Path

from database import db

from database.models import (
    Chat,
    Document
)


def test_chat_crud_and_messages(
    client
):
    create_response = client.post(
        "/api/chats"
    )

    assert create_response.status_code == 201

    chat = create_response.get_json()
    chat_id = chat["id"]

    list_response = client.get(
        "/api/chats"
    )

    assert list_response.status_code == 200
    assert any(
        item["id"] == chat_id
        for item in list_response.get_json()
    )

    update_response = client.patch(
        f"/api/chats/{chat_id}",
        json={
            "title": "Production test",
            "is_pinned": True
        }
    )

    assert update_response.status_code == 200
    assert (
        update_response.get_json()[
            "title"
        ]
        == "Production test"
    )

    message_response = client.post(
        f"/api/chats/{chat_id}/messages",
        json={
            "role": "user",
            "content": "Hello",
            "model": "test-model",
            "mode": "single"
        }
    )

    assert message_response.status_code == 201

    messages_response = client.get(
        f"/api/chats/{chat_id}/messages"
    )

    assert messages_response.status_code == 200
    assert (
        messages_response.get_json()[0][
            "content"
        ]
        == "Hello"
    )


def test_chat_validation(
    client
):
    chat_id = client.post(
        "/api/chats"
    ).get_json()["id"]

    response = client.patch(
        f"/api/chats/{chat_id}",
        json={
            "title": ""
        }
    )

    assert response.status_code == 400
    assert response.get_json()[
        "code"
    ] == "invalid_chat_title"

    response = client.post(
        f"/api/chats/{chat_id}/messages",
        json={
            "role": "invalid",
            "content": "Hello"
        }
    )

    assert response.status_code == 400


def test_deleting_chat_removes_file(
    app,
    client
):
    with app.app_context():
        chat = Chat(
            title="Delete me"
        )

        db.session.add(
            chat
        )
        db.session.commit()

        stored_filename = (
            "chat-delete-test.txt"
        )

        upload_path = (
            Path(
                app.config[
                    "UPLOAD_FOLDER"
                ]
            )
            / stored_filename
        )

        upload_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        upload_path.write_text(
            "temporary",
            encoding="utf-8"
        )

        document = Document(
            chat_id=chat.id,
            original_filename="test.txt",
            stored_filename=stored_filename,
            file_type="txt",
            file_size=9,
            status="ready",
            chunk_count=0,
            text_length=9
        )

        db.session.add(
            document
        )
        db.session.commit()

        chat_id = chat.id

    response = client.delete(
        f"/api/chats/{chat_id}"
    )

    assert response.status_code == 200
    assert response.get_json()[
        "success"
    ] is True
    assert not upload_path.exists()

    with app.app_context():
        assert db.session.get(
            Chat,
            chat_id
        ) is None
