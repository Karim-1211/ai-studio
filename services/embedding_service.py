import requests

from config import (
    EMBEDDING_MODEL,
    OLLAMA_URL
)


class EmbeddingServiceError(Exception):
    pass


def generate_embeddings(
    texts,
    batch_size=16
):
    if isinstance(
        texts,
        str
    ):
        texts = [
            texts
        ]

    texts = [
        text.strip()
        for text in texts
        if text and text.strip()
    ]

    if not texts:
        return []

    all_embeddings = []

    for start in range(
        0,
        len(texts),
        batch_size
    ):
        batch = texts[
            start:start + batch_size
        ]

        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/embed",
                json={
                    "model": EMBEDDING_MODEL,
                    "input": batch,
                    "truncate": True
                },
                timeout=180
            )

            response.raise_for_status()
            data = response.json()

        except requests.Timeout as error:
            raise EmbeddingServiceError(
                (
                    "The embedding request "
                    "timed out."
                )
            ) from error

        except requests.ConnectionError as error:
            raise EmbeddingServiceError(
                (
                    "Could not connect to Ollama "
                    "for embeddings."
                )
            ) from error

        except requests.RequestException as error:
            raise EmbeddingServiceError(
                (
                    "Ollama embedding request failed: "
                    f"{error}"
                )
            ) from error

        except ValueError as error:
            raise EmbeddingServiceError(
                (
                    "Ollama returned an invalid "
                    "embedding response."
                )
            ) from error

        embeddings = data.get(
            "embeddings"
        )

        if not embeddings:
            raise EmbeddingServiceError(
                "Ollama returned no embeddings."
            )

        if len(embeddings) != len(
            batch
        ):
            raise EmbeddingServiceError(
                (
                    "Ollama returned an unexpected "
                    "number of embeddings."
                )
            )

        all_embeddings.extend(
            embeddings
        )

    return all_embeddings


def generate_embedding(
    text
):
    embeddings = generate_embeddings(
        [
            text
        ]
    )

    if not embeddings:
        raise EmbeddingServiceError(
            (
                "Could not create the "
                "query embedding."
            )
        )

    return embeddings[0]
