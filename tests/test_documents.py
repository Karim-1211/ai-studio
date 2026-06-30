import io
from pathlib import Path

from database import db

from database.models import (
    Document,
    GlobalDocument
)


def fake_extraction(
    *_args,
    **_kwargs
):
    return {
        "text": (
            "This is searchable test "
            "document content."
        ),
        "method": "native",
        "ocr_used": False,
        "pages_processed": 1,
        "native_pages": 1,
        "ocr_pages": 0
    }


def fake_embeddings(
    chunks
):
    return [
        [
            0.1,
            0.2,
            0.3
        ]
        for _chunk in chunks
    ]


def test_chat_document_upload_and_delete(
    app,
    client,
    monkeypatch
):
    monkeypatch.setattr(
        "routes.document_routes.extract_text_from_file",
        fake_extraction
    )

    monkeypatch.setattr(
        "routes.document_routes.generate_embeddings",
        fake_embeddings
    )

    chat_id = client.post(
        "/api/chats"
    ).get_json()["id"]

    response = client.post(
        f"/api/chats/{chat_id}/documents",
        data={
            "file": (
                io.BytesIO(
                    b"test document"
                ),
                "test.txt"
            )
        },
        content_type="multipart/form-data"
    )

    assert response.status_code == 201

    payload = response.get_json()
    document_id = payload[
        "document"
    ]["id"]

    with app.app_context():
        document = (
            db.session.get(
                Document,
                document_id
            )
        )

        stored_path = (
            Path(
                app.config[
                    "UPLOAD_FOLDER"
                ]
            )
            / document.stored_filename
        )

        assert stored_path.exists()
        assert document.status == "ready"
        assert document.chunk_count == 1

    delete_response = client.delete(
        f"/api/documents/{document_id}"
    )

    assert delete_response.status_code == 200
    assert not stored_path.exists()


def test_global_document_upload_and_delete(
    app,
    client,
    monkeypatch
):
    monkeypatch.setattr(
        "routes.global_document_routes.extract_text_from_file",
        fake_extraction
    )

    monkeypatch.setattr(
        "routes.global_document_routes.generate_embeddings",
        fake_embeddings
    )

    response = client.post(
        "/api/global-documents",
        data={
            "file": (
                io.BytesIO(
                    b"global document"
                ),
                "global.txt"
            )
        },
        content_type="multipart/form-data"
    )

    assert response.status_code == 201

    document_id = (
        response
        .get_json()[
            "document"
        ][
            "id"
        ]
    )

    with app.app_context():
        document = (
            db.session.get(
                GlobalDocument,
                document_id
            )
        )

        stored_path = (
            Path(
                app.config[
                    "UPLOAD_FOLDER"
                ]
            )
            / document.stored_filename
        )

        assert stored_path.exists()

    delete_response = client.delete(
        (
            "/api/global-documents/"
            f"{document_id}"
        )
    )

    assert delete_response.status_code == 200
    assert not stored_path.exists()


def test_unsupported_document_type(
    client
):
    chat_id = client.post(
        "/api/chats"
    ).get_json()["id"]

    response = client.post(
        f"/api/chats/{chat_id}/documents",
        data={
            "file": (
                io.BytesIO(
                    b"binary"
                ),
                "malware.exe"
            )
        },
        content_type="multipart/form-data"
    )

    assert response.status_code == 400
    assert response.get_json()[
        "code"
    ] == "unsupported_file_type"
