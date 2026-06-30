def test_chat_requires_prompt_and_model(
    client
):
    response = client.post(
        "/chat",
        json={}
    )

    assert response.status_code == 400
    assert (
        "Prompt is required"
        in response.get_data(
            as_text=True
        )
    )


def test_chat_rejects_invalid_mode(
    client
):
    response = client.post(
        "/chat",
        json={
            "prompt": "Hello",
            "model": "test-model",
            "mode": "unknown",
            "use_documents": False
        }
    )

    assert response.status_code == 400
