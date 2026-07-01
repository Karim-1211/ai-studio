# Troubleshooting

## Gemini key missing

Check Render environment:

```env
GEMINI_API_KEY=<your key>
```

## Knowledge not working

Check:

```env
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=gemini-embedding-001
```

## Ollama unavailable locally

Run:

```powershell
ollama serve
ollama list
```

## Render deploy failed

Check Render logs and confirm environment variables.
