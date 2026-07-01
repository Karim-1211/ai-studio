# AI Studio Professional v2.2 — Reliability Edition

## Summary

This release improves reliability around Gemini quota/rate-limit conditions.

## Changes

- Added retry/backoff behavior for Gemini calls.
- Added fallback model attempts using configured Gemini models plus safe flash fallbacks.
- Added short-lived in-memory response caching to reduce repeated calls during testing.
- Preserved complete-response behavior to avoid truncated answers.
- Continued hiding provider URLs/API keys from user-visible errors.

## Database migration

No migration required.

## Render environment changes

No changes required.
