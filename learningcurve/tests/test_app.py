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
