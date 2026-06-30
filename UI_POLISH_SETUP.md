# AI Studio UI Polish Update

This update improves the compact workspace without changing chats, documents, knowledge sources, OCR, voice, attachments, or database data.

## Changes

- Professional Markdown paragraph, heading, and list spacing.
- Removes exaggerated blank space caused by preserved whitespace after Markdown rendering.
- Wider assistant responses on desktop and half-width windows.
- Responsive Knowledge Sources bar that prevents title/action overlap.
- Compact icon-only send button aligned with attachment and voice controls.
- Stop-generation icon state while a response is streaming.
- Microphone permission policy corrected to `microphone=(self)`.

## Install

Stop Flask, copy this package over the project while excluding `.env`, uploads, logs, and virtual environments, then restart Flask and hard-refresh the browser.

No database migration is required.
