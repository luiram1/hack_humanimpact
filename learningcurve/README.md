# LearningCurve app

See the [repository README](../README.md) for current deployment and [INTEGRATIONS.md](INTEGRATIONS.md) for Unity Gateway and Google Calendar setup. These describe the updated journey: no demo entry point, no downloads, independent budgets, optional AI background review and feedback, and a free-text mission assistant.

## Run

From this directory, install requirements.txt and pytest, then run `python -m streamlit run app.py`. Run tests using `python -m pytest tests -q`. Python 3.11 or 3.12 is supported.

## Data preparation

The app reads data/prepared/evidence.json if present; otherwise it uses the explicitly illustrative fixture. Invalid data never silently falls back. Actual Lightcast source files and their interpretation are separate from model-generated practice.

Use databricks_prepare.py in notebook compute to prepare a snapshot from Unity Catalog. Set app_folder to the full Workspace directory containing scripts/prepare_data.py. Known catalog/schema: thebuilders_luis.oct26_humanedgestudio. Tables: lc_occupation_ai_profile and lc_occupation_skills; skill ID: skill_id; Massachusetts geography: MA. Confirm units and dataset version. Skills percentages were checked against counts; GenAI profile units remain unverified in the previously prepared snapshot. This branch preserves that snapshot unchanged.

For source CSVs, use scripts/prepare_data.py with --input-dir, --skill-id-column, --geography, --percent-scale and --version. Required CSVs are lc_occupation_ai_profile.csv and lc_occupation_skills.csv. Do not infer units solely from small values. Only commit prepared data if the source sharing terms permit it.

## Architecture

app.py provides the session-local interface. models.py stores journey state. matching.py suggests phrase connections; AI suggestions additionally validate exact text spans. simulation.py validates generated scenarios; assessment.py calculates action criteria independently of models. ai_simulation.py provides generation, customer dialogue, coach and explanation review. gateway.py authenticates to Unity Gateway using the app service principal. calendar_tools.py prepares user-reviewed Google Calendar links with explicit time zones. recommendations.py filters resources by time, skills and independent Free/Paid selection.

Versioned content lives in content/. The legacy demo fixture and export utility remain for compatibility tests, but are not exposed through the UI. No raw résumé or user progress is written to shared files. Background text is sent to the model only when the user explicitly requests AI background analysis. Coach requests do not include background text or hidden scenario answers. Model logging/retention is controlled by workspace configuration.

## Limits

Only IT support is implemented. Current curated resources are free; paid-only selection can return no results. Progress is session-only. Keyword checks and AI feedback are not professional certification or hiring assessments. Practice is simulated; no operating-system commands run. Calendar drafts require the user to click Save in Google Calendar and do not survive as app-linked bookings. Model inference may incur usage charges.

The evidence view includes posting counts, coverage, confidence flags and interpretation limits. Postings measure advertised demand, not hires. Additional occupations and datasets remain future work.
