
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

## AI Studio Cloud Edition v1.1

- Added Gemini embedding provider for Render cloud deployments.
- Changed cloud embedding default from local Ollama `embeddinggemma` to `gemini-embedding-001`.
- Updated health checks so Gemini deployments no longer depend on Ollama availability.
- Updated Render defaults for Gemini chat and Gemini embeddings.
- No database migration required.
