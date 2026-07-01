# AI Studio Professional Edition v2.0 — Rollback Guide

If the release causes issues, rollback with Git:

```powershell
git log --oneline -5
```

Find the commit before `Release AI Studio Professional Edition v2.0`, then run:

```powershell
git revert HEAD
git push origin main
```

Render will redeploy the previous version automatically.

No database rollback is needed because this release has no migration.
