def test_security_headers(
    client
):
    response = client.get(
        "/"
    )

    assert response.status_code == 200
    assert (
        response.headers[
            "X-Content-Type-Options"
        ]
        == "nosniff"
    )
    assert (
        response.headers[
            "X-Frame-Options"
        ]
        == "DENY"
    )
    assert (
        "Content-Security-Policy"
        in response.headers
    )
    assert (
        "X-Request-ID"
        in response.headers
    )
