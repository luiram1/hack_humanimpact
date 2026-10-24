# LearningCurve

IT support practice with experience review, optional PDF résumé input, generated simulations, customer dialogue, an AI practice assistant, criterion-level feedback, revisions, and session-local shift history.

## Deploy this branch

1. In Databricks App resources add GPT OSS 120B (`system.ai.gpt-oss-120b`), permission **Can execute**, resource key **model**.
2. Deploy From Git, branch **codex/learningcurve-ai-updates**. Source code path can be **learningcurve** or the repository root: both have matching launch/dependency files.
3. The app uses the app service principal and `DATABRICKS_MODEL`; no OpenAI API-key secret is required by either launch file.
4. Start with **Build my learning path**. Try profile suggestions, the built-in shift, the assistant, then a generated shift and its customer dialogue. Model responses are validated but may still be mistaken.
5. Profile also has **Schedule this practice in Google Calendar**. This opens a draft the user saves in Google Calendar; it does not automatically write events or read availability.

See [integration and Calendar API guidance](learningcurve/INTEGRATIONS.md) for complete setup, data boundaries, and the OAuth steps needed for direct Calendar API access.

Progress is session-only. There is no demo start or app download feature. Existing résumé upload and simulation features from main are preserved. Do not merge into main until you have tested this branch in your workspace.

## Local development

Use Python 3.11 or 3.12. Install requirements.txt and pytest, then run:

```sh
python -m pytest learningcurve/tests -q
python -m streamlit run learningcurve/app.py
```

For local built-in practice no model credentials are needed. For Databricks AI, use supported SDK authentication and set DATABRICKS_MODEL to your model service name. Do not put tokens or secrets in Git.

## Verification

64 tests passed locally: résumé handling, generated simulations and revision/history, full Streamlit journey, budget selection, calendar UTC conversion and DST rejection, coach state isolation, and mocked Unity Gateway authentication/schema validation. No live model calls or Google Calendar saves were performed. The app has not been redeployed by this change.
