import io
from pathlib import Path

from database import db
from database.models import MessageAttachment


def fake_extraction(*_args, **_kwargs):
    return {
        "text": (
            "The attached report says the launch date is 15 July 2026. "
            "This text is long enough to create a searchable attachment chunk."
        ),
        "method": "native",
        "ocr_used": False,
        "pages_processed": 1
    }


def fake_embeddings(chunks):
    return [[1.0, 0.0, 0.0] for _chunk in chunks]


def test_text_attachment_upload_save_and_delete_with_chat(
    app,
    client,
    monkeypatch
):
    monkeypatch.setattr(
        "routes.attachment_routes.extract_text_from_file",
        fake_extraction
    )
    monkeypatch.setattr(
        "routes.attachment_routes.generate_embeddings",
        fake_embeddings
    )

    chat_id = client.post("/api/chats").get_json()["id"]

    upload = client.post(
        f"/api/chats/{chat_id}/attachments",
        data={
            "file": (
                io.BytesIO(b"attachment content"),
                "launch-report.txt"
            )
        },
        content_type="multipart/form-data"
    )

    assert upload.status_code == 201
    attachment = upload.get_json()["attachment"]
    assert attachment["status"] == "ready"
    assert attachment["chunk_count"] == 1

    with app.app_context():
        record = db.session.get(MessageAttachment, attachment["id"])
        stored_path = Path(app.config["UPLOAD_FOLDER"]) / record.stored_filename
        assert stored_path.exists()
        assert record.message_id is None

    saved = client.post(
        f"/api/chats/{chat_id}/messages",
        json={
            "role": "user",
            "content": "When is the launch?",
            "attachment_ids": [attachment["id"]]
        }
    )

    assert saved.status_code == 201
    assert saved.get_json()["attachments"][0]["id"] == attachment["id"]

    messages = client.get(
        f"/api/chats/{chat_id}/messages"
    ).get_json()
    assert messages[0]["attachments"][0]["original_filename"] == "launch-report.txt"

    cannot_remove_sent = client.delete(
        f"/api/attachments/{attachment['id']}"
    )
    assert cannot_remove_sent.status_code == 409

    deleted_chat = client.delete(f"/api/chats/{chat_id}")
    assert deleted_chat.status_code == 200
    assert not stored_path.exists()


def test_chat_uses_selected_attachment_text(
    client,
    monkeypatch
):
    monkeypatch.setattr(
        "routes.attachment_routes.extract_text_from_file",
        fake_extraction
    )
    monkeypatch.setattr(
        "routes.attachment_routes.generate_embeddings",
        fake_embeddings
    )
    monkeypatch.setattr(
        "services.rag_service.generate_embedding",
        lambda _query: [1.0, 0.0, 0.0]
    )
    monkeypatch.setattr(
        "routes.chat_routes.stream_ollama_response",
        lambda **_kwargs: iter(["The launch date is 15 July 2026."])
    )

    chat_id = client.post("/api/chats").get_json()["id"]
    upload = client.post(
        f"/api/chats/{chat_id}/attachments",
        data={
            "file": (
                io.BytesIO(b"attachment content"),
                "launch-report.txt"
            )
        },
        content_type="multipart/form-data"
    )
    attachment_id = upload.get_json()["attachment"]["id"]

    response = client.post(
        "/chat",
        json={
            "prompt": "When is the launch?",
            "model": "test-model",
            "mode": "single",
            "chat_id": chat_id,
            "use_documents": False,
            "strict_documents": True,
            "attachment_ids": [attachment_id]
        }
    )

    assert response.status_code == 200
    assert response.headers["X-RAG-Used"] == "true"
    assert response.headers.get("X-RAG-Sources")
    assert "15 July 2026" in response.get_data(as_text=True)


def test_pending_attachment_can_be_removed(
    app,
    client,
    monkeypatch
):
    monkeypatch.setattr(
        "routes.attachment_routes.extract_text_from_file",
        fake_extraction
    )
    monkeypatch.setattr(
        "routes.attachment_routes.generate_embeddings",
        fake_embeddings
    )

    chat_id = client.post("/api/chats").get_json()["id"]
    upload = client.post(
        f"/api/chats/{chat_id}/attachments",
        data={
            "file": (io.BytesIO(b"temporary"), "temporary.txt")
        },
        content_type="multipart/form-data"
    )
    attachment_id = upload.get_json()["attachment"]["id"]

    with app.app_context():
        record = db.session.get(MessageAttachment, attachment_id)
        stored_path = Path(app.config["UPLOAD_FOLDER"]) / record.stored_filename
        assert stored_path.exists()

    response = client.delete(f"/api/attachments/{attachment_id}")
    assert response.status_code == 200
    assert not stored_path.exists()


def test_image_attachment_is_sent_to_vision_model(
    client,
    monkeypatch
):
    from PIL import Image

    image_bytes = io.BytesIO()
    Image.new("RGB", (24, 24), "white").save(image_bytes, format="PNG")
    image_bytes.seek(0)

    chat_id = client.post("/api/chats").get_json()["id"]
    upload = client.post(
        f"/api/chats/{chat_id}/attachments",
        data={
            "file": (image_bytes, "screenshot.png")
        },
        content_type="multipart/form-data"
    )

    assert upload.status_code == 201
    attachment = upload.get_json()["attachment"]
    assert attachment["attachment_kind"] == "image"
    assert attachment["preview_url"]

    captured = {}
    monkeypatch.setattr(
        "routes.chat_routes.find_vision_model",
        lambda selected_model, preferred_model=None: selected_model
    )
    monkeypatch.setattr(
        "routes.chat_routes.model_supports_vision",
        lambda _model: True
    )

    def fake_stream(**kwargs):
        captured.update(kwargs)
        return iter(["The screenshot contains a blank white image."])

    monkeypatch.setattr(
        "routes.chat_routes.stream_ollama_response",
        fake_stream
    )

    response = client.post(
        "/chat",
        json={
            "prompt": "Describe this screenshot.",
            "model": "vision-test-model",
            "mode": "single",
            "chat_id": chat_id,
            "use_documents": False,
            "strict_documents": True,
            "attachment_ids": [attachment["id"]]
        }
    )

    assert response.status_code == 200
    assert len(captured["image_paths"]) == 1
    assert captured["image_paths"][0].endswith(".png")
    assert "blank white image" in response.get_data(as_text=True)


def test_pending_attachment_count_limit(
    app,
    client,
    monkeypatch
):
    app.config["ATTACHMENT_MAX_FILES"] = 1
    monkeypatch.setattr(
        "routes.attachment_routes.extract_text_from_file",
        fake_extraction
    )
    monkeypatch.setattr(
        "routes.attachment_routes.generate_embeddings",
        fake_embeddings
    )

    chat_id = client.post("/api/chats").get_json()["id"]
    first = client.post(
        f"/api/chats/{chat_id}/attachments",
        data={"file": (io.BytesIO(b"one"), "one.txt")},
        content_type="multipart/form-data"
    )
    second = client.post(
        f"/api/chats/{chat_id}/attachments",
        data={"file": (io.BytesIO(b"two"), "two.txt")},
        content_type="multipart/form-data"
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.get_json()["code"] == "attachment_count_limit"
