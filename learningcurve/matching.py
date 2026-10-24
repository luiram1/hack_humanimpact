"""Conservative phrase suggestions, never proficiency verification."""
import re

MAX_EXPERIENCE_CHARS = 30_000

def suggest(text, skills):
    if len(text) > MAX_EXPERIENCE_CHARS:
        raise ValueError('Experience must be at most 30,000 characters.')
    sentences = [m.group(0).strip() for m in re.finditer(r'[^.!?\n]+(?:[.!?]+|(?=\n|$))', text)]
    result = []
    for skill in skills:
        for sentence in sentences:
            # Skip explicit negative claims rather than suggesting their inverse.
            if re.search(r"\b(no|not|never|haven't|didn't|cannot|can't)\b", sentence, re.I):
                continue
            alias = next((a for a in skill['aliases'] if re.search(
                r'(?<!\w)' + re.escape(a) + r'(?!\w)', sentence, re.I)), None)
            if alias:
                result.append({'id': skill['id'], 'sentence': sentence,
                               'explanation': f'The phrase “{alias}” may connect to {skill["name"].lower()}.'})
                break
    return result

def confirmed(journey):
    return [m for m in journey['matches'] if journey['decisions'].get(m['id']) == 'Confirm'] + journey['manual']

def prioritize(skills, evidence, shares):
    ids = {e['id'] for e in evidence}
    return sorted(skills, key=lambda s: (s['id'] in ids, -shares.get(s['id'], 0)))
