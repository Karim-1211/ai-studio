"""Embedding provider service for AI Studio.

Cloud Edition v1.0 supports Gemini embeddings for Render/Neon deployments and
keeps Ollama embeddings available for local development.
"""

import os

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


def get_embedding_provider():
    provider = (
        os.getenv("EMBEDDING_PROVIDER")
        or ("gemini" if str(AI_PROVIDER).lower() == "gemini" else "ollama")
    )
    provider = provider.strip().lower()
    if provider not in {"gemini", "ollama"}:
        provider = "gemini" if str(AI_PROVIDER).lower() == "gemini" else "ollama"
    return provider


def get_embedding_model():
    configured = str(EMBEDDING_MODEL or "").strip()
    if configured:
        return configured
    if get_embedding_provider() == "gemini":
        return "gemini-embedding-001"
    return "embeddinggemma"


def normalize_texts(texts):
    if isinstance(texts, str):
        texts = [texts]
    return [str(text).strip() for text in texts if text and str(text).strip()]


def generate_embeddings(texts, batch_size=16, task_type="RETRIEVAL_DOCUMENT"):
    texts = normalize_texts(texts)
    if not texts:
        return []

    provider = get_embedding_provider()
    if provider == "gemini":
        return generate_gemini_embeddings(texts, task_type=task_type)

    return generate_ollama_embeddings(texts, batch_size=batch_size)


def generate_embedding(text):
    embeddings = generate_embeddings([text], task_type="RETRIEVAL_QUERY")
    if not embeddings:
        raise EmbeddingServiceError("Could not create the query embedding.")
    return embeddings[0]


def generate_gemini_embeddings(texts, task_type="RETRIEVAL_DOCUMENT"):
    if not GEMINI_API_KEY:
        raise EmbeddingServiceError("GEMINI_API_KEY is not configured for embeddings.")

    model = get_embedding_model()
    base_url = GEMINI_BASE_URL.rstrip("/")
    url = f"{base_url}/models/{model}:embedContent?key={GEMINI_API_KEY}"
    embeddings = []

    for text in texts:
        payload = {
            "content": {
                "parts": [
                    {"text": text}
                ]
            }
        }

        # Gemini text embedding models accept taskType for retrieval quality.
        # If Google changes support for a model, retry without taskType below.
        if task_type:
            payload["taskType"] = task_type

        data = post_gemini_embedding(url, payload, model)
        values = extract_gemini_embedding_values(data)
        embeddings.append(values)

    return embeddings


def post_gemini_embedding(url, payload, model):
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=(10, 120),
        )

        if response.status_code == 400 and "taskType" in payload:
            retry_payload = dict(payload)
            retry_payload.pop("taskType", None)
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=retry_payload,
                timeout=(10, 120),
            )

        response.raise_for_status()
        return response.json()

    except requests.Timeout as error:
        raise EmbeddingServiceError("Gemini embedding request timed out.") from error
    except requests.ConnectionError as error:
        raise EmbeddingServiceError("Could not connect to Gemini for embeddings.") from error
    except requests.HTTPError as error:
        detail = read_error_detail(error.response)
        raise EmbeddingServiceError(
            f"Gemini embedding request failed for model '{model}': {detail or error}"
        ) from error
    except requests.RequestException as error:
        raise EmbeddingServiceError(f"Gemini embedding request failed: {error}") from error
    except ValueError as error:
        raise EmbeddingServiceError("Gemini returned an invalid embedding response.") from error


def extract_gemini_embedding_values(data):
    embedding = data.get("embedding") or {}
    values = embedding.get("values")

    if not values:
        raise EmbeddingServiceError("Gemini returned no embedding values.")

    try:
        return [float(value) for value in values]
    except (TypeError, ValueError) as error:
        raise EmbeddingServiceError("Gemini returned non-numeric embedding values.") from error


def read_error_detail(response):
    if response is None:
        return ""
    try:
        data = response.json()
    except ValueError:
        return response.text[:500]

    error = data.get("error")
    if isinstance(error, dict):
        return error.get("message") or str(error)
    return str(data)[:500]


def generate_ollama_embeddings(texts, batch_size=16):
    model = get_embedding_model()
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
