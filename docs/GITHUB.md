# GitHub Portfolio Guide

## Before the first push

Confirm that these files are not committed:

- `.env`
- `.env.docker`
- `uploads/` contents
- `logs/`
- `.venv/`
- database passwords or API secrets

Run:

```powershell
git status
```

## Initialize the repository

```powershell
git init
git add .
git commit -m "Build AI Studio local RAG workspace"
git branch -M main
```

Create an empty GitHub repository, then connect it:

```powershell
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

## Continuous integration

`.github/workflows/ci.yml` runs on pushes and pull requests. It:

- tests Python 3.12 and 3.13
- validates Python syntax
- validates browser JavaScript syntax
- runs pytest with coverage output
- builds the Docker image

## Recommended screenshots

Use sanitized screenshots that do not show:

- private CV details
- database passwords
- local usernames or paths
- private customer documents

Suggested images:

1. Compact chat workspace
2. Knowledge drawer with sample documents
3. RAG answer with source citations
4. Light theme
5. System health popover

Store images under `docs/images/` and reference them from `README.md`.

## Release checklist

Use `RELEASE_CHECKLIST.md` before publishing a tagged release.
