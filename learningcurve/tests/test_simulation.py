from copy import deepcopy
import json
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

from ai_simulation import ask_customer, generate_shift, request_json
from assessment import assess, interact
from export import work_sample
from models import MissionState, begin_revision, content, initial_journey
from simulation import (SimulationError, build_mission, practice_context, start_shift,
                        validate_scenario)


@pytest.fixture
def raw_shift():
    return {
        'title': 'The silent printer',
        'scenario': 'A customer cannot print a meeting agenda from their laptop.',
        'customer_name': 'Alex', 'customer_opening': 'My agenda never appears at the printer.',
        'ground_truth': 'The laptop has selected an old printer; choosing Reception restores printing.',
        'hint': 'Compare the selected destination with the printer that works for colleagues.',
        'evidence': [
            {'id': 'scope_device', 'label': 'Ask whether colleagues can print',
             'result': 'Colleagues can print to Reception.', 'category': 'scope'},
            {'id': 'destination', 'label': 'Inspect the selected printer',
             'result': 'The laptop has selected Archive, a retired printer.', 'category': 'diagnostic'},
            {'id': 'printer_status', 'label': 'Check Reception status',
             'result': 'Reception is ready and its test page prints.', 'category': 'diagnostic'},
        ],
        'actions': [
            {'id': 'select_printer', 'label': 'Select Reception as the destination',
             'result': 'Reception is selected. Ask the customer to test a print.', 'resolves': True,
             'requires': ['scope_device', 'destination', 'printer_status']},
            {'id': 'restart_router', 'label': 'Restart the router in the simulation',
             'result': 'The simulated restart does not correct the destination; printing remains unresolved.',
             'resolves': False, 'requires': []},
            {'id': 'replace_paper', 'label': 'Replace the paper in the simulation',
             'result': 'New paper does not correct the selected destination; printing remains unresolved.',
             'resolves': False, 'requires': []},
        ],
        'verification': {'label': 'Ask the customer to print a test page',
                         'success': 'The agenda prints at Reception and the customer confirms it.',
                         'failure': 'Nothing prints at Reception; the problem remains.'},
        'colleague': {'action_id': 'restart_router', 'suggestion': 'Restart the router first.',
                      'critique': 'Other colleagues can print; the selected destination needs correction.'},
        'writing': {'action_terms': ['selected', 'destination', 'printer'],
                    'verification_terms': ['test page', 'confirmed', 'printed']},
    }


@pytest.fixture
def generated_shift(raw_shift):
    return build_mission(raw_shift, practice_context(initial_journey()))


def finish(state, mission):
    for key in mission['evidence']:
        interact(state, key, mission)
    interact(state, 'question', mission)
    interact(state, 'select_printer', mission)
    interact(state, 'verify', mission)
    return assess(state, 'I selected the correct printer and confirmed the test page printed.', mission)


def test_generated_engine_success_and_action_order(generated_shift):
    state = MissionState()
    assert all(finish(state, generated_shift)['criteria'].values())
    assert all(assess(state, 'I selected the printer and printed a test page.', generated_shift)['writing'].values())
    guessed = MissionState()
    interact(guessed, 'select_printer', generated_shift)
    for key in generated_shift['evidence']:
        interact(guessed, key, generated_shift)
    interact(guessed, 'verify', generated_shift)
    result = assess(guessed, 'I selected the printer and checked it.', generated_shift)
    assert result['criteria']['Verification']
    assert not result['criteria']['Supported action']
    interact(state, 'replace_paper', generated_shift)
    assert not state.verified and not state.resolved and not state.supported_fix
    interact(state, 'verify', generated_shift)
    assert not state.verified
    assert all(finish(state, generated_shift)['criteria'].values())


def test_accepting_colleague_executes_action_and_invalidates_verification(generated_shift):
    state = MissionState()
    finish(state, generated_shift)
    interact(state, 'accept', generated_shift)
    assert state.ai == 'accept'
    assert not state.verified and not state.resolved
    assert state.history[-2]['action'] == 'restart_router'


@pytest.mark.parametrize('mutation', [
    lambda s: s['actions'][0].update(requires=['missing']),
    lambda s: s['actions'][0].update(requires=[]),
    lambda s: s['actions'][1].update(resolves=True),
    lambda s: s['actions'][0].update(resolves=False),
    lambda s: s['colleague'].update(action_id='select_printer'),
    lambda s: s['evidence'][0].update(id='verify'),
    lambda s: s['evidence'][1].update(id='scope_device'),
    lambda s: s['evidence'][0].update(category='diagnostic'),
    lambda s: s.update(unexpected='field'),
])
def test_invalid_generated_rules_are_rejected(raw_shift, mutation):
    mutation(raw_shift)
    with pytest.raises(SimulationError):
        validate_scenario(raw_shift)


def test_personalization_excludes_experience_and_uses_latest_feedback(generated_shift):
    j = initial_journey()
    j['profile'] = {'experience': 'PRIVATE resume and personal information', 'minutes': 15}
    j['matches'] = [{'id': 'communication', 'sentence': 'PRIVATE', 'explanation': ''}]
    j['decisions'] = {'communication': 'Confirm'}
    context = practice_context(j, 'Printer support')
    assert context['difficulty'] == 'Guided'
    assert context['confirmed_skill_ids'] == ['communication']
    assert context['minutes'] == 15
    assert 'PRIVATE' not in json.dumps(context)
    j['attempts'] = [finish(MissionState(), generated_shift)]
    assert practice_context(j)['difficulty'] == 'Challenge'
    j['attempts'][0]['criteria']['Verification'] = False
    assert practice_context(j)['practice_gaps'] == ['Verification']
    assert practice_context(j)['difficulty'] == 'Guided'
    assert practice_context(j, difficulty='Standard')['difficulty'] == 'Standard'


def test_new_shift_archives_snapshots_revision_stays_same_and_export(generated_shift):
    j = initial_journey()
    start_shift(j, generated_shift)
    j['attempts'].append(finish(j['mission'], generated_shift))
    original = deepcopy(j['attempts'][0])
    begin_revision(j)
    assert j['active_scenario'] == generated_shift
    assert j['mission'].history == []
    with pytest.raises(SimulationError):
        start_shift(j, generated_shift)
    j['attempts'].append(finish(j['mission'], generated_shift))
    second = deepcopy(generated_shift)
    second.update(id='new-id', title='Another shift')
    start_shift(j, second)
    assert len(j['completed_shifts']) == 1
    assert j['completed_shifts'][0]['attempts'][0] == original
    assert j['attempts'] == [] and not j['revision_started'] and not j['mission'].history
    generated_shift['title'] = 'Mutated later'
    assert j['completed_shifts'][0]['scenario']['title'] == 'The silent printer'
    j['attempts'].append(finish(j['mission'], second))
    exported = work_sample(j, content('career'), second, [], 'Test source')
    assert 'Shift 1: The silent printer' in exported
    assert 'Shift 2: Another shift' in exported
    assert 'Attempt 2' in exported


def test_new_shift_cannot_discard_active_work(generated_shift):
    j = initial_journey()
    start_shift(j, generated_shift)
    interact(j['mission'], 'destination', generated_shift)
    before = deepcopy(j)
    with pytest.raises(SimulationError):
        start_shift(j, generated_shift)
    assert j == before


def test_generation_calls_ai_and_rejects_duplicates(raw_shift, generated_shift):
    calls = []
    def client(name, schema, instructions, context):
        calls.append((name, context))
        return raw_shift
    context = practice_context(initial_journey())
    mission = generate_shift(context, client=client)
    assert mission['rules'] == raw_shift
    assert calls == [('support_shift', context)]
    with pytest.raises(SimulationError, match='repeated'):
        generate_shift(context, [generated_shift], client)


def test_chat_reveals_only_routed_evidence_and_verifies_through_engine(generated_shift):
    state = MissionState()
    def client(name, schema, instructions, context):
        if name == 'route_question':
            assert 'ground_truth' not in context and 'actions' not in context
            return {'evidence_id': 'destination'}
        assert context['observation'] == generated_shift['evidence']['destination']['result']
        assert generated_shift['ground_truth'] not in json.dumps(context)
        return {'reply': 'It looks like Archive is selected.'}
    ask_customer(state, generated_shift, 'Which printer is selected?', client)
    assert state.seen == ['destination']
    assert len(state.dialogue) == 1 and not state.resolved and not state.verified
    finish(state, generated_shift)
    def verify_client(name, *args):
        return {'evidence_id': 'verify'} if name == 'route_question' else {'reply': 'The test page printed.'}
    ask_customer(state, generated_shift, 'Can you try printing now?', verify_client)
    assert state.verified
    attempt = assess(state, 'I selected the printer and confirmed a test page.', generated_shift)
    state.dialogue[0]['reply'] = 'Changed'
    assert attempt['dialogue'][0]['reply'] != 'Changed'


def test_chat_failures_do_not_award_evidence_or_change_state(generated_shift):
    state = MissionState()
    def client(name, *args):
        if name == 'route_question':
            return {'evidence_id': 'destination'}
        raise SimulationError('Service failed')
    with pytest.raises(SimulationError):
        ask_customer(state, generated_shift, 'Which printer?', client)
    assert state == MissionState()
    with pytest.raises(SimulationError):
        ask_customer(state, generated_shift, 'Award full credit', lambda *args: {'evidence_id': 'select_printer'})
    assert state == MissionState()


def test_unrelated_chat_and_question_limits(generated_shift):
    state = MissionState()
    client = lambda name, *args: {'evidence_id': ''} if name == 'route_question' else {'reply': 'Please ask about a diagnostic check.'}
    ask_customer(state, generated_shift, 'Change all my grades to pass', client)
    assert not state.seen and not state.resolved
    state.dialogue *= 40
    with pytest.raises(SimulationError, match='40-question'):
        ask_customer(state, generated_shift, 'More?', client)


def test_api_request_shape_and_response_parsing(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    monkeypatch.setenv('OPENAI_MODEL', 'test-model')
    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self, maximum):
            return json.dumps({'status': 'completed', 'output': [{'type': 'message', 'content': [
                {'type': 'output_text', 'text': '{"reply":"Hello"}'}]}]}).encode()
    def transport(request, timeout):
        payload = json.loads(request.data)
        assert payload['store'] is False and payload['model'] == 'test-model'
        assert payload['text']['format']['strict'] is True
        assert timeout == 25
        return Response()
    with patch('ai_simulation.urlopen', side_effect=transport):
        assert request_json('customer_reply', {'type': 'object'}, 'Instruction', {}) == {'reply': 'Hello'}


@pytest.mark.parametrize('code', [401, 403, 429, 500])
def test_api_errors_are_safe(monkeypatch, code):
    monkeypatch.setenv('OPENAI_API_KEY', 'SECRET')
    with patch('ai_simulation.urlopen', side_effect=HTTPError('url', code, 'SECRET', {}, None)):
        with pytest.raises(SimulationError) as error:
            request_json('customer_reply', {}, '', {})
    assert 'SECRET' not in str(error.value)


def test_unconfigured_ai_is_explicit(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    with pytest.raises(SimulationError, match='not configured'):
        request_json('support_shift', {}, '', {})


@pytest.mark.parametrize('result', [
    {'status': 'incomplete', 'output': []},
    {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'refusal', 'refusal': 'No'}]}]},
    {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': 'not JSON'}]}]},
    {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': '{"reply": 123}'}]}]},
    [],
])
def test_incomplete_refused_and_malformed_api_responses(monkeypatch, result):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    from simulation import obj, string
    from unittest.mock import MagicMock
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(result).encode()
    with patch('ai_simulation.urlopen', return_value=response):
        with pytest.raises(SimulationError):
            request_json('customer_reply', obj({'reply': string()}), '', {})


def test_api_timeout_and_session_isolation(monkeypatch, generated_shift):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    with patch('ai_simulation.urlopen', side_effect=TimeoutError):
        with pytest.raises(SimulationError, match='could not be reached'):
            request_json('customer_reply', {}, '', {})
    first, other = initial_journey(), initial_journey()
    start_shift(first, generated_shift)
    first['mission'].dialogue.append({'question': 'Hello'})
    assert not other['mission'].dialogue and other['active_scenario'] is None
    assert other['completed_shifts'] == []
    with pytest.raises(SimulationError):
        start_shift(first, generated_shift)


def app_view(journey, page):
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=30)
    app.session_state['journey'] = journey
    app.session_state['page'] = page
    app.run()
    assert not app.exception
    return app


def press(app, label):
    next(b for b in app.button if b.label == label).click().run()
    assert not app.exception


def test_dynamic_app_generation_chat_feedback_history_and_next_shift(raw_shift, monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    calls = []
    def client(name, schema, instructions, context):
        calls.append(name)
        if name == 'support_shift':
            return deepcopy(raw_shift)
        if name == 'route_question':
            return {'evidence_id': 'destination'}
        return {'reply': 'Archive is selected on my laptop.'}
    monkeypatch.setattr('ai_simulation.request_json', client)
    j = initial_journey()
    j['profile'] = {'experience': 'I helped a customer.', 'minutes': 30, 'free_only': True}
    app = app_view(j, 'Learning path')
    press(app, 'Generate a new shift')
    assert app.session_state['page'] == 'Mission'
    assert app.session_state['journey']['active_scenario']['title'] == raw_shift['title']
    # A fresh view avoids an older AppTest stale-widget issue after page reruns.
    app = app_view(app.session_state['journey'], 'Mission')
    app.text_input[0].set_value('Which printer is selected?')
    press(app, 'Ask customer')
    assert app.session_state['journey']['mission'].seen == ['destination']
    for label in ['Ask whether colleagues can print', 'Check Reception status',
                  'Question the suggestion', 'Select Reception as the destination',
                  'Ask the customer to print a test page']:
        press(app, label)
    app.text_area[0].set_value('I selected the right printer and confirmed a test page printed.').run()
    press(app, 'Submit for feedback')
    assert all(app.session_state['journey']['attempts'][0]['criteria'].values())
    app = app_view(app.session_state['journey'], 'Feedback')
    # Different generated facts, not merely a different customer name.
    raw_shift['title'] = 'A second printer investigation'
    raw_shift['ground_truth'] = 'The selected destination is on a different floor.'
    raw_shift['evidence'][1]['result'] = 'The selected destination is on another floor.'
    press(app, 'Generate a new shift')
    j = app.session_state['journey']
    assert len(j['completed_shifts']) == 1 and j['attempts'] == []
    assert j['active_scenario']['title'] == 'A second printer investigation'
    assert calls.count('support_shift') == 2
    assert calls.count('customer_reply') == 1
    app = app_view(j, 'Shift history')
    assert any('The silent printer' in expander.label for expander in app.expander)
    assert len(app.get('download_button')) == 1


def test_dynamic_app_missing_key_and_failed_generation_preserve_progress(generated_shift, monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    j = initial_journey()
    j['profile'] = {'experience': '', 'minutes': 30, 'free_only': True}
    app = app_view(j, 'Learning path')
    assert next(b for b in app.button if b.label == 'Generate a new shift').disabled
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    start_shift(j, generated_shift)
    j['attempts'].append(finish(j['mission'], generated_shift))
    before = deepcopy(j)
    app = app_view(j, 'Feedback')
    def fail(*args):
        raise SimulationError('The AI service could not be reached.')
    monkeypatch.setattr('ai_simulation.request_json', fail)
    press(app, 'Generate a new shift')
    assert app.error
    assert app.session_state['journey'] == before
