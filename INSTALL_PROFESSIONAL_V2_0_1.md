# AI Studio Professional v2.0.1 Stability Fix

This release fixes the response truncation and Gemini 429 behavior introduced around the v2.0 streaming experiment.

## What changes

- Gemini cloud generation uses the stable `generateContent` endpoint instead of `streamGenerateContent`.
- Browser-visible Gemini errors no longer expose full provider URLs or API keys.
- 3 Options mode now uses one Gemini request instead of three separate requests.
- Single Answer, Detailed, RAG, website knowledge, and social knowledge remain unchanged in behavior.
- No database migration required.
- No Render environment changes required.

## Files changed

- `services/ai_provider_service.py`
- `routes/chat_routes.py`
- `static/js/options.js`

