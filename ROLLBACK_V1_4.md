# Rollback Guide — AI Studio Portfolio v1.4

This release only updates documentation and portfolio files.

## Rollback with Git revert

```powershell
git log --oneline -5
git revert <v1.4-commit-id>
git push origin main
```

## When to rollback

Rollback only if:

- README formatting is broken.
- Wrong public information was committed.
- You want to restore the previous repository presentation.

No database rollback is required.
