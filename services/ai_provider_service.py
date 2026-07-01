"""AI provider abstraction for local and hosted AI providers.

Supported providers:
- ollama: local Ollama models for private/local development
- openai: OpenAI Chat Completions API
- openrouter: OpenRouter, via OpenAI-compatible Chat Completions API
- gemini: Google Gemini API
- anthropic/claude: Anthropic Messages API
"""

import base64
import hashlib
import json
import mimetypes
import threading
import time

import requests

from config import (
    AI_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    OPENAI_MODELS,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
    OPENROUTER_MODELS,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_MODELS,
    GEMINI_BASE_URL,
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    ANTHROPIC_MODELS,
    ANTHROPIC_BASE_URL,
    ANTHROPIC_VERSION,
)
from services.ollama_service import (
    stream_ollama_response,
    get_ollama_models,
)
from services.text_quality_service import polish_assistant_text


SUPPORTED_PROVIDERS = {"ollama", "openai", "openrouter", "gemini", "anthropic", "claude"}
OPENAI_COMPATIBLE_PROVIDERS = {"openai", "openrouter"}

# Small in-memory cache for identical Gemini requests in the same Render process.
# This protects the free Gemini quota during repeated testing and does not store
# user data outside the running process. Render may clear this on restart.
_GEMINI_RESPONSE_CACHE = {}
_GEMINI_CACHE_LOCK = threading.Lock()
_GEMINI_CACHE_TTL_SECONDS = 600
_GEMINI_MAX_CACHE_ITEMS = 80
_GEMINI_RETRY_DELAYS = (2, 5, 10)



def get_ai_provider():
    provider = str(AI_PROVIDER or "ollama").strip().lower()
    if provider == "claude":
        return "anthropic"
    if provider not in SUPPORTED_PROVIDERS:
        return "ollama"
    return provider


def provider_supports_direct_images(provider=None):
    provider = provider or get_ai_provider()
    return provider in {"openai", "openrouter", "gemini", "anthropic"}


def get_available_models():
    provider = get_ai_provider()

    if provider == "openai":
        return list(OPENAI_MODELS)
    if provider == "openrouter":
        return list(OPENROUTER_MODELS)
    if provider == "gemini":
        return list(GEMINI_MODELS)
    if provider == "anthropic":
        return list(ANTHROPIC_MODELS)

    return get_ollama_models()


def stream_ai_response(
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
    image_paths=None,
):
    provider = get_ai_provider()

    if provider == "openai":
        yield from stream_openai_compatible_response(
            provider_name="OpenAI",
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
            default_model=OPENAI_MODEL,
            model=model,
            prompt=prompt,
            mode=mode,
            option_number=option_number,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            image_paths=image_paths,
        )
        return

    if provider == "openrouter":
        yield from stream_openai_compatible_response(
            provider_name="OpenRouter",
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            default_model=OPENROUTER_MODEL,
            model=model,
            prompt=prompt,
            mode=mode,
            option_number=option_number,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            image_paths=image_paths,
            extra_headers={
                "HTTP-Referer": "https://github.com/Karim-1211/ai-studio",
                "X-Title": "AI Studio",
            },
        )
        return

    if provider == "gemini":
        yield from stream_gemini_response(
            model=model,
            prompt=prompt,
            mode=mode,
            option_number=option_number,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            image_paths=image_paths,
        )
        return

    if provider == "anthropic":
        yield from stream_anthropic_response(
            model=model,
            prompt=prompt,
            mode=mode,
            option_number=option_number,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            image_paths=image_paths,
        )
        return

    yield from stream_ollama_response(
        model=model,
        prompt=prompt,
        mode=mode,
        option_number=option_number,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        top_k=top_k,
        repeat_penalty=repeat_penalty,
        context_length=context_length,
        image_paths=image_paths,
    )


def stream_openai_compatible_response(
    provider_name,
    api_key,
    base_url,
    default_model,
    model,
    prompt,
    mode="single",
    option_number=None,
    system_prompt="",
    temperature=None,
    max_tokens=None,
    top_p=None,
    image_paths=None,
    extra_headers=None,
):
    if not api_key:
        yield f"\n\nError: {provider_name} API key is not configured."
        return

    selected_model = str(model or "").strip() or default_model
    final_prompt = build_prompt(prompt, mode, option_number)

    payload = {
        "model": selected_model,
        "messages": build_openai_messages(final_prompt, system_prompt, image_paths),
        "stream": True,
        "temperature": resolve_temperature(mode, temperature),
    }

    resolved_max_tokens = resolve_max_tokens(mode, max_tokens)
    if resolved_max_tokens is not None:
        payload["max_tokens"] = resolved_max_tokens

    if top_p is not None:
        payload["top_p"] = float(top_p)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    try:
        with requests.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
            stream=True,
            timeout=(10, 600),
        ) as response:
            response.raise_for_status()

            for raw_line in response.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue

                line = raw_line.strip()
                if not line.startswith("data:"):
                    continue

                data = line.removeprefix("data:").strip()
                if data == "[DONE]":
                    break

                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue

                for choice in chunk.get("choices", []):
                    delta = choice.get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content

    except requests.Timeout:
        yield f"\n\nError: {provider_name} took too long to respond."
    except requests.ConnectionError:
        yield f"\n\nError: Could not connect to {provider_name}."
    except requests.HTTPError as error:
        detail = read_error_detail(error.response)
        yield f"\n\nError from {provider_name}: {detail or error}"
    except requests.RequestException as error:
        yield f"\n\nError communicating with {provider_name}: {error}"
    except Exception as error:
        yield f"\n\nError: {error}"


def stream_gemini_response(
    model,
    prompt,
    mode="single",
    option_number=None,
    system_prompt="",
    temperature=None,
    max_tokens=None,
    top_p=None,
    image_paths=None,
):
    """Generate a Gemini response with quota-safe reliability behavior.

    v2.2 intentionally keeps Gemini on generateContent instead of the unstable
    streaming endpoint. It yields the finished text progressively after a
    complete provider response is received. This prevents partial/truncated
    answers while still giving a readable typing effect in the UI.

    Reliability improvements:
    - short-lived response cache for identical repeated prompts
    - exponential backoff for temporary quota/network issues
    - fallback model attempts when configured models are available
    - sanitized user-visible errors with no provider URL or API key exposure
    """
    if not GEMINI_API_KEY:
        yield "\n\nError: GEMINI_API_KEY is not configured."
        return

    selected_model = str(model or "").strip() or GEMINI_MODEL
    final_prompt = build_prompt(prompt, mode, option_number)
    resolved_max_tokens = resolve_gemini_max_tokens(mode, max_tokens)

    cache_key = build_gemini_cache_key(
        model=selected_model,
        prompt=final_prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=resolved_max_tokens,
        top_p=top_p,
        image_paths=image_paths,
    )

    cached_text = get_cached_gemini_response(cache_key)
    if cached_text:
        yield from yield_text_progressively(cached_text)
        return

    payload_template = {
        "contents": build_gemini_contents(final_prompt, image_paths),
        "generationConfig": {
            "temperature": resolve_temperature(mode, temperature),
        },
    }

    if system_prompt:
        payload_template["systemInstruction"] = {
            "parts": [{"text": str(system_prompt)}]
        }

    if resolved_max_tokens is not None:
        payload_template["generationConfig"]["maxOutputTokens"] = resolved_max_tokens
    if top_p is not None:
        payload_template["generationConfig"]["topP"] = float(top_p)

    last_error_message = ""
    rate_limited = False

    for candidate_model in get_gemini_fallback_models(selected_model):
        url = build_gemini_generate_url(candidate_model)

        for attempt, delay in enumerate(_GEMINI_RETRY_DELAYS, start=1):
            try:
                response = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload_template,
                    timeout=(10, 600),
                )

                if response.status_code == 429:
                    rate_limited = True
                    last_error_message = build_quota_message(candidate_model)
                    if attempt < len(_GEMINI_RETRY_DELAYS):
                        time.sleep(delay)
                        continue
                    break

                response.raise_for_status()
                data = response.json()
                text = polish_assistant_text(extract_gemini_text(data)).strip()

                if not text:
                    finish_reason = extract_gemini_finish_reason(data)
                    if finish_reason:
                        last_error_message = (
                            "Gemini returned no text. "
                            f"Finish reason: {finish_reason}."
                        )
                    else:
                        last_error_message = "Gemini returned no text."
                    break

                set_cached_gemini_response(cache_key, text)
                yield from yield_text_progressively(text)
                return

            except requests.Timeout:
                last_error_message = "Gemini took too long to respond."
            except requests.ConnectionError:
                last_error_message = "Could not connect to Gemini."
            except requests.HTTPError as error:
                status_code = getattr(error.response, "status_code", None)
                if status_code == 429:
                    rate_limited = True
                    last_error_message = build_quota_message(candidate_model)
                else:
                    detail = read_error_detail(error.response)
                    last_error_message = (
                        detail
                        or f"Gemini request failed with status {status_code}."
                    )
            except requests.RequestException:
                last_error_message = "Gemini request failed. Please try again."
            except Exception as error:
                last_error_message = str(error)

            if attempt < len(_GEMINI_RETRY_DELAYS):
                time.sleep(delay)

    if rate_limited:
        yield (
            "\n\nError from Gemini: Gemini rate limit reached. "
            "Please wait 2-5 minutes before trying again. "
            "Use Single Answer and turn off knowledge when testing simple chat. "
            "AI Studio has already retried safely and hidden provider details."
        )
        return

    yield f"\n\nError from Gemini: {sanitize_provider_error(last_error_message)}"


def build_gemini_generate_url(model_name):
    safe_model = str(model_name or GEMINI_MODEL).strip() or GEMINI_MODEL
    return (
        f"{GEMINI_BASE_URL.rstrip('/')}/models/"
        f"{safe_model}:generateContent?key={GEMINI_API_KEY}"
    )


def get_gemini_fallback_models(selected_model):
    models = []

    def add(value):
        cleaned = str(value or "").strip()
        if cleaned and cleaned not in models:
            models.append(cleaned)

    add(selected_model)
    add(GEMINI_MODEL)

    for configured_model in GEMINI_MODELS:
        add(configured_model)

    # Safe public fallbacks commonly available in Gemini API projects.
    # They are only attempted after the selected/configured model fails.
    add("gemini-1.5-flash")
    add("gemini-2.0-flash")

    return models


def resolve_gemini_max_tokens(mode, max_tokens):
    resolved = resolve_max_tokens(mode, max_tokens)

    if mode == "options_batch":
        if resolved is None or resolved > 850:
            return 850

    if mode == "options":
        if resolved is None or resolved > 450:
            return 450

    if resolved is not None:
        return int(resolved)

    return None


def build_gemini_cache_key(
    model,
    prompt,
    system_prompt="",
    temperature=None,
    max_tokens=None,
    top_p=None,
    image_paths=None,
):
    image_fingerprint = ",".join(
        str(path) for path in (image_paths or [])
    )
    raw = "\n".join([
        str(model or ""),
        str(prompt or ""),
        str(system_prompt or ""),
        str(temperature or ""),
        str(max_tokens or ""),
        str(top_p or ""),
        image_fingerprint,
    ])
    return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()


def get_cached_gemini_response(cache_key):
    now = time.time()
    with _GEMINI_CACHE_LOCK:
        item = _GEMINI_RESPONSE_CACHE.get(cache_key)
        if not item:
            return ""

        created_at, text = item
        if now - created_at > _GEMINI_CACHE_TTL_SECONDS:
            _GEMINI_RESPONSE_CACHE.pop(cache_key, None)
            return ""

        return text


def set_cached_gemini_response(cache_key, text):
    if not text:
        return

    with _GEMINI_CACHE_LOCK:
        if len(_GEMINI_RESPONSE_CACHE) >= _GEMINI_MAX_CACHE_ITEMS:
            oldest_key = min(
                _GEMINI_RESPONSE_CACHE,
                key=lambda key: _GEMINI_RESPONSE_CACHE[key][0],
            )
            _GEMINI_RESPONSE_CACHE.pop(oldest_key, None)

        _GEMINI_RESPONSE_CACHE[cache_key] = (time.time(), text)


def build_quota_message(model_name):
    return (
        f"Gemini rate limit reached while using {model_name}. "
        "AI Studio will retry safely and fall back when possible."
    )


def stream_anthropic_response(
    model,
    prompt,
    mode="single",
    option_number=None,
    system_prompt="",
    temperature=None,
    max_tokens=None,
    top_p=None,
    image_paths=None,
):
    if not ANTHROPIC_API_KEY:
        yield "\n\nError: ANTHROPIC_API_KEY is not configured."
        return

    selected_model = str(model or "").strip() or ANTHROPIC_MODEL
    final_prompt = build_prompt(prompt, mode, option_number)

    payload = {
        "model": selected_model,
        "messages": build_anthropic_messages(final_prompt, image_paths),
        "max_tokens": resolve_max_tokens(mode, max_tokens) or 1024,
        "temperature": resolve_temperature(mode, temperature),
        "stream": True,
    }
    if system_prompt:
        payload["system"] = str(system_prompt)
    if top_p is not None:
        payload["top_p"] = float(top_p)

    try:
        with requests.post(
            f"{ANTHROPIC_BASE_URL.rstrip('/')}/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": ANTHROPIC_VERSION,
                "Content-Type": "application/json",
            },
            json=payload,
            stream=True,
            timeout=(10, 600),
        ) as response:
            response.raise_for_status()
            for raw_line in response.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                line = raw_line.strip()
                if not line.startswith("data:"):
                    continue
                data = line.removeprefix("data:").strip()
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if chunk.get("type") == "content_block_delta":
                    delta = chunk.get("delta", {})
                    text = delta.get("text")
                    if text:
                        yield text
    except requests.Timeout:
        yield "\n\nError: Anthropic took too long to respond."
    except requests.ConnectionError:
        yield "\n\nError: Could not connect to Anthropic."
    except requests.HTTPError as error:
        detail = read_error_detail(error.response)
        yield f"\n\nError from Anthropic: {detail or error}"
    except requests.RequestException as error:
        yield f"\n\nError communicating with Anthropic: {error}"
    except Exception as error:
        yield f"\n\nError: {error}"


def build_openai_messages(prompt, system_prompt="", image_paths=None):
    messages = []
    cleaned_system_prompt = str(system_prompt or "").strip()
    if cleaned_system_prompt:
        messages.append({"role": "system", "content": cleaned_system_prompt})

    if image_paths:
        content = [{"type": "text", "text": prompt}]
        for path in image_paths:
            content.append({
                "type": "image_url",
                "image_url": {"url": file_to_data_url(path)},
            })
        messages.append({"role": "user", "content": content})
    else:
        messages.append({"role": "user", "content": prompt})

    return messages


def build_gemini_contents(prompt, image_paths=None):
    parts = [{"text": prompt}]
    for path in image_paths or []:
        mime_type, encoded = encode_file(path)
        parts.append({"inlineData": {"mimeType": mime_type, "data": encoded}})
    return [{"role": "user", "parts": parts}]


def build_anthropic_messages(prompt, image_paths=None):
    if not image_paths:
        return [{"role": "user", "content": prompt}]

    content = [{"type": "text", "text": prompt}]
    for path in image_paths:
        mime_type, encoded = encode_file(path)
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": mime_type,
                "data": encoded,
            },
        })
    return [{"role": "user", "content": content}]


def file_to_data_url(path):
    mime_type, encoded = encode_file(path)
    return f"data:{mime_type};base64,{encoded}"


def encode_file(path):
    mime_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as file:
        encoded = base64.b64encode(file.read()).decode("ascii")
    return mime_type, encoded


def extract_gemini_text(chunk):
    text_parts = []
    for candidate in chunk.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            text = part.get("text")
            if text:
                text_parts.append(text)
    return "".join(text_parts)


def extract_gemini_finish_reason(chunk):
    for candidate in chunk.get("candidates", []):
        reason = candidate.get("finishReason")
        if reason:
            return str(reason)
    return ""


def yield_text_progressively(text, chunk_size=36):
    """Yield text in small, readable chunks without splitting words badly."""
    words = str(text).split(" ")
    buffer = ""

    for word in words:
        next_piece = word if not buffer else f" {word}"
        if len(buffer) + len(next_piece) >= chunk_size:
            if buffer:
                yield buffer
            buffer = word
        else:
            buffer += next_piece

    if buffer:
        yield buffer


def sanitize_provider_error(message):
    cleaned = str(message or "").strip()
    if not cleaned:
        return "The provider returned an error."

    # Never expose provider URLs or API keys in browser-visible errors.
    if "generativelanguage.googleapis.com" in cleaned or "key=" in cleaned:
        return "Gemini request failed. Please try again shortly."

    return cleaned[:500]


def resolve_temperature(mode, temperature):
    if temperature is not None:
        return float(temperature)
    if mode == "creative":
        return 0.95
    if mode == "precise":
        return 0.2
    if mode == "fast":
        return 0.4
    return 0.7


def resolve_max_tokens(mode, max_tokens):
    if max_tokens is not None:
        return int(max_tokens)
    if mode == "fast":
        return 250
    return None


def build_prompt(prompt, mode, option_number=None):
    if mode == "options_batch":
        return f"""
Create exactly three concise, complete answer options for the following request.

Quality requirements:
- Use clean Markdown and normal spacing between all words.
- Do not merge words such as "digital marketingagency" or "withdata-driven".
- Keep citations readable, for example: [Source 1].
- Each option must be complete and should not stop mid-sentence.

Use this exact format:

### Option 1
<complete answer, max 120 words>

### Option 2
<complete answer, max 120 words>

### Option 3
<complete answer, max 120 words>

Request:

{prompt}
""".strip()

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

Quality requirements:
- Use clean Markdown and normal spacing between words.
- Use complete sentences.
- If source text has spacing artifacts, repair spacing only and keep facts unchanged.

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

Quality requirements:
- Use clean Markdown and normal spacing between words.
- Use complete sentences.
- Avoid unnecessary details.

Request:

{prompt}
""".strip()

    if mode == "fast":
        return f"""
Give a concise and direct answer to the following request.

Use clean Markdown and normal spacing between words.

Request:

{prompt}
""".strip()

    return f"""
Answer the following request clearly and professionally.

Quality requirements:
- Use clean Markdown and normal spacing between words.
- Use complete sentences.
- If source text has spacing artifacts, repair spacing only and keep facts unchanged.

Request:

{prompt}
""".strip()


def read_error_detail(response):
    if response is None:
        return ""

    try:
        payload = response.json()
        error = payload.get("error")
        if isinstance(error, dict):
            return str(error.get("message") or error)
        if error:
            return str(error)
        return response.text[:500]
    except ValueError:
        return response.text[:500]
