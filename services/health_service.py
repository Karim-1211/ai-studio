import os
import tempfile
import time

import requests

from sqlalchemy import text

from config import (
    AI_PROVIDER,
    EMBEDDING_MODEL,
    GEMINI_API_KEY,
    OLLAMA_URL
)

from database import db

from services.document_service import (
    get_ocr_status
)


def _component(
    ok,
    status,
    message,
    latency_ms=None,
    details=None
):
    result = {
        "ok": bool(ok),
        "status": status,
        "message": message
    }

    if latency_ms is not None:
        result["latency_ms"] = round(
            float(latency_ms),
            1
        )

    if details:
        result["details"] = details

    return result


def check_database():
    started = time.perf_counter()

    try:
        db.session.execute(
            text("SELECT 1")
        )

        latency = (
            time.perf_counter()
            - started
        ) * 1000

        return _component(
            True,
            "ready",
            "PostgreSQL is reachable.",
            latency
        )

    except Exception as error:
        db.session.rollback()

        latency = (
            time.perf_counter()
            - started
        ) * 1000

        return _component(
            False,
            "unavailable",
            "Database check failed.",
            latency,
            str(error)
        )


def check_ollama(timeout):
    started = time.perf_counter()

    try:
        response = requests.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=timeout
        )

        response.raise_for_status()

        data = response.json()
        models = data.get(
            "models",
            []
        )

        names = [
            str(model.get("name", ""))
            for model in models
            if model.get("name")
        ]

        latency = (
            time.perf_counter()
            - started
        ) * 1000

        return _component(
            True,
            "ready",
            (
                f"Ollama is reachable with "
                f"{len(names)} model"
                f"{'' if len(names) == 1 else 's'}."
            ),
            latency,
            {
                "model_count": len(names),
                "models": names
            }
        )

    except Exception as error:
        latency = (
            time.perf_counter()
            - started
        ) * 1000

        return _component(
            False,
            "unavailable",
            "Ollama is not reachable.",
            latency,
            str(error)
        )


def check_embedding_model(
    ollama_component
):
    if not ollama_component.get("ok"):
        return _component(
            False,
            "blocked",
            "Embedding model check is blocked because Ollama is unavailable."
        )

    models = (
        ollama_component
        .get("details", {})
        .get("models", [])
    )

    expected_base = (
        EMBEDDING_MODEL
        .split(":")[0]
        .lower()
    )

    present = any(
        model.split(":")[0].lower()
        == expected_base
        for model in models
    )

    if present:
        return _component(
            True,
            "ready",
            (
                f"Embedding model "
                f"'{EMBEDDING_MODEL}' is installed."
            )
        )

    return _component(
        False,
        "missing",
        (
            f"Embedding model "
            f"'{EMBEDDING_MODEL}' is not installed."
        )
    )


def check_ocr(config):
    status = get_ocr_status(
        config
    )

    enabled = bool(
        status.get("enabled")
    )
    available = bool(
        status.get("available")
    )

    if not enabled:
        return _component(
            True,
            "disabled",
            "OCR is disabled."
        )

    if available:
        return _component(
            True,
            "ready",
            (
                "OCR is available with "
                f"language '{status.get('language', 'eng')}'."
            )
        )

    return _component(
        False,
        "unavailable",
        "OCR is enabled but Tesseract is unavailable."
    )


def check_upload_folder(upload_folder):
    try:
        os.makedirs(
            upload_folder,
            exist_ok=True
        )

        with tempfile.NamedTemporaryFile(
            dir=upload_folder,
            prefix=".health-",
            delete=True
        ) as test_file:
            test_file.write(b"ok")
            test_file.flush()

        return _component(
            True,
            "ready",
            "Upload storage is writable."
        )

    except Exception as error:
        return _component(
            False,
            "unavailable",
            "Upload storage is not writable.",
            details=str(error)
        )


def check_cloud_ai_provider():
    provider = str(
        os.getenv("AI_PROVIDER")
        or AI_PROVIDER
        or "ollama"
    ).strip().lower()

    if provider == "claude":
        provider = "anthropic"

    if provider == "gemini":
        configured = bool(GEMINI_API_KEY)
        return _component(
            configured,
            "ready" if configured else "unavailable",
            (
                "Gemini provider is configured."
                if configured
                else "GEMINI_API_KEY is not configured."
            ),
            details={"provider": "gemini"}
        )

    key_name = {
        "openai": "OPENAI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY"
    }.get(provider)

    configured = bool(key_name and os.getenv(key_name))
    return _component(
        configured,
        "ready" if configured else "unavailable",
        (
            f"{provider.title()} provider is configured."
            if configured
            else f"{key_name or 'AI provider'} is not configured."
        ),
        details={"provider": provider}
    )


def check_cloud_embedding_provider():
    provider = str(
        os.getenv("EMBEDDING_PROVIDER")
        or ("gemini" if str(AI_PROVIDER).lower() == "gemini" else "ollama")
    ).strip().lower()

    if provider == "gemini":
        configured = bool(GEMINI_API_KEY)
        return _component(
            configured,
            "ready" if configured else "unavailable",
            (
                f"Gemini embeddings are configured with model '{EMBEDDING_MODEL}'."
                if configured
                else "GEMINI_API_KEY is required for Gemini embeddings."
            ),
            details={
                "provider": "gemini",
                "model": EMBEDDING_MODEL
            }
        )

    return None


def get_system_health(config):
    database = check_database()

    ai_provider = str(
        os.getenv("AI_PROVIDER")
        or AI_PROVIDER
        or "ollama"
    ).strip().lower()

    if ai_provider == "ollama":
        ai = check_ollama(
            config.get(
                "HEALTH_HTTP_TIMEOUT",
                3.0
            )
        )
        embedding = check_embedding_model(ai)
        components = {
            "database": database,
            "ollama": ai,
            "ai": ai,
            "embedding": embedding,
        }
    else:
        ai = check_cloud_ai_provider()
        embedding = check_cloud_embedding_provider() or _component(
            True,
            "ready",
            "Cloud embedding provider is configured.",
        )
        components = {
            "database": database,
            "ai": ai,
            "embedding": embedding,
        }

    ocr = check_ocr(config)
    uploads = check_upload_folder(config["UPLOAD_FOLDER"])
    components.update({
        "ocr": ocr,
        "uploads": uploads
    })

    essential_ready = all([
        database["ok"],
        ai["ok"],
        embedding["ok"],
        uploads["ok"]
    ])

    optional_ready = ocr["ok"]

    if essential_ready and optional_ready:
        overall = "ready"
    elif essential_ready:
        overall = "degraded"
    else:
        overall = "unavailable"

    return {
        "status": overall,
        "ready": essential_ready,
        "provider": ai_provider,
        "components": components
    }
