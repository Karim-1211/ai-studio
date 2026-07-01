# AI Studio Professional v2.0.2 Validation

Expected behavior:

- Single Answer still works.
- If Gemini returns 429, the user sees a friendly quota message.
- Gemini API URLs and API keys are not shown in the UI.
- 3 Options uses one backend request and enters cooldown after quota errors.
- RAG continues to work.
