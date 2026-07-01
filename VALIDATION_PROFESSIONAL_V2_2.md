# AI Studio Professional v2.2 — Validation Guide

After installing and deploying:

1. Hard refresh with Ctrl + Shift + R.
2. Set Response to Single Answer.
3. Turn Use knowledge OFF for a simple chat test.
4. Ask: `Hi, how are you?`
5. Turn Use knowledge ON.
6. Ask: `Describe DeepTechArt in 5 bullet points.`

Expected:

- Complete responses when Gemini quota is available.
- Friendly quota message if Gemini returns 429.
- No raw Google API URL shown in the answer.
- No API key shown in the answer.

If quota is exhausted, wait 5-10 minutes and test again.
