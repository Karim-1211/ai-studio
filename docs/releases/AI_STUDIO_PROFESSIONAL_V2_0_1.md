# AI Studio Professional Edition v2.0.1

## Summary

v2.0.1 restores stable full-length Gemini responses and makes comparison mode safer on free-tier Gemini API limits.

## Fixes

- Fixed incomplete/truncated Gemini answers.
- Reduced 3 Options mode from three provider calls to one provider call.
- Prevented API key leakage in browser-visible Gemini error messages.
- Added gentle retry handling for temporary Gemini 429 responses.

## Migration

No database migration is required.

