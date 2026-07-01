"""Text quality helpers for AI Studio responses and RAG context.

This module fixes formatting artifacts that can appear when website text,
OCR text, or streamed model chunks contain collapsed whitespace. It does not
invent facts; it only normalizes spacing, punctuation, and common word-boundary
issues before content is sent to or displayed from the model.
"""

import re


KNOWN_JOIN_BOUNDARIES = (
    # Articles/prepositions glued to common business words.
    (r"\b(a|an|the|and|or|with|without|from|to|for|of|in|on|as|by|that|which|who)(?=(professional|digital|creative|technical|global|Swiss|data|marketing|agency|results|business|businesses|brands|services|clients|startups|established|affordable|pricing|reach|quality|SEO|Local|Social|Web|Email|Image|Video|B2B|B2C|Lead|Generation))", r"\1 "),
    # Frequent RAG/OCR/web-crawl glued phrases seen in marketing content.
    (r"\b(describing)(?=(DeepTechArt|Karimul|AI Studio|Gemini|Ollama))", r"\1 "),
    (r"\b(marketing)(?=(agency|services|strategy|content|campaigns))", r"\1 "),
    (r"\b(digital)(?=(marketing|agency|services|strategy))", r"\1 "),
    (r"\b(creative)(?=(agency|services|partner|content))", r"\1 "),
    (r"\b(technical)(?=(partner|services|SEO|support))", r"\1 "),
    (r"\b(global)(?=(brands|reach|clients|markets))", r"\1 "),
    (r"\b(Swiss)(?=(businesses|quality|brands|market))", r"\1 "),
    (r"\b(data-driven)(?=(digital|marketing|services|strategy))", r"\1 "),
    (r"\b(measurable)(?=(results|growth|outcomes))", r"\1 "),
    (r"\b(affordable)(?=(pricing|solutions|services))", r"\1 "),
    (r"\b(quality)(?=(precision|service|standards))", r"\1 "),
    (r"\b(clients)(?=(from|across|worldwide))", r"\1 "),
    (r"\b(startups)(?=(to|and|worldwide))", r"\1 "),
    (r"\b(businesses)(?=(and|globally|worldwide))", r"\1 "),
    (r"\b(focusing)(?=(on|primarily))", r"\1 "),
    (r"\b(increasing)(?=(visibility|traffic|leads|sales))", r"\1 "),
    (r"\b(deliver)(?=(Swiss|measurable|professional))", r"\1 "),
    (r"\b(include)(?=(SEO|Social|Web|Email|Image|Video|B2B))", r"\1 "),
    (r"\b(including)(?=(clients|Swiss|global|e-commerce))", r"\1 "),
    (r"\b(serving)(?=(both|Swiss|global))", r"\1 "),
    (r"\b(operate)(?=(as|globally))", r"\1 "),
)

BRAND_BOUNDARIES = (
    "DeepTechArt",
    "Karimul",
    "AI Studio",
    "Gemini",
    "Ollama",
    "OpenAI",
    "OpenRouter",
    "Anthropic",
)


def normalize_whitespace(text):
    value = str(text or "")
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = value.replace("\u00a0", " ").replace("\t", " ")
    value = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", value)
    value = re.sub(r"[ ]{2,}", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def repair_common_boundaries(text):
    value = str(text or "")

    for pattern, replacement in KNOWN_JOIN_BOUNDARIES:
        value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)

    # Add a space before important brand names when they are glued to a prior word.
    for brand in BRAND_BOUNDARIES:
        escaped = re.escape(brand)
        value = re.sub(rf"(?<=[a-z])(?={escaped})", " ", value)

    # Add spaces around source citations and after punctuation when missing.
    value = re.sub(r"(?<!\s)(\[Source\s+\d+\])", r" \1", value)
    value = re.sub(r"(\[Source\s+\d+\])(?=\w)", r"\1 ", value)
    value = re.sub(r"([.!?])(?=[A-Z0-9])", r"\1 ", value)
    value = re.sub(r"([,;:])(?=[A-Za-z0-9])", r"\1 ", value)

    # Clean markdown bullet spacing.
    value = re.sub(r"(?m)^\s*[-*]\s*", "- ", value)
    value = re.sub(r"(?m)^\s*(\d+)\.\s*", r"\1. ", value)

    return normalize_whitespace(value)


def normalize_source_text(text, limit=None):
    """Normalize retrieved source text before it enters the prompt."""
    value = repair_common_boundaries(normalize_whitespace(text))
    if limit and len(value) > int(limit):
        value = value[: int(limit)].rsplit(" ", 1)[0].strip()
    return value


def polish_assistant_text(text):
    """Normalize model output spacing without changing factual content."""
    value = repair_common_boundaries(normalize_whitespace(text))
    return value
