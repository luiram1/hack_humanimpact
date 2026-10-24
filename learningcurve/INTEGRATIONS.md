# Deployment and calendar integration

This branch starts from main commit 828ff1a and preserves résumé upload, generated shifts, customer conversations, and shift history. It removes the demo start and app downloads, adds independent Free/Paid filters, AI experience suggestions and explanation feedback, a mission coach, scope timing feedback, and practice scheduling.

## Databricks Unity Gateway

In LearningCurve app resources, save GPT OSS 120B (`system.ai.gpt-oss-120b`) with **Can execute**, resource key **model**. `app.yaml` maps this resource to `DATABRICKS_MODEL`. The app service principal authenticates through the Databricks SDK; no personal API key is needed. This resource must be present before deployment.

Deploy from Git branch `codex/learningcurve-ai-updates`, source code path `learningcurve`. No need to merge into main to test the branch. The former OpenAI secret is no longer required by app.yaml. The legacy OpenAI provider remains available for local compatibility only when DATABRICKS_MODEL is unset and OPENAI_API_KEY is set; there is no silent cross-provider fallback after a failed Databricks request.

Gateway requests use `/ai-gateway/mlflow/v1/chat/completions`. Generated JSON is validated against the existing scenario schema before changing state. The coach receives only the current scenario, recorded observations, and recent coach messages; it does not receive hidden ground truth or résumé text. It cannot award action credit. AI background analysis is a separate explicit user action with disclosure that imported résumé text will be sent. Endpoint logging and retention follow the workspace configuration. Model requests may incur usage charges.

Live model behavior and workspace permissions still need testing after deployment. Local tests mock the model and do not send inference requests.

Reference: https://docs.databricks.com/aws/en/machine-learning/model-serving/query-chat-models

## Google Calendar: available now

Profile → select practice duration → expand **Schedule this practice in Google Calendar** → choose date, time and time zone → **Open in Google Calendar**. Review the event and click Save in Google Calendar.

This is a prefilled calendar draft link, not an authenticated Calendar API connection. No Google Cloud setup is required. It does not read busy times, confirm that an event was saved, synchronize edits, or automatically create events. Event text contains only a generic LearningCurve practice description and duration, never background, résumé or assessment text. Repeated saves can produce duplicate events. The user must return to the app themselves; their current journey is still session-only. DST gaps and ambiguous times are rejected rather than silently scheduled at the wrong instant.

## Google Calendar API: direct creation or availability (future integration)

Google provides the API. To enable a fully connected experience:

1. Create a Google Cloud project and enable **Google Calendar API**.
2. Configure the Google Auth Platform consent screen, audience and test users. Add your app identity and privacy policy as required for publishing.
3. Create an **OAuth client ID → Web application**. Register the exact HTTPS callback URL you implement under your deployed app domain. Do not register an invented callback that has no handler.
4. Add the client ID and client secret through Databricks secret resources. Never commit secrets or request users' Google passwords.
5. Implement an authorization-code flow with CSRF state validation and per-user session binding. Streamlit alone does not provide the callback/session-storage flow used here: add a small authenticated backend or a carefully integrated OAuth component. Preserve journey state across redirects and store refresh tokens encrypted per user in durable storage, not shared JSON or global session variables.
6. Request the narrowest scopes: `https://www.googleapis.com/auth/calendar.events` for event creation, and an appropriate free/busy scope only if you implement availability lookup. Request only the features you actually use. Google verification requirements depend on scopes and audience.
7. Show a proposed event preview, then call `events.insert(calendarId='primary', body=...)` only after the user's Save action. Use a stable unique event ID per booking to avoid duplicates on retries; store the returned event ID/link and support revoked access and retryable errors.
8. For availability, query `freebusy.query` with an explicit time range and time zone. Propose slots of the selected practice duration; do not interpret an empty calendar as authorization to schedule automatically.
9. Test consent denial, revoked tokens, DST changes, multiple users, reconnects and duplicate submission. Provide a disconnect action.

The Calendar API integration is not enabled by an API key alone; each user must authorize access to their calendar. It is deliberately not claimed as implemented in this branch.

Official guides:
- https://developers.google.com/workspace/calendar/api/guides/create-events
- https://developers.google.com/identity/protocols/oauth2/web-server

## Data

Prepared data files from main are preserved. This change does not resolve the earlier uncertainty about GenAI percentage units. Other occupations and additional datasets remain later work. All curated resources are currently free, so selecting Paid only shows an empty state.
