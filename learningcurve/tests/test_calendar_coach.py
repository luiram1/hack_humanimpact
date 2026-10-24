from datetime import date, time
from urllib.parse import urlparse, parse_qs
from copy import deepcopy
import pytest
from models import MissionState, content
from calendar_tools import calendar_link
from ai_simulation import ask_coach, suggest_experience
from simulation import SimulationError
from recommendations import recommend

def test_calendar_duration_timezone_and_no_background():
    query = parse_qs(urlparse(calendar_link(date(2026, 10, 24), time(18), 'America/New_York', 30)).query)
    assert query['dates'] == ['20261024T220000Z/20261024T223000Z']
    assert query['ctz'] == ['America/New_York']
    assert set(query) == {'action', 'text', 'dates', 'ctz', 'details'}

@pytest.mark.parametrize('day,clock', [(date(2026, 3, 8), time(2, 30)), (date(2026, 11, 1), time(1, 30))])
def test_calendar_rejects_dst_gaps_and_ambiguity(day, clock):
    with pytest.raises(ValueError):
        calendar_link(day, clock, 'America/New_York', 30)

def test_coach_never_gets_hidden_truth_or_awards_credit():
    state = MissionState()
    def fake(name, schema, instructions, context):
        assert 'ground_truth' not in context
        assert 'evidence' not in context
        return {'reply': 'Check whether the issue affects other devices.'}
    ask_coach(state, content('mission'), 'Where should I start?', client=fake)
    assert len(state.coach_dialogue) == 1
    assert not state.history and not state.seen and not state.resolved
    before = deepcopy(state)
    def broken(*args):
        raise SimulationError('Unavailable')
    with pytest.raises(SimulationError):
        ask_coach(state, content('mission'), 'Help?', client=broken)
    assert state == before

def test_ai_evidence_cannot_invent_quote():
    def fake(*args):
        return {'suggestions': [{'id': 'communication', 'sentence': 'Invented', 'explanation': 'Test'}]}
    with pytest.raises(SimulationError):
        suggest_experience('I answered customer questions.', content('career')['skills'], client=fake)

def test_independent_budgets():
    free = content('resources')['resources'][0]
    paid = dict(free, paid=True)
    assert recommend([free, paid], 30, False, free['skills'], budgets=['Paid']) == [paid]
    assert recommend([free, paid], 30, False, free['skills'], budgets=['Free', 'Paid']) == [free, paid]

def test_gateway_auth_payload_and_invalid_response(monkeypatch):
    import gateway
    import requests
    import databricks.sdk.core
    monkeypatch.setenv('DATABRICKS_MODEL', 'system.ai.gpt-oss-120b')
    class Config:
        host = 'https://workspace.example.com'
        def authenticate(self):
            return {'Authorization': 'Bearer test-only'}
    monkeypatch.setattr(databricks.sdk.core, 'Config', Config)
    captured = {}
    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return {'choices': [{'finish_reason': 'stop', 'message': {'content': '{"reply":"Check scope."}'}}]}
    def post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return Response()
    monkeypatch.setattr(requests, 'post', post)
    schema = {'type': 'object', 'properties': {'reply': {'type': 'string'}}, 'required': ['reply']}
    assert gateway.request_json('coach', schema, 'Coach only', {}) == {'reply': 'Check scope.'}
    assert captured['url'].endswith('/ai-gateway/mlflow/v1/chat/completions')
    assert captured['json']['model'] == 'system.ai.gpt-oss-120b'
    assert captured['headers']['Authorization'] == 'Bearer test-only'
    with pytest.raises(SimulationError):
        gateway.request_json('coach', {'type': 'array'}, 'Coach only', {})

def test_profile_calendar_and_budget_ui():
    from streamlit.testing.v1 import AppTest
    from models import ROOT
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=30).run()
    next(b for b in app.button if b.label == 'Build my learning path').click().run()
    app.multiselect[0].set_value(['Free', 'Paid']).run()
    assert any('calendar.google.com' in link.proto.url for link in app.get('link_button'))
    next(b for b in app.button if b.label == 'Review skill suggestions').click().run()
    assert app.session_state['journey']['profile']['budgets'] == ['Free', 'Paid']
    assert not app.exception
