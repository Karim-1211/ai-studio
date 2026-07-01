# Pre-Phase 4 Social, Google Business Profile, and UI Fix

This package is a focused correction before Phase 4. It does not start deployment or portfolio-release work.

## What changed

- Social import now explains that HTTP `202` means manual content is required, not that the database or Flask route failed.
- Added **Open source** and **Paste from clipboard** controls.
- Added clearer guidance for LinkedIn, Facebook, and Instagram restrictions.
- Facebook `/share/...` links receive a direct explanation because they are redirect-style share links rather than stable page URLs.
- Added Google Maps and Google Business Profile links as supported knowledge sources.
- Optional automatic Google Business Profile import through the official Places API.
- Stronger dark-mode text and control contrast throughout Manage Knowledge.
- Organizer view buttons now use a balanced two-by-two grid at sidebar width.

## Install

Copy the package over the existing project while excluding `.env`, uploads, logs, virtual environments, and Git data.

No database migration is required. The existing `social_sources` and `social_chunks` tables store both social and Google Business Profile knowledge.

Expected migration revision:

```text
20260628_0007 (head)
```

## Social source workflow

1. Paste a direct public profile, page, or post URL.
2. Click **Import public**.
3. When public HTML is available, AI Studio indexes it.
4. When the platform returns no readable public HTML, AI Studio opens the manual panel.
5. Click **Open source**.
6. Copy the visible About text, caption, description, post text, services, contact details, or other useful public content.
7. Return to AI Studio and click **Paste from clipboard**.
8. Review the text and click **Index pasted content**.

Use direct Page/Profile/Post URLs when possible. Facebook `/share/...` links may redirect or expire and are less reliable as permanent knowledge-source URLs.

## Google Business Profile automatic import

Automatic Google Business Profile import requires Google Maps Platform Places API.

Add to `.env`:

```env
GOOGLE_MAPS_API_KEY=YOUR_RESTRICTED_KEY
GOOGLE_PLACES_LANGUAGE_CODE=en
GOOGLE_PLACES_MAX_REVIEWS=5
```

The key should be restricted to the Places API and to the deployment environment where possible. Do not commit the real key to Git.

Then restart AI Studio and add a link such as:

```text
https://www.google.com/maps/place/Business+Name/
```

Short `maps.app.goo.gl` and `g.page` links are resolved before the Places search. When a short link does not expose the business name, enter the business name in **Source title** and retry.

Without a Google Maps API key, open the profile, copy the visible business name, description, address, phone, hours, services, and other useful details, then index them through the manual workflow.

## Verification

```powershell
python -m compileall -q .
python -m pytest
```

Expected result for this package:

```text
84 passed, 1 skipped
```

The skipped module is the optional live Playwright browser suite.
