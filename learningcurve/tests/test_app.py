from pathlib import Path
from io import BytesIO
from unittest.mock import patch
import sys
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
    assert not any(b.label == 'Try the demo' for b in app.button)
    click(app, 'Build my learning path')
    app.text_area[0].set_value('I installed software and answered customer questions.').run()
    click(app, 'Review skill suggestions')
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
    from data_access import load_data
    assert any('ILLUSTRATIVE' in w.value for w in app.warning) == load_data()['illustrative']
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


def test_resume_upload_edit_navigation_and_learning_path(resume_pdf):
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    click(app, 'Build my learning path')
    click(app, 'Add resume')
    upload = BytesIO(resume_pdf('Installed software\nTroubleshooting'))
    with patch('streamlit.file_uploader', return_value=upload):
        app.run()
        assert not app.exception
        assert 'Installed software' in app.text_area[0].value
        app.text_area[0].set_value(app.text_area[0].value + '\nCustomer support').run()
        edited = app.text_area[0].value
        app.select_slider[0].set_value(60).run()
        assert app.text_area[0].value == edited
        click(app, 'Review skill suggestions')
    assert app.session_state['journey']['profile']['experience'] == edited
    assert app.session_state['journey']['matches']
    # Inspect the persisted journey in a fresh view: older AppTest versions retain
    # stale profile widgets after st.rerun(), even in the original application.
    journey = app.session_state['journey']
    app = AppTest.from_file(str(APP), default_timeout=30)
    app.session_state['journey'] = journey
    app.session_state['page'] = 'Evidence review'
    app.run()
    for radio in app.radio:
        radio.set_value('Confirm')
    app.run()
    click(app, 'See my learning path')
    assert any('Installed software' in text.value for text in app.text)
    click(app, 'Profile')
    assert app.text_area[0].value == edited
    app.checkbox[0].check().run()
    click(app, 'Clear all progress')
    assert 'resume_digest' not in app.session_state['journey']


def test_invalid_resume_preserves_typed_experience():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    click(app, 'Build my learning path')
    app.text_area[0].set_value('Installed software').run()
    click(app, 'Add resume')
    with patch('streamlit.file_uploader', return_value=BytesIO(b'%PDF-broken')):
        app.run()
    assert not app.exception
    assert app.error
    assert app.text_area[0].value == 'Installed software'


def test_app_opens_and_preserves_experience_without_pypdf():
    with patch.dict(sys.modules, {'pypdf': None}):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        assert not app.exception
        click(app, 'Build my learning path')
        app.text_area[0].set_value('Installed software').run()
        click(app, 'Add resume')
        with patch('streamlit.file_uploader', return_value=BytesIO(b'%PDF-1.7\n')):
            app.run()
        assert not app.exception
        assert any('server is missing pypdf' in error.value for error in app.error)
        assert app.text_area[0].value == 'Installed software'
