# Rollback Guide - AI Studio Dual Mode v1.3

If the live app has any problem after deploying v1.3, use GitHub/Render rollback.

## Option 1 - Render rollback

1. Open Render > ai-studio > Deploys.
2. Select the previous successful deploy.
3. Click rollback/redeploy previous deploy if available.

## Option 2 - Git rollback

In VS Code terminal:

```powershell
git log --oneline -5
```

Find the commit before `Release AI Studio Dual Mode v1.3`, then run:

```powershell
git revert <v1.3_commit_hash>
git push origin main
```

Render will redeploy the reverted version.

## Important

No database migration is included in v1.3, so rollback does not require database changes.
