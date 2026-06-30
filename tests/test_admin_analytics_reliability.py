from pathlib import Path

import pytest

from app import create_app
from database import db
from database.models import (
    AuditLog,
    Chat,
    User,
    HealthCheckEvent,
    Message,
    ModelUsageEvent,
    RequestMetric,
)
from services.auth_service import create_user
from services.rate_limit_service import SlidingWindowRateLimiter


@pytest.fixture()
def admin_app(tmp_path):
    app = create_app({
        "TESTING": True,
        "DEBUG": False,
        "AUTH_REQUIRED": True,
        "WTF_CSRF_ENABLED": False,
        "AUTO_CREATE_DATABASE": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'admin.db'}",
        "SQLALCHEMY_ENGINE_OPTIONS": {},
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        "LOG_FOLDER": str(tmp_path / "logs"),
        "SECURITY_HEADERS_ENABLED": True,
        "OCR_ENABLED": False,
        "METRICS_ENABLED": True,
    })
    with app.app_context():
        db.create_all()
        create_user(
            email="admin@example.com",
            display_name="Administrator",
            password="VerySecure123!",
            is_admin=True,
        )
        create_user(
            email="member@example.com",
            display_name="Member User",
            password="VerySecure123!",
            is_admin=False,
        )
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def admin_client(admin_app):
    client = admin_app.test_client()
    response = client.post(
        "/login",
        data={"email": "admin@example.com", "password": "VerySecure123!"},
    )
    assert response.status_code == 302
    return client


def test_admin_dashboard_and_analytics(admin_app, admin_client):
    with admin_app.app_context():
        user = db.session.execute(
            db.select(User).where(User.email == "admin@example.com")
        ).scalar_one()
        chat = Chat(user_id=user.id, title="Analytics chat")
        db.session.add(chat)
        db.session.flush()
        db.session.add_all([
            Message(chat_id=chat.id, role="user", content="Hello"),
            Message(chat_id=chat.id, role="bot", content="Hi", model="gemma3:4b"),
            ModelUsageEvent(
                user_id=user.id,
                chat_id=chat.id,
                model="gemma3:4b",
                mode="detailed",
                duration_ms=1250,
                success=True,
                used_rag=False,
                source_count=0,
            ),
        ])
        db.session.commit()

    page = admin_client.get("/admin/dashboard")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert "Admin dashboard" in html
    assert "User activity and storage" in html

    response = admin_client.get("/api/admin/analytics?days=30")
    assert response.status_code == 200
    data = response.get_json()
    assert data["summary"]["users"] == 2
    assert data["summary"]["chats"] == 1
    assert data["summary"]["messages"] == 2
    assert data["model_usage"][0]["model"] == "gemma3:4b"


def test_non_admin_cannot_open_dashboard(admin_app):
    client = admin_app.test_client()
    client.post(
        "/login",
        data={"email": "member@example.com", "password": "VerySecure123!"},
    )
    response = client.get("/admin/dashboard")
    assert response.status_code == 403


def test_admin_cleanup_preview_and_delete(admin_app, admin_client):
    upload_folder = Path(admin_app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)
    orphan = upload_folder / "orphan.txt"
    orphan.write_text("unused")

    preview = admin_client.get("/api/admin/cleanup/preview")
    assert preview.status_code == 200
    assert preview.get_json()["count"] == 1

    rejected = admin_client.post(
        "/api/admin/cleanup/orphans",
        json={"confirm": False},
    )
    assert rejected.status_code == 400
    assert orphan.exists()

    removed = admin_client.post(
        "/api/admin/cleanup/orphans",
        json={"confirm": True},
    )
    assert removed.status_code == 200
    assert not orphan.exists()

    with admin_app.app_context():
        assert AuditLog.query.filter_by(action="storage.orphan_cleanup").count() == 1


def test_request_and_model_telemetry(client, app, monkeypatch):
    response = client.get("/api/chats")
    assert response.status_code == 200

    monkeypatch.setattr(
        "routes.chat_routes.stream_ollama_response",
        lambda **_kwargs: iter(["Telemetry response"]),
    )
    chat_response = client.post(
        "/chat",
        json={
            "prompt": "Hello",
            "model": "test-model",
            "mode": "single",
            "use_documents": False,
        },
    )
    assert chat_response.status_code == 200
    assert chat_response.get_data(as_text=True) == "Telemetry response"

    with app.app_context():
        assert RequestMetric.query.filter_by(path="/api/chats").count() == 1
        event = ModelUsageEvent.query.filter_by(model="test-model").one()
        assert event.success is True
        assert event.duration_ms >= 0


def test_health_history_is_sampled(client, app, monkeypatch):
    result = {
        "status": "ready",
        "ready": True,
        "components": {
            "database": {"ok": True, "status": "ready", "latency_ms": 1.0},
        },
    }
    monkeypatch.setattr("routes.health_routes.get_system_health", lambda _config: result)

    assert client.get("/api/health").status_code == 200
    assert client.get("/api/health").status_code == 200

    with app.app_context():
        assert HealthCheckEvent.query.count() == 1


def test_sliding_window_rate_limiter():
    limiter = SlidingWindowRateLimiter()
    assert limiter.check("user", 2, 60, now=100)[0] is True
    assert limiter.check("user", 2, 60, now=101)[0] is True
    allowed, remaining, retry_after = limiter.check("user", 2, 60, now=102)
    assert allowed is False
    assert remaining == 0
    assert retry_after > 0
    assert limiter.check("user", 2, 60, now=161)[0] is True


def test_rate_limit_integration(tmp_path):
    from services.rate_limit_service import rate_limiter

    rate_limiter.reset()
    limited_app = create_app({
        "TESTING": False,
        "DEBUG": True,
        "AUTH_REQUIRED": False,
        "WTF_CSRF_ENABLED": False,
        "AUTO_CREATE_DATABASE": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'rate-limit.db'}",
        "SQLALCHEMY_ENGINE_OPTIONS": {},
        "UPLOAD_FOLDER": str(tmp_path / "uploads-rate"),
        "LOG_FOLDER": str(tmp_path / "logs-rate"),
        "OCR_ENABLED": False,
        "RATE_LIMIT_ENABLED": True,
        "RATE_LIMIT_API_PER_MINUTE": 1,
        "METRICS_ENABLED": False,
    })
    with limited_app.app_context():
        db.create_all()

    limited_client = limited_app.test_client()
    first = limited_client.post("/api/chats", json={"title": "Allowed"})
    second = limited_client.post("/api/chats", json={"title": "Blocked"})

    assert first.status_code == 201
    assert second.status_code == 429
    assert second.get_json()["code"] == "rate_limit_exceeded"
    assert second.headers["X-RateLimit-Remaining"] == "0"

    with limited_app.app_context():
        db.session.remove()
        db.drop_all()
    rate_limiter.reset()


def test_admin_dashboard_can_disable_and_enable_member(admin_app, admin_client):
    with admin_app.app_context():
        member = User.query.filter_by(email="member@example.com").one()
        member_id = member.id

    disabled = admin_client.post(
        f"/api/admin/users/{member_id}/status",
        json={"active": False},
    )
    assert disabled.status_code == 200
    assert disabled.get_json()["active"] is False

    enabled = admin_client.post(
        f"/api/admin/users/{member_id}/status",
        json={"active": True},
    )
    assert enabled.status_code == 200
    assert enabled.get_json()["active"] is True

    with admin_app.app_context():
        member = db.session.get(User, member_id)
        assert member.active is True
        assert AuditLog.query.filter_by(
            action="admin.user_status_changed",
            target_user_id=member_id,
        ).count() == 2
