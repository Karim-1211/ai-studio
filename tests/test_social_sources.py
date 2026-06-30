import pytest

from database import db
from database.models import SocialChunk, SocialSource
from services.social_service import (
    SocialSourceError,
    detect_social_platform,
    normalize_social_url
)


MANUAL_TEXT = (
    "Our Facebook page states that the community workshop takes place "
    "on 20 August 2026 at the Central Library. Registration is free."
)


def test_social_platform_detection_and_validation():
    assert detect_social_platform("https://www.facebook.com/example") == "Facebook"
    assert detect_social_platform("https://x.com/example/status/1") == "X"
    assert detect_social_platform("https://www.linkedin.com/company/example") == "LinkedIn"

    normalized, platform = normalize_social_url(
        "https://Instagram.com/example/#post"
    )
    assert normalized == "https://instagram.com/example/"
    assert platform == "Instagram"

    with pytest.raises(SocialSourceError):
        normalize_social_url("https://example.com/not-social")


def test_manual_social_source_crud(
    app,
    client,
    monkeypatch
):
    monkeypatch.setattr(
        "routes.social_routes.generate_embeddings",
        lambda chunks: [[1.0, 0.0, 0.0] for _chunk in chunks]
    )

    response = client.post(
        "/api/social-sources",
        json={
            "url": "https://facebook.com/example/posts/123",
            "title": "Community workshop announcement",
            "manual_text": MANUAL_TEXT
        }
    )

    assert response.status_code == 201
    source = response.get_json()["social_source"]
    assert source["status"] == "ready"
    assert source["platform"] == "Facebook"
    assert source["extraction_method"] == "manual"
    assert source["chunk_count"] >= 1

    listing = client.get("/api/social-sources")
    assert listing.status_code == 200
    assert len(listing.get_json()) == 1

    duplicate = client.post(
        "/api/social-sources",
        json={
            "url": "https://facebook.com/example/posts/123",
            "manual_text": MANUAL_TEXT
        }
    )
    assert duplicate.status_code == 200
    assert duplicate.get_json()["updated"] is True

    cannot_refresh = client.post(
        f"/api/social-sources/{source['id']}/refresh"
    )
    assert cannot_refresh.status_code == 409

    with app.app_context():
        record = db.session.get(SocialSource, source["id"])
        assert record is not None
        assert SocialChunk.query.filter_by(
            social_source_id=source["id"]
        ).count() == record.chunk_count

    deleted = client.delete(f"/api/social-sources/{source['id']}")
    assert deleted.status_code == 200

    with app.app_context():
        assert db.session.get(SocialSource, source["id"]) is None


def test_chat_uses_selected_social_source(
    app,
    client,
    monkeypatch
):
    chat_id = client.post("/api/chats").get_json()["id"]

    with app.app_context():
        source = SocialSource(
            url="https://facebook.com/example/posts/123",
            canonical_url="https://facebook.com/example/posts/123",
            title="Community workshop announcement",
            platform="Facebook",
            domain="facebook.com",
            extraction_method="manual",
            status="ready",
            chunk_count=1,
            text_length=len(MANUAL_TEXT)
        )
        db.session.add(source)
        db.session.flush()
        db.session.add(
            SocialChunk(
                social_source_id=source.id,
                chunk_index=0,
                content=MANUAL_TEXT,
                embedding=[1.0, 0.0, 0.0]
            )
        )
        db.session.commit()
        source_id = source.id

    monkeypatch.setattr(
        "services.rag_service.generate_embedding",
        lambda _query: [1.0, 0.0, 0.0]
    )
    monkeypatch.setattr(
        "routes.chat_routes.stream_ollama_response",
        lambda **_kwargs: iter([
            "The workshop is on 20 August 2026 at the Central Library."
        ])
    )

    response = client.post(
        "/chat",
        json={
            "prompt": "When and where is the workshop?",
            "model": "test-model",
            "mode": "single",
            "chat_id": chat_id,
            "use_documents": True,
            "strict_documents": True,
            "document_ids": [],
            "use_global_documents": False,
            "global_document_ids": [],
            "use_website_sources": False,
            "website_source_ids": [],
            "use_social_sources": True,
            "social_source_ids": [source_id]
        }
    )

    assert response.status_code == 200
    assert response.headers["X-RAG-Used"] == "true"
    assert response.headers.get("X-RAG-Sources")
    assert "20 August 2026" in response.get_data(as_text=True)
