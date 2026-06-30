import base64
import json

import requests

from config import (
    EMBEDDING_MODEL,
    OLLAMA_URL
)


_MODEL_CAPABILITY_CACHE = {}


class OllamaVisionError(Exception):
    pass


def get_ollama_models():
    try:
        response = requests.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=10
        )

        response.raise_for_status()

        models = response.json().get(
            "models",
            []
        )

        embedding_model_base = (
            EMBEDDING_MODEL
            .split(":")[0]
            .lower()
        )

        generation_models = []

        for model in models:
            model_name = model.get(
                "name",
                ""
            )

            model_base = (
                model_name
                .split(":")[0]
                .lower()
            )

            if model_base == embedding_model_base:
                continue

            generation_models.append(
                model_name
            )

        return generation_models

    except (
        requests.RequestException,
        ValueError
    ):
        return []



def get_model_capabilities(model, refresh=False):
    model_name = str(model or "").strip()
    if not model_name:
        return []

    if not refresh and model_name in _MODEL_CAPABILITY_CACHE:
        return list(_MODEL_CAPABILITY_CACHE[model_name])

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/show",
            json={"model": model_name},
            timeout=15
        )
        response.raise_for_status()
        capabilities = response.json().get("capabilities", [])
        normalized = [
            str(item).strip().lower()
            for item in capabilities
            if str(item).strip()
        ]
        _MODEL_CAPABILITY_CACHE[model_name] = normalized
        return list(normalized)
    except (requests.RequestException, ValueError):
        return []


def model_supports_vision(model):
    return "vision" in get_model_capabilities(model)


def find_vision_model(selected_model, preferred_model=None):
    candidates = []

    for candidate in [selected_model, preferred_model]:
        name = str(candidate or "").strip()
        if name and name not in candidates:
            candidates.append(name)

    for name in get_ollama_models():
        if name not in candidates:
            candidates.append(name)

    for candidate in candidates:
        if model_supports_vision(candidate):
            return candidate

    return None


def encode_image_files(image_paths):
    encoded = []
    for path in image_paths or []:
        with open(path, "rb") as image_file:
            encoded.append(
                base64.b64encode(image_file.read()).decode("ascii")
            )
    return encoded


def generate_vision_analysis(model, prompt, image_paths):
    if not image_paths:
        return ""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": (
                    "Analyze the attached image or images carefully. "
                    "Describe the visible content, read important text, "
                    "and extract facts needed to answer this request:\n\n"
                    f"{prompt}"
                ),
                "images": encode_image_files(image_paths),
                "stream": False,
                "options": {"temperature": 0.2}
            },
            timeout=(10, 600)
        )
        response.raise_for_status()
        text = str(response.json().get("response", "")).strip()
        if not text:
            raise OllamaVisionError(
                "The vision model returned an empty image analysis."
            )
        return text
    except requests.Timeout as error:
        raise OllamaVisionError(
            "The vision model took too long to analyze the image."
        ) from error
    except requests.RequestException as error:
        raise OllamaVisionError(
            f"The image could not be analyzed by Ollama: {error}"
        ) from error
    except (OSError, ValueError) as error:
        raise OllamaVisionError(
            f"The image attachment could not be prepared: {error}"
        ) from error

def build_prompt(
    prompt,
    mode,
    option_number=None
):
    if mode == "options":
        return f"""
Create option {option_number} for the following request.

Make this option high-quality, useful, and meaningfully different from the other options.

Request:

{prompt}
""".strip()

    if mode == "detailed":
        return f"""
Answer the following request in a detailed and structured way.

Include:
- A clear explanation
- Relevant examples
- Best practices
- Important limitations or notes

Request:

{prompt}
""".strip()

    if mode == "creative":
        return f"""
Answer the following request creatively.

Provide original, useful, and well-developed ideas.

Request:

{prompt}
""".strip()

    if mode == "precise":
        return f"""
Answer the following request accurately, directly, and professionally.

Avoid unnecessary details.

Request:

{prompt}
""".strip()

    if mode == "fast":
        return f"""
Give a concise and direct answer to the following request.

Request:

{prompt}
""".strip()

    return prompt


def get_options_for_mode(
    mode,
    temperature=None,
    max_tokens=None,
    top_p=None,
    top_k=None,
    repeat_penalty=None,
    context_length=None
):
    options = {}

    if temperature is not None:
        options["temperature"] = float(
            temperature
        )
    elif mode == "options":
        options["temperature"] = 0.85
    elif mode == "creative":
        options["temperature"] = 0.95
    elif mode == "precise":
        options["temperature"] = 0.2
    elif mode == "fast":
        options["temperature"] = 0.4
    else:
        options["temperature"] = 0.7

    if max_tokens is not None:
        options["num_predict"] = int(
            max_tokens
        )
    elif mode == "fast":
        options["num_predict"] = 250

    if top_p is not None:
        options["top_p"] = float(
            top_p
        )

    if top_k is not None:
        options["top_k"] = int(
            top_k
        )

    if repeat_penalty is not None:
        options["repeat_penalty"] = float(
            repeat_penalty
        )

    if context_length is not None:
        options["num_ctx"] = int(
            context_length
        )

    return options


def stream_ollama_response(
    model,
    prompt,
    mode="single",
    option_number=None,
    system_prompt="",
    temperature=None,
    max_tokens=None,
    top_p=None,
    top_k=None,
    repeat_penalty=None,
    context_length=None,
    image_paths=None
):
    try:
        final_prompt = build_prompt(
            prompt,
            mode,
            option_number
        )

        options = get_options_for_mode(
            mode=mode,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            top_k=top_k,
            repeat_penalty=repeat_penalty,
            context_length=context_length
        )

        request_payload = {
            "model": model,
            "prompt": final_prompt,
            "stream": True,
            "options": options
        }

        if image_paths:
            request_payload["images"] = encode_image_files(image_paths)

        cleaned_system_prompt = str(
            system_prompt or ""
        ).strip()

        if cleaned_system_prompt:
            request_payload["system"] = (
                cleaned_system_prompt
            )

        with requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=request_payload,
            stream=True,
            timeout=(10, 600)
        ) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue

                chunk = json.loads(
                    line.decode("utf-8")
                )

                response_text = chunk.get(
                    "response"
                )

                if response_text:
                    yield response_text

                if chunk.get("done"):
                    break

    except requests.Timeout:
        yield (
            "\n\nError: Ollama took too long "
            "to respond."
        )

    except requests.ConnectionError:
        yield (
            "\n\nError: Could not connect to "
            "Ollama. Make sure Ollama is running."
        )

    except requests.RequestException as error:
        yield (
            "\n\nError communicating with "
            f"Ollama: {error}"
        )

    except (
        ValueError,
        json.JSONDecodeError
    ) as error:
        yield (
            "\n\nError reading the Ollama "
            f"response: {error}"
        )

    except Exception as error:
        yield f"\n\nError: {error}"
