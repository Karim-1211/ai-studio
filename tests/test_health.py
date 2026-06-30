def test_liveness(
    client
):
    response = client.get(
        "/api/health/live"
    )

    assert response.status_code == 200
    assert response.get_json()[
        "status"
    ] == "alive"


def test_health_endpoint(
    client,
    monkeypatch
):
    fake_health = {
        "status": "ready",
        "ready": True,
        "components": {
            "database": {
                "ok": True,
                "status": "ready",
                "message": "ok"
            },
            "ollama": {
                "ok": True,
                "status": "ready",
                "message": "ok"
            },
            "embedding": {
                "ok": True,
                "status": "ready",
                "message": "ok"
            },
            "ocr": {
                "ok": True,
                "status": "ready",
                "message": "ok"
            },
            "uploads": {
                "ok": True,
                "status": "ready",
                "message": "ok"
            }
        }
    }

    monkeypatch.setattr(
        "routes.health_routes.get_system_health",
        lambda _config: fake_health
    )

    response = client.get(
        "/api/health"
    )

    assert response.status_code == 200
    assert response.get_json()[
        "status"
    ] == "ready"

    ready_response = client.get(
        "/api/health/ready"
    )

    assert ready_response.status_code == 200
