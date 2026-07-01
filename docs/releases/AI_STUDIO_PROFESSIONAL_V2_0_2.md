# AI Studio Professional v2.0.2 - Quota Guard

## Added

- Gemini quota cooldown handling.
- Friendly 429 messages.
- Client-side protection against repeated 3 Options calls during cooldown.
- Lighter RAG context for comparison mode.

## Fixed

- Prevents Gemini API URLs from being exposed to users.
- Reduces repeated comparison-mode requests after quota errors.

## Notes

This release cannot increase your Gemini free-tier quota. It protects the app experience when the quota is temporarily exhausted.
