# Validation — Professional v2.0.1

After deployment, test these in order:

1. Single Answer + Use Knowledge ON
   - Prompt: `Explain DeepTechArt in 5 complete bullet points.`
   - Expected: all 5 bullets complete.

2. Detailed mode
   - Prompt: `Explain DeepTechArt's services in detail.`
   - Expected: complete multi-paragraph answer.

3. 3 Options mode
   - Prompt: `Explain DeepTechArt in 5 bullet points.`
   - Expected: 3 cards generated from one backend request; no immediate Gemini 429.

4. Knowledge source check
   - Expected: source badges remain visible under the answer.

5. Security check
   - Expected: any provider error must not expose a full URL containing `key=`.

