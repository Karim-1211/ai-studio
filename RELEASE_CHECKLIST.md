# Release Checklist

- [ ] `python -m pytest` passes.
- [ ] `python -m compileall -q .` passes.
- [ ] Every file in `static/js/` passes `node --check`.
- [ ] `docker build -t ai-studio:release .` succeeds.
- [ ] `.env` and `.env.docker` are not tracked.
- [ ] Screenshots contain no private documents or local credentials.
- [ ] Database migrations are current.
- [ ] Normal chat works.
- [ ] Streaming stop and regenerate work.
- [ ] Chat document RAG works.
- [ ] Global document RAG works in a new chat.
- [ ] OCR image and scanned PDF uploads work.
- [ ] Composer paperclip upload works for PDF and image files.
- [ ] Drag-and-drop and clipboard screenshot paste work.
- [ ] A vision-capable Ollama model analyzes visual image content.
- [ ] Saved message attachments remain visible after reopening a chat.
- [ ] Deleting a chat removes its attachment files.
- [ ] Source citations render after page refresh.
- [ ] Light and dark themes work.
- [ ] Knowledge drawer works on desktop and mobile.
- [ ] Health checks report expected services.
- [ ] README installation instructions were tested from a clean clone.
- [ ] A repository license has been selected before public release.

## Website knowledge

- [ ] Add, select, refresh, cite, and delete a public webpage
- [ ] Discover pages from a homepage and sitemap.xml
- [ ] Confirm crawl depth and maximum-page controls are respected
- [ ] Select only chosen discovered pages before indexing
- [ ] Refresh and delete all indexed pages for one domain
- [ ] Confirm login, checkout, admin, search, file-download, localhost, and private-network URLs are rejected or excluded
- [ ] Confirm the `20260628_0002` migration is applied


## Social knowledge

- [ ] Add and cite a publicly readable social-media link
- [ ] Trigger a blocked public social import and confirm the manual fallback opens automatically
- [ ] Add a blocked/login-only social link using pasted visible text
- [ ] Confirm the original social URL remains the citation for pasted content
- [ ] Confirm no social-media password or access token is requested
- [ ] Select and deselect social sources
- [ ] Refresh an automatically extracted social source
- [ ] Confirm a manually pasted source correctly rejects automatic refresh
- [ ] Delete a social source
- [ ] Confirm unsupported domains are rejected
- [ ] Confirm the `20260628_0003` migration is applied


## Voice chat

- [ ] Allow microphone permission in Edge or Chrome
- [ ] Confirm speech appears in the prompt and remains editable
- [ ] Confirm manual **Read aloud** works on a saved response
- [ ] Confirm automatic read-aloud persists after refresh
- [ ] Confirm active speech can be stopped
- [ ] Confirm deployed microphone access uses HTTPS


## Sidebar and settings polish

- [ ] Confirm a pinned chat uses the new pin with its point directed down-left
- [ ] Confirm pin and unpin states remain accessible with `aria-pressed`
- [ ] Open Advanced and click outside it to confirm it closes
- [ ] Open Advanced and press Escape to confirm it closes and returns focus

## Secure accounts and workspace isolation

- [ ] Back up PostgreSQL before applying migration `20260628_0004`
- [ ] Confirm `AUTO_CREATE_DATABASE=false`
- [ ] Apply migration `20260628_0004` without using `db stamp`
- [ ] Run `bootstrap-owner` and confirm legacy chats and knowledge sources are claimed
- [ ] Sign in and sign out successfully
- [ ] Confirm failed-login lockout works after the configured attempt limit
- [ ] Confirm one user cannot read, modify, export, or delete another user's chats
- [ ] Confirm global files, website memberships, and social memberships are isolated per user
- [ ] Confirm administrator create, disable, promote, and delete actions work
- [ ] Confirm account profile, password change, and account deletion work
- [ ] Confirm POST, PATCH, and DELETE API requests reject missing or invalid CSRF tokens
- [ ] Confirm authenticated pages use private no-store caching

## Scrollable Manage Knowledge drawer

- [ ] Open the drawer on a short or half-height display
- [ ] Confirm the drawer content scrolls independently to the Social Sources section
- [ ] Confirm the drawer header, switches, and tabs remain visible
- [ ] Confirm the underlying chat page does not scroll while the drawer is open
- [ ] Confirm mouse wheel, trackpad, touch, and keyboard scrolling work

## Light theme and branding polish

- [ ] Confirm primary, secondary, disabled, refresh, delete, and selection buttons are readable in light mode
- [ ] Confirm active and inactive Knowledge tabs have clear contrast
- [ ] Confirm success, working, and error messages remain readable in light mode
- [ ] Confirm inputs and placeholders remain readable in light mode
- [ ] Confirm the AI Assistant neon title is legible in dark and light themes

## Chat organization and backup

- [ ] Back up PostgreSQL before applying migration `20260628_0005`
- [ ] Confirm `python -m flask --app app:create_app db current` shows `20260628_0005 (head)`
- [ ] Create, rename, filter, and delete a folder without deleting its chats
- [ ] Create, apply, filter, and remove a tag
- [ ] Favorite, archive, and restore a chat
- [ ] Drag a chat onto a folder in the Organize panel
- [ ] Run a bulk archive, restore, move, tag, and delete action
- [ ] Download a workspace backup and confirm `.env` is not present
- [ ] Restore the backup into a test account and confirm chats and files appear
- [ ] Trigger a blocked public social import and confirm it returns the manual workflow rather than a hard error
- [ ] Index pasted social content with an optional blank title

## Prompt library, branching, and conversation layout

- [ ] Back up PostgreSQL before applying migration `20260628_0006`
- [ ] Confirm `python -m flask --app app:create_app db current` shows `20260628_0006 (head)` after upgrade
- [ ] Create, search, categorize, favorite, edit, copy, insert, and delete a prompt template
- [ ] Save the current composer text as a reusable prompt
- [ ] Branch from a user message and an assistant message
- [ ] Confirm a branch contains only history through the selected message
- [ ] Use **Edit in branch** and confirm the original conversation remains unchanged
- [ ] Confirm prompt templates and branch relationships survive workspace backup and restore
- [ ] At full desktop width, confirm user and assistant messages sit closer to a shared reading rail
- [ ] At half-window and mobile widths, confirm message layout remains responsive
- [ ] Confirm each chat row has one visible overflow button
- [ ] Confirm favorite and pin actions work from the overflow menu and state badges remain visible

## Admin analytics and reliability

- [ ] `python -m flask --app app:create_app db current` reports `20260628_0007 (head)`
- [ ] Admin dashboard is available only to administrators
- [ ] User totals, storage totals, model analytics, failures, and health history render
- [ ] User administration can enable and disable a non-current account
- [ ] Orphan cleanup preview is checked before deletion
- [ ] Telemetry retention is configured appropriately
- [ ] Rate-limit values are reviewed for the deployment size
- [ ] Light-theme button labels, source badges, placeholders, and disabled states are readable
- [ ] RAG sources are collapsed by default and keyboard accessible
- [ ] Mobile, tablet, half-screen, desktop, and wide-desktop layouts are checked
- [ ] PostgreSQL backup is created and a restore rehearsal is completed against a separate database
- [ ] Optional browser tests are run with a disposable test account


## Phase 4 - Deployment and portfolio release

- [ ] Commit only the cleaned project, not `.env`, logs, cache folders, or private uploads.
- [ ] Confirm `AI_PROVIDER=openai` on Render and `AI_PROVIDER=ollama` locally.
- [ ] Set `OPENAI_API_KEY` as a Render secret environment variable.
- [ ] Connect Render PostgreSQL and verify migrations run.
- [ ] Confirm `/api/health/live` is healthy.
- [ ] Test login, chat, file upload, RAG, prompt library, admin dashboard, and mobile layout.
- [ ] Add sanitized screenshots to `docs/images/`.
- [ ] Add the live demo link to README after deployment.
- [ ] Create a GitHub release tag, for example `v1.0.0`.
