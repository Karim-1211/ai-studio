from io import BytesIO
from pathlib import Path


def test_oversized_prompt_is_rejected_before_model_call(client):
    response = client.post(
        "/chat",
        json={
            "prompt": "x" * 50_001,
            "model": "test-model",
            "mode": "single",
            "use_documents": False,
        },
    )
    assert response.status_code == 413
    assert "50,000" in response.get_data(as_text=True)


def test_attachment_file_limit_removes_rejected_file(client, app):
    app.config["ATTACHMENT_MAX_FILE_BYTES"] = 10
    chat = client.post("/api/chats", json={"title": "Limits"}).get_json()

    response = client.post(
        f"/api/chats/{chat['id']}/attachments",
        data={"file": (BytesIO(b"0123456789abcdef"), "large.txt")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 413
    assert response.get_json()["code"] == "attachment_too_large"

    upload_folder = Path(app.config["UPLOAD_FOLDER"])
    assert list(upload_folder.glob("*")) == []
