"""Scenario contracts, personalization, and session-local shift lifecycle."""
from copy import deepcopy
from hashlib import sha256
import json
from uuid import uuid4

from jsonschema import Draft202012Validator, ValidationError

from matching import confirmed
from models import MissionState, content


def obj(properties):
    return {'type': 'object', 'properties': properties, 'required': list(properties),
            'additionalProperties': False}


def string(limit=1500):
    return {'type': 'string', 'minLength': 1, 'maxLength': limit}


def array(items, minimum=1, maximum=12):
    return {'type': 'array', 'items': items, 'minItems': minimum, 'maxItems': maximum}


SCENARIO_SCHEMA = obj({
    'title': string(120), 'scenario': string(2000), 'customer_name': string(80),
    'customer_opening': string(600), 'ground_truth': string(), 'hint': string(600),
    'evidence': array(obj({
        'id': string(40), 'label': string(160), 'result': string(),
        'category': {'type': 'string', 'enum': ['scope', 'diagnostic']},
    }), 3, 8),
    'actions': array(obj({
        'id': string(40), 'label': string(160), 'result': string(),
        'resolves': {'type': 'boolean'}, 'requires': array(string(40), 0, 8),
    }), 3, 6),
    'verification': obj({'label': string(160), 'success': string(600), 'failure': string(600)}),
    'colleague': obj({'action_id': string(40), 'suggestion': string(600), 'critique': string(600)}),
    'writing': obj({'action_terms': array(string(50), 1, 8),
                    'verification_terms': array(string(50), 1, 8)}),
})


class SimulationError(ValueError):
    """A safe, user-facing simulation or generation error."""


def validate_scenario(raw):
    try:
        Draft202012Validator(SCENARIO_SCHEMA).validate(raw)
    except ValidationError as exc:
        raise SimulationError('The generated shift has an invalid format. Please try again.') from exc
    evidence_ids = [e['id'] for e in raw['evidence']]
    action_ids = [a['id'] for a in raw['actions']]
    reserved = {'verify', 'accept', 'question', 'reject', 'hint'}
    ids = evidence_ids + action_ids
    if len(set(ids)) != len(ids) or set(ids) & reserved:
        raise SimulationError('The generated shift has conflicting action identifiers. Please try again.')
    categories = {e['category'] for e in raw['evidence']}
    if categories != {'scope', 'diagnostic'}:
        raise SimulationError('The generated shift needs scope and diagnostic evidence. Please try again.')
    solutions = [a for a in raw['actions'] if a['resolves']]
    if len(solutions) != 1:
        raise SimulationError('The generated shift needs one clear resolution. Please try again.')
    for action in raw['actions']:
        if not set(action['requires']).issubset(evidence_ids):
            raise SimulationError('The generated shift references missing evidence. Please try again.')
    if set(solutions[0]['requires']) != set(evidence_ids):
        raise SimulationError('The generated resolution must be supported by all required evidence. Please try again.')
    suggested = next((a for a in raw['actions'] if a['id'] == raw['colleague']['action_id']), None)
    if suggested is None or suggested['resolves']:
        raise SimulationError('The colleague suggestion needs an evidence-based challenge. Please try again.')
    return deepcopy(raw)


def fingerprint(raw):
    # Ignore cosmetic title/name changes when detecting repeat situations.
    facts = [raw['ground_truth'], [e['result'] for e in raw['evidence']],
             [a['label'] for a in raw['actions']]]
    return sha256(json.dumps(facts, sort_keys=True).encode()).hexdigest()


def build_mission(raw, preferences):
    raw = validate_scenario(raw)
    return {
        'id': uuid4().hex, 'title': raw['title'], 'scenario': raw['scenario'],
        'ground_truth': raw['ground_truth'], 'customer_name': raw['customer_name'],
        'customer_opening': raw['customer_opening'], 'hint': raw['hint'],
        'evidence': {e['id']: {'label': e['label'], 'result': e['result']} for e in raw['evidence']},
        'actions': {a['id']: a['label'] for a in raw['actions']},
        'ai_suggestion': raw['colleague']['suggestion'],
        'provenance': 'AI-generated fictional practice shift; not an expert-reviewed assessment.',
        'rules': raw, 'preferences': deepcopy(preferences), 'fingerprint': fingerprint(raw),
    }


def practice_context(journey, topic='Surprise me', difficulty='Automatic'):
    from careers import career_for, IT
    career = career_for(journey['profile'].get('onet', IT))
    known = sorted({e['id'] for e in confirmed(journey)})
    skills = [s['id'] for s in career['skills']]
    previous = list(journey.get('completed_shifts', []))
    if journey['attempts']:
        previous.append({'attempts': journey['attempts']})
    latest = previous[-1]['attempts'][-1] if previous else None
    gaps = [k for k, passed in latest['criteria'].items() if not passed] if latest else []
    if difficulty == 'Automatic':
        difficulty = ('Challenge' if latest and all(latest['criteria'].values())
                      else 'Guided' if gaps or len(known) < 2 else 'Standard')
    return {'topic': topic, 'difficulty': difficulty,
            'occupation_code': career['onet'], 'occupation_title': career['title'],
            'source_skills': [{'id': s['id'], 'name': s['name']} for s in career['skills']],
            'practice_boundary': 'Use fictional, reversible workplace administration, planning, communication or document-checking tasks. No diagnosis, treatment, legal advice, investment advice, weapons, emergency response or hazardous physical procedures. High-stakes occupations must use administrative coordination only.',
            'minutes': journey['profile'].get('minutes', 30),
            'confirmed_skill_ids': known, 'practice_skill_ids': [s for s in skills if s not in known],
            'practice_gaps': gaps,
            'recent_situations': [s['scenario']['scenario'] for s in journey.get('completed_shifts', [])[-5:]]
                                + ([journey['active_scenario']['scenario']] if journey.get('active_scenario') else []),
            'variation_seed': uuid4().hex}


def start_shift(journey, mission):
    """Install only a fully generated shift; failed generation never clears progress."""
    if (journey['mission'].history or journey['mission'].dialogue or journey['draft'].strip()) and not journey['attempts']:
        raise SimulationError('Finish this shift before starting another one.')
    if journey.get('revision_started') and len(journey['attempts']) == 1:
        raise SimulationError('Submit your revision before starting another shift.')
    if journey['attempts']:
        journey.setdefault('completed_shifts', []).append(deepcopy({
            'scenario': journey.get('active_scenario') or content('mission'),
            'attempts': journey['attempts'],
        }))
    journey['active_scenario'] = deepcopy(mission)
    journey['mission'] = MissionState()
    journey['attempts'] = []
    journey['revision_started'] = False
    journey['draft'] = ''


def shift_records(journey, mission):
    records = list(journey.get('completed_shifts', []))
    if journey['attempts']:
        records.append({'scenario': mission, 'attempts': journey['attempts']})
    return records
