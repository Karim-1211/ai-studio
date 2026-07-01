# Local Ollama Mode

Local mode allows AI Studio to run with Ollama models on your computer.

## Requirements

- Ollama installed
- At least one chat model installed
- Optional embedding model installed

## Example Commands

```powershell
ollama list
ollama pull llama3
ollama pull mistral
```

## Local Environment

```env
APP_ENV=development
AI_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
EMBEDDING_MODEL=embeddinggemma
AUTH_REQUIRED=false
```

Render does not use your local `.env`, so local Ollama mode will not affect the live cloud app.
