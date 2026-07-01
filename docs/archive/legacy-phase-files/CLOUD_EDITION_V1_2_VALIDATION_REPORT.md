# AI Studio Cloud Edition v1.2 Validation Report

## Validation performed before package delivery

- Python compile-all: passed.
- Updated embedding service syntax: passed.
- Updated health service syntax: passed.
- Updated authentication route syntax: passed.
- Updated attachment route syntax: passed.
- Document, global document, website, social, and chat route syntax: passed.
- Database migration added: no.
- Render config updated for external `DATABASE_URL`: yes.

## Important runtime requirements

Render environment must contain:

- `AI_PROVIDER=gemini`
- `GEMINI_MODEL=gemini-2.5-flash`
- `GEMINI_API_KEY`
- `EMBEDDING_PROVIDER=gemini`
- `EMBEDDING_MODEL=gemini-embedding-001`
- `GEMINI_EMBEDDING_DIMENSIONS=768`
- `DATABASE_URL`

Old failed records created before this release must be deleted and re-uploaded because failed embedding rows are not automatically repaired.
