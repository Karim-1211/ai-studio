# Rollback — Professional v2.0.1

If this release causes a problem, use GitHub/Render rollback:

1. Render → ai-studio → Events
2. Find the previous successful deploy before v2.0.1
3. Click Rollback

Or locally:

```powershell
git log --oneline -5
git revert HEAD
git push origin main
```

