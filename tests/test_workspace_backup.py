import io
import json
import zipfile

from app import create_app
from database import db
from database.models import Chat, Message
from services.auth_service import create_user


def test_authenticated_workspace_backup_and_restore(tmp_path):
    app = create_app({
        "TESTING": True,
        "DEBUG": False,
        "AUTH_REQUIRED": True,
        "WTF_CSRF_ENABLED": False,
        "AUTO_CREATE_DATABASE": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'backup.db'}",
        "SQLALCHEMY_ENGINE_OPTIONS": {},
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        "LOG_FOLDER": str(tmp_path / "logs"),
        "SECURITY_HEADERS_ENABLED": True,
        "OCR_ENABLED": False,
    })

    with app.app_context():
        db.create_all()
        user = create_user(
            email="backup@example.com",
            display_name="Backup User",
            password="VerySecure123!",
        )
        chat = Chat(user_id=user.id, title="Backup chat", is_favorite=True)
        db.session.add(chat)
        db.session.flush()
        db.session.add(Message(chat_id=chat.id, role="user", content="Hello backup"))
        db.session.commit()

    client = app.test_client()
    login = client.post(
        "/login",
        data={"email": "backup@example.com", "password": "VerySecure123!"},
    )
    assert login.status_code == 302

    response = client.get("/api/workspace/backup")
    assert response.status_code == 200
    assert response.mimetype == "application/zip"

    backup_bytes = response.data
    with zipfile.ZipFile(io.BytesIO(backup_bytes)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["format"] == "ai-studio-workspace"
        assert manifest["chats"][0]["title"] == "Backup chat"
        assert manifest["chats"][0]["messages"][0]["content"] == "Hello backup"

    restored = client.post(
        "/api/workspace/restore",
        data={
            "backup": (io.BytesIO(backup_bytes), "workspace.zip"),
        },
        content_type="multipart/form-data",
    )
    assert restored.status_code == 200
    assert restored.get_json()["summary"]["chats"] == 1

    with app.app_context():
        assert Chat.query.count() == 2

    with app.app_context():
        db.session.remove()
        db.drop_all()
