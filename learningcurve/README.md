# LearningCurve — Databricks edition

A complete Streamlit career-practice application for IT support. The existing Studybug application in the parent directory is unchanged.

## Start in Databricks

1. Upload this entire `learningcurve` directory into a Databricks Workspace folder or sync it through your Git folder. Keep the directory structure intact. These are Python **files**, not individual notebook cells. Only `databricks_prepare.py` is a notebook source file.
2. Create a Databricks App using the workspace's Apps interface. Choose this `learningcurve` folder as its source, with `app.py`, `requirements.txt`, and `app.yaml` at the source root. Deploy the source. Databricks installs the requirements and runs `streamlit run app.py`.
3. Open the app URL and select **Try the demo**. It runs without table credentials or external AI services. Until you prepare real data, every evidence chart is explicitly illustrative.
4. Keep app access restricted to the intended workspace users. No public deployment has been performed by this project.

Databricks Apps runs a web application, separately from notebook compute. Pasting `app.py` into a notebook does not launch the intended UI. Apps availability depends on workspace features and permissions; if your workspace does not offer Apps, ask the workspace administrator about availability or run locally using the instructions below.

Official deployment reference: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/tutorial-streamlit

## Connect your existing shared data

Your known catalog is `thebuilders_luis`, and schema is `oct26_humanedgestudio`. Actual table names and schemas have not yet been supplied. The preparation notebook discovers table names; it does not guess them.

1. Import `databricks_prepare.py` as a Python notebook (or copy its COMMAND-separated sections into separate cells). Attach serverless notebook compute or another supported compute resource.
2. Run its first cell to list tables in your schema.
3. Run the widget-definition cell. Set `app_folder` to the full absolute Workspace path of this app directory, for example `/Workspace/Users/YOUR_WORKSPACE_USER/learningcurve` (replace with your real path). This directory must contain `scripts/prepare_data.py` and be writable by your notebook identity.
4. Set `profile_table` and `skills_table` to the actual table names corresponding to the occupation AI profile and occupation skills datasets. Enter only the table name, without the catalog/schema prefix.
5. Run the inspection cell to see actual columns and geography values. Inspect your data dictionary. Set `skill_id_column` to the source's actual skill-ID column. Set `geography` to its exact Massachusetts value. Set `percent_scale` to `percent` for values from 0–100 or `fraction` for values from 0–1. Do not infer the unit just because values are small. Verify `dataset_version` against the supplied source.
6. Run the final cell. It reads only the selected occupation and geography, validates the data, and writes `data/prepared/evidence.json` into the app source directory. Redeploy the app to include that file.

Notebook access requires USE CATALOG, USE SCHEMA, and SELECT on the shared tables. The deployed app consumes the included snapshot and does not require direct Unity Catalog or SQL warehouse access. Snapshot updates are deliberate: rerun preparation and redeploy. It is not a live data connection. Respect any provider restrictions on redistributing the prepared snapshot or granting app access.

The notebook verifies occupation code `15-1232.00` against the occupation title in the profile source. If your schema differs, preparation fails with the missing column names; adapt the mapping after inspecting the actual data rather than silently renaming unknown semantics. The percentage-unit option currently applies to both rate columns: if the source dictionary specifies different units, normalize one source column explicitly before preparation.

## CSV preparation alternative

The source CSVs and data dictionary were not present in the supplied repository. With local CSV files, use:

```sh
python scripts/prepare_data.py --input-dir /path/to/source-files --skill-id-column ACTUAL_ID_COLUMN --geography "ACTUAL_MASSACHUSETTS_LABEL" --percent-scale percent --version 2026-10-12
```

Replace the uppercase arguments and verify the version and units. Required files:

- `lc_occupation_ai_profile.csv`
- `lc_occupation_skills.csv`

Inspect `lc_human_edge_data_dictionary_2026_10_12.xlsx` yourself to confirm IDs, units and geography labels. Metadata and specialized LOT tables are not required or joined by this MVP. The preparation preserves available source columns, selects the latest complete profile year for skills, validates source keys, and never aggregates duplicate posting counts. 2026 must have nine months and is labeled January–September, partial year. Missing CSVs fail preparation clearly; the app can still run using the separate illustrative fixture. Invalid prepared JSON stops the app instead of substituting demo values.

## Dynamic practice shifts

The original DNS shift remains available without an AI service. For genuinely generated
situations, configure `OPENAI_API_KEY` in the app server environment and optionally
`OPENAI_MODEL` (default: `gpt-4o-mini`). The model must support the Responses API and
strict structured outputs. Example variable names are in `.env.example`; files named
`.env` are not loaded automatically. Keep real keys out of GitHub.

Locally, set these variables in your shell before launching Streamlit. In Databricks,
bind a secret resource to `OPENAI_API_KEY` in the app environment, then redeploy. An
administrator must allow outbound access to `https://api.openai.com/v1/responses`.

For Databricks, add a **Secret** resource to the app pointing to your stored API key,
give that resource the key `openai_api_key`, then add this optional block below the
existing `command` in the deployed `app.yaml`:

```yaml
env:
  - name: OPENAI_API_KEY
    valueFrom: openai_api_key
  - name: OPENAI_MODEL
    value: gpt-4o-mini
```

Use the same resource key in the app and `valueFrom`. Add the resource before
deploying that configuration; keep the block absent for the built-in-only app.
See [Databricks secret resources](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/secrets).

From **Learning path**, expand **Generate a personalized shift**. Choose a topic and
difficulty, then **Generate a new shift**. The service creates the customer problem,
diagnostic observations, action choices and outcomes, hint, and writing checks; it does
not just select from a fixed scenario library. Automatic difficulty uses confirmed
experience and the most recent feedback. New requests include recent situations to
discourage repetition, and exact repeated causes/facts are rejected. Semantic novelty
is model-dependent, so similar problem types can recur.

Inside a generated shift, ask the customer questions in your own words. The app maps
questions to the scenario's observations or verification step, then generates a reply
using that observation and the current resolution state. The recorded observation is
shown alongside the reply. Diagnostic buttons remain available if chat fails. The
customer does not invent new scoring rules or silently change the underlying cause;
the same generated facts and rules stay in place for a revision.

After submitting feedback, **Try a new shift** generates another situation and archives
the previous attempts. **Shift history** and the work-sample download retain all completed
shifts for this session. Finish an active attempt or revision before replacing it.
Generation failures leave current progress intact; the built-in exercise is explicitly
labeled and is never presented as newly AI-generated.

Only confirmed skill IDs, practice time, selected topic/difficulty, criterion gaps, and
recent fictional situations are sent for generation. The experience description is not
sent. Customer questions and recent conversation are sent when you use customer chat.
Requests use `store: false`; the app keeps no shared user-data files. Each shift allows
up to 40 questions. Generation makes one API request; a question makes two (routing and
reply), with 25-second timeouts per request. API charges and account limits apply.

Generated structures, IDs, prerequisites, and the single resolving action are validated.
Scoring is deterministic: evidence must precede the resolving action, verification must
follow it, and later actions invalidate verification. Structural validation does not
establish that every generated technical claim is correct. Scenarios and customer
dialogue are AI-authored practice content, not expert-reviewed assessments.

API format reference: [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

## Local setup

Use Python 3.11 or 3.12. From this directory:

```sh
python -m venv .venv
# Windows PowerShell:
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m streamlit run app.py
# macOS/Linux: use .venv/bin/python instead.
```

Production dependencies are in `requirements.txt`; pytest is development-only. The app uses supported Streamlit widgets and a native theme rather than internal CSS selectors.

## Files and architecture

| File | Responsibility |
| --- | --- |
| `app.py` | Landing, profile, editable evidence, milestones, mission, feedback, resources, charts and downloads |
| `models.py` | Content loading and per-session journey state |
| `matching.py` | Conservative phrase matches with exact original sentence spans; user confirmations |
| `assessment.py` | Pure simulation transitions, action rubric and revision comparison |
| `simulation.py` | Generated scenario contract, validation, personalization and shift history |
| `ai_simulation.py` | Responses API requests, scenario generation and grounded customer dialogue |
| `recommendations.py` | Budget, duration and skill filtering |
| `export.py` | Markdown work sample without the background description |
| `data_access.py` | Prepared snapshot loading and interpretation rules |
| `content/*.json` | Versioned career, mission, resources and demo profile |
| `data/prepared/illustrative.json` | Explicitly invented example values |
| `scripts/prepare_data.py` | CSV and pandas preparation with validation |
| `databricks_prepare.py` | Notebook adapter for your Unity Catalog tables |
| `tests/` | Logic, data and Streamlit AppTest journey tests |
| `app.yaml` | Databricks launch command |
| `.streamlit/config.toml` | Theme and headless runtime setting |

Session state contains experience, confirmation decisions, the active scenario, completed shifts, and up to two submitted attempt snapshots per shift (original plus one revision). No shared file stores user data. Navigating does not restart a simulation. The reset control asks for confirmation. Core logic is independent of Streamlit.

The built-in scenario is original and fictional. No operating-system commands run. A successful action without prior evidence does not earn the supported-action criterion. Incorrect actions can be followed by recovery. The built-in colleague is scripted; generated shifts use an AI-authored colleague suggestion and live customer dialogue.

## Data and resource interpretation

Measured snapshots display **Data Source: Lightcast, 2026**. Illustrative values are never described as Lightcast measurements. The evidence view includes posting counts, flags, coverage, denominators, geography, dataset version, and limitations. Exact skill-label matching is deliberately conservative; when source labels differ, the UI shows source skills for context instead of claiming an equivalence.

Cloudflare's public DNS reading page was checked on 2026-10-24. Its assigned activity is bounded to 15 minutes; this is not a claim about course completion. Other resources are original in-app activities. All current resources are free, so enabling paid options currently returns the same collection. Filtering supports paid entries when verified ones are added. No certification value or free coaching is claimed.

## Known limits

- Progress is session-only and does not persist across devices or server restarts. Download the work sample and optional practice notes before leaving.
- Phrase matching misses paraphrases and cannot verify truth. Evidence confirmation is self-report. Writing feedback checks limited content only and can misread negation or context.
- Only IT support is implemented. No accounts, uploads, job scraping, or hiring-readiness scores. Optional generated shifts and customer dialogue require an AI API key; customer replies can contain model errors.
- Prepared data is a deployment snapshot. The actual shared-table schema and source data have not been tested in your workspace.
- Databricks deployment must be completed in your workspace; these files do not imply a deployment already exists.

See `TEST_REPORT.md` for the validation actually performed in the authoring environment.
