# Portfolio Release Guide

## What to publish

Publish the cleaned repository and the Render live demo link.

Recommended project description:

> AI Studio is a production-style AI workspace built with Flask, PostgreSQL, Docker, RAG, file uploads, prompt templates, admin analytics, accessibility checks, and a hybrid AI provider layer. It supports local Ollama models for development and a hosted provider for public demos.

## Suggested screenshots

Add screenshots under `docs/images/`:

1. Login screen
2. Main chat interface
3. Streaming response with Markdown/code
4. Prompt Library
5. File upload and RAG answer with sources
6. Admin dashboard
7. Mobile responsive layout

## Demo script

1. Log in as a demo user.
2. Create a new chat.
3. Ask a normal question.
4. Show response mode/model controls.
5. Upload a small document.
6. Ask a question from the document.
7. Show prompt library and saved prompts.
8. Open admin dashboard with analytics.

## Final release checklist

- [ ] `.env` removed from GitHub
- [ ] Uploads and logs removed from GitHub
- [ ] Render deployment works
- [ ] PostgreSQL attached
- [ ] Migrations run successfully
- [ ] Hosted AI provider responds
- [ ] Ollama local mode documented
- [ ] README includes live demo link
- [ ] Screenshots added
- [ ] Changelog updated
- [ ] Version tag created, for example `v1.0.0`
