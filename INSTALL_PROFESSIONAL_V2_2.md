# AI Studio Professional v2.2 — Reliability Edition Install Guide

This release improves Gemini reliability without changing database tables or Render environment variables.

## What it changes

- Adds safer Gemini retry/backoff behavior.
- Adds fallback model attempts when configured models are available.
- Adds a short in-memory response cache for repeated identical prompts.
- Keeps Gemini on the stable non-streaming endpoint, then displays the complete response progressively.
- Keeps provider URLs/API keys hidden from browser-visible errors.

## Install

Run the commands from the main AI Studio project folder in VS Code PowerShell.
