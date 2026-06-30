# Secure Accounts + Scrollable Knowledge Drawer Setup

This release adds local user accounts, per-user workspace isolation, administrator controls, CSRF protection, and a fully scrollable Manage Knowledge drawer.

## Important database behavior

Migration `20260628_0004` creates:

- `users`
- `user_website_sources`
- `user_social_sources`
- `chats.user_id`
- `global_documents.user_id`

Existing chats and global files remain in the database with no owner until `bootstrap-owner` assigns them to the first administrator. Existing website and social sources are linked to that owner by the same command.

Do not run `db stamp` for this release.

## 1. Back up PostgreSQL

Create a normal pgAdmin backup before applying the migration.

## 2. Environment settings

Keep the existing database, Ollama, embedding, OCR, and vision values. Add or confirm:

```env
AUTO_CREATE_DATABASE=false
AUTH_REQUIRED=true
ALLOW_REGISTRATION=false
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_SAMESITE=Lax
REMEMBER_COOKIE_DAYS=30
LOGIN_MAX_ATTEMPTS=5
LOGIN_LOCK_MINUTES=15
PASSWORD_MIN_LENGTH=10
```

Use `SESSION_COOKIE_SECURE=false` only for local `http://127.0.0.1`. Set it to `true` after deploying behind HTTPS.

## 3. Install dependencies

```powershell
python -m pip install -r requirements-dev.txt
```

New dependencies:

- Flask-Login
- Flask-WTF

## 4. Apply migration 0004

Check the current revision:

```powershell
python -m flask --app app:create_app db current
```

Before this update, the expected result is:

```text
20260628_0003 (head)
```

Apply the new migration:

```powershell
python -m flask --app app:create_app db upgrade
```

Verify:

```powershell
python -m flask --app app:create_app db current
```

Expected:

```text
20260628_0004 (head)
```

## 5. Create the owner and claim existing data

Run:

```powershell
python -m flask --app app:create_app bootstrap-owner
```

Enter:

- Owner email
- Display name
- A password containing at least 10 characters
- Password confirmation

The command reports how many existing chats, global documents, website sources, and social sources were assigned.

## 6. Validate

```powershell
python -m compileall -q .
python -m pytest
```

Expected:

```text
51 passed
```

Optional JavaScript checks:

```powershell
Get-ChildItem static\js\*.js |
ForEach-Object {
    node --check $_.FullName
}
```

## 7. Start and sign in

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

Sign in using the owner account created by `bootstrap-owner`.

## Account management

Create additional users from **Sidebar account menu → User administration**, or use:

```powershell
python -m flask --app app:create_app create-user
```

Reset a forgotten password:

```powershell
python -m flask --app app:create_app reset-user-password
```

Users can update their profile, change their password, or delete their workspace from **Account settings**.

## Registration

Public registration is disabled by default. To show the registration page:

```env
ALLOW_REGISTRATION=true
```

For a private local or family installation, administrator-created accounts are safer.

## Knowledge drawer scrolling

The drawer header, switches, and Chat/Global tabs remain visible. The content below them now scrolls independently. This allows access to global files, website groups, crawler controls, and social sources on smaller displays.

Test:

1. Open **Knowledge Sources → Manage**.
2. Select **Global library**.
3. Move the pointer over the drawer.
4. Scroll with the mouse wheel or trackpad.
5. Confirm the underlying chat page remains fixed.

## Docker

After the containers are running and migration 0004 is applied, create the owner inside the application container:

```powershell
docker compose --env-file .env.docker exec app `
  python -m flask --app app:create_app bootstrap-owner
```

For HTTPS deployments set:

```env
SESSION_COOKIE_SECURE=true
ENABLE_HSTS=true
TRUST_PROXY_HEADERS=true
```

Only enable HSTS after HTTPS is working correctly.
