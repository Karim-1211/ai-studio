# Validation report

Validated in the artifact environment:

- Python compilation: passed
- JavaScript syntax checks: passed
- Existing and new pytest suite: 78 passed, 1 optional browser module skipped
- Fresh Alembic migration chain: passed
- Migration head: `20260628_0007`
- Admin dashboard route and API tests: passed
- Per-user analytics tests: passed
- Orphan cleanup confirmation tests: passed
- Request and model telemetry tests: passed
- Health-history sampling test: passed
- Rate-limiter unit and integration tests: passed
- Accessibility and collapsible-source contract tests: passed

The graphical browser suite is included but was not run in the artifact environment because it requires a live AI Studio server, browser binaries, and a disposable login account.
