# LearningCurve — complete source files

Use README.md for Databricks setup. Each section below is one complete file.

## .gitignore

````text
__pycache__/
.pytest_cache/
.venv/
.streamlit/secrets.toml
data/raw/

````

## .streamlit/config.toml

````toml
[theme]
primaryColor = "#22766B"
backgroundColor = "#FAFAF7"
secondaryBackgroundColor = "#EAF0EB"
textColor = "#182C29"
font = "sans serif"

[server]
headless = true

````

## app.py

````python
"""LearningCurve — run with streamlit run app.py, or deploy as a Databricks App."""
import pandas as pd
import plotly.express as px
import streamlit as st
from models import content, initial_journey, begin_revision
from matching import suggest, confirmed, prioritize
from assessment import interact, assess, differences, RUBRIC
from recommendations import recommend
from data_access import load_data, skill_shares, LIMITATIONS
from export import work_sample

st.set_page_config(page_title='LearningCurve', page_icon='🌱', layout='wide')
career, mission = content('career'), content('mission')
resources = content('resources')['resources']
if 'journey' not in st.session_state:
    st.session_state.journey = initial_journey()
    st.session_state.page = 'Welcome'
j = st.session_state.journey

def go(page):
    st.session_state.page = page
    st.rerun()

def button(label, page, **kwargs):
    if st.button(label, **kwargs):
        go(page)

def perform(action):
    interact(j['mission'], action, mission)
    st.rerun()

def selected_resources():
    profile = j['profile']
    return recommend(resources, profile.get('minutes', 30), profile.get('free_only', True),
                     [s['id'] for s in career['skills']])

with st.sidebar:
    st.title('LearningCurve')
    st.caption('A next step you can explain.')
    for page in ['Welcome', 'Profile', 'Evidence review', 'Learning path', 'Mission', 'Feedback', 'Resources', 'Why these skills?']:
        disabled = page not in ('Welcome', 'Profile', 'Why these skills?') and not j['profile']
        if page == 'Feedback' and not j['attempts']:
            disabled = True
        button(page, page, key='nav_' + page, disabled=disabled, use_container_width=True)
    st.divider()
    st.caption('Progress lasts for this session only. It does not persist across devices or server restarts. Download your work sample before leaving.')
    with st.expander('Reset progress'):
        clear = st.checkbox('I want to clear this session', key='reset_confirm')
        if st.button('Clear all progress', disabled=not clear):
            st.session_state.clear()
            st.rerun()

try:
    data = load_data()
except (ValueError, OSError) as exc:
    st.error(f'Cannot read prepared data: {exc}. Fix or regenerate data/prepared/evidence.json; invalid data is never replaced silently.')
    st.stop()

page = st.session_state.page
if page == 'Welcome':
    st.caption('LEARNINGCURVE / YOUR FIRST NEXT STEP')
    st.title('Your first opportunity starts with a next step.')
    st.markdown('Recognize the experience you already have. Practice a relevant skill. Build something you can explain.')
    st.info('Guided career practice, not a hiring assessment. Start with IT support; no résumé or personal identifiers needed.')
    a, b = st.columns(2)
    with a:
        button('Build my learning path', 'Profile', type='primary')
    with b:
        if st.button('Try the demo'):
            if j['profile']:
                st.warning('A journey is already active. Continue it or use Reset progress before loading the demo.')
            else:
                demo = content('demo_profile')
                j['profile'] = {k: demo[k] for k in ('experience', 'minutes', 'free_only')}
                j['matches'] = suggest(demo['experience'], career['skills'])
                go('Evidence review')
    st.divider()
    for col, title, text in zip(st.columns(3), ['01 · Recognize', '02 · Practice', '03 · Take a next step'],
                              ['Connect your own experiences to skills.', 'Investigate a fictional support ticket.', 'Download your simulated work sample.']):
        with col:
            st.subheader(title)
            st.write(text)

elif page == 'Profile':
    st.title('Start with what you have done')
    st.selectbox('Target career', [career['title']])
    st.caption('IT support is the supported path. Coursework, work, projects, volunteering and personal responsibilities can all provide relevant examples.')
    profile = j['profile']
    # Persist drafts outside widget state, which Streamlit removes when navigating away.
    if 'experience_draft' not in j:
        j['experience_draft'] = profile.get('experience', '')
    experience = st.text_area('Describe your experience', value=j['experience_draft'], max_chars=3000, height=180)
    j['experience_draft'] = experience
    time_value = j.get('time_draft', profile.get('minutes', 30))
    minutes = st.select_slider('Available practice time (minutes)', [15, 30, 60], value=time_value)
    free_only = st.radio('Budget preference', ['Free resources only', 'Include paid options'],
                         index=0 if j.get('budget_draft', profile.get('free_only', True)) else 1) == 'Free resources only'
    j['time_draft'], j['budget_draft'] = minutes, free_only
    st.caption('The current curated collection is free. Choosing paid options permits them if added later; it does not hide free materials.')
    if st.button('Review skill suggestions', type='primary'):
        if experience != profile.get('experience'):
            j['matches'] = suggest(experience, career['skills'])
            j['decisions'] = {}
        j['profile'] = {'experience': experience, 'minutes': minutes, 'free_only': free_only}
        go('Evidence review')

elif page == 'Evidence review':
    st.title('You decide which connections fit')
    st.caption('These are phrase-based suggestions. Confirmation records a self-reported connection, not verified proficiency.')
    names = {s['id']: s['name'] for s in career['skills']}
    if not j['matches']:
        st.info('Not yet demonstrated: no explicit phrase matches were found. Add evidence below or continue to practice.')
    for match in j['matches']:
        with st.container(border=True):
            st.subheader(names[match['id']])
            st.text(match['sentence'])
            st.write(match['explanation'])
            options = ['Not reviewed', 'Confirm', 'Reject']
            choice = st.radio('Your decision', options,
                              index=options.index(j['decisions'].get(match['id'], 'Not reviewed')),
                              key='decision_' + match['id'], horizontal=True)
            j['decisions'][match['id']] = choice
    with st.expander('Add evidence manually'):
        skill = st.selectbox('Skill', list(names), format_func=lambda x: names[x])
        manual = st.text_area('Describe a specific example', value=j.get('manual_draft', ''), max_chars=1000)
        j['manual_draft'] = manual
        if st.button('Add self-reported evidence'):
            if not manual.strip():
                st.error('Enter a specific example first.')
            elif not any(m['id'] == skill and m['sentence'] == manual.strip() for m in j['manual']):
                j['manual'].append({'id': skill, 'sentence': manual.strip(), 'explanation': 'Manually added, self-reported evidence.'})
                st.rerun()
    for index, item in enumerate(j['manual']):
        st.write(f'{names[item["id"]]} — self-reported')
        st.text(item['sentence'])
        if st.button('Remove this evidence', key=f'remove_{index}'):
            j['manual'].pop(index)
            st.rerun()
    button('See my learning path', 'Learning path', type='primary')

elif page == 'Learning path':
    st.title('Three skills. One support shift.')
    st.caption('Priority heuristic: skills without confirmed experience come first, then posting share where an exact source label is available. This is not a readiness score.')
    evidence = confirmed(j)
    shares = {} if data['illustrative'] else skill_shares(data, career['skills'])
    for s in prioritize(career['skills'], evidence, shares):
        with st.container(border=True):
            st.subheader(s['name'])
            st.write(s['why'])
            own = [e for e in evidence if e['id'] == s['id']]
            st.write('Experience: ' + ('Experience confirmed by user' if own else 'No evidence added — Not yet demonstrated'))
            for e in own:
                st.text(e['sentence'])
            status = 'Practice completed with feedback' if j['attempts'] else ('Practice in progress' if j['mission'].history else 'Not started')
            if j['revision_started'] and len(j['attempts']) == 1:
                status = 'Revision in progress; first attempt retained'
            st.write('Practice: ' + status)
            st.caption('Practice status records participation in the shared mission, not mastery of the skill.')
            if s['id'] in shares and shares[s['id']] > 0:
                st.write(f'Massachusetts {data["skill_year"]}: {shares[s["id"]]:g}% of occupational postings request this exact skill label. {data["source"]}.')
            else:
                st.caption('No measured exact-label demand shown here. See Why these skills? for source coverage.')
            st.write('Practice action: ' + s['activity'])
    button('Open support shift', 'Mission', type='primary')

elif page == 'Mission':
    st.title(mission['title'])
    st.write(mission['scenario'])
    st.caption(mission['provenance'] + ' All actions are simulated; no device settings are changed.')
    locked = len(j['attempts']) == 2 or (len(j['attempts']) == 1 and not j['revision_started'])
    if locked:
        st.info('This attempt has been submitted. View feedback to use the one available revision or download your work sample.')
        button('View feedback', 'Feedback', type='primary')
    else:
        state = j['mission']
        st.subheader('Investigate the ticket')
        left, right = st.columns([1, 1])
        with left:
            for key, entry in mission['evidence'].items():
                if st.button(entry['label'], key=key, disabled=key in state.seen, use_container_width=True):
                    perform(key)
        with right:
            st.info(mission['ai_suggestion'])
            for action, label in [('accept', 'Accept suggestion (simulate)'), ('question', 'Question the suggestion'), ('reject', 'Reject the suggestion')]:
                if st.button(label, disabled=state.ai == action):
                    perform(action)
            if state.ai:
                st.caption('The suggestion lacks evidence of a firewall block. A DNS comparison supports a narrower change; disabling protection is not justified by this ticket.')
        st.subheader('Choose an action')
        for key, label in mission['actions'].items():
            if st.button(label, key='action_' + key):
                perform(key)
        if st.button('Verify portal access', type='primary'):
            perform('verify')
        if state.history:
            st.subheader('Action history')
            for n, entry in enumerate(state.history, 1):
                st.write(f'{n}. {entry["result"]}')
        st.subheader('Explain the outcome to the customer')
        explanation = st.text_area('What did you do, and how did you check the outcome?', value=j['draft'], max_chars=2000, height=130)
        j['draft'] = explanation
        if st.button('Submit for feedback'):
            try:
                attempt = assess(state, explanation)
                j['attempts'].append(attempt)
                go('Feedback')
            except ValueError as exc:
                st.error(str(exc))

elif page == 'Feedback':
    st.title('What your attempt demonstrated')
    attempt = j['attempts'][-1]
    st.caption('Only this exercise is assessed. No hiring or professional-competence score is generated.')
    with st.expander('Visible exercise rubric'):
        for criterion, rule in RUBRIC.items():
            st.write(f'**{criterion}:** {rule}')
    for criterion, passed in attempt['criteria'].items():
        st.write(f'{"✓" if passed else "○"} **{criterion}:** {"Observed" if passed else "Not yet demonstrated"}')
    good = [k for k, passed in attempt['criteria'].items() if passed]
    st.success('What went well: ' + (', '.join(good) if good else 'You recorded an attempt to review. No objective criteria were demonstrated yet.'))
    st.info('One improvement: ' + attempt['improvement'])
    st.write('Next step: ' + attempt['next_step'])
    with st.expander('Evidence from your actions', expanded=True):
        if not attempt['history']:
            st.write('No diagnostic actions were recorded.')
        for entry in attempt['history']:
            st.write(f'**{entry["action"]}:** {entry["result"]}')
    st.subheader('Automated writing content checks')
    st.caption('Limited phrase checks can miss paraphrases or accept inaccurate claims. They do not measure empathy, reasoning, or professional competence; action criteria above are evaluated independently.')
    for criterion, passed in attempt['writing'].items():
        st.write(f'{criterion}: {"Phrase detected" if passed else "Not detected"}')
    st.text(attempt['explanation'])
    if len(j['attempts']) == 1 and not j['revision_started']:
        if st.button('Revise once — replay the shift', type='primary'):
            begin_revision(j)
            go('Mission')
    elif len(j['attempts']) == 1:
        button('Continue revision', 'Mission', type='primary')
    else:
        st.subheader('What changed in your revision')
        for change in differences(*j['attempts']):
            st.write(change)
        with st.expander('Original attempt retained'):
            st.json(j['attempts'][0])
    button('Choose my next activity', 'Resources')
    st.download_button('Download simulated work sample', work_sample(j, career, mission, selected_resources(), data['source']),
                       file_name='learningcurve-work-sample.md', mime='text/markdown')

elif page == 'Resources':
    st.title('Leave with one practical next step')
    st.caption(f'Activities fit within your {j["profile"]["minutes"]}-minute preference. Durations are estimates for the activity, not an entire course. Current resources are all free; no exams or certificates included.')
    for r in selected_resources():
        with st.container(border=True):
            st.subheader(r['title'])
            st.write(f'{r["provider"]} · Estimated {r["minutes"]} minutes · {r["cost"]}')
            st.write(r['why'])
            st.write('Your activity: ' + r['activity'])
            if r['url']:
                st.link_button('Open learning material', r['url'])
                st.caption(f'Public reading checked {r["verified"]}; access conditions can change.')
            else:
                st.caption('Original activity: use the notes below to practice here.')
    notes = st.text_area('Practice notes', value=j['resource_notes'], max_chars=3000)
    j['resource_notes'] = notes
    st.download_button('Download practice notes', notes, file_name='learningcurve-practice-notes.txt')
    if j['attempts']:
        st.download_button('Download simulated work sample', work_sample(j, career, mission, selected_resources(), data['source']),
                           file_name='learningcurve-work-sample.md', mime='text/markdown')
    else:
        button('Complete the support shift for a work sample', 'Mission')

elif page == 'Why these skills?':
    st.title('Why these skills?')
    if data['illustrative']:
        st.warning('ILLUSTRATIVE DATA — invented example values, not measured findings. Prepare the real source data before interpreting these charts.')
    st.write(data['source'])
    st.caption(f'Occupation: {data["occupation"]} · Geography: {data["geography"]} · Dataset version: {data["version"]}')
    profile = pd.DataFrame(data['profile'])
    profile['coverage'] = profile.apply(lambda r: f'{int(r.year)} · {r.period} · {int(r.months_covered)} months' + (' · PARTIAL YEAR' if r.months_covered < 12 else ''), axis=1)
    prefix = 'Illustrative — ' if data['illustrative'] else ''
    st.subheader(prefix + 'GenAI skill demand')
    st.caption('Denominator: Massachusetts postings for this occupation in each covered period. Values are percentages explicitly requesting listed GenAI skills. 2026 is January–September, a partial year.')
    st.plotly_chart(px.line(profile, x='coverage', y='ma_pct_postings_genai_skills', markers=True,
                            labels={'coverage': 'Year and coverage', 'ma_pct_postings_genai_skills': 'Share of postings (%)'}), use_container_width=True)
    st.dataframe(profile[['coverage', 'ma_job_postings', 'ma_pct_postings_genai_skills', 'ma_confidence_flag']], hide_index=True)
    st.subheader(prefix + f'Requested skills · {data["skill_year"]}')
    skills = pd.DataFrame(data['skills'])
    relevant = skills[skills['skill_name'].str.casefold().isin([s['name'].casefold() for s in career['skills']])]
    if relevant.empty:
        st.info('No exact matches for the three milestone labels. Showing the ten highest listed source skills for occupational context, not as validation of this simulation.')
        relevant = skills.nlargest(10, 'pct_postings')
    st.plotly_chart(px.bar(relevant, x='pct_postings', y='skill_name', orientation='h',
                           labels={'pct_postings': 'Share of occupational postings (%)', 'skill_name': 'Source skill'}), use_container_width=True)
    st.caption('Denominator: Massachusetts postings for this occupation in the selected complete year. Skills can overlap; percentages must not be summed. The profile table above supplies posting counts and period coverage.')
    st.dataframe(relevant[['skill_name', 'skill_type', 'pct_postings', 'confidence_flag']], hide_index=True)
    with st.expander('Interpretation and limitations', expanded=True):
        st.write(LIMITATIONS)

````

## app.yaml

````yaml
command: ['streamlit', 'run', 'app.py']

````

## assessment.py

````python
"""Deterministic simulation. No operating-system commands are executed."""
import re
from copy import deepcopy

def interact(state, action, mission):
    if action in mission['evidence']:
        if action in state.seen:
            return
        state.seen.append(action)
        message = mission['evidence'][action]['result']
    elif action in ('accept', 'question', 'reject'):
        state.ai = action
        message = f'AI suggestion: {action}. '
        if action == 'accept':
            message += 'The simulated firewall change does not fix the issue and is rolled back.'
        else:
            message += 'No firewall change made. Compare evidence before selecting a fix.'
    elif action in mission['actions']:
        state.verified = False
        if action == 'refresh':
            state.resolved = True
            state.supported_fix = {'websites', 'others', 'dns'}.issubset(state.seen)
            message = 'Cached DNS refreshed in the simulation. Test portal access to check the result.'
        else:
            message = 'The simulated change does not address the stale cache; it is rolled back. You can gather evidence and try another action.'
    elif action == 'verify':
        state.verified = state.resolved
        message = ('The portal opens on the affected device and the customer confirms access.'
                   if state.resolved else 'The portal still fails to open. Continue investigating.')
    else:
        raise ValueError('Unknown simulation action.')
    state.history.append({'action': action, 'result': message})

RUBRIC = {
    'Scope': 'Ask about other websites AND another device.',
    'Evidence': 'Inspect the browser error AND compare DNS results.',
    'Supported action': 'Gather scope and DNS evidence BEFORE refreshing cached DNS.',
    'AI check': 'Question or reject the unsupported firewall suggestion.',
    'Verification': 'Test portal access successfully after the simulated fix.'
}

def assess(state, explanation):
    if not explanation.strip() or len(explanation) > 2000:
        raise ValueError('Write an explanation between 1 and 2,000 characters.')
    criteria = {
        'Scope': {'websites', 'others'}.issubset(state.seen),
        'Evidence': {'browser', 'dns'}.issubset(state.seen),
        'Supported action': state.resolved and state.supported_fix,
        'AI check': state.ai in ('question', 'reject'),
        'Verification': state.verified
    }
    lower = explanation.lower()
    writing = {
        'Mentions cache action': bool(re.search(r'\b(refresh\w*|clear\w*|flush\w*)\b', lower)) and ('dns' in lower or 'cache' in lower),
        'Mentions verification': bool(re.search(r'\b(test\w*|verif\w*|check\w*|confirm\w*)\b', lower)) and ('portal' in lower or 'access' in lower)
    }
    missing = [RUBRIC[k] for k, passed in criteria.items() if not passed]
    if not all(writing.values()):
        missing.append('Explain the cache action and how you checked portal access.')
    return {'criteria': criteria, 'writing': writing, 'explanation': explanation,
            'history': deepcopy(state.history),
            'improvement': missing[0] if missing else 'Explain why the DNS discrepancy supports the chosen action.',
            'next_step': missing[0] if missing else 'Practice explaining this fix without unexplained acronyms.'}

def differences(first, second):
    changes = [f'{k}: {"observed" if first["criteria"][k] else "not observed"} → {"observed" if v else "not observed"}'
               for k, v in second['criteria'].items() if first['criteria'][k] != v]
    changes += [f'Writing check {k}: {first["writing"][k]} → {v}' for k, v in second['writing'].items() if first['writing'][k] != v]
    if first['explanation'] != second['explanation']:
        changes.append('Customer explanation revised.')
    return changes or ['No criterion or explanation changes.']

````

## content/career.json

````json
{
  "version": "1.0",
  "title": "IT Support / Computer User Support Specialists",
  "onet": "15-1232.00",
  "skills": [
    {"id": "troubleshooting", "name": "Troubleshooting", "why": "Narrow the problem using observations before changing a system.", "aliases": ["troubleshot", "troubleshooting", "diagnosed a", "fixed a laptop", "fixed my laptop"], "activity": "Compare cached DNS with the approved resolver."},
    {"id": "communication", "name": "Communication", "why": "Explain findings and next steps in language the customer can use.", "aliases": ["customer service", "customer-facing", "explained to customers", "answered customer questions", "trained new staff"], "activity": "Write an explanation of the action and verification."},
    {"id": "technical_support", "name": "Technical support", "why": "Help someone recover access while respecting approved procedures.", "aliases": ["laptop troubleshooting", "installed software", "reset passwords", "technical support", "set up a printer"], "activity": "Choose a proportionate fix and verify access."}
  ]
}

````

## content/demo_profile.json

````json
{
  "version": "1.0",
  "experience": "I worked in a customer-facing role and answered customer questions about returns. I also helped my family with laptop troubleshooting when a website would not load.",
  "minutes": 30,
  "free_only": true
}

````

## content/mission.json

````json
{
  "version": "1.0",
  "title": "Your First Support Shift",
  "scenario": "A user can access other websites, but the company's internal support portal will not load.",
  "provenance": "Original fictional scenario designed to practice the selected skills; not an occupational task dataset.",
  "ground_truth": "A stale cached DNS entry on the affected device points to 192.0.2.10. The approved resolver returns 192.0.2.20. Refreshing cached DNS resolves the simulated issue.",
  "evidence": {
    "websites": {"label": "Ask whether other websites work", "result": "The customer can open other websites on this device."},
    "others": {"label": "Ask whether other users are affected", "result": "A colleague can open support.example.com from another device."},
    "browser": {"label": "Inspect the browser error", "result": "support.example.com: connection timed out. This symptom alone does not identify a cause."},
    "dns": {"label": "Compare cached DNS and approved resolver", "result": "Fictional diagnostic log — device cache: support.example.com → 192.0.2.10; approved resolver: support.example.com → 192.0.2.20. The entries disagree."},
    "status": {"label": "Check simulated service status", "result": "The fictional portal service reports healthy. No incident is listed; a status page alone cannot rule out a local issue."},
    "hint": {"label": "Reveal a hint", "result": "Compare the two DNS addresses, check the scope, then choose the smallest supported change."}
  },
  "ai_suggestion": "Simulated AI colleague: Disable the firewall to make the portal load.",
  "actions": {
    "refresh": "Refresh cached DNS using the approved procedure",
    "firewall": "Disable the firewall",
    "password": "Reset the customer's password"
  }
}

````

## content/resources.json

````json
{
  "version": "1.0",
  "resources": [
    {"id": "dns", "title": "What is DNS?", "provider": "Cloudflare Learning Center", "url": "https://www.cloudflare.com/learning/dns/what-is-dns/", "skills": ["troubleshooting", "technical_support"], "paid": false, "cost": "Free public reading; no certificate included.", "minutes": 15, "activity": "Read the DNS caching section and write two sentences explaining why an outdated address could affect one device.", "why": "Builds background for comparing the cache and resolver in this exercise.", "verified": "2026-10-24"},
    {"id": "explanation", "title": "Explain a fix clearly", "provider": "LearningCurve", "url": null, "skills": ["communication"], "paid": false, "cost": "Free original in-app activity.", "minutes": 15, "activity": "Write three sentences: the observed symptom, the action taken, and how you checked the result. Avoid unexplained acronyms.", "why": "Practices a concise handoff without claiming to assess empathy.", "verified": null},
    {"id": "compare", "title": "Build a diagnostic comparison", "provider": "LearningCurve", "url": null, "skills": ["troubleshooting", "technical_support"], "paid": false, "cost": "Free original in-app activity.", "minutes": 30, "activity": "Create a two-column note comparing the affected device with a working device. List what each observation rules out and what it does not.", "why": "Practices making the evidence behind an action explicit.", "verified": null}
  ]
}

````

## data/prepared/illustrative.json

````json
{
  "version": "illustrative-1",
  "illustrative": true,
  "source": "Illustrative LearningCurve data — invented values for demonstrating the interface; not Lightcast findings.",
  "geography": "Massachusetts (illustrative)",
  "occupation": "Computer User Support Specialists",
  "onet": "15-1232.00",
  "skill_year": 2025,
  "profile": [
    {"year": 2024, "period": "January–December", "months_covered": 12, "ma_job_postings": 1000, "ma_pct_postings_genai_skills": 1.0, "ma_confidence_flag": "Illustrative"},
    {"year": 2025, "period": "January–December", "months_covered": 12, "ma_job_postings": 1100, "ma_pct_postings_genai_skills": 1.5, "ma_confidence_flag": "Illustrative"},
    {"year": 2026, "period": "January–September — partial year", "months_covered": 9, "ma_job_postings": 800, "ma_pct_postings_genai_skills": 2.0, "ma_confidence_flag": "Illustrative"}
  ],
  "skills": [
    {"skill_name": "Troubleshooting", "skill_type": "Illustrative", "skill_id": "troubleshooting", "pct_postings": 40, "confidence_flag": "Illustrative"},
    {"skill_name": "Communication", "skill_type": "Illustrative", "skill_id": "communication", "pct_postings": 35, "confidence_flag": "Illustrative"},
    {"skill_name": "Technical Support", "skill_type": "Illustrative", "skill_id": "technical_support", "pct_postings": 30, "confidence_flag": "Illustrative"}
  ]
}

````

## data_access.py

````python
import json
from models import ROOT

LIMITATIONS = '''Postings measure advertised demand, not hires or employment. GenAI demand is the share of postings explicitly requesting listed GenAI skills. AI exposure is not a probability of job loss, and exposure scores are fixed across years in this dataset. Broad AI-skill indicators include Python and are not direct measures of GenAI use. Top-ranked skills are not exhaustive occupational requirements. Posting-volume confidence flags are not statistical confidence intervals. Occupation demand cannot establish individual employability. Massachusetts aggregates do not establish Worcester-specific demand. These data do not establish experience requirements, wages, demographic effects, an apprenticeship shortage, or causal effects of AI. Demand for a skill does not validate this exact simulation.'''

def load_data(directory=None):
    directory = directory or ROOT / 'data' / 'prepared'
    actual = directory / 'evidence.json'
    path = actual if actual.exists() else directory / 'illustrative.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    for key in ('source', 'illustrative', 'profile', 'skills', 'skill_year', 'version'):
        if key not in data:
            raise ValueError(f'{path.name} is missing {key}; rerun data preparation.')
    if not data['profile'] or not data['skills']:
        raise ValueError('Prepared evidence is empty. Rerun data preparation.')
    return data

def skill_shares(data, skills):
    # Only exact labels; do not claim a related source skill is an identical construct.
    return {s['id']: max((float(row['pct_postings']) for row in data['skills']
                         if row['skill_name'].casefold() == s['name'].casefold()), default=0)
            for s in skills}

````

## databricks_prepare.py

````python
# Databricks notebook source
# Import this as a Python notebook, or paste each COMMAND section into a cell.
# This notebook runs on notebook compute; the Streamlit app does not use Spark.
display(spark.sql('SHOW TABLES IN thebuilders_luis.oct26_humanedgestudio'))

# COMMAND ----------
dbutils.widgets.text('app_folder', '', 'Absolute /Workspace/.../learningcurve folder')
dbutils.widgets.text('profile_table', '', 'Actual occupation profile table name')
dbutils.widgets.text('skills_table', '', 'Actual occupation skills table name')
dbutils.widgets.text('skill_id_column', '', 'Actual skill ID column from source')
dbutils.widgets.text('geography', '', 'Exact Massachusetts geography label')
dbutils.widgets.dropdown('percent_scale', 'UNSET', ['UNSET', 'percent', 'fraction'])
dbutils.widgets.text('dataset_version', '2026-10-12', 'Dataset version (verify with source)')

# COMMAND ----------
# Set the widgets before running this cell. Do not guess table or column names.
import re
import sys
from pathlib import Path

folder = Path(dbutils.widgets.get('app_folder'))
if not folder.is_absolute() or not (folder / 'scripts' / 'prepare_data.py').is_file():
    raise ValueError('Set app_folder to the absolute Workspace path containing the supplied app files.')
sys.path.insert(0, str(folder))
from scripts.prepare_data import prepare, write_prepared

def source_table(widget):
    table = dbutils.widgets.get(widget)
    if not re.fullmatch(r'[A-Za-z0-9_]+', table):
        raise ValueError(f'Set {widget} to a table name from the first cell; letters, digits and underscores only.')
    return spark.table(f'thebuilders_luis.oct26_humanedgestudio.{table}')

profile_source = source_table('profile_table')
skill_source = source_table('skills_table')
print('Profile columns:', profile_source.columns)
print('Skill columns:', skill_source.columns)
display(skill_source.select('geography').distinct())

# COMMAND ----------
# Inspect source columns and the supplied data dictionary before setting units.
from pyspark.sql import functions as F
occupation = '15-1232.00'
profile = profile_source.where(F.col('onet') == occupation).toPandas()
skills = skill_source.where((F.col('onet') == occupation) &
                           (F.col('geography') == dbutils.widgets.get('geography'))).toPandas()
result = prepare(profile, skills,
                 skill_id_column=dbutils.widgets.get('skill_id_column'),
                 geography=dbutils.widgets.get('geography'),
                 percent_scale=dbutils.widgets.get('percent_scale'),
                 version=dbutils.widgets.get('dataset_version'))
destination = folder / 'data' / 'prepared' / 'evidence.json'
write_prepared(result, destination)
print(f'Prepared {destination}. Redeploy the app to include this snapshot.')

````

## export.py

````python
from assessment import differences

def work_sample(journey, career, mission, resources, source):
    lines = ['# LearningCurve work sample',
             '**Simulated practice exercise, not employment experience or a professional certification.**',
             f'Target occupation: {career["title"]}', f'Scenario: {mission["title"]}',
             mission['scenario'], mission['provenance'],
             'Skills practiced: ' + ', '.join(s['name'] for s in career['skills'])]
    for i, attempt in enumerate(journey['attempts'], 1):
        lines += [f'\n## Attempt {i}', '\n### Decisions']
        lines += [f'- {h["action"]}: {h["result"]}' for h in attempt['history']]
        lines += ['\n### Customer explanation', attempt['explanation'], '\n### Observed actions']
        lines += [f'- {k}: {"Observed" if v else "Not yet demonstrated"}' for k, v in attempt['criteria'].items()]
        lines += ['\n### Automated writing content checks (not competence ratings)']
        lines += [f'- {k}: {v}' for k, v in attempt['writing'].items()]
        lines += ['Improvement: ' + attempt['improvement'], 'Next step: ' + attempt['next_step']]
    if len(journey['attempts']) == 2:
        lines += ['\n## Revision differences'] + differences(*journey['attempts'])
    lines += ['\n## Recommended next activities']
    for r in resources:
        lines += [f'- {r["title"]}: {r["activity"]} Estimated {r["minutes"]} minutes. {r["cost"]}', r['url'] or 'Original in-app activity.']
    lines += ['\n## Data attribution', source,
              'Occupation-level demand does not establish individual employability. Progress is session-only.']
    return '\n\n'.join(lines)

````

## matching.py

````python
"""Conservative phrase suggestions, never proficiency verification."""
import re

def suggest(text, skills):
    if len(text) > 3000:
        raise ValueError('Experience must be at most 3,000 characters.')
    sentences = [m.group(0).strip() for m in re.finditer(r'[^.!?\n]+(?:[.!?]+|$)', text)]
    result = []
    for skill in skills:
        for sentence in sentences:
            # Skip explicit negative claims rather than suggesting their inverse.
            if re.search(r"\b(no|not|never|haven't|didn't|cannot|can't)\b", sentence, re.I):
                continue
            alias = next((a for a in skill['aliases'] if re.search(
                r'(?<!\w)' + re.escape(a) + r'(?!\w)', sentence, re.I)), None)
            if alias:
                result.append({'id': skill['id'], 'sentence': sentence,
                               'explanation': f'The phrase “{alias}” may connect to {skill["name"].lower()}.'})
                break
    return result

def confirmed(journey):
    return [m for m in journey['matches'] if journey['decisions'].get(m['id']) == 'Confirm'] + journey['manual']

def prioritize(skills, evidence, shares):
    ids = {e['id'] for e in evidence}
    return sorted(skills, key=lambda s: (s['id'] in ids, -shares.get(s['id'], 0)))

````

## models.py

````python
"""Session-local state. No user data is stored in shared files."""
from copy import deepcopy
from dataclasses import dataclass, field
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def content(name):
    return json.loads((ROOT / 'content' / f'{name}.json').read_text(encoding='utf-8'))

@dataclass
class MissionState:
    seen: list = field(default_factory=list)
    history: list = field(default_factory=list)
    ai: str = ''
    resolved: bool = False
    verified: bool = False
    supported_fix: bool = False

def initial_journey():
    return {'profile': {}, 'matches': [], 'decisions': {}, 'manual': [],
            'mission': MissionState(), 'attempts': [], 'revision_started': False,
            'draft': '', 'resource_notes': ''}

def begin_revision(journey):
    if len(journey['attempts']) != 1 or journey['revision_started']:
        raise ValueError('One revision is available after the first attempt.')
    journey['revision_started'] = True
    journey['mission'] = MissionState()

def snapshot(state):
    return deepcopy(state)

````

## README.md

````text
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

## Local run and tests

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

Session state contains experience, confirmation decisions, simulation state, and two immutable submitted attempt snapshots (original plus one revision). No shared file stores user data. Navigating does not restart a simulation. The reset control asks for confirmation. Core logic is independent of Streamlit.

The scenario is original and fictional. Reserved example domains and documentation IP addresses are used. No operating-system commands run. Refreshing the cache changes simulated state; the learner must separately test portal access. A successful action without prior scope and DNS evidence does not earn the supported-action criterion. Incorrect actions can be followed by recovery. The AI colleague is scripted, not an external model.

## Data and resource interpretation

Measured snapshots display **Data Source: Lightcast, 2026**. Illustrative values are never described as Lightcast measurements. The evidence view includes posting counts, flags, coverage, denominators, geography, dataset version, and limitations. Exact skill-label matching is deliberately conservative; when source labels differ, the UI shows source skills for context instead of claiming an equivalence.

Cloudflare's public DNS reading page was checked on 2026-10-24. Its assigned activity is bounded to 15 minutes; this is not a claim about course completion. Other resources are original in-app activities. All current resources are free, so enabling paid options currently returns the same collection. Filtering supports paid entries when verified ones are added. No certification value or free coaching is claimed.

## Known limits

- Progress is session-only and does not persist across devices or server restarts. Download the work sample and optional practice notes before leaving.
- Phrase matching misses paraphrases and cannot verify truth. Evidence confirmation is self-report. Writing feedback checks limited content only and can misread negation or context.
- Only IT support is implemented. No accounts, uploads, job scraping, LLM calls, or hiring-readiness scores.
- Prepared data is a deployment snapshot. The actual shared-table schema and source data have not been tested in your workspace.
- Databricks deployment must be completed in your workspace; these files do not imply a deployment already exists.

See `TEST_REPORT.md` for the validation actually performed in the authoring environment.

````

## recommendations.py

````python
def recommend(resources, minutes, free_only, skill_ids):
    if minutes not in (15, 30, 60):
        raise ValueError('Choose 15, 30, or 60 minutes.')
    return [r for r in resources if r['minutes'] <= minutes
            and (not free_only or not r['paid']) and set(r['skills']).intersection(skill_ids)]

````

## requirements-dev.txt

````text
-r requirements.txt
pytest==9.1.1

````

## requirements.txt

````text
streamlit==1.66.1
pandas==2.3.3
plotly==6.9.0

````

## scripts/package_release.py

````python
"""Create a source-only ZIP and a readable document containing every source file."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'.venv', '__pycache__', '.pytest_cache', '.git'}
files = sorted(p for p in ROOT.rglob('*') if p.is_file()
               and not set(p.relative_to(ROOT).parts).intersection(EXCLUDED)
               and p.name not in {'ALL_CODE.md', 'secrets.toml'}
               and p.suffix in {'.py', '.json', '.md', '.txt', '.toml', '.yaml'}
               or p.is_file() and p.parent == ROOT and p.name == '.gitignore')
sections = ['# LearningCurve — complete source files\n',
            'Use README.md for Databricks setup. Each section below is one complete file.\n']
for path in files:
    language = {'.py': 'python', '.json': 'json', '.yaml': 'yaml', '.toml': 'toml'}.get(path.suffix, 'text')
    sections += [f'## {path.relative_to(ROOT).as_posix()}\n',
                 f'````{language}\n{path.read_text(encoding="utf-8")}\n````\n']
(ROOT / 'ALL_CODE.md').write_text('\n'.join(sections), encoding='utf-8')
output = ROOT.parent / 'LearningCurve-Databricks.zip'
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in files + [ROOT / 'ALL_CODE.md']:
        archive.write(path, 'learningcurve/' + path.relative_to(ROOT).as_posix())
print(f'{output}: {len(files) + 1} files')

````

## scripts/prepare_data.py

````python
"""Reproducible CSV/table preparation with explicit source semantics."""
import argparse
import json
from pathlib import Path
import pandas as pd

OCCUPATION = 'Computer User Support Specialists'
CODE = '15-1232.00'
PROFILE_COLUMNS = ['onet', 'onet_name', 'year', 'period', 'months_covered',
                   'ma_job_postings', 'ma_pct_postings_genai_skills', 'ma_confidence_flag']
SKILL_COLUMNS = ['onet', 'year', 'geography', 'skill_name', 'skill_type',
                 'pct_postings', 'confidence_flag']

def require(frame, columns, label):
    missing = set(columns) - set(frame.columns)
    if missing:
        raise ValueError(f'{label}: missing columns {sorted(missing)}. Available: {list(frame.columns)}')
    if frame[columns].isna().any().any():
        raise ValueError(f'{label}: required columns contain nulls.')

def numeric(frame, columns):
    for column in columns:
        frame[column] = pd.to_numeric(frame[column], errors='raise')
        if not frame[column].map(lambda x: float('-inf') < x < float('inf')).all():
            raise ValueError(f'{column} contains non-finite values.')

def prepare(profile, skills, *, skill_id_column, geography, percent_scale, version):
    profile, skills = profile.copy(), skills.copy()
    require(profile, PROFILE_COLUMNS, 'Occupation profile')
    require(skills, SKILL_COLUMNS + [skill_id_column], 'Skills')
    numeric(profile, ['year', 'months_covered', 'ma_job_postings', 'ma_pct_postings_genai_skills'])
    numeric(skills, ['year', 'pct_postings'])
    if profile.duplicated(['onet', 'year']).any():
        raise ValueError('Profile must have one row per occupation/year. Do not sum duplicate counts.')
    if skills.duplicated(['onet', 'year', 'geography', 'skill_type', skill_id_column]).any():
        raise ValueError('Duplicate occupation/year/geography/skill-type/skill-ID keys.')
    if not profile['months_covered'].between(1, 12).all() or (profile['ma_job_postings'] < 0).any():
        raise ValueError('Invalid month coverage or posting counts.')
    for frame, cols in [(profile, ['year', 'months_covered', 'ma_job_postings']), (skills, ['year'])]:
        if any((frame[c] % 1 != 0).any() for c in cols):
            raise ValueError('Years, month coverage, and posting counts must be integers.')
    selected = profile[profile['onet_name'].str.casefold() == OCCUPATION.casefold()].copy()
    if selected.empty or set(selected['onet'].astype(str)) != {CODE}:
        raise ValueError(f'Expected {OCCUPATION} with source code {CODE}; inspect source mapping.')
    if ((selected['year'] == 2026) & (selected['months_covered'] != 9)).any():
        raise ValueError('Expected January–September coverage (9 months) for 2026; inspect the source version.')
    complete = selected[selected['months_covered'] == 12]
    if complete.empty:
        raise ValueError('No complete year is available for skill selection.')
    year = int(complete['year'].max())
    chosen = skills[(skills['onet'].astype(str) == CODE) & (skills['year'] == year)
                    & (skills['geography'] == geography)].copy()
    if chosen.empty:
        raise ValueError(f'No skill rows for {CODE}, {year}, {geography!r}. Check geography labels.')
    if percent_scale not in ('percent', 'fraction'):
        raise ValueError('Explicitly choose percent or fraction from the data dictionary.')
    for frame, col in [(selected, 'ma_pct_postings_genai_skills'), (chosen, 'pct_postings')]:
        maximum = 1 if percent_scale == 'fraction' else 100
        if not frame[col].between(0, maximum).all():
            raise ValueError(f'{col} is outside the selected {percent_scale} range.')
        if percent_scale == 'fraction':
            frame[col] *= 100
    selected.loc[selected['year'] == 2026, 'period'] = 'January–September — partial year'
    if skill_id_column != 'skill_id':
        chosen = chosen.rename(columns={skill_id_column: 'skill_id'})
    return {'version': version, 'illustrative': False, 'source': 'Data Source: Lightcast, 2026',
            'occupation': OCCUPATION, 'onet': CODE, 'geography': 'Massachusetts',
            'source_geography_label': geography, 'skill_year': year,
            'profile': json.loads(selected.sort_values('year').to_json(orient='records')),
            'skills': json.loads(chosen.sort_values('pct_postings', ascending=False).to_json(orient='records'))}

def write_prepared(data, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(data, indent=2, allow_nan=False), encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'data/prepared/evidence.json')
    parser.add_argument('--skill-id-column', required=True)
    parser.add_argument('--geography', required=True, help='Exact Massachusetts label from source')
    parser.add_argument('--percent-scale', choices=['percent', 'fraction'], required=True)
    parser.add_argument('--version', required=True)
    args = parser.parse_args()
    files = [args.input_dir / name for name in ['lc_occupation_ai_profile.csv', 'lc_occupation_skills.csv']]
    if not all(p.is_file() for p in files):
        parser.error('Both source CSV files are required. App remains runnable with the separately labeled illustrative fixture.')
    profile, skills = [pd.read_csv(p, dtype={'onet': str}) for p in files]
    result = prepare(profile, skills, skill_id_column=args.skill_id_column,
                     geography=args.geography, percent_scale=args.percent_scale, version=args.version)
    write_prepared(result, args.output)
    print(f'Prepared {args.output}. No joins or posting-count aggregation performed.')

if __name__ == '__main__':
    main()

````

## TEST_REPORT.md

````text
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

````

## tests/conftest.py

````python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

````

## tests/test_app.py

````python
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / 'app.py'

def click(app, label):
    matches = [b for b in app.button if b.label == label]
    assert matches, label
    matches[0].click().run()
    assert not app.exception

def test_full_demo_revision_reset_and_second_session():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    click(app, 'Try the demo')
    for radio in app.radio:
        radio.set_value('Confirm')
    app.run()
    click(app, 'See my learning path')
    click(app, 'Open support shift')
    for label in ['Ask whether other websites work', 'Ask whether other users are affected',
                  'Inspect the browser error', 'Compare cached DNS and approved resolver',
                  'Question the suggestion', 'Refresh cached DNS using the approved procedure', 'Verify portal access']:
        click(app, label)
    app.text_area[0].set_value('I refreshed the DNS cache and verified portal access.').run()
    click(app, 'Submit for feedback')
    assert all(app.session_state['journey']['attempts'][0]['criteria'].values())
    click(app, 'Revise once — replay the shift')
    click(app, 'Disable the firewall')
    click(app, 'Verify portal access')
    app.text_area[0].set_value('I checked portal access; it still fails.').run()
    click(app, 'Submit for feedback')
    assert len(app.session_state['journey']['attempts']) == 2
    assert not app.session_state['journey']['attempts'][1]['criteria']['Verification']
    click(app, 'Choose my next activity')
    assert not app.exception
    click(app, 'Why these skills?')
    assert any('ILLUSTRATIVE' in w.value for w in app.warning)
    other = AppTest.from_file(str(APP), default_timeout=30).run()
    assert other.session_state['journey']['attempts'] == []
    app.checkbox[0].check().run()
    click(app, 'Clear all progress')
    assert app.session_state['journey']['attempts'] == []

def test_empty_profile_and_rejected_match_navigation():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    click(app, 'Build my learning path')
    click(app, 'Review skill suggestions')
    assert app.session_state['journey']['matches'] == []
    click(app, 'See my learning path')
    click(app, 'Profile')
    app.text_area[0].set_value('I installed software.').run()
    click(app, 'Review skill suggestions')
    app.radio[0].set_value('Reject').run()
    click(app, 'See my learning path')
    click(app, 'Evidence review')
    assert app.radio[0].value == 'Reject'

````

## tests/test_data_preparation.py

````python
import pandas as pd
import pytest
from models import ROOT
from data_access import load_data
from scripts.prepare_data import prepare

def frames():
    d = load_data()
    p = pd.DataFrame(d['profile']).assign(onet='15-1232.00', onet_name='Computer User Support Specialists')
    s = pd.DataFrame(d['skills']).assign(onet='15-1232.00', year=2025, geography='Massachusetts')
    return p, s

def run(p, s):
    return prepare(p, s, skill_id_column='skill_id', geography='Massachusetts', percent_scale='percent', version='test')

def test_counts_and_partial_year():
    p, s = frames()
    result = run(p, s)
    assert sum(r['ma_job_postings'] for r in result['profile']) == p.ma_job_postings.sum()
    assert result['skill_year'] == 2025
    assert 'partial year' in result['profile'][-1]['period']

def test_duplicate_keys_and_invalid_schema_fail():
    p, s = frames()
    with pytest.raises(ValueError, match='one row'):
        run(pd.concat([p, p.iloc[[0]]]), s)
    with pytest.raises(ValueError, match='Duplicate'):
        run(p, pd.concat([s, s.iloc[[0]]]))
    with pytest.raises(ValueError, match='missing columns'):
        run(p.drop(columns='ma_job_postings'), s)

def test_invalid_prepared_data_never_silently_falls_back(tmp_path):
    (tmp_path / 'evidence.json').write_text('{}')
    with pytest.raises(ValueError):
        load_data(tmp_path)

````

## tests/test_logic.py

````python
import pytest
from models import content, initial_journey, MissionState, begin_revision
from matching import suggest, confirmed
from assessment import interact, assess, differences
from recommendations import recommend
from export import work_sample

SKILLS = content('career')['skills']
MISSION = content('mission')

@pytest.mark.parametrize('text', ['', 'I work and help with a computer.', 'I like gardening.', 'I have never installed software.'])
def test_no_fabricated_matches(text):
    assert suggest(text, SKILLS) == []

def test_spans_and_rejections():
    text = content('demo_profile')['experience']
    j = initial_journey()
    j['matches'] = suggest(text, SKILLS)
    assert j['matches']
    assert all(m['sentence'] in text for m in j['matches'])
    j['decisions'] = {m['id']: 'Reject' for m in j['matches']}
    assert confirmed(j) == []

def test_recovery_and_revision_preserve_original():
    j = initial_journey()
    s = j['mission']
    interact(s, 'firewall', MISSION)
    interact(s, 'verify', MISSION)
    original = assess(s, 'I checked portal access but it still failed.')
    assert not original['criteria']['Verification']
    j['attempts'].append(original)
    begin_revision(j)
    s = j['mission']
    for action in ['websites', 'others', 'browser', 'dns', 'question', 'refresh', 'verify']:
        interact(s, action, MISSION)
    revision = assess(s, 'I refreshed the DNS cache and verified portal access.')
    j['attempts'].append(revision)
    assert all(revision['criteria'].values())
    assert not original['criteria']['Verification']
    assert differences(original, revision)
    with pytest.raises(ValueError):
        begin_revision(j)
    exported = work_sample(j, content('career'), MISSION, [], 'Illustrative')
    assert 'Simulated practice exercise, not employment experience' in exported
    assert 'Attempt 1' in exported and 'Attempt 2' in exported

def test_guess_does_not_receive_supported_action_credit():
    s = MissionState()
    for action in ['refresh', 'websites', 'others', 'dns', 'verify']:
        interact(s, action, MISSION)
    result = assess(s, 'I refreshed the DNS cache and checked portal access.')
    assert result['criteria']['Verification']
    assert not result['criteria']['Supported action']
    with pytest.raises(ValueError):
        interact(s, 'execute shell command', MISSION)

def test_filter_and_isolation():
    resources = content('resources')['resources']
    paid = dict(resources[0], paid=True, id='paid')
    assert all(not r['paid'] and r['minutes'] <= 15 for r in recommend(resources + [paid], 15, True, ['troubleshooting']))
    assert paid in recommend([paid], 30, False, ['troubleshooting'])
    first, second = initial_journey(), initial_journey()
    first['mission'].history.append({'action': 'test'})
    assert second['mission'].history == []

````
