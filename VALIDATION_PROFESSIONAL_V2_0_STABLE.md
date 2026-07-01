# AI Studio Professional Edition v2.0 Stable — Validation

## Expected results

After deployment:

1. Single Answer mode streams text gradually and finishes completely.
2. 3 Options mode produces complete option cards.
3. RAG answers still include knowledge source indicators.
4. Attachments still upload and can be used in chat.
5. Global knowledge, website knowledge, and social knowledge still work.

## Browser validation

Hard refresh after deploy:

```text
Ctrl + Shift + R
```

Test prompt:

```text
Explain DeepTechArt in 5 complete bullet points.
```

Expected: full response, no mid-sentence cutoff.
