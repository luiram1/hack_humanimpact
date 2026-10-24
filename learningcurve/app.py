"""LearningCurve — run with streamlit run app.py, or deploy as a Databricks App."""
from hashlib import sha256

import pandas as pd
import plotly.express as px
import streamlit as st
from models import content, initial_journey, begin_revision
from matching import suggest, confirmed, prioritize, MAX_EXPERIENCE_CHARS
from resume import extract_resume
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
    if 'profile_experience' not in st.session_state:
        st.session_state['profile_experience'] = j['experience_draft']
    if st.button('Add resume'):
        j['resume_upload_open'] = True
    if j.get('resume_upload_open'):
        uploaded = st.file_uploader('Upload your resume (PDF)', type=['pdf'], key='resume_upload',
                                    help='Up to 5 MB and 10 pages. Use a PDF with selectable text.')
        st.caption('Resume text fills in your experience below and is used for your skill suggestions and learning path. It stays in this session; the file is not saved to disk.')
        if uploaded is not None:
            resume_data = uploaded.getvalue()
            digest = sha256(resume_data).hexdigest()
            if digest != j.get('resume_digest'):
                try:
                    resume_text = extract_resume(resume_data)
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    j['experience_draft'] = resume_text
                    st.session_state['profile_experience'] = resume_text
                    j['resume_digest'] = digest
                    st.success('Resume added. Review or edit the extracted experience below, then continue.')
    experience = st.text_area('Describe your experience', key='profile_experience',
                              max_chars=MAX_EXPERIENCE_CHARS, height=180)
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
