# Authentication and Workspace Validation Report

## Completed checks

- Python compilation passed.
- JavaScript syntax checks passed.
- HTML duplicate-ID validation passed.
- Existing feature regression suite passed.
- Authentication and data-isolation tests passed.
- CSRF form and API-header flow passed.
- Unauthenticated page redirect passed.
- Unauthenticated API rejection passed.
- Chat isolation between two users passed.
- Global-document isolation passed.
- Website membership isolation passed.
- Public-registration disabled behavior passed.
- Knowledge drawer scroll CSS validation passed.
- Fresh SQLite migration from empty database passed.
- Upgrade from revision `20260628_0003` with legacy data passed.
- `bootstrap-owner` legacy-data claim passed.

## Automated test result

```text
51 passed
```

## Migration result

```text
20260628_0004 (head)
```

## Legacy-data simulation

A database was created at revision 0003 with an existing chat, global document, website source, and social source. Migration 0004 was applied, followed by `bootstrap-owner`. The validation confirmed:

- existing chat received the owner user ID
- existing global document received the owner user ID
- existing website source received an owner membership
- existing social source received an owner membership

## Not performed in the artifact environment

- A live migration against the user's PostgreSQL database
- Browser microphone and speech-synthesis testing
- A live Docker image build
- External website and social-platform requests

These are environment-dependent and remain covered by the existing local validation steps.
