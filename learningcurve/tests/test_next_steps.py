from models import initial_journey, ROOT
from careers import career_for
from next_steps import plan
from streamlit.testing.v1 import AppTest

def test_next_step_uses_feedback_and_career_credentials():
    j = initial_journey()
    j['attempts'] = [{'next_step': 'Verify the result before closing.'}]
    result = plan(j, career_for('13-2011.00'))
    assert result['action'] == 'Verify the result before closing.'
    assert result['certifications']
    assert all(r['skill_type'] == 'Certification' for r in result['certifications'])
    assert 'Accountants and Auditors' in result['project']

def test_final_section_renders_without_model():
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=30)
    j = initial_journey()
    j['profile'] = {'onet': '13-2011.00', 'minutes': 30, 'budgets': ['Free'], 'experience': ''}
    app.session_state['journey'] = j
    app.session_state['page'] = 'Next steps'
    app.run()
    assert not app.exception
    assert app.title[0].value == 'Next steps'
    assert any('not been verified' in w.value for w in app.warning)
    assert not app.get('download_button')
