# Career-specific exploration and practice

The profile searches 972 occupation names from the user-supplied Databricks export. 895 occupations have matching Massachusetts skill records for 2025, full year (12 months). Missing rows are labeled as missing records for this filter, not as absence of jobs or skills.

`scripts/import_careers.py career_data.zip` reproduces `data/prepared/careers.json`. It validates unique occupation and skill keys, names, coverage, finite percentages and consistent posting denominators. The snapshot comes from the user's Lightcast export; attribution is Data Source: Lightcast, 2026. No source posting counts are summed across skills.

Non-IT career exploration selects up to six highest-share non-certification skills, deduplicated by source ID. This is a visible product heuristic, not a complete curriculum. Certification rows remain in the evidence view and are never treated as credentials earned through the app. Single-word skill labels do not produce automatic phrase matches; manual evidence and explicitly requested AI review remain available.

## Simulations

The same validated scenario engine now receives the selected occupation code/title, actual skill names/IDs, previous feedback, time and difficulty. The model generates the situation, evidence, choices, resolution and rubric terms for that context. A non-IT occupation never falls back to the built-in DNS ticket. Each career's evidence, attempts, conversations and shift history are stored separately in the current session and restored when switching back.

Careers with no non-certification skill rows cannot generate a career-specific shift. Careers with skill rows need a functioning model resource for generation; IT support additionally retains its built-in offline shift. The model coach remains distinct from the fictional stakeholder conversation and cannot award action credit.

High-stakes careers are instructed to use fictional administrative coordination, planning, communication or document-consistency tasks only. No clinical treatment, legal judgment, investment decisions, weapons, emergency response or hazardous physical procedures are requested. These are prompt constraints, not proof of model compliance. JSON/transition validation checks structure and consistency; it does not certify domain accuracy, career relevance or safety of generated language. Scenarios are visibly labeled AI-generated and not expert-reviewed. Live samples and expert review are still needed before presenting them as professional training.

## Validation and deployment

67 local tests passed, including occupation coverage, isolated/restored career state, occupation-specific generation context, non-IT UI gating and all previous regression tests. Live inference was not performed. No claim is made that all 895 careers have been individually evaluated.

Deploy Git branch `codex/learningcurve-ai-updates` with source path `learningcurve` (or the repository root, which also has launch files). Keep the model resource key `model`. Rebuild/redeploy to include the new career snapshot. The previous GenAI-unit uncertainty applies to the old IT snapshot; the new career export contains skill shares, not occupation-specific GenAI time series.

## Final Next steps section

The final sidebar section combines feedback-based next actions, up to five source-ranked certification candidates, curated IT resources (or an honest unavailable state for other careers), a fictional project prompt, notes, Calendar scheduling and practice navigation. Credential names and posting shares come from the career snapshot. Issuers, eligibility and current costs are not verified: links explicitly open a web search for the issuer, not a purported official course page. Free-only users are warned that credential exams may cost money. No downloads were added.

Validation: 69 tests passed, including career-specific credential selection and rendering the final section without model access. Live external links, model inference and Databricks deployment were not exercised.
