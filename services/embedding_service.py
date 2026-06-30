"""Embedding provider service for AI Studio.

Cloud mode uses the Gemini embeddings endpoint. Local mode continues to
support Ollama so local development still works, but Render/Gemini deployments
no longer depend on Ollama for RAG, attachments, websites, or social sources.
"""

import os
import time

import requests

from config import (
    AI_PROVIDER,
    EMBEDDING_MODEL,
    GEMINI_API_KEY,
    GEMINI_BASE_URL,
    OLLAMA_URL,
)


class EmbeddingServiceError(Exception):
    pass


DEFAULT_GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
DEFAULT_OUTPUT_DIMENSIONALITY = 768


def _normalise_texts(texts):
    if isinstance(texts, str):
        texts = [texts]

    return [
        text.strip()
        for text in texts
        if text and str(text).strip()
    ]


def _embedding_provider():
    provider = (
        os.getenv("EMBEDDING_PROVIDER")
        or os.getenv("AI_PROVIDER")
        or AI_PROVIDER
        or "ollama"
    ).strip().lower()

    if provider == "cloud":
        provider = "gemini"

    if provider not in {"gemini", "ollama"}:
        provider = "gemini" if (AI_PROVIDER == "gemini") else "ollama"

    return provider


def _embedding_model(provider):
    model = (os.getenv("EMBEDDING_MODEL") or EMBEDDING_MODEL or "").strip()

    if provider == "gemini":
        if not model or model in {"embeddinggemma", "nomic-embed-text", "text-embedding-004"}:
            return DEFAULT_GEMINI_EMBEDDING_MODEL
        return model

    return model or "embeddinggemma"


def _embedding_dimensions():
    raw_value = os.getenv("GEMINI_EMBEDDING_DIMENSIONS", "768")

    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return DEFAULT_OUTPUT_DIMENSIONALITY

    if value not in {768, 1536, 3072}:
        return DEFAULT_OUTPUT_DIMENSIONALITY

    return value


def _gemini_model_path(model):
    model = model.strip()
    if model.startswith("models/"):
        return model
    return f"models/{model}"


def _gemini_endpoint(model):
    return f"{GEMINI_BASE_URL.rstrip('/')}/{_gemini_model_path(model)}:embedContent"


def _extract_gemini_values(data):
    embedding = data.get("embedding") or {}
    values = embedding.get("values")

    if not isinstance(values, list) or not values:
        raise EmbeddingServiceError("Gemini returned no embedding values.")

    return [float(value) for value in values]


def _generate_gemini_embeddings(texts, task_type="RETRIEVAL_DOCUMENT"):
    if not GEMINI_API_KEY:
        raise EmbeddingServiceError("GEMINI_API_KEY is not configured for embeddings.")

    model = _embedding_model("gemini")
    endpoint = _gemini_endpoint(model)
    dimensions = _embedding_dimensions()
    results = []

    for text in texts:
        payload = {
            "content": {
                "parts": [
                    {"text": text[:12000]}
                ]
            },
            "taskType": task_type,
            "outputDimensionality": dimensions,
        }

        try:
            response = requests.post(
                endpoint,
                params={"key": GEMINI_API_KEY},
                json=payload,
                timeout=(10, 120),
            )

            response.raise_for_status()
            data = response.json()
            results.append(_extract_gemini_values(data))

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
                f"Gemini embedding request failed for model '{model}': {detail or error}"
            ) from error

        except ValueError as error:
            raise EmbeddingServiceError("Gemini returned an invalid embedding response.") from error

        # Be gentle with free-tier API limits when indexing many pages at once.
        time.sleep(float(os.getenv("GEMINI_EMBEDDING_DELAY_SECONDS", "0.05")))

    return results


def _generate_ollama_embeddings(texts, batch_size=16):
    model = _embedding_model("ollama")
    all_embeddings = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]

        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/embed",
                json={
                    "model": model,
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


def generate_embeddings(texts, batch_size=16, task_type="RETRIEVAL_DOCUMENT"):
    texts = _normalise_texts(texts)

    if not texts:
        return []

    provider = _embedding_provider()

    if provider == "gemini":
        return _generate_gemini_embeddings(texts, task_type=task_type)

    return _generate_ollama_embeddings(texts, batch_size=batch_size)


def generate_embedding(text):
    provider = _embedding_provider()
    task_type = "RETRIEVAL_QUERY" if provider == "gemini" else "RETRIEVAL_DOCUMENT"

    embeddings = generate_embeddings([text], task_type=task_type)

    if not embeddings:
        raise EmbeddingServiceError("Could not create the query embedding.")

    return embeddings[0]


def get_embedding_status():
    provider = _embedding_provider()
    model = _embedding_model(provider)

    configured = True
    message = f"{provider.title()} embeddings are configured."

    if provider == "gemini" and not GEMINI_API_KEY:
        configured = False
        message = "GEMINI_API_KEY is not configured for embeddings."

    return {
        "ok": configured,
        "provider": provider,
        "model": model,
        "dimensions": _embedding_dimensions() if provider == "gemini" else None,
        "message": message,
    }
