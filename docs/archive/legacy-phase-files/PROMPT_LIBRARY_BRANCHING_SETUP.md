# Prompt Library, Conversation Branching, and Layout Polish

This phase adds reusable prompt templates, safe conversation branching, a tighter wide-screen conversation rail, and cleaner sidebar chat actions.

## Included features

### Prompt library

- Save reusable prompts per signed-in user.
- Search prompts and filter by category or favorites.
- Insert a saved prompt at the current composer cursor position.
- Create, edit, favorite, copy, and delete templates.
- Save the current composer text as a new template.
- Prompt usage counts are recorded for personal organization.

Open the library with the prompt-template button beside the attachment and microphone controls.

### Conversation branching

Every user and assistant message now has a **Branch** action. A branch copies the conversation through the selected message into a new chat while leaving the original conversation unchanged.

User messages also have **Edit in branch**. This creates a branch immediately before the selected user message, opens the new chat, and places the original message text in the composer for revision.

Branch chats display a small branch badge in the sidebar. Workspace backups include branch relationships and prompt templates.

### Wide-screen conversation layout

On displays wider than 1180 px, user and assistant messages are brought inward toward a shared reading rail. This reduces the large empty middle gap visible on very wide screens while preserving the existing half-window and mobile layouts.

### Compact sidebar actions

Each chat row now keeps only one visible overflow button. Favorite and pin actions are available inside that menu. Small state badges show whether a chat is favorite, pinned, or branched, giving the title more usable space.

## Installation

1. Stop AI Studio.
2. Copy this package over the project while excluding `.env`, uploads, logs, virtual environments, and Git data.
3. Back up PostgreSQL.
4. Confirm the current migration is `20260628_0005 (head)`.
5. Apply the new migration:

```powershell
python -m flask --app app:create_app db upgrade
```

6. Confirm:

```powershell
python -m flask --app app:create_app db current
```

Expected:

```text
20260628_0006 (head)
```

Do not use `db stamp` for this phase.

## Validation

```powershell
python -m compileall -q .
python -m pytest
Get-ChildItem static\js\*.js | ForEach-Object { node --check $_.FullName }
```

Expected automated result:

```text
64 passed
```

Then start the application and perform a hard refresh:

```powershell
python app.py
```

Open `http://127.0.0.1:5000` and press `Ctrl + F5`.

## Suggested acceptance checks

- Create, edit, favorite, insert, copy, and delete a prompt template.
- Branch from an assistant message and confirm the copied history ends at that message.
- Use **Edit in branch** on a user message and confirm the original chat remains unchanged.
- Open AI Studio at full desktop width and confirm the two message sides are closer together.
- Resize to half-screen width and confirm the prior responsive layout remains comfortable.
- Confirm each sidebar row has one visible menu button and that favorite and pin actions work from its menu.
- Download a workspace backup and verify prompt templates and branch metadata restore into a test account.
