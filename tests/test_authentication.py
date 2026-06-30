from pathlib import Path

import pytest

from app import create_app
from database import db
from database.models import Chat, GlobalDocument, User, WebsiteSource
from database.crud import add_website_source_to_user
from services.auth_service import create_user


@pytest.fixture()
def auth_app(tmp_path):
    app = create_app({
        "TESTING": True,
        "DEBUG": False,
        "AUTH_REQUIRED": True,
        "ALLOW_REGISTRATION": False,
        "WTF_CSRF_ENABLED": False,
        "AUTO_CREATE_DATABASE": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'auth.db'}",
        "SQLALCHEMY_ENGINE_OPTIONS": {},
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        "LOG_FOLDER": str(tmp_path / "logs"),
        "SECURITY_HEADERS_ENABLED": True,
        "OCR_ENABLED": False,
    })

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def auth_client(auth_app):
    return auth_app.test_client()


def make_user(app, email, name, admin=False):
    with app.app_context():
        return create_user(
            email=email,
            display_name=name,
            password="VerySecure123!",
            is_admin=admin,
        ).id


def login(client, email):
    return client.post(
        "/login",
        data={
            "email": email,
            "password": "VerySecure123!",
        },
        follow_redirects=False,
    )


def test_authentication_is_required(auth_client):
    response = auth_client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    api_response = auth_client.get("/api/chats")
    assert api_response.status_code == 401
    assert api_response.get_json()["code"] == "authentication_required"


def test_owner_can_sign_in_and_render_workspace(auth_app, auth_client):
    make_user(auth_app, "owner@example.com", "Owner", admin=True)

    response = login(auth_client, "owner@example.com")
    assert response.status_code == 302

    workspace = auth_client.get("/")
    assert workspace.status_code == 200
    html = workspace.get_data(as_text=True)
    assert "Owner" in html
    assert 'name="csrf-token"' in html
    assert "Account settings" in html


def test_chats_are_isolated_between_users(auth_app, auth_client):
    first_id = make_user(auth_app, "first@example.com", "First")
    second_id = make_user(auth_app, "second@example.com", "Second")

    login(auth_client, "first@example.com")
    created = auth_client.post("/api/chats", json={"title": "Private chat"})
    assert created.status_code == 201
    chat_id = created.get_json()["id"]

    auth_client.post("/logout")
    login(auth_client, "second@example.com")

    chats = auth_client.get("/api/chats")
    assert chats.status_code == 200
    assert chats.get_json() == []

    other_chat = auth_client.get(f"/api/chats/{chat_id}/messages")
    assert other_chat.status_code == 404

    with auth_app.app_context():
        assert db.session.get(Chat, chat_id).user_id == first_id
        assert first_id != second_id


def test_global_documents_are_isolated(auth_app, auth_client):
    first_id = make_user(auth_app, "first@example.com", "First")
    make_user(auth_app, "second@example.com", "Second")

    with auth_app.app_context():
        db.session.add(
            GlobalDocument(
                user_id=first_id,
                original_filename="private.txt",
                stored_filename="private-uuid.txt",
                file_type="txt",
                file_size=7,
                status="ready",
            )
        )
        db.session.commit()

    login(auth_client, "second@example.com")
    response = auth_client.get("/api/global-documents")
    assert response.status_code == 200
    assert response.get_json() == []


def test_public_website_source_membership_is_per_user(auth_app, auth_client):
    first_id = make_user(auth_app, "first@example.com", "First")
    make_user(auth_app, "second@example.com", "Second")

    with auth_app.app_context():
        source = WebsiteSource(
            url="https://example.com/",
            canonical_url="https://example.com/",
            title="Example",
            domain="example.com",
            status="ready",
            chunk_count=0,
            text_length=100,
        )
        db.session.add(source)
        db.session.commit()
        add_website_source_to_user(source, user_id=first_id)

    login(auth_client, "second@example.com")
    response = auth_client.get("/api/website-sources")
    assert response.status_code == 200
    assert response.get_json() == []


def test_public_registration_is_disabled(auth_client):
    response = auth_client.get("/register", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def _extract_csrf(html):
    import re
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match
    return match.group(1)


def test_csrf_protects_authenticated_api(tmp_path):
    app = create_app({
        "TESTING": True,
        "DEBUG": False,
        "AUTH_REQUIRED": True,
        "ALLOW_REGISTRATION": False,
        "WTF_CSRF_ENABLED": True,
        "AUTO_CREATE_DATABASE": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'csrf.db'}",
        "SQLALCHEMY_ENGINE_OPTIONS": {},
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        "LOG_FOLDER": str(tmp_path / "logs"),
        "SECURITY_HEADERS_ENABLED": True,
        "OCR_ENABLED": False,
    })

    with app.app_context():
        db.create_all()
        create_user(
            email="csrf@example.com",
            display_name="CSRF User",
            password="VerySecure123!",
        )

    client = app.test_client()
    login_page = client.get("/login")
    login_token = _extract_csrf(login_page.get_data(as_text=True))
    login_response = client.post(
        "/login",
        data={
            "csrf_token": login_token,
            "email": "csrf@example.com",
            "password": "VerySecure123!",
        },
    )
    assert login_response.status_code == 302

    rejected = client.post("/api/chats", json={"title": "Rejected"})
    assert rejected.status_code == 400
    assert rejected.get_json()["code"] == "csrf_failed"

    workspace = client.get("/")
    import re
    meta_match = re.search(
        r'name="csrf-token" content="([^"]+)"',
        workspace.get_data(as_text=True),
    )
    assert meta_match

    accepted = client.post(
        "/api/chats",
        json={"title": "Accepted"},
        headers={"X-CSRFToken": meta_match.group(1)},
    )
    assert accepted.status_code == 201

    with app.app_context():
        db.session.remove()
        db.drop_all()
