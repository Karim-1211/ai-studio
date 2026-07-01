# Contributing

Thank you for your interest in AI Studio.

## Development Guidelines

- Create a feature branch.
- Keep cloud and local mode separated.
- Do not commit secrets.
- Validate before pushing.

## Validation

```powershell
python -m compileall -q .
```

## Pull Request Checklist

- Code compiles.
- Documentation updated.
- No `.env` files committed.
- Cloud mode still works.
- Local mode still works.
