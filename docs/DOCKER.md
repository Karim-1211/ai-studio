# Docker Guide

## Prerequisites

- Docker Desktop on Windows or macOS, or Docker Engine with Compose on Linux.
- Ollama running on the host, unless using `compose.ollama.yaml`.

## Host Ollama mode

Create the Docker environment file:

```powershell
Copy-Item .env.docker.example .env.docker
```

Generate values:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Put the first value in `POSTGRES_PASSWORD` and the second in `SECRET_KEY`.

Start the stack:

```powershell
docker compose --env-file .env.docker up --build -d
```

Open:

```text
http://127.0.0.1:5000
```

View logs:

```powershell
docker compose --env-file .env.docker logs -f app
```

Stop the stack:

```powershell
docker compose --env-file .env.docker down
```

## Fully containerized Ollama mode

Start AI Studio, PostgreSQL, and Ollama:

```powershell
docker compose `
  --env-file .env.docker `
  -f compose.yaml `
  -f compose.ollama.yaml `
  up --build -d
```

Pull models:

```powershell
docker compose `
  --env-file .env.docker `
  -f compose.yaml `
  -f compose.ollama.yaml `
  exec ollama ollama pull embeddinggemma
```

Pull at least one generation model, for example:

```powershell
docker compose `
  --env-file .env.docker `
  -f compose.yaml `
  -f compose.ollama.yaml `
  exec ollama ollama pull gemma3:4b
```

## Persistent data

Compose creates named volumes for:

- PostgreSQL data
- uploaded files
- application logs
- optional Ollama models

To remove containers while keeping data:

```powershell
docker compose --env-file .env.docker down
```

To remove containers and all Compose-managed data:

```powershell
docker compose --env-file .env.docker down -v
```

The `-v` command permanently removes the Compose volumes.


## Vision attachments

For image understanding, pull a vision-capable model and optionally set it in `.env.docker`:

```powershell
ollama pull gemma3:4b
```

```env
VISION_MODEL=gemma3:4b
```

When Ollama is containerized, run the pull command through the Ollama service as shown above. Attachment files remain in the `uploads_data` volume.
