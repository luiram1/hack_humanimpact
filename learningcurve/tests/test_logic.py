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
