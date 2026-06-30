# Testing, accessibility, and reliability

## Automated test layers

The standard suite covers authentication, chats, uploads, OCR/RAG flows, websites, crawler behavior, social sources, voice controls, backups, prompt branching, admin analytics, cleanup, telemetry, rate limiting, accessibility markup, and responsive UI contracts.

```powershell
python -m pytest
```

## Browser tests

Browser tests are opt-in because they require a running AI Studio instance and a dedicated test account.

```powershell
$env:E2E_BASE_URL = "http://127.0.0.1:5000"
$env:E2E_EMAIL = "test-admin@example.com"
$env:E2E_PASSWORD = "YOUR_TEST_PASSWORD"
.\scripts\run-e2e.ps1
```

Use a disposable account and non-sensitive test documents.

## Manual viewport matrix

Check these viewport widths after UI changes:

- 390 px mobile
- 768 px tablet
- 1024 px half-screen desktop
- 1440 px desktop
- 1920 px wide desktop

Verify that drawers scroll, buttons remain reachable, the prompt composer stays visible, and no text overlaps.

## Keyboard checks

- `Tab` reaches all interactive controls in a logical order.
- `Enter` and `Space` activate buttons and summaries.
- `Escape` closes drawers and floating panels where supported.
- The skip link moves focus to the main chat area.
- Visible focus indicators remain present in both themes.

## Screen-reader checks

- Buttons have accessible names.
- Status areas use `aria-live` where updates matter.
- Source citations use native `details` and `summary` controls.
- Decorative icons are hidden from assistive technology.

## Colour contrast

The light-theme overrides use darker text, stronger borders, and explicit disabled-state colours. Recheck contrast after changing brand colours or opacity values.

## Rate limiting

The built-in limiter is process-local and appropriate for the default single-process Waitress deployment. A future multi-instance deployment should use a shared limiter backed by Redis or an API gateway.
