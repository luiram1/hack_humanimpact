# hack_humanimpact
hackathon project repo

The Streamlit app is in [learningcurve](learningcurve/README.md). It supports
optional AI-generated support shifts, customer dialogue, and session-local shift
history. See [setup and configuration](learningcurve/README.md#dynamic-practice-shifts)
to enable generation in Databricks or locally.

## Test on Databricks

1. Store your OpenAI API key in a Databricks secret scope. In your app's
   **App resources**, add a **Secret** pointing to that scope and secret, grant
   **Can read**, and set the resource key to **`openai_api_key`**. The supplied
   `app.yaml` maps this resource to `OPENAI_API_KEY`; no real key goes in GitHub.
2. Commit and push these files to the branch your app deploys. For a Workspace
   Git folder, **Pull** there too. Direct Git deployments read the selected branch
   or commit when you deploy.
3. Deploy using this repository's root as the **Source code path**. It now
   contains `app.yaml` and `requirements.txt`, with `learningcurve/` beside them.
   Deploying just `learningcurve/` also works with its own matching launch file.
4. Open the app, choose **Try the demo**, review the skill suggestions, and
   choose **See my learning path**. Expand **Generate a personalized shift**,
   choose a topic, and press **Generate a new shift**.
5. Ask the customer a question, check the recorded observation, investigate,
   choose an action, verify, and submit for feedback. Generate another shift
   and confirm the previous results appear in **Shift history**.

Both launch files bind Streamlit to the Databricks-assigned port. They expect the
`openai_api_key` resource to exist before deployment. To deploy the built-in shift
without AI, remove the `OPENAI_API_KEY` entry from the selected `app.yaml`; local
Streamlit runs still work without a key. `.env` files are not loaded automatically.

The app server needs outbound HTTPS access to `api.openai.com`, and the API key
needs access to `gpt-4o-mini` (or change `OPENAI_MODEL` in the selected launch file).
An authorization error indicates key/model access; a usage-limit error indicates
quota or billing; an unreachable-service error indicates outbound connectivity
or a timeout. Live generation uses your API account.

Local regression test (does not contact the AI service):

```sh
.venv/bin/python -m pytest learningcurve/tests/test_simulation.py -q
```

References: [Databricks secret resources](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/secrets),
[Git deployments](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy).
