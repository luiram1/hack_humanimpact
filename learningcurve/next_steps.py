"""Career-aware next actions and source-based credential candidates."""
from urllib.parse import urlencode
from datetime import datetime, time
from zoneinfo import ZoneInfo
from careers import catalog, IT
from calendar_tools import calendar_link

def plan(journey, career):
    attempts = journey.get('attempts', [])
    entry = catalog()['occupations'][career['onet']]
    certificates = sorted((r for r in entry['skills'] if r['skill_type'] == 'Certification'),
                          key=lambda r: (-r['pct_postings'], r['skill_name']))
    seen, unique = set(), []
    for row in certificates:
        if row['skill_id'] not in seen:
            unique.append(row)
            seen.add(row['skill_id'])
    skill = career['skills'][0]['name'] if career['skills'] else 'a skill you want to explore'
    action = attempts[-1]['next_step'] if attempts else f'Write one specific example of how you used {skill}, then identify what you would like to practice.'
    return {'action': action, 'certifications': unique[:5],
            'project': f'Create a one-page fictional workplace case for {career["title"]}: describe the problem, list three observations, explain one proposed action, and describe how you would check the result. Focus on {skill}. Use administrative or communication tasks for high-stakes roles.'}

def render(journey, career, resources):
    import streamlit as st
    result = plan(journey, career)
    minutes = journey['profile'].get('minutes', 30)
    st.title('Next steps')
    st.caption(career['title'])
    st.subheader('Your recommended next action')
    st.info(result['action'])
    st.caption('Based on your latest submitted attempt.' if journey['attempts'] else 'A starting activity based on your selected career; complete a simulation for feedback-based guidance.')
    with st.expander('Relevant certifications and credentials'):
        st.caption('Candidates mentioned in Massachusetts job postings, not a verified beginner shortlist. Data Source: Lightcast, 2026 · 2025 full year. A certification, course certificate and professional license are different credentials.')
        st.warning('Issuer, eligibility, current cost and credential type have not been verified for these candidates. Check the official issuer before choosing or paying. Posting demand does not establish suitability or guarantee employment.')
        if 'Paid' not in journey['profile'].get('budgets', ['Free']):
            st.caption('You selected free resources. These credentials are research candidates only; exams may cost money and are not being recommended as free activities.')
        if not result['certifications']:
            st.info('No certification rows were found for this career in the selected dataset.')
        for row in result['certifications']:
            st.markdown('**' + row['skill_name'] + '**')
            st.caption(f"Requested in {row['pct_postings']:g}% of {row['job_postings']:,.0f} occupational postings · source flag: {row['confidence_flag']}")
            url = 'https://www.google.com/search?' + urlencode({'q': row['skill_name'] + ' official issuer certification prerequisites exam cost'})
            st.link_button('Find the official issuer — web search', url)
    with st.expander('Learning resources'):
        if career['onet'] != IT:
            st.info('Verified external learning resources are not curated for this career yet. Use the original reflection and project activities below; no course links have been invented.')
        elif not resources:
            st.info('No curated resources match your budget and duration. Adjust your profile preferences.')
        else:
            for resource in resources:
                st.markdown('**' + resource['title'] + '**')
                st.write(resource['provider'] + ' · ' + resource['cost'])
                st.write(resource['activity'])
                st.caption(f"Estimated activity duration: {resource['minutes']} minutes. " + resource['why'])
                if resource['url']:
                    st.link_button('Open learning material', resource['url'])
                    st.caption('Link checked: ' + str(resource['verified']))
    with st.expander('Build a small practice project'):
        st.write(result['project'])
        st.caption(f'Use your {minutes}-minute session to draft an outline. This is simulated practice, not employment experience or certification.')
        journey['resource_notes'] = st.text_area('Project and next-step notes', value=journey['resource_notes'], max_chars=3000)
    with st.expander('Schedule your next practice session'):
        zones = ['America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles', 'Europe/London', 'UTC']
        zone = st.selectbox('Time zone', zones, index=zones.index(journey.get('next_zone', zones[0])))
        day = st.date_input('Practice date', value=journey.get('next_day', datetime.now(ZoneInfo(zone)).date()))
        clock = st.time_input('Start time', value=journey.get('next_clock', time(18)))
        journey.update(next_zone=zone, next_day=day, next_clock=clock)
        st.caption(f'{minutes} minutes. Opens a calendar draft for you to review and save; does not check availability. Your assessment and background are not included.')
        try:
            st.link_button('Open in Google Calendar', calendar_link(day, clock, zone, minutes, career['title']))
        except ValueError as exc:
            st.error(str(exc))
    if career['skills'] and st.button('Practice again', type='primary'):
        st.session_state.page = 'Mission'
        st.rerun()
    if st.button('Update my goals and preferences'):
        st.session_state.page = 'Profile'
        st.rerun()
