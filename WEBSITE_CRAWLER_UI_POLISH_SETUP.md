# Website Crawler, Sitemap Import, and UI Polish

This release adds selective website crawling on top of the existing website knowledge source tables. It also updates the pinned-chat icon and makes the Advanced settings panel dismiss when clicking outside it or pressing Escape.

## Install

1. Stop Flask with `Ctrl + C`.
2. Copy this package over the existing AI Studio project while excluding `.env`, `.env.docker`, `.venv`, `uploads`, `logs`, `.git`, `.idea`, `__pycache__`, and `.pytest_cache`.
3. Install dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

4. Run validation:

```powershell
python -m compileall -q .
python -m pytest
Get-ChildItem static\js\*.js | ForEach-Object { node --check $_.FullName }
```

5. Start AI Studio:

```powershell
python app.py
```

No new database migration is required. The crawler stores each selected page in the existing `website_sources` and `website_chunks` tables.

## Use the crawler

1. Open **Knowledge Sources → Manage → Global Library**.
2. Enter the homepage or another starting page.
3. Open **Crawl and sitemap options** when different page/depth limits are needed.
4. Click **Discover site**.
5. Review the discovered-page preview.
6. Select or clear pages.
7. Click **Index selected pages**.

Indexed pages are grouped by domain. The group header provides whole-site refresh and delete controls, while each page keeps its own refresh and delete controls.

## Safety behavior

- Only `http://` and `https://` are accepted.
- Localhost, private, reserved, loopback, and link-local addresses are blocked.
- Redirect destinations are validated.
- Crawling stays on the same hostname, allowing only the common `www` variant.
- `robots.txt` is respected.
- `sitemap.xml` and sitemap locations from `robots.txt` are bounded by size and count limits.
- Login, account, checkout, cart, admin, search, feeds, previews, and common downloadable-file URLs are excluded.

## Optional environment settings

```env
WEBSITE_CRAWLER_DEFAULT_MAX_PAGES=25
WEBSITE_CRAWLER_MAX_PAGES=100
WEBSITE_CRAWLER_DEFAULT_DEPTH=2
WEBSITE_CRAWLER_MAX_DEPTH=5
WEBSITE_CRAWLER_DISCOVERY_BYTES=750000
WEBSITE_CRAWLER_SITEMAP_BYTES=1000000
WEBSITE_CRAWLER_MAX_SITEMAPS=8
```

## UI checks

- Pin a chat and confirm the modern pin point tilts down-left.
- Open **Advanced**, click anywhere outside the panel, and confirm it closes.
- Open **Advanced**, press Escape, and confirm it closes.
