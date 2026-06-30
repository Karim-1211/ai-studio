# Chat Organization, Workspace Backup, and Social Import Repair

This phase adds chat folders, tags, favorites, archive views, multi-select actions, drag-to-folder organization, and per-user workspace backup and restore. It also repairs blocked social-media imports so platform restrictions open a reliable pasted-content workflow instead of ending as a hard failure.

## Database migration

Back up PostgreSQL first. Existing installations should currently be at:

```text
20260628_0004 (head)
```

Apply the new migration:

```powershell
python -m flask --app app:create_app db upgrade
python -m flask --app app:create_app db current
```

Expected result:

```text
20260628_0005 (head)
```

Do not run `db stamp`. Migration `20260628_0005` creates `chat_folders`, `chat_tags`, and `chat_tag_links`, and adds folder, favorite, and archive fields to `chats`.

## Chat organization

Open **Organize** under the chat search box.

- Use Active, Favorites, Archived, and All views.
- Filter by folder or tag.
- Create folders and tags.
- Drag a chat onto a folder.
- Use the chat menu to favorite, archive, move, or assign tags.
- Enable multi-select to archive, restore, favorite, move, tag, or delete several chats.

Deleting a folder does not delete its chats. Deleting a tag only removes that label from chats.

## Workspace backup

Open the sidebar account menu and choose **Download workspace backup**.

The ZIP contains:

- folders and tags
- chats and messages
- chat documents and message attachments
- global documents
- indexed website and social-source metadata and chunks
- the current user's associated upload files

Passwords, session cookies, `.env`, logs, and database credentials are never included.

Choose **Restore workspace backup** to add the backed-up items to the signed-in workspace. Existing data remains in place. Restoring the same backup twice creates another copy of its chats and uploaded documents.

Large backups must fit within Flask's `MAX_CONTENT_LENGTH`. Increase that setting before restore when the ZIP is larger than the configured request limit.

## Social source repair

For publicly readable pages, **Import public** indexes the page normally. When Facebook, LinkedIn, Instagram, or another platform blocks automated reading, AI Studio now returns a normal manual-required state and opens the pasted-content section.

1. Keep the original social URL.
2. Copy the visible About text, description, caption, or post content.
3. Paste at least 40 readable characters.
4. Click **Index pasted content**.

The title is optional. A title is generated from the platform and URL when left blank. Re-indexing an existing URL updates the source instead of returning a duplicate error.

## Validation

```powershell
python -m compileall -q .
python -m pytest
Get-ChildItem static\js\*.js | ForEach-Object { node --check $_.FullName }
```

Expected automated test result:

```text
59 passed
```
