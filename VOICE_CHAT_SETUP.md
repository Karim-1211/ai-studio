# Voice Chat Setup

AI Studio now includes two-way browser voice controls without adding a server-side dependency or database migration.

## Features

- Microphone button beside the attachment button
- Live speech-to-text transcription in the prompt box
- Start and stop listening from the same button
- Automatic assistant read-aloud toggle
- Read-aloud button on every saved and newly generated assistant response
- Read button on each generated option card
- Stop speech by clicking the active read button or speaker button
- Voice preference stored in browser local storage
- Browser capability detection and useful error messages

## Controls

### Microphone

Click the microphone button, allow microphone access, speak, and click it again when finished. The transcript is placed in the prompt box so it can be reviewed or edited before sending.

### Speaker

Click the speaker button to turn automatic read-aloud on or off. When enabled, normal assistant responses are spoken after generation finishes.

Every assistant answer also has a **Read aloud** button. This works even when automatic read-aloud is disabled.

## Browser requirements

Speech input uses the browser Speech Recognition API. Current Chromium-based browsers, especially Microsoft Edge and Google Chrome, provide the best support.

Speech output uses the browser Speech Synthesis API and the voices installed or exposed by the browser and operating system.

Microphone access works on `http://localhost` and `http://127.0.0.1`. A deployed non-local site normally requires HTTPS before the browser will allow microphone access.

## Privacy note

Text generation, RAG, OCR, attachments, and database storage remain in AI Studio. Browser speech recognition may use the browser vendor's speech service depending on the browser and operating system. Audio is not uploaded to the AI Studio Flask backend by this feature.

A fully local speech-to-text implementation would require a separate local model such as Whisper and is not included in this update.

## Installation

This update is installed over the previous Chat Attachments + Social Knowledge Sources package.

No new Python package and no database migration are required.

After copying the files:

```powershell
cd "C:\Users\islam\PythonProject\AI-Chat-App"
python -m compileall -q .
python -m pytest
python app.py
```

Then open `http://127.0.0.1:5000` and press `Ctrl + F5`.

## Test checklist

1. Click the microphone button.
2. Allow microphone access.
3. Speak a sentence and stop listening.
4. Confirm the transcript appears in the prompt.
5. Send the message.
6. Click **Read aloud** on the response.
7. Enable the speaker button and send another message.
8. Confirm the new normal response is read automatically.
9. Reload the page and confirm the automatic read-aloud preference remains saved.
