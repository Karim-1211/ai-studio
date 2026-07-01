# AI Studio Project Roadmap

## Current release

AI Studio v2.5 — reliable social-source fallback, accessible light theme, and neon workspace branding

## Completed

### AI chat

- Local Ollama generation
- Dynamic model selection
- Streaming responses
- Stop and regenerate
- Markdown and syntax highlighting
- Copy controls
- Multiple response modes
- Three progressive option cards

### Authentication and workspace isolation

- Secure local account login
- Strong password hashing and session protection
- Login lockout after repeated failures
- Per-user chats, uploads, global files, website memberships, and social memberships
- Administrator user management
- Password reset CLI and self-service account deletion
- CSRF protection for forms and API mutations

### Persistence and chat management

- PostgreSQL chat history
- Message persistence
- Search, pin, rename, delete, and export
- Alembic migrations
- Transaction-aware file cleanup

### Knowledge and RAG

- Chat-specific documents
- Message-level PDF, document, and image attachments
- Drag-and-drop and clipboard screenshot paste
- Ollama vision capability detection and fallback image analysis
- Reusable global knowledge library
- PDF, DOCX, TXT, PNG, JPG, and JPEG uploads
- OCR for images and scanned PDFs
- Ollama embeddings
- Selected-source retrieval
- Strict document answers
- Source citations, excerpts, and relevance scores
- Website crawler with sitemap import, same-domain discovery, page preview, and grouped management
- Indexed Facebook, Instagram, X, TikTok, LinkedIn, YouTube, Threads, and Bluesky links
- Pasted social-content fallback for login-only and JavaScript-heavy pages

### Interface

- Responsive dark and light themes
- Persistent generation settings
- Compact model toolbar
- Compact knowledge summary
- Right-side knowledge drawer
- Floating health-status popover
- Expanded chat reading area
- Advanced settings close on outside click or Escape
- Modern directional pin state for pinned chats
- Independently scrollable Manage Knowledge drawer with sticky controls
- Account menu in the sidebar
- Automatic manual fallback when social platforms block public reading
- High-contrast light-theme buttons, tabs, fields, states, and status messages
- Neon gradient AI Assistant title in dark and light themes

### Production engineering

- Application factory
- Development, testing, and production configuration
- Waitress server
- Structured rotating logs
- Health and readiness endpoints
- Security headers
- Automated pytest suite
- Dockerfile and Docker Compose
- GitHub Actions CI
- Portfolio README and architecture documentation

## Recommended next milestones

### v2.6 Background processing

- Queue document extraction and embeddings
- Upload progress polling
- Retry failed OCR and embedding jobs
- Cancel long-running indexing tasks

### v2.7 Retrieval quality

- Hybrid semantic and keyword search
- Document metadata filters
- Reranking
- Chunk previews and source navigation
- Retrieval evaluation dataset

### v2.8 Deployment

- Reverse proxy and TLS
- Backup and restore automation
- Monitoring and alerting
- Cloud or home-server deployment guide
- Versioned releases and changelog

## Website knowledge sources

- [x] Add one public webpage at a time
- [x] Safe URL validation and private-network blocking
- [x] HTML cleanup, chunking, embeddings, refresh, delete, and citations
- [x] Website source migration and automated tests
- [x] Homepage discovery and sitemap.xml import
- [x] Page preview and selective batch indexing
- [x] Same-domain, depth, page-limit, robots.txt, and private-network safeguards
- [x] Domain-group refresh and delete controls


## Attachments and social knowledge

- [x] Composer paperclip, drag-and-drop, and clipboard image paste
- [x] Message attachment persistence and file cleanup
- [x] PDF/document RAG and OCR
- [x] Vision-capable Ollama model detection and fallback
- [x] Supported social URL validation
- [x] Public social-page extraction and pasted-text fallback
- [x] Social selection, refresh, delete, citations, migration, and tests
- [x] Automatic blocked-platform fallback that opens and focuses the pasted-text workflow
- [x] Separate public-import and pasted-content actions with clear privacy guidance

## Future social connectors

- [ ] OAuth connection for owned Facebook Pages and Instagram professional accounts
- [ ] Platform-specific scheduled synchronization
- [ ] Token lifecycle and permission management
- [ ] Post-level incremental updates and rate-limit handling


## Voice chat

- [x] Browser microphone speech-to-text
- [x] Live prompt transcription with start and stop controls
- [x] Automatic assistant read-aloud toggle
- [x] Per-response and option-card read controls
- [x] Browser support detection and accessible status messages
- [ ] Optional fully local Whisper speech-to-text backend

## Chat organization and workspace backup

- [x] Per-user chat folders
- [x] Per-user chat tags with color labels
- [x] Favorite and archive states
- [x] Active, favorites, archived, all, folder, and tag filters
- [x] Drag chats into folders
- [x] Multi-select archive, restore, favorite, move, tag, and delete actions
- [x] Per-user ZIP workspace backup
- [x] Additive workspace restore with upload files and knowledge metadata
- [x] Social-platform blocked-import manual-required workflow
- [x] Existing social URL update instead of duplicate failure
- [x] Migration `20260628_0005` and automated tests

## Prompt library and conversation branching

- [x] Per-user reusable prompt templates
- [x] Prompt search, categories, favorites, editing, copying, and usage tracking
- [x] Insert saved prompts at the composer cursor
- [x] Branch a conversation from any user or assistant message
- [x] Edit a previous user message safely in a new branch
- [x] Preserve original conversations and show branch state in the sidebar
- [x] Include prompt templates and branch metadata in workspace backup and restore
- [x] Bring wide-screen user and assistant messages into a shared reading rail
- [x] Replace three always-visible chat-row controls with one compact action menu
- [x] Migration `20260628_0006` and automated regression tests

## Admin dashboard, reliability, accessibility, and security

- [x] Administrator operations dashboard
- [x] Per-user chat, message, knowledge-source, and storage analytics
- [x] Model usage and end-to-end generation-duration telemetry
- [x] Failed-request history and sampled health history
- [x] Account enable/disable controls linked from the dashboard
- [x] Orphan-upload cleanup and telemetry-retention tools
- [x] Audit log for important account and maintenance actions
- [x] Process-local rate limiting and abuse protection
- [x] Browser-test harness and responsive viewport checks
- [x] Keyboard navigation, skip link, focus indicators, and screen-reader labels
- [x] Stronger light-theme contrast
- [x] Collapsible RAG source lists
- [x] Oversized prompt and attachment-limit tests
- [x] PostgreSQL backup and restore rehearsal scripts and documentation
- [x] Migration `20260628_0007`

## Remaining final phase

### Final Deployment and Portfolio Release

- [ ] Production Docker verification on the target machine
- [ ] HTTPS reverse proxy and domain configuration
- [ ] Shared production secrets and secure environment review
- [ ] Scheduled PostgreSQL backup automation
- [ ] Final repository cleanup and public-safe screenshots
- [ ] Architecture diagram refresh
- [ ] Changelog, release version, and final release checklist
- [ ] Deployment rehearsal and rollback plan
