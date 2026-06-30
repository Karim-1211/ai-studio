# AI Provider Configuration

AI Studio supports multiple AI backends through one provider layer. The UI stays the same; the backend switches provider based on environment variables.

## Supported providers

| Provider | `AI_PROVIDER` value | Best use |
|---|---|---|
| Ollama | `ollama` | Local/private development |
| OpenAI | `openai` | Production demos using OpenAI |
| OpenRouter | `openrouter` | Access many hosted models through one API |
| Google Gemini | `gemini` | Low-cost/public portfolio demos |
| Anthropic Claude | `anthropic` | Claude-based hosted demos |

## Recommended portfolio deployment

For Render, the default Blueprint uses Gemini:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_google_ai_studio_key
GEMINI_MODEL=gemini-1.5-flash
```

This lets clients chat with the deployed assistant without installing Ollama.

## Local Ollama development

```env
AI_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
```

## OpenAI

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_MODELS=gpt-4o-mini
```

## OpenRouter

```env
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_MODELS=openai/gpt-4o-mini
```

## Anthropic

```env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_key
ANTHROPIC_MODEL=claude-3-5-haiku-latest
ANTHROPIC_MODELS=claude-3-5-haiku-latest
```

## Notes

- Only set the API key for the provider you are actively using.
- Ollama remains fully supported for local use.
- Hosted providers are required for a public client demo because users cannot access Ollama running on your computer.
- Image uploads are sent directly to hosted providers only when the selected provider supports image input.
