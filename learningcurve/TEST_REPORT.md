# Validation — 2026-10-24

## Main merged into simulation

Combined resume-upload and dynamic-simulation suite:
`python -m pytest learningcurve/tests -q --tb=short`: **52 passed, 2 failed**.
Both failures are the previously documented illustrative-data assumption and
older Streamlit AppTest stale-widget issue. Resume upload, generated shifts,
customer dialogue, and shift-history tests passed together. Both PDF extraction
and JSON-schema dependencies are retained, along with the Databricks AI launch
configuration. Conflict-marker and whitespace checks passed.

## Databricks deployment preparation

Added repository-root launch and requirements files and configured both deployment
layouts to use the Databricks-assigned port and the `openai_api_key` app Secret
resource. Parsed both manifests as YAML and checked their command targets, secret
bindings, and dependency paths. Both entry points executed successfully through
Streamlit AppTest using Streamlit's bootstrap import setup. The dynamic-simulation
suite passed again: **32 passed**. `git diff --check` passed.

These are local readiness checks, not a live Databricks deployment. Workspace secret
permissions, outbound network access, dependency installation in Databricks, and live
AI requests still require verification in the user's workspace. The root README now
includes the exact deployment and manual test steps.

## Dynamic simulation update

Tested on macOS with Python 3.9.6, Streamlit 1.50.0 and the available local
dependencies. This differs from the project's recommended Python 3.11/3.12 and
pinned production Streamlit version.

`python -m pytest learningcurve/tests -q --tb=short`: **43 passed, 2 failed**.
The 32 new dynamic-simulation tests pass, including the Streamlit generation,
customer dialogue, submission, history and next-shift flow with a mocked AI service.
Other coverage includes rule/reference validation, evidence-before-action credit,
verification invalidation, recovery, scenario-preserving revisions, immutable archived
attempts, multi-shift exports, session isolation, private-profile exclusion, repeat
detection, chat limits, and safe handling of missing credentials, API errors, malformed
responses, refusals, incomplete responses and timeouts.

Both failing existing UI tests were reproduced against the unchanged `HEAD` app:
one assumes illustrative data despite the included real prepared snapshot; the other
hits a stale-widget error in the installed older Streamlit AppTest after navigation.
No live AI request, model-quality evaluation, Databricks deployment, or browser visual
test was performed for this update. AI-service tests use mocks and do not incur charges.

## Original validation record

Environment: Windows, Python 3.12; Streamlit 1.66.1, pandas 2.3.3, Plotly 6.9.0, pytest 9.1.1. These direct dependencies are pinned in the supplied requirement files.

`python -m pytest -q`: **13 passed in 11.20 seconds**.

Validated:

- Blank, unrelated, generic and explicitly negated experience does not fabricate suggestions.
- Suggested evidence spans occur in the original experience text; rejected matches stay rejected across navigation.
- Successful and incorrect simulation branches, supported-action timing, successful verification, recovery, and invalid action rejection.
- Revision retains the original attempt and only one revision is allowed.
- Resource budget and time filters, independent journey state, and simulated work sample labeling.
- Duplicate source keys and missing source columns fail; posting totals remain unchanged; 2026 partial-year labeling remains visible; invalid prepared JSON does not silently fall back.
- Streamlit AppTest walkthrough: landing → demo → confirm evidence → learning path → mission → feedback → revision → resources; also evidence view, blank profile, reset, and second independent session.
- Markdown export contents tested directly. Browser file-download behavior was not exercised.

Python compilation passed for app and logic modules. The source package contains no virtual environment, raw user data, secrets, or caches.

Not verified: actual Lightcast source files, actual Unity Catalog tables, Databricks App deployment, real workspace permissions, browser visual layout, or browser download delivery. A local Streamlit launch was attempted, but the browser could not connect before the preview process was stopped. AppTest successfully executed the interface; it is not a visual browser test.

The Cloudflare resource page and Databricks deployment documentation were opened during implementation. The source files and supplied Excel dictionary were absent; real-data configuration remains explicit and requires their actual column names and units.
