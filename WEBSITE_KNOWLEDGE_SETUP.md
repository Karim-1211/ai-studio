# Website Knowledge Sources

This phase adds indexed public webpages to the Global Library.

## Added

- Add one public `http://` or `https://` page at a time
- Clean HTML and extract readable text
- Generate embeddings and store searchable chunks
- Select or clear individual website sources
- Refresh a page to re-index current content
- Delete an indexed page
- Open website citations from AI responses
- Search chat files, global files, and website pages together
- Block localhost, private, reserved, link-local, multicast, and unspecified addresses
- Limit redirects, request duration, response size, and extracted text
- Respect `robots.txt` by default
- Database migration and automated tests

## Files added

- `routes/website_routes.py`
- `services/website_service.py`
- `migrations/versions/20260628_0002_website_sources.py`
- `tests/test_websites.py`

## Important database step

For your existing AI Studio database, run:

```powershell
python -m flask --app app:create_app db upgrade
```

Expected migration head:

```text
20260628_0002 (head)
```

Do not run `db stamp head` for this phase because your database is already registered at the previous migration.

## Installation

After copying this package into the project:

```powershell
python -m pip install -r requirements-dev.txt
python -m flask --app app:create_app db upgrade
python -m pytest
python app.py
```

Refresh the browser with `Ctrl + F5`.

## Test

1. Open **Knowledge Sources**.
2. Click **Manage**.
3. Open **Global Library**.
4. Enter a public page URL.
5. Click **Add website**.
6. Wait for the source to show **Ready**.
7. Ask a question answered by the page.
8. Open the Web citation.
9. Click Refresh and confirm the indexed date changes.
10. Delete the website source.

## Optional `.env` settings

```env
WEBSITE_CONNECT_TIMEOUT=5
WEBSITE_READ_TIMEOUT=15
WEBSITE_MAX_RESPONSE_BYTES=2000000
WEBSITE_MAX_REDIRECTS=3
WEBSITE_MAX_TEXT_CHARACTERS=500000
WEBSITE_MIN_TEXT_CHARACTERS=120
WEBSITE_RESPECT_ROBOTS=true
WEBSITE_USER_AGENT=AI-Studio-KnowledgeIndexer/1.0
```

The first release indexes static HTML and text pages. JavaScript-only pages may not expose enough readable HTML without browser automation.
