import json
from models import ROOT

LIMITATIONS = '''Postings measure advertised demand, not hires or employment. GenAI demand is the share of postings explicitly requesting listed GenAI skills. AI exposure is not a probability of job loss, and exposure scores are fixed across years in this dataset. Broad AI-skill indicators include Python and are not direct measures of GenAI use. Top-ranked skills are not exhaustive occupational requirements. Posting-volume confidence flags are not statistical confidence intervals. Occupation demand cannot establish individual employability. Massachusetts aggregates do not establish Worcester-specific demand. These data do not establish experience requirements, wages, demographic effects, an apprenticeship shortage, or causal effects of AI. Demand for a skill does not validate this exact simulation.'''

def load_data(directory=None):
    directory = directory or ROOT / 'data' / 'prepared'
    actual = directory / 'evidence.json'
    path = actual if actual.exists() else directory / 'illustrative.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    for key in ('source', 'illustrative', 'profile', 'skills', 'skill_year', 'version'):
        if key not in data:
            raise ValueError(f'{path.name} is missing {key}; rerun data preparation.')
    if not data['profile'] or not data['skills']:
        raise ValueError('Prepared evidence is empty. Rerun data preparation.')
    return data

def skill_shares(data, skills):
    # Only exact labels; do not claim a related source skill is an identical construct.
    return {s['id']: max((float(row['pct_postings']) for row in data['skills']
                         if row['skill_name'].casefold() == s['name'].casefold()), default=0)
            for s in skills}
