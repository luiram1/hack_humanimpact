"""Occupation-specific exploration; only IT support has simulation content."""
import json
from functools import lru_cache
from models import ROOT, content, initial_journey

IT = '15-1232.00'

@lru_cache(maxsize=1)
def catalog():
    return json.loads((ROOT / 'data/prepared/careers.json').read_text(encoding='utf-8'))

def career_for(code):
    if code == IT:
        return content('career')
    entry = catalog()['occupations'].get(code)
    if entry is None:
        raise ValueError('Unknown occupation code.')
    # Certifications remain visible as source requirements, never inferred proficiency.
    rows = sorted((r for r in entry['skills'] if r['skill_type'] != 'Certification'),
                  key=lambda r: (-r['pct_postings'], r['skill_id']))
    selected, seen = [], set()
    for row in rows:
        if row['skill_id'] in seen:
            continue
        seen.add(row['skill_id'])
        label = row['skill_name']
        selected.append({'id': row['skill_id'], 'name': label,
                         'aliases': [label] if len(label.split()) > 1 else [],
                         'why': f"Requested in {row['pct_postings']:g}% of the selected occupational postings.",
                         'activity': 'Describe one example, your own action, and the result; identify what you still need to practice.'})
        if len(selected) == 6:
            break
    return {'onet': code, 'title': entry['name'], 'skills': selected}

def switch_career(journey, code):
    """Save separate career journeys; never carry an IT attempt into another occupation."""
    career_for(code)  # Validate before mutating state.
    previous = journey.get('profile', {}).get('onet', IT)
    if previous == code:
        return journey
    archives = journey.setdefault('career_journeys', {})
    from copy import deepcopy
    archives[previous] = deepcopy({k: v for k, v in journey.items() if k != 'career_journeys'})
    destination = deepcopy(archives.get(code, initial_journey()))
    destination['career_journeys'] = archives
    return destination
