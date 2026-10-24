"""Deterministic simulation. No operating-system commands are executed."""
import re
from copy import deepcopy

def interact(state, action, mission):
    if 'rules' in mission:
        return interact_generated(state, action, mission)
    if action in mission['evidence']:
        if action in state.seen:
            return
        state.seen.append(action)
        message = mission['evidence'][action]['result']
    elif action in ('accept', 'question', 'reject'):
        state.ai = action
        message = f'AI suggestion: {action}. '
        if action == 'accept':
            message += 'The simulated firewall change does not fix the issue and is rolled back.'
        else:
            message += 'No firewall change made. Compare evidence before selecting a fix.'
    elif action in mission['actions']:
        state.verified = False
        if action == 'refresh':
            state.resolved = True
            state.supported_fix = {'websites', 'others', 'dns'}.issubset(state.seen)
            message = 'Cached DNS refreshed in the simulation. Test portal access to check the result.'
        else:
            message = 'The simulated change does not address the stale cache; it is rolled back. You can gather evidence and try another action.'
    elif action == 'verify':
        state.verified = state.resolved
        message = ('The portal opens on the affected device and the customer confirms access.'
                   if state.resolved else 'The portal still fails to open. Continue investigating.')
    else:
        raise ValueError('Unknown simulation action.')
    state.history.append({'action': action, 'result': message})


def interact_generated(state, action, mission):
    rules = mission['rules']
    if action in mission['evidence']:
        if action in state.seen:
            return
        state.seen.append(action)
        message = mission['evidence'][action]['result']
    elif action == 'hint':
        message = rules['hint']
    elif action in ('accept', 'question', 'reject'):
        state.ai = action
        if action == 'accept':
            interact_generated(state, rules['colleague']['action_id'], mission)
            message = 'Accepted the colleague suggestion and applied its simulated action.'
        else:
            message = 'Questioned the suggestion; gather observations before choosing an action.'
    elif action in mission['actions']:
        entry = next(a for a in rules['actions'] if a['id'] == action)
        state.verified = False
        state.resolved = entry['resolves']
        state.supported_fix = state.resolved and set(entry['requires']).issubset(state.seen)
        message = entry['result']
    elif action == 'verify':
        state.verified = state.resolved
        message = rules['verification']['success' if state.resolved else 'failure']
    else:
        raise ValueError('Unknown simulation action.')
    state.history.append({'action': action, 'result': message})

RUBRIC = {
    'Scope': 'Ask about other websites AND another device.',
    'Evidence': 'Inspect the browser error AND compare DNS results.',
    'Supported action': 'Gather scope and DNS evidence BEFORE refreshing cached DNS.',
    'AI check': 'Question or reject the unsupported firewall suggestion.',
    'Verification': 'Test portal access successfully after the simulated fix.'
}

def rubric_for(mission):
    if not mission or 'rules' not in mission:
        return RUBRIC
    rules = mission['rules']
    labels = lambda category: '; '.join(e['label'] for e in rules['evidence'] if e['category'] == category)
    return {'Scope': 'Gather scope observations: ' + labels('scope'),
            'Evidence': 'Gather diagnostic observations: ' + labels('diagnostic'),
            'Supported action': 'Collect the scope and diagnostic evidence before applying the resolving action.',
            'AI check': 'Question or reject the unsupported colleague suggestion.',
            'Verification': rules['verification']['label'] + ' after resolving the issue.'}


def assess(state, explanation, mission=None):
    if not explanation.strip() or len(explanation) > 2000:
        raise ValueError('Write an explanation between 1 and 2,000 characters.')
    rules = mission.get('rules') if mission else None
    scope = {e['id'] for e in rules['evidence'] if e['category'] == 'scope'} if rules else {'websites', 'others'}
    diagnostics = {e['id'] for e in rules['evidence'] if e['category'] == 'diagnostic'} if rules else {'browser', 'dns'}
    criteria = {
        'Scope': scope.issubset(state.seen),
        'Evidence': diagnostics.issubset(state.seen),
        'Supported action': state.resolved and state.supported_fix,
        'AI check': state.ai in ('question', 'reject'),
        'Verification': state.verified
    }
    lower = explanation.lower()
    writing = {
        'Mentions cache action': bool(re.search(r'\b(refresh\w*|clear\w*|flush\w*)\b', lower)) and ('dns' in lower or 'cache' in lower),
        'Mentions verification': bool(re.search(r'\b(test\w*|verif\w*|check\w*|confirm\w*)\b', lower)) and ('portal' in lower or 'access' in lower)
    }
    if rules:
        mentions = lambda terms: any(re.search(r'(?<!\w)' + re.escape(t.casefold()) + r'(?!\w)', lower) for t in terms)
        writing = {'Mentions the action': mentions(rules['writing']['action_terms']),
                   'Mentions verification': mentions(rules['writing']['verification_terms'])}
    rubric = rubric_for(mission)
    missing = [rubric[k] for k, passed in criteria.items() if not passed]
    if not all(writing.values()):
        missing.append('Explain the action taken and how you checked the outcome.' if rules else 'Explain the cache action and how you checked portal access.')
    improvement = 'Explain which observations supported your action and how you verified the outcome.' if rules else 'Explain why the DNS discrepancy supports the chosen action.'
    return {'criteria': criteria, 'writing': writing, 'explanation': explanation,
            'history': deepcopy(state.history), 'dialogue': deepcopy(state.dialogue),
            'improvement': missing[0] if missing else improvement,
            'next_step': missing[0] if missing else 'Practice explaining this fix without unexplained acronyms.'}

def differences(first, second):
    changes = [f'{k}: {"observed" if first["criteria"][k] else "not observed"} → {"observed" if v else "not observed"}'
               for k, v in second['criteria'].items() if first['criteria'][k] != v]
    changes += [f'Writing check {k}: {first["writing"][k]} → {v}' for k, v in second['writing'].items() if first['writing'][k] != v]
    if first['explanation'] != second['explanation']:
        changes.append('Customer explanation revised.')
    return changes or ['No criterion or explanation changes.']
