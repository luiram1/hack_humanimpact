"""Session-local state. No user data is stored in shared files."""
from copy import deepcopy
from dataclasses import dataclass, field
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def content(name):
    return json.loads((ROOT / 'content' / f'{name}.json').read_text(encoding='utf-8'))

@dataclass
class MissionState:
    seen: list = field(default_factory=list)
    history: list = field(default_factory=list)
    ai: str = ''
    resolved: bool = False
    verified: bool = False
    supported_fix: bool = False

def initial_journey():
    return {'profile': {}, 'matches': [], 'decisions': {}, 'manual': [],
            'mission': MissionState(), 'attempts': [], 'revision_started': False,
            'draft': '', 'resource_notes': ''}

def begin_revision(journey):
    if len(journey['attempts']) != 1 or journey['revision_started']:
        raise ValueError('One revision is available after the first attempt.')
    journey['revision_started'] = True
    journey['mission'] = MissionState()

def snapshot(state):
    return deepcopy(state)
