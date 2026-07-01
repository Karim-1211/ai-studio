# Rollback — AI Studio Professional Edition v2.0 Stable

If anything goes wrong, use Git to return to the previous commit:

```powershell
git log --oneline -5
git revert HEAD
git push origin main
```

Render will redeploy the previous version automatically.
