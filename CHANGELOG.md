
## AI Studio Dual Mode v1.3

- Added documented local Ollama mode using `.env.local.example`.
- Added cloud Gemini reference configuration using `.env.cloud.example`.
- Added beginner-safe local Ollama setup guide.
- Kept Render/Gemini production mode isolated from local development.
- No database migration required.


## Phase 4.1 - Multi-provider portfolio demo

- Added AI provider support for Ollama, OpenAI, OpenRouter, Gemini, and Anthropic.
- Updated Render Blueprint to use free plans and Gemini by default for public demos.
- Added provider configuration documentation.

# Changelog

## v1.0.0 - Portfolio Release

### Added
- Hybrid AI provider support for local Ollama and hosted OpenAI-compatible deployment.
- Render Blueprint configuration for Flask + PostgreSQL deployment.
- Production deployment guide.
- Portfolio release guide.

### Preserved
- Local Ollama chat support.
- RAG, OCR, file upload, website/social knowledge sources, prompt library, admin analytics, authentication, accessibility, and production hardening features.

### Security
- Clean release package excludes `.env`, logs, cache files, generated uploads, and old nested workspace copies.
