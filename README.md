# AI Studio

**Enterprise AI Workspace for Knowledge, Documents, Websites, and Local/Cloud AI**

Built by **Karim-ul Islam** — **AI Solutions Developer | SEO & Digital Marketing Professional**

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black)
![Gemini](https://img.shields.io/badge/Gemini-Cloud%20AI-purple)
![Ollama](https://img.shields.io/badge/Ollama-Local%20AI-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![Render](https://img.shields.io/badge/Render-Deployed-brightgreen)
![RAG](https://img.shields.io/badge/RAG-Knowledge%20Search-orange)
![Status](https://img.shields.io/badge/Status-Stable-success)

---

## Live Demo

```text
https://ai-studio-ty6z.onrender.com
```

---

## Overview

AI Studio is a full-stack AI workspace that supports both cloud-hosted AI and local AI development. It combines chat, document understanding, OCR, website knowledge, social knowledge, file uploads, RAG, authentication, and production deployment into one professional portfolio-ready application.

AI Studio started as a local Ollama-powered assistant and evolved into a cloud-ready Gemini-powered platform while preserving local Ollama mode for development and model experimentation.

---

## Key Features

### AI Chat
- Gemini-powered cloud chat
- Ollama-powered local chat
- Multiple chat sessions
- Markdown-friendly responses
- Persistent conversation history
- Cloud/local provider separation

### Knowledge & RAG
- PDF knowledge ingestion
- DOCX knowledge ingestion
- TXT knowledge ingestion
- Image OCR
- Website knowledge indexing
- Social knowledge import
- Knowledge-based question answering

### Attachments
- Chat-level file uploads
- Attachment previews
- OCR processing
- Knowledge extraction
- Searchable document chunks

### Deployment
- Render-ready deployment
- Neon PostgreSQL support
- Docker configuration
- Secure production settings
- Health monitoring

### Local Development
- Ollama local model support
- Local embedding support
- Local database option
- Safe separation from production cloud mode

---

## Architecture

```text
Browser
  |
  v
Flask AI Studio App
  |
  +--> Provider Manager
  |      +--> Cloud Mode: Gemini
  |      +--> Local Mode: Ollama
  |
  +--> Knowledge Pipeline
  |      +--> PDF / DOCX / TXT / Images
  |      +--> OCR
  |      +--> Website Knowledge
  |      +--> Social Knowledge
  |      +--> Embeddings
  |      +--> Retrieval
  |
  +--> PostgreSQL / Local Database
  |
  +--> Render / Localhost
```

See [`docs/03-Architecture.md`](docs/03-Architecture.md) for details.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | PostgreSQL, SQLAlchemy, Alembic |
| AI Cloud | Google Gemini |
| AI Local | Ollama |
| RAG | Custom ingestion and retrieval pipeline |
| OCR | Tesseract / OCR pipeline |
| Deployment | Docker, Render |
| Storage | Local upload storage + database metadata |
| Frontend | HTML, CSS, JavaScript |

---

## Quick Start

### Cloud Mode

Use Render with:

```env
AI_PROVIDER=gemini
EMBEDDING_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=gemini-embedding-001
DATABASE_URL=<your Neon PostgreSQL URL>
GEMINI_API_KEY=<your Gemini key>
```

See [`docs/05-Cloud-Deployment.md`](docs/05-Cloud-Deployment.md).

### Local Mode

Use Ollama with:

```env
AI_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
EMBEDDING_MODEL=embeddinggemma
```

See [`docs/06-Local-Ollama.md`](docs/06-Local-Ollama.md).

---

## Documentation

- [Documentation Index](docs/README.md)
- [Overview](docs/01-Overview.md)
- [Features](docs/02-Features.md)
- [Architecture](docs/03-Architecture.md)
- [Installation](docs/04-Installation.md)
- [Cloud Deployment](docs/05-Cloud-Deployment.md)
- [Local Ollama Mode](docs/06-Local-Ollama.md)
- [User Guide](docs/07-User-Guide.md)
- [Admin Guide](docs/08-Admin-Guide.md)
- [Developer Guide](docs/09-Developer-Guide.md)
- [Troubleshooting](docs/10-Troubleshooting.md)
- [Roadmap](docs/11-Roadmap.md)
- [Career Materials](docs/career/README.md)
- [Release Notes Archive](docs/releases/README.md)

---

## Portfolio Summary

AI Studio demonstrates full-stack AI product development, including authentication, AI provider abstraction, document ingestion, RAG, OCR, cloud deployment, Docker, PostgreSQL, and local development workflows.

It is designed as a flagship portfolio project for an **AI Solutions Developer | SEO & Digital Marketing Professional**.

---

## Author

**Karim-ul Islam**  
AI Solutions Developer | SEO & Digital Marketing Professional  
GitHub: [Karim-1211](https://github.com/Karim-1211)  
LinkedIn: [Karimul Islam](https://www.linkedin.com/in/karimul-islam-seo-and-digital-marketing-expert/)
