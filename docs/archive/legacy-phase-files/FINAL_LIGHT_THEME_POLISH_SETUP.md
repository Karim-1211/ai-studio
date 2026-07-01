# Final Light Theme Polish

This is a UI-only refinement applied after the combined Admin, Reliability, Accessibility, and Security phase.

## Changes

- Improves sidebar tag contrast in light mode.
- Uses dark readable text on pastel tag backgrounds.
- Softens and modernizes the New Chat gradient.
- Improves active-chat, menu-button, message-card, composer, and attachment contrast.
- Makes PDF and other attachment-type labels clearly visible.
- Keeps dark mode and all application behavior unchanged.

## Installation

Copy the package over the existing project while preserving `.env`, uploads, logs, the virtual environment, and Git data.

No database migration is required. The database remains at revision `20260628_0007`.

After copying, run:

```powershell
python -m compileall -q .
python -m pytest
python app.py
```

Open `http://127.0.0.1:5000` and press `Ctrl + F5`.
