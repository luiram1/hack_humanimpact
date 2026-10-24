"""LearningCurve — run with streamlit run app.py, or deploy as a Databricks App."""
from hashlib import sha256
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from models import content, initial_journey, begin_revision
from matching import suggest, confirmed, prioritize, MAX_EXPERIENCE_CHARS
from resume import extract_resume
from assessment import interact, assess, differences, rubric_for
from ai_simulation import ai_available, generate_shift, ask_customer
from simulation import practice_context, start_shift, shift_records, SimulationError
from recommendations import recommend
from data_access import load_data, skill_shares, LIMITATIONS
from calendar_tools import calendar_link
from datetime import datetime, time
from zoneinfo import ZoneInfo
from ai_simulation import ask_coach, review_explanation, suggest_experience
from careers import catalog, career_for, switch_career, IT
from next_steps import render as render_next_steps

st.set_page_config(page_title='LearningCurve', page_icon='🌱', layout='wide')
career = content('career')
resources = content('resources')['resources']
if 'journey' not in st.session_state:
    st.session_state.journey = initial_journey()
    st.session_state.page = 'Welcome'
j = st.session_state.journey
career = career_for(j.get('profile', {}).get('onet', IT))
is_it = career['onet'] == IT
supports_simulation = bool(career['skills'])
mission = j.get('active_scenario') or content('mission')

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
                     [s['id'] for s in career['skills']], budgets=profile.get('budgets'))


def new_shift_controls():
    st.subheader('Try a new shift')
    st.write('Generate a fictional workplace problem for ' + career['title'] + ', with evidence and actions tailored to your practice needs.')
    available = ai_available()
    if not available:
        st.info('Connect the model resource to generate a shift.' + (' The built-in IT shift is available.' if is_it else ' Career skill exploration remains available.'))
    topics = ['Surprise me', 'Network access', 'Printer support', 'Account access', 'Suspicious email'] if is_it else ['Surprise me', 'Document consistency', 'Planning and prioritization', 'Stakeholder communication']
    topic = st.selectbox('Practice topic', topics, key='shift_topic_' + career['onet'])
    if not is_it:
        st.caption('AI-generated practice, not expert-reviewed training. High-stakes careers use administrative and communication tasks only.')
    difficulty = st.selectbox('Shift difficulty', ['Automatic', 'Guided', 'Standard', 'Challenge'], key='shift_difficulty')
    st.caption('Generation uses your confirmed skills, practice time, and previous feedback. Your experience description is not sent. Customer questions are sent to the AI service when you ask them; keep personal details out of the conversation.')
    unfinished = bool((j['mission'].history or j['mission'].dialogue or j['draft'].strip()) and not j['attempts']) or (j['revision_started'] and len(j['attempts']) == 1)
    if unfinished:
        st.caption('Submit your current attempt or revision before starting another shift.')
    if st.button('Generate a new shift', disabled=not available or unfinished, type='primary'):
        try:
            preferences = practice_context(j, topic, difficulty)
            previous = [r['scenario'] for r in j.get('completed_shifts', [])] + [mission]
            with st.spinner('Creating your next shift…'):
                generated = generate_shift(preferences, previous)
            start_shift(j, generated)
        except SimulationError as exc:
            st.error(str(exc))
        else:
            go('Mission')


def customer_conversation():
    state = j['mission']
    st.subheader('Talk with the customer')
    st.caption('Ask diagnostic questions in your own words. Replies adapt to your questions and progress. Only recorded observations and simulated actions determine feedback.')
    with st.chat_message('assistant'):
        st.write(f'{mission["customer_name"]}: {mission["customer_opening"]}')
    for turn in state.dialogue:
        with st.chat_message('user'):
            st.write(turn['question'])
        with st.chat_message('assistant'):
            st.write(turn['reply'])
            st.caption('Recorded observation: ' + turn['observation'])
    with st.form('customer_question_' + mission['id'], clear_on_submit=True):
        question = st.text_input('Ask the customer a question', max_chars=1000)
        sent = st.form_submit_button('Ask customer', disabled=not ai_available() or len(state.dialogue) >= 40)
    if sent:
        try:
            with st.spinner('The customer is responding…'):
                ask_customer(state, mission, question)
        except SimulationError as exc:
            st.error(str(exc))
        else:
            st.rerun()
    if not ai_available():
        st.info('Customer chat is unavailable while the AI service is unconfigured. You can still finish using the diagnostic buttons.')

with st.sidebar:
    st.image(str(Path(__file__).parent / 'content' / 'learningcurve_logo.svg'), width=180)
    st.caption('A next step you can explain.')
    navigation = {
        'GET STARTED': ['Welcome', 'Profile'],
        'BUILD YOUR PATH': ['Evidence review', 'Learning path'],
        'PRACTICE': ['Mission', 'Feedback', 'Shift history'],
        'NEXT STEPS': ['Next steps', 'Why these skills?'],
    }
    for section, pages in navigation.items():
        st.caption(section)
        for destination in pages:
            disabled = destination not in ('Welcome', 'Profile', 'Why these skills?') and not j['profile']
            if destination == 'Feedback' and not j['attempts']:
                disabled = True
            if destination in ('Mission', 'Feedback', 'Shift history') and not supports_simulation:
                disabled = True
            button(destination, destination, key='nav_' + destination, disabled=disabled,
                   use_container_width=True, type='primary' if destination == st.session_state.page else 'secondary')
    st.divider()
    st.caption('Progress lasts for this session only. It does not persist across devices or server restarts.')
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
journey_steps = ['Profile', 'Evidence review', 'Learning path', 'Mission', 'Feedback', 'Next steps']
progress_page = 'Next steps' if page == 'Resources' else page
if progress_page in journey_steps:
    step = journey_steps.index(progress_page) + 1
    st.progress(step / len(journey_steps), text=f'Step {step} of {len(journey_steps)} · {progress_page}')
if page in ('Resources', 'Next steps'):
    if not j['profile']:
        go('Profile')
    render_next_steps(j, career, selected_resources() if is_it else [])
    st.stop()
if not supports_simulation and page in ('Mission', 'Feedback', 'Shift history'):
    st.info('Career-specific simulations are not available for this occupation yet. Explore its skills and add your own evidence.')
    button('Explore my learning path', 'Learning path')
    st.stop()

if not is_it and page == 'Mission' and not j.get('active_scenario'):
    st.title('Your first ' + career['title'] + ' practice shift')
    new_shift_controls()
    st.stop()

if not is_it and page in ('Learning path', 'Why these skills?'):
    entry = catalog()['occupations'][career['onet']]
    st.title(career['title'])
    st.caption('Source-based skill exploration · AI-generated workplace practice · No expert-reviewed career curriculum')
    st.write('Data Source: Lightcast, 2026 · Massachusetts · 2025 full year (12 months)')
    if not entry['skills']:
        st.info('No matching Massachusetts skill records in the selected 2025 full-year dataset. This does not mean there are no jobs or skill requirements for this occupation.')
        button('Choose another career', 'Profile')
        st.stop()
    if page == 'Why these skills?':
        source = pd.DataFrame(entry['skills'])
        st.caption(f"Denominator: {source.iloc[0]['job_postings']:,.0f} occupational postings. Skills overlap; percentages must not be summed. Source version: {catalog()['version']}.")
        st.plotly_chart(px.bar(source.nlargest(15, 'pct_postings'), x='pct_postings', y='skill_name', orientation='h',
                              labels={'pct_postings': 'Share of occupational postings (%)', 'skill_name': 'Source skill'}),
                        use_container_width=True, config={'displayModeBar': False})
        st.table(source[['skill_name', 'skill_type', 'pct_postings', 'job_postings', 'confidence_flag']])
        st.caption('Certification rows describe advertised demand. They are not credentials earned by using this app. No GenAI trend for this occupation was supplied in the career export.')
        st.write(LIMITATIONS)
    else:
        evidence = confirmed(j)
        shares = {r['skill_id']: r['pct_postings'] for r in entry['skills']}
        st.caption('Exploration heuristic: up to six highest-share non-certification skills; unconfirmed skills first. This is not a complete curriculum or a readiness score.')
        for skill in prioritize(career['skills'], evidence, shares):
            with st.container(border=True):
                st.subheader(skill['name'])
                st.write(skill['why'])
                own = [e for e in evidence if e['id'] == skill['id']]
                st.write('Experience confirmed by user' if own else 'Not yet demonstrated')
                for item in own:
                    st.text(item['sentence'])
                st.write('Original reflection activity: ' + skill['activity'])
        if page == 'Resources':
            st.caption('Free reflection activity, estimated 15 minutes. No job-specific technical procedure or credential instruction is supplied.')
            j['resource_notes'] = st.text_area('Career reflection notes', value=j['resource_notes'], max_chars=3000)
        else:
            button('Review my evidence', 'Evidence review')
            button('View next steps', 'Next steps')
            if supports_simulation:
                button('Open career practice shift', 'Mission', type='primary')
    st.stop()

if page == 'Welcome':
    st.caption('LEARNINGCURVE / YOUR FIRST NEXT STEP')
    st.title('Your first opportunity starts with a next step.')
    st.markdown('Recognize the experience you already have. Practice a relevant skill. Build something you can explain.')
    st.info('Explore 972 careers. Generate workplace practice where skill data is available, or start with the built-in IT support shift. This is not a hiring assessment.')
    button('Build my learning path', 'Profile', type='primary')
    st.divider()
    for col, title, text in zip(st.columns(3), ['01 · Recognize', '02 · Practice', '03 · Take a next step'],
                              ['Connect your own experiences to skills.', 'Investigate a fictional support ticket.', 'Choose and schedule your next practice activity.']):
        with col:
            st.subheader(title)
            st.write(text)

elif page == 'Profile':
    st.title('Start with what you have done')
    choices = list(catalog()['occupations'])
    selected_code = st.selectbox('Target career — type to search', choices,
                                index=choices.index(j.get('career_draft', career['onet'])),
                                format_func=lambda code: catalog()['occupations'][code]['name'] + (' · Simulation available' if code == IT else ''))
    j['career_draft'] = selected_code
    if selected_code != IT:
        st.info('Explore this career’s skills and generate fictional workplace practice. High-stakes roles use administrative and communication tasks only; scenarios are not expert-reviewed.')
        if not catalog()['occupations'][selected_code]['skills']:
            st.warning('No matching Massachusetts skill records in the selected 2025 full-year dataset.')
    if selected_code != career['onet']:
        st.caption('Continuing switches careers and retains your previous career’s progress separately. Your current background and preferences will be used for the selected career.')
    st.caption('Coursework, work, projects, volunteering and personal responsibilities can all provide relevant examples.')
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
    budgets = st.multiselect('Resource budgets — choose either or both', ['Free', 'Paid'],
                            default=j.get('budgets_draft', profile.get('budgets', ['Free'])))
    j['time_draft'], j['budgets_draft'] = minutes, budgets
    st.caption('Current curated resources are free; paid-only selection may return no matches.')
    with st.expander('Schedule this practice in Google Calendar'):
        st.caption('Choose a time, then review and save the event in Google Calendar. This does not read your calendar or check availability. No background or résumé text is included.')
        zone = st.selectbox('Time zone', ['America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles', 'Europe/London', 'UTC'], index=j.get('calendar_zone_index', 0))
        j['calendar_zone_index'] = ['America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles', 'Europe/London', 'UTC'].index(zone)
        day = st.date_input('Practice date', value=j.get('calendar_day', datetime.now(ZoneInfo(zone)).date()))
        clock = st.time_input('Practice start time', value=j.get('calendar_clock', time(18, 0)))
        j['calendar_day'], j['calendar_clock'] = day, clock
        try:
            link = calendar_link(day, clock, zone, minutes, catalog()['occupations'][selected_code]['name'])
            st.write(f'{day} at {clock.strftime("%H:%M")} · {zone} · {minutes} minutes')
            st.link_button('Open in Google Calendar', link)
            st.caption('The event is not saved until you click Save in Google Calendar. Opening the draft repeatedly may create duplicates if you save each one.')
        except ValueError as exc:
            st.error(str(exc))
    st.caption('Review skill suggestions connects specific phrases in your background to skills. You can confirm, reject, edit, or ask AI for additional suggestions next.')
    if st.button('Review skill suggestions', type='primary'):
        if not budgets:
            st.error('Select at least one budget option.')
            st.stop()
        if selected_code != career['onet']:
            st.session_state.journey = switch_career(j, selected_code)
            j = st.session_state.journey
            career = career_for(selected_code)
            profile = j['profile']
            for key in list(st.session_state):
                if key.startswith('decision_'):
                    del st.session_state[key]
        if experience != profile.get('experience'):
            j['matches'] = suggest(experience, career['skills'])
            j['decisions'] = {}
        if not budgets:
            st.error('Select at least one budget option.')
            st.stop()
        j['profile'] = {'experience': experience, 'minutes': minutes, 'free_only': 'Paid' not in budgets, 'budgets': budgets, 'onet': selected_code}
        j['experience_draft'] = experience
        go('Evidence review')

elif page == 'Evidence review':
    st.title('You decide which connections fit')
    st.caption('These are phrase-based suggestions. Confirmation records a self-reported connection, not verified proficiency.')
    names = {s['id']: s['name'] for s in career['skills']}
    st.caption('Selected career: ' + career['title'])
    if not names:
        st.info('No non-certification skill rows are available for evidence matching in this export. Choose another career or inspect its data coverage.')
        button('Choose a career', 'Profile')
        button('See data coverage', 'Why these skills?')
        st.stop()
    button('Edit my background', 'Profile')
    with st.expander('Ask AI to suggest skill connections'):
        st.caption('This sends your background text, including any imported résumé text, to the configured model. Remove personal details before requesting a review. Suggestions still need your confirmation.')
        if st.button('Analyze my experience with AI', disabled=not ai_available() or not j['profile']['experience'].strip()):
            try:
                with st.spinner('Reviewing your examples…'):
                    suggestions = suggest_experience(j['profile']['experience'], career['skills'])
                existing = {m['id'] for m in j['matches']}
                added = [m for m in suggestions if m['id'] not in existing]
                j['matches'].extend(added)
                st.success(f'{len(added)} additional suggestions. Existing decisions were preserved.')
            except SimulationError as exc:
                st.error(str(exc))
        if not ai_available():
            st.info('AI is not configured. Phrase matching and manual evidence still work.')
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
    st.title('Three skills. Your next support shift.')
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
    with st.expander('Generate a personalized shift'):
        new_shift_controls()

elif page == 'Mission':
    st.title(mission['title'])
    st.write(mission['scenario'])
    st.caption(mission['provenance'] + ' All actions are simulated; no device settings are changed.')
    if 'rules' in mission:
        preferences = mission['preferences']
        st.caption(f'{preferences["difficulty"]} · Fits your {preferences["minutes"]}-minute practice preference · AI-generated situation')
        with st.expander('Why this shift?'):
            st.write('Practice gaps: ' + (', '.join(preferences['practice_gaps']) or 'Build experience with your selected skills.'))
            skill_names = {s['id']: s['name'] for s in career['skills']}
            st.write('Skills to practice: ' + (', '.join(skill_names.get(s, s) for s in preferences['practice_skill_ids']) or 'Continue practicing your confirmed skills.'))
    else:
        with st.expander('Generate a personalized shift'):
            new_shift_controls()
    locked = len(j['attempts']) == 2 or (len(j['attempts']) == 1 and not j['revision_started'])
    if locked:
        st.info('This attempt has been submitted. View feedback to use the one available revision or choose a next activity.')
        button('View feedback', 'Feedback', type='primary')
    else:
        state = j['mission']
        if 'rules' in mission:
            customer_conversation()
        st.subheader('Investigate the ticket')
        left, right = st.columns([1, 1])
        with left:
            for key, entry in mission['evidence'].items():
                if st.button(entry['label'], key='evidence_' + mission.get('id', 'builtin') + '_' + key, disabled=key in state.seen, use_container_width=True):
                    perform(key)
            st.subheader('Choose an action')
            for key, label in mission['actions'].items():
                if st.button(label, key='action_' + mission.get('id', 'builtin') + '_' + key):
                    perform(key)
            if st.button(mission['rules']['verification']['label'] if 'rules' in mission else 'Verify portal access', type='primary', key='verify_outcome'):
                perform('verify')
        with right:
            st.subheader('Action history')
            with st.container(height=280, border=True):
                if not state.history:
                    st.caption('Observations and results appear here as you investigate.')
                for n, entry in enumerate(state.history, 1):
                    st.write(f'{n}. {entry["result"]}')
            st.subheader('AI practice assistant')
            st.caption('Ask for guidance in your own words. The assistant sees this scenario and your recorded observations, not your résumé. Advice does not perform actions or earn credit.')
            with st.container(height=220, border=True):
                for turn in state.coach_dialogue:
                    st.text('You: ' + turn['question'])
                    st.text('AI assistant: ' + turn['reply'])
            with st.form('coach_question', clear_on_submit=True):
                question = st.text_input('Ask your practice assistant', max_chars=1000)
                sent = st.form_submit_button('Ask assistant', disabled=not ai_available() or len(state.coach_dialogue) >= 20)
            if not ai_available():
                st.info('Connect a model resource to enable the assistant. Diagnostic actions remain available.')
            if sent:
                try:
                    with st.spinner('Preparing guidance…'):
                        ask_coach(state, mission, question)
                except SimulationError as exc:
                    st.error(str(exc))
                else:
                    st.rerun()
        with st.expander('Evaluate a scripted AI suggestion'):
            st.info(mission['ai_suggestion'])
            for action, label in [('accept', 'Accept suggestion (simulate)'), ('question', 'Question the suggestion'), ('reject', 'Reject the suggestion')]:
                if st.button(label, disabled=state.ai == action):
                    perform(action)
            if state.ai:
                st.caption('Compare the suggestion against the observations before choosing an action.' if 'rules' in mission else 'The suggestion lacks evidence of a firewall block. A DNS comparison supports a narrower change; disabling protection is not justified by this ticket.')
            if 'rules' in mission and st.button('Reveal a hint'):
                perform('hint')
        st.subheader('Explain the outcome to the customer')
        explanation = st.text_area('What did you do, and how did you check the outcome?', value=j['draft'], max_chars=2000, height=130,
                                   key='explanation_' + mission.get('id', 'builtin') + ('_revision' if j['revision_started'] else '_original'))
        j['draft'] = explanation
        if st.button('Submit for feedback'):
            try:
                attempt = assess(state, explanation, mission)
                j['attempts'].append(attempt)
                go('Feedback')
            except ValueError as exc:
                st.error(str(exc))

elif page == 'Feedback':
    st.title('What your attempt demonstrated')
    attempt = j['attempts'][-1]
    st.caption('Only this exercise is assessed. No hiring or professional-competence score is generated.')
    with st.expander('Visible exercise rubric'):
        for criterion, rule in rubric_for(mission).items():
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
    st.subheader('Scope evaluation')
    st.write(attempt.get('scope_feedback', 'Review the scope criterion and action record above.'))
    st.subheader('AI explanation review')
    st.caption('Sends your explanation and action record to the configured model. Reviews accuracy and clarity alongside keyword checks; it cannot change action credit.')
    if st.button('Review explanation with AI', disabled=not ai_available()):
        try:
            with st.spinner('Reviewing your explanation…'):
                attempt['ai_review'] = review_explanation(attempt)
        except SimulationError as exc:
            st.error(str(exc))
    if attempt.get('ai_review'):
        st.caption('AI-generated feedback may be mistaken. Compare it with the recorded actions.')
        st.text(attempt['ai_review'])
    if 'rules' in mission:
        with st.expander('The cause and supporting reasoning'):
            st.write(mission['ground_truth'])
            st.write(mission['rules']['colleague']['critique'])
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
    button('Choose my next activity', 'Next steps')
    st.divider()
    new_shift_controls()

elif page == 'Shift history':
    st.title('Your practice shifts')
    records = shift_records(j, mission)
    if not records:
        st.info('Complete a shift to see your feedback here.')
    for index, record in enumerate(records, 1):
        with st.expander(f'{index}. {record["scenario"]["title"]}', expanded=index == len(records)):
            st.write(record['scenario']['scenario'])
            st.caption(record['scenario']['provenance'])
            for number, attempt in enumerate(record['attempts'], 1):
                st.write(f'Attempt {number}')
                for criterion, passed in attempt['criteria'].items():
                    st.write(f'{criterion}: {"Observed" if passed else "Not yet demonstrated"}')
                st.text(attempt['explanation'])
                st.write('One improvement: ' + attempt['improvement'])

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
                            labels={'coverage': 'Year and coverage', 'ma_pct_postings_genai_skills': 'Share of postings (%)'}), use_container_width=True, config={'displayModeBar': False})
    st.table(profile[['coverage', 'ma_job_postings', 'ma_pct_postings_genai_skills', 'ma_confidence_flag']])
    st.subheader(prefix + f'Requested skills · {data["skill_year"]}')
    skills = pd.DataFrame(data['skills'])
    relevant = skills[skills['skill_name'].str.casefold().isin([s['name'].casefold() for s in career['skills']])]
    if relevant.empty:
        st.info('No exact matches for the three milestone labels. Showing the ten highest listed source skills for occupational context, not as validation of this simulation.')
        relevant = skills.nlargest(10, 'pct_postings')
    st.plotly_chart(px.bar(relevant, x='pct_postings', y='skill_name', orientation='h',
                           labels={'pct_postings': 'Share of occupational postings (%)', 'skill_name': 'Source skill'}), use_container_width=True, config={'displayModeBar': False})
    st.caption('Denominator: Massachusetts postings for this occupation in the selected complete year. Skills can overlap; percentages must not be summed. The profile table above supplies posting counts and period coverage.')
    st.table(relevant[['skill_name', 'skill_type', 'pct_postings', 'confidence_flag']])
    with st.expander('Interpretation and limitations', expanded=True):
        st.write(LIMITATIONS)
