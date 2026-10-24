"""Deterministic simulation. No operating-system commands are executed."""
import re
from copy import deepcopy

def interact(state, action, mission):
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

RUBRIC = {
    'Scope': 'Ask about other websites AND another device.',
    'Evidence': 'Inspect the browser error AND compare DNS results.',
    'Supported action': 'Gather scope and DNS evidence BEFORE refreshing cached DNS.',
    'AI check': 'Question or reject the unsupported firewall suggestion.',
    'Verification': 'Test portal access successfully after the simulated fix.'
}

def assess(state, explanation):
    if not explanation.strip() or len(explanation) > 2000:
        raise ValueError('Write an explanation between 1 and 2,000 characters.')
    criteria = {
        'Scope': {'websites', 'others'}.issubset(state.seen),
        'Evidence': {'browser', 'dns'}.issubset(state.seen),
        'Supported action': state.resolved and state.supported_fix,
        'AI check': state.ai in ('question', 'reject'),
        'Verification': state.verified
    }
    lower = explanation.lower()
    writing = {
        'Mentions cache action': bool(re.search(r'\b(refresh\w*|clear\w*|flush\w*)\b', lower)) and ('dns' in lower or 'cache' in lower),
        'Mentions verification': bool(re.search(r'\b(test\w*|verif\w*|check\w*|confirm\w*)\b', lower)) and ('portal' in lower or 'access' in lower)
    }
    missing = [RUBRIC[k] for k, passed in criteria.items() if not passed]
    if not all(writing.values()):
        missing.append('Explain the cache action and how you checked portal access.')
    return {'criteria': criteria, 'writing': writing, 'explanation': explanation,
            'history': deepcopy(state.history),
            'improvement': missing[0] if missing else 'Explain why the DNS discrepancy supports the chosen action.',
            'next_step': missing[0] if missing else 'Practice explaining this fix without unexplained acronyms.'}

def differences(first, second):
    changes = [f'{k}: {"observed" if first["criteria"][k] else "not observed"} → {"observed" if v else "not observed"}'
               for k, v in second['criteria'].items() if first['criteria'][k] != v]
    changes += [f'Writing check {k}: {first["writing"][k]} → {v}' for k, v in second['writing'].items() if first['writing'][k] != v]
    if first['explanation'] != second['explanation']:
        changes.append('Customer explanation revised.')
    return changes or ['No criterion or explanation changes.']
