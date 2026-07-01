# AI Studio Dual Mode v1.3 - Local Ollama Mode Setup

This guide lets you run AI Studio locally with Ollama without touching the live Render/Gemini deployment.

## Important safety rule

Your live Render app uses Render environment variables. Your local computer uses `.env`.

Do not commit `.env` to GitHub. It is already ignored by `.gitignore`.

## Step 1 - Open the project in VS Code

Open this folder:

```powershell
C:\Users\islam\Downloads\AI-Chat-App-phase4-multi-provider-render-ready\AI-Chat-App
```

Open Terminal > New Terminal.

## Step 2 - Create local `.env`

Run:

```powershell
Copy-Item .env.local.example .env -Force
Test-Path .env
```

Expected:

```text
True
```

## Step 3 - Start Ollama

Open a separate terminal and run:

```powershell
ollama serve
```

If Ollama is already running, this may say the port is already in use. That is okay.

## Step 4 - Confirm local models

In a terminal, run:

```powershell
ollama list
```

You should see your local models, such as llama3, mistral, qwen, phi, or gemma.

## Step 5 - Confirm local embedding model

Your `.env.local.example` uses:

```text
EMBEDDING_MODEL=embeddinggemma
```

If you do not have it, either install it or change `.env` to an embedding model you already have.

Check with:

```powershell
ollama list
```

## Step 6 - Validate Python files

Run:

```powershell
python -m compileall -q .
python -m py_compile config.py
python -m py_compile services/ai_provider_service.py
python -m py_compile services/embedding_service.py
python -m py_compile services/health_service.py
python -m py_compile routes/model_routes.py
```

Expected: no output.

## Step 7 - Start AI Studio locally

Run:

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Step 8 - Test local Ollama mode

1. Check the status badge.
2. Open the model dropdown.
3. Confirm local Ollama models appear.
4. Send: `Hello from local Ollama.`
5. Upload a small TXT file and ask for a summary.

## Step 9 - Return to Cloud/Render work

No action is needed. Render does not use your local `.env`.

Do not change Render environment variables when testing local mode.
