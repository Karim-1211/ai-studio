# AI Studio Architecture

## High-Level Architecture

```text
Browser
  |
  v
Flask Application
  |
  +-- Authentication
  +-- Chat Management
  +-- Knowledge Management
  +-- Provider Manager
  |
  +-- Cloud Mode: Gemini
  +-- Local Mode: Ollama
  |
  +-- PostgreSQL / Local DB
```

## Cloud Mode

```text
User Browser
  |
  v
Render Web Service
  |
  v
Flask AI Studio
  |
  +-- Gemini Chat
  +-- Gemini Embeddings
  +-- Neon PostgreSQL
```

## Local Mode

```text
Local Browser
  |
  v
Flask AI Studio on localhost
  |
  +-- Ollama Models
  +-- Local Embeddings
  +-- Local Database
```

## RAG Pipeline

```text
Document / Website / Social Source
  |
  v
Text Extraction / OCR
  |
  v
Chunking
  |
  v
Embedding
  |
  v
Vector Search
  |
  v
Gemini or Ollama Answer
```
