"""Embedding provider abstraction for AI Studio.

Cloud Edition v1.0 supports Gemini embeddings for Render/Neon deployments
and keeps Ollama embeddings for local development.
"""

import requests

from config import (
    AI_PROVIDER,
    EMBEDDING_MODEL,
    EMBEDDING_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_BASE_URL,
    OLLAMA_URL,
)


class EmbeddingServiceError(Exception):
    pass


def get_embedding_provider():
    provider = str(EMBEDDING_PROVIDER or AI_PROVIDER or "ollama").strip().lower()

    if provider == "claude":
        provider = "anthropic"

    if provider not in {"ollama", "gemini"}:
        raise EmbeddingServiceError(
            f"Embedding provider '{provider}' is not supported yet. "
            "Use EMBEDDING_PROVIDER=gemini for cloud deployment or ollama locally."
        )

    return provider


def generate_embeddings(texts, batch_size=16):
    if isinstance(texts, str):
        texts = [texts]

    texts = [text.strip() for text in texts if text and text.strip()]

    if not texts:
        return []

    provider = get_embedding_provider()

    if provider == "gemini":
        return generate_gemini_embeddings(texts, batch_size=batch_size)

    return generate_ollama_embeddings(texts, batch_size=batch_size)


def generate_ollama_embeddings(texts, batch_size=16):
    all_embeddings = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]

        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/embed",
                json={
                    "model": EMBEDDING_MODEL,
                    "input": batch,
                    "truncate": True,
                },
                timeout=180,
            )
            response.raise_for_status()
            data = response.json()

        except requests.Timeout as error:
            raise EmbeddingServiceError("The Ollama embedding request timed out.") from error

        except requests.ConnectionError as error:
            raise EmbeddingServiceError("Could not connect to Ollama for embeddings.") from error

        except requests.RequestException as error:
            raise EmbeddingServiceError(f"Ollama embedding request failed: {error}") from error

        except ValueError as error:
            raise EmbeddingServiceError("Ollama returned an invalid embedding response.") from error

        embeddings = data.get("embeddings")

        if not embeddings:
            raise EmbeddingServiceError("Ollama returned no embeddings.")

        if len(embeddings) != len(batch):
            raise EmbeddingServiceError("Ollama returned an unexpected number of embeddings.")

        all_embeddings.extend(embeddings)

    return all_embeddings


def generate_gemini_embeddings(texts, batch_size=16):
    if not GEMINI_API_KEY:
        raise EmbeddingServiceError("GEMINI_API_KEY is required for Gemini embeddings.")

    model = str(EMBEDDING_MODEL or "text-embedding-004").strip()
    model_name = model if model.startswith("models/") else f"models/{model}"
    url = f"{GEMINI_BASE_URL.rstrip('/')}/{model_name}:batchEmbedContents"

    all_embeddings = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]

        payload = {
            "requests": [
                {
                    "model": model_name,
                    "content": {
                        "parts": [
                            {"text": text}
                        ]
                    },
                }
                for text in batch
            ]
        }

        try:
            response = requests.post(
                url,
                params={"key": GEMINI_API_KEY},
                json=payload,
                timeout=180,
            )
            response.raise_for_status()
            data = response.json()

        except requests.Timeout as error:
            raise EmbeddingServiceError("The Gemini embedding request timed out.") from error

        except requests.ConnectionError as error:
            raise EmbeddingServiceError("Could not connect to Gemini for embeddings.") from error

        except requests.HTTPError as error:
            detail = ""
            try:
                detail = response.json().get("error", {}).get("message", "")
            except Exception:
                detail = response.text[:500] if response is not None else ""
            raise EmbeddingServiceError(
                f"Gemini embedding request failed: {detail or error}"
            ) from error

        except requests.RequestException as error:
            raise EmbeddingServiceError(f"Gemini embedding request failed: {error}") from error

        except ValueError as error:
            raise EmbeddingServiceError("Gemini returned an invalid embedding response.") from error

        embeddings = data.get("embeddings", [])
        values = [item.get("values") for item in embeddings if item.get("values")]

        if len(values) != len(batch):
            raise EmbeddingServiceError("Gemini returned an unexpected number of embeddings.")

        all_embeddings.extend(values)

    return all_embeddings


def generate_embedding(text):
    embeddings = generate_embeddings([text])

    if not embeddings:
        raise EmbeddingServiceError("Could not create the query embedding.")

    return embeddings[0]
