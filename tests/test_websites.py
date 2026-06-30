from datetime import datetime

import pytest

from database import db
from database.models import WebsiteChunk, WebsiteSource
from services.website_service import (
    WebsiteSourceError,
    normalize_website_url,
    validate_website_url_for_fetch
)


SAMPLE_RESULT = {
    "url": "https://example.com/about",
    "canonical_url": "https://example.com/about",
    "title": "Example About",
    "domain": "example.com",
    "text": (
        "Example Company builds private local AI tools for teams. "
        "This page contains enough readable text for indexing and testing."
    ),
    "http_status": 200,
    "content_type": "text/html",
    "fetched_at": datetime(2026, 6, 28, 12, 0, 0)
}


def test_website_url_normalization():
    assert normalize_website_url(
        "https://Example.COM/about#team"
    ) == "https://example.com/about"

    with pytest.raises(WebsiteSourceError):
        normalize_website_url("ftp://example.com/file")

    with pytest.raises(WebsiteSourceError):
        validate_website_url_for_fetch(
            "http://127.0.0.1/admin"
        )

    with pytest.raises(WebsiteSourceError):
        validate_website_url_for_fetch(
            "http://localhost:5000"
        )


def test_website_source_crud(
    app,
    client,
    monkeypatch
):
    monkeypatch.setattr(
        "routes.website_routes.fetch_website_content",
        lambda _url, _settings: dict(SAMPLE_RESULT)
    )

    monkeypatch.setattr(
        "routes.website_routes.generate_embeddings",
        lambda chunks: [
            [1.0, 0.0, 0.0]
            for _chunk in chunks
        ]
    )

    response = client.post(
        "/api/website-sources",
        json={
            "url": "https://example.com/about"
        }
    )

    assert response.status_code == 201

    payload = response.get_json()
    source_id = payload["website"]["id"]

    assert payload["website"]["status"] == "ready"
    assert payload["website"]["domain"] == "example.com"
    assert payload["website"]["chunk_count"] >= 1

    listing = client.get(
        "/api/website-sources"
    )

    assert listing.status_code == 200
    assert len(listing.get_json()) == 1

    duplicate = client.post(
        "/api/website-sources",
        json={
            "url": "https://example.com/about"
        }
    )

    assert duplicate.status_code == 409

    refreshed_result = dict(SAMPLE_RESULT)
    refreshed_result["title"] = "Updated Example About"
    refreshed_result["text"] = (
        "Updated website content for the Example Company. "
        "This refreshed page includes enough searchable text."
    )

    monkeypatch.setattr(
        "routes.website_routes.fetch_website_content",
        lambda _url, _settings: refreshed_result
    )

    refreshed = client.post(
        f"/api/website-sources/{source_id}/refresh"
    )

    assert refreshed.status_code == 200
    assert (
        refreshed.get_json()["website"]["title"]
        == "Updated Example About"
    )

    with app.app_context():
        source = db.session.get(
            WebsiteSource,
            source_id
        )

        assert source is not None
        assert source.chunk_count >= 1
        assert (
            WebsiteChunk.query
            .filter_by(
                website_source_id=source_id
            )
            .count()
            == source.chunk_count
        )

    deleted = client.delete(
        f"/api/website-sources/{source_id}"
    )

    assert deleted.status_code == 200

    with app.app_context():
        assert db.session.get(
            WebsiteSource,
            source_id
        ) is None


def test_website_source_rejects_invalid_body(client):
    response = client.post(
        "/api/website-sources",
        data="not-json",
        content_type="text/plain"
    )

    assert response.status_code == 400
    assert response.get_json()["code"] == "invalid_json_body"


def test_chat_uses_selected_website_source(
    app,
    client,
    monkeypatch
):
    chat_id = client.post(
        "/api/chats"
    ).get_json()["id"]

    with app.app_context():
        source = WebsiteSource(
            url="https://example.com/about",
            canonical_url="https://example.com/about",
            title="Example About",
            domain="example.com",
            status="ready",
            chunk_count=1,
            text_length=80
        )
        db.session.add(source)
        db.session.flush()

        db.session.add(
            WebsiteChunk(
                website_source_id=source.id,
                chunk_index=0,
                content=(
                    "Example Company was founded in 2024 "
                    "and builds private local AI workspaces."
                ),
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
            "Example Company was founded in 2024."
        ])
    )

    response = client.post(
        "/chat",
        json={
            "prompt": "When was Example Company founded?",
            "model": "test-model",
            "mode": "single",
            "chat_id": chat_id,
            "use_documents": True,
            "strict_documents": True,
            "document_ids": [],
            "use_global_documents": False,
            "global_document_ids": [],
            "use_website_sources": True,
            "website_source_ids": [source_id]
        }
    )

    assert response.status_code == 200
    assert response.headers["X-RAG-Used"] == "true"
    assert response.headers.get("X-RAG-Sources")
    assert "founded in 2024" in response.get_data(
        as_text=True
    )
