from models import initial_journey, content
from careers import catalog, career_for, switch_career, IT
from simulation import practice_context
from streamlit.testing.v1 import AppTest
from pathlib import Path

def test_source_coverage_and_occupation_specific_skills():
    entries = catalog()['occupations']
    assert len(entries) == 972
    assert sum(bool(e['skills']) for e in entries.values()) == 895
    accounting = career_for('13-2011.00')
    assert accounting['title'] == 'Accountants and Auditors'
    assert accounting['skills']
    assert {s['id'] for s in accounting['skills']}.isdisjoint(s['id'] for s in content('career')['skills'])

def test_switch_restores_separate_progress_and_context():
    j = initial_journey()
    j['profile'] = {'onet': IT, 'minutes': 30}
    j['draft'] = 'IT explanation'
    j = switch_career(j, '13-2011.00')
    assert not j['draft'] and not j['attempts']
    j['profile'] = {'onet': '13-2011.00', 'minutes': 30}
    context = practice_context(j)
    assert context['occupation_title'] == 'Accountants and Auditors'
    assert context['source_skills']
    assert 'practice_boundary' in context
    j = switch_career(j, IT)
    assert j['draft'] == 'IT explanation'

def test_non_it_ui_does_not_show_dns_fallback():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=30).run()
    next(b for b in app.button if b.label == 'Build my learning path').click().run()
    app.selectbox[0].set_value('13-2011.00').run()
    next(b for b in app.button if b.label == 'Review skill suggestions').click().run()
    assert not app.exception
    next(b for b in app.button if b.label == 'See my learning path').click().run()
    next(b for b in app.button if b.label == 'Open career practice shift').click().run()
    assert not app.exception
    assert not any('DNS' in b.label for b in app.button)
    assert any(b.label == 'Generate a new shift' for b in app.button)
