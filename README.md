# hack_humanimpact
hackathon project repo

## Run in Databricks Apps

Use this repository's root folder as the app's **Source code path**, then deploy.
The root `app.yaml` starts `streamlit run learningcurve/app.py`, and the root
`requirements.txt` installs the dependencies from `learningcurve/requirements.txt`.
Keep the entire `learningcurve` folder in the deployed source.

If Databricks reports **No command to run and no Python file found**, check that
the selected source folder contains `app.yaml` and `requirements.txt` directly,
with the `learningcurve` folder beside them. Upload or sync the updated files and
redeploy; restarting an older deployment does not include these changes.

You can also deploy the `learningcurve` folder itself. It has its own `app.yaml`
and `requirements.txt` for that layout. See [the app README](learningcurve/README.md)
for data preparation and local setup.
