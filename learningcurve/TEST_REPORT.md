# Validation — 2026-10-24

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
