#!/usr/bin/env python3
"""Compare context characters on a synthetic project; never report model-token savings."""

import copy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import portal


def sample_state(count=60):
    state = portal.initial()
    features = []
    for index in range(count):
        identifier = 'feature' + str(index)
        features.append({'id': identifier, 'title': 'Feature ' + str(index), 'kind': 'primary',
                         'acceptance': [f'{operation} records with validation, permissions, and failure handling.'
                                        for operation in ('Create', 'Read', 'Update', 'Delete')],
                         'ownedPaths': [f'src/{identifier}.py', f'tests/test_{identifier}.py']})
        state['progress'][identifier] = {
            'track1': {'status': 'passed' if index < count // 2 else 'pending',
                       'changeIdentity': 'sha256:' + str(index).zfill(64),
                       'evidence': [f'.projectPilot/evidence/{identifier}-local.txt']},
            'track2': {'status': 'pending'}, 'nextCheck': 'Verify the recorded adopted operations'}
    state['proposal'] = {'idea': 'Synthetic multi-feature project for a repeatable context-size comparison.',
                         'features': features, 'edges': [], 'decisions': ['Use the existing project stack.']}
    state['baseline'] = {'proposal': copy.deepcopy(state['proposal']), 'questions': [], 'answers': {},
                         'selected': [feature['id'] for feature in features]}
    state['phase'] = 'execution'
    state['handoff'] = {'lastAction': 'Completed local verification for feature29.',
                        'nextAction': 'Verify integration for feature0.', 'featureId': 'feature0'}
    return state


def measure():
    state = sample_state()
    full = len(json.dumps(state, ensure_ascii=False, indent=2))
    summary = len(json.dumps(portal.brief(state), ensure_ascii=False, separators=(',', ':')))
    packet = len(json.dumps(portal.feature_context(state, 'feature0'), ensure_ascii=False, indent=2))
    return {'scenario': '60 synthetic primary features, four acceptance operations each',
            'unit': 'characters, not model tokens', 'fullState': full, 'resumeBrief': summary,
            'oneFeature': packet, 'briefAndFeature': summary + packet,
            'contextReductionPercent': round((1 - (summary + packet) / full) * 100, 2),
            'limits': 'Synthetic payload comparison only; actual tokens, repeated reads, and savings depend on the model and workflow.'}


if __name__ == '__main__':
    print(json.dumps(measure(), indent=2))
