"""Embedding service with Ollama support and a cloud-safe local fallback.

Local development can use Ollama embeddings. Cloud deployments such as Render
usually do not have Ollama running, so this module falls back to a deterministic
hashing-vector embedding. That keeps attachments, global knowledge, websites,
and social/manual knowledge usable with hosted chat providers like Gemini.
"""

import hashlib
import math
import os
import re

import requests

from config import (
    AI_PROVIDER,
    EMBEDDING_MODEL,
    OLLAMA_URL,
)


class EmbeddingServiceError(Exception):
    pass


HASH_EMBEDDING_DIMENSIONS = int(
    os.getenv("HASH_EMBEDDING_DIMENSIONS", "384")
)

EMBEDDING_PROVIDER = (
    os.getenv("EMBEDDING_PROVIDER", "auto")
    .strip()
    .lower()
)

ALLOW_HASH_EMBEDDING_FALLBACK = (
    os.getenv("ALLOW_HASH_EMBEDDING_FALLBACK", "true")
    .strip()
    .lower()
    in {"1", "true", "yes", "on"}
)

TOKEN_PATTERN = re.compile(r"[\w']+", re.UNICODE)


def _normalize_texts(texts):
    if isinstance(texts, str):
        texts = [texts]

    return [
        text.strip()
        for text in texts
        if text and str(text).strip()
    ]


def _should_use_ollama():
    if EMBEDDING_PROVIDER in {"hash", "local", "local_hash"}:
        return False

    if EMBEDDING_PROVIDER == "ollama":
        return True

    # Auto mode: use Ollama only for the local Ollama provider. Hosted providers
    # such as Gemini/OpenAI/OpenRouter/Anthropic use local hash embeddings so the
    # app can work on Render without an Ollama sidecar.
    return str(AI_PROVIDER or "ollama").strip().lower() == "ollama"


def _tokenize(text):
    tokens = TOKEN_PATTERN.findall(text.lower())
    if tokens:
        return tokens
    return [text.lower()] if text else []


def _hash_embedding(text, dimensions=HASH_EMBEDDING_DIMENSIONS):
    """Create a deterministic normalized hashing-vector embedding.

    This is not as semantically strong as model embeddings, but it is reliable,
    free, and works in production without Ollama. It is good enough for a
    portfolio demo and keeps all knowledge-source features operational.
    """

    vector = [0.0] * dimensions
    tokens = _tokenize(text)

    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        weight = 1.0 + min(len(token), 20) / 20.0
        vector[index] += sign * weight

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector

    return [value / norm for value in vector]


def generate_hash_embeddings(texts):
    return [_hash_embedding(text) for text in _normalize_texts(texts)]


def _generate_ollama_embeddings(texts, batch_size=16):
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
            raise EmbeddingServiceError("The embedding request timed out.") from error

        except requests.ConnectionError as error:
            raise EmbeddingServiceError(
                "Could not connect to Ollama for embeddings."
            ) from error

        except requests.RequestException as error:
            raise EmbeddingServiceError(
                f"Ollama embedding request failed: {error}"
            ) from error

        except ValueError as error:
            raise EmbeddingServiceError(
                "Ollama returned an invalid embedding response."
            ) from error

        embeddings = data.get("embeddings")

        if not embeddings:
            raise EmbeddingServiceError("Ollama returned no embeddings.")

        if len(embeddings) != len(batch):
            raise EmbeddingServiceError(
                "Ollama returned an unexpected number of embeddings."
            )

        all_embeddings.extend(embeddings)

    return all_embeddings


def generate_embeddings(texts, batch_size=16):
    texts = _normalize_texts(texts)

    if not texts:
        return []

    if not _should_use_ollama():
        return generate_hash_embeddings(texts)

    try:
        return _generate_ollama_embeddings(texts, batch_size=batch_size)
    except EmbeddingServiceError:
        if ALLOW_HASH_EMBEDDING_FALLBACK:
            return generate_hash_embeddings(texts)
        raise


def generate_embedding(text):
    embeddings = generate_embeddings([text])

    if not embeddings:
        raise EmbeddingServiceError("Could not create the query embedding.")

    return embeddings[0]
