# AI Studio Professional Edition v2.0 — Installation Guide

This release improves the real-time chat experience while keeping the stable Gemini/Ollama dual-mode architecture intact.

## What changes

- Improves streaming response cancellation.
- Keeps partial responses when the user stops generation.
- Saves stopped partial responses to chat history instead of replacing them with only `[Generation stopped]`.
- Updates the no-model warning so it works for both Gemini and Ollama mode.

## What does not change

- No database migration.
- No Render environment change.
- No RAG pipeline change.
- No authentication change.
- No deployment configuration change.

## Install

Open VS Code terminal in your project folder:

```powershell
C:\Users\islam\Downloads\AI-Chat-App-phase4-multi-provider-render-ready\AI-Chat-App
```

Then run:

```powershell
$zip = "$env:USERPROFILE\Downloads\ai_studio_professional_v2_0.zip"
$source = "$env:USERPROFILE\Downloads\ai_studio_professional_v2_0"

Remove-Item $source -Recurse -Force -ErrorAction SilentlyContinue
Expand-Archive -Path $zip -DestinationPath $source -Force

powershell -ExecutionPolicy Bypass -File "$source\scripts\install_professional_v2_0.ps1" `
  -ProjectPath "C:\Users\islam\Downloads\AI-Chat-App-phase4-multi-provider-render-ready\AI-Chat-App"
```

Expected result:

```text
AI Studio Professional Edition v2.0 installed.
```

## Validate

```powershell
powershell -ExecutionPolicy Bypass -File "$source\scripts\validate_professional_v2_0.ps1" `
  -ProjectPath "C:\Users\islam\Downloads\AI-Chat-App-phase4-multi-provider-render-ready\AI-Chat-App"
```

Expected result:

```text
Validation passed.
```

## Commit and push

```powershell
cd "C:\Users\islam\Downloads\AI-Chat-App-phase4-multi-provider-render-ready\AI-Chat-App"

git status
git add .
git commit -m "Release AI Studio Professional Edition v2.0"
git push origin main
```

## Render

Render should deploy automatically. Do not change Render environment variables.

## Post-deployment test

1. Open the live AI Studio app.
2. Send a long prompt, such as: `Write a detailed 700-word explanation of RAG.`
3. While the answer is streaming, click the stop button.
4. Expected: the partial answer remains visible and ends with `[Generation stopped]`.
5. Refresh the chat.
6. Expected: the stopped partial response remains in chat history.
7. Send a normal message.
8. Expected: streaming still works normally.
