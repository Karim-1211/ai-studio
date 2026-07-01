# AI Studio Professional v2.2 — Rollback Guide

If needed, use Git to return to the previous working commit:

```powershell
git log --oneline -5
git revert <v2.2_commit_hash>
git push origin main
```

Then wait for Render to redeploy.
