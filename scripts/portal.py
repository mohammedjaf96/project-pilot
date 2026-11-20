#!/usr/bin/env python3
"""Local Project Pilot portal. Standard library only; no telemetry or dependencies."""
import argparse
import copy
import hmac
import hashlib
import json
import os
from pathlib import Path
import secrets
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import webbrowser

LOCK = threading.RLock()
ASSET = Path(__file__).resolve().parent.parent / 'assets' / 'portal.html'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    data['revision'] = data.get('revision', 0) + 1
    data['updatedAt'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    handle, name = tempfile.mkstemp(dir=path.parent, prefix='.pilot-')
    try:
        with os.fdopen(handle, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def validate(data):
    if data.get('finalChecks', {}).get('status') == 'passed' and not data.get('baseline'):
        raise ValueError('Final checks require an adopted baseline')
    features = (data.get('baseline') or {}).get('proposal', data.get('proposal', {})).get('features', [])
    identifiers = [feature['id'] for feature in features]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError('Feature IDs must be unique')
    for feature in features:
        if feature.get('kind', 'primary') not in ('primary', 'secondary'):
            raise ValueError('Feature kind must be primary or secondary')
        if feature.get('kind') == 'secondary' and not any(
                parent['id'] == feature.get('parent') and parent.get('kind', 'primary') == 'primary'
                for parent in features):
            raise ValueError('Secondary feature requires a primary parent')
    if data.get('readyForAdoption'):
        if not features or any(not feature.get('acceptance') for feature in features if feature.get('kind', 'primary') == 'primary'):
            raise ValueError('Ready proposals require features and primary acceptance criteria')
    for edge in data.get('proposal', {}).get('edges', []):
        if edge['from'] not in identifiers or edge['to'] not in identifiers or not edge.get('reason'):
            raise ValueError('Each graph edge needs valid endpoints and a reason')
    baseline = data.get('baseline')
    if baseline:
        progress = data.get('progress', {})
        def passed(identifier, track):
            return progress.get(identifier, {}).get(track, {}).get('status') == 'passed'
        for identifier in baseline['selected']:
            if passed(identifier, 'track2'):
                required = dependency_ids(data, identifier)
                if not passed(identifier, 'track1') or any(not passed(other, 'track1') for other in required):
                    raise ValueError('Track 2 requires local passes for the feature and all direct dependencies')
        if data.get('finalChecks', {}).get('status') == 'passed':
            if any(not passed(identifier, 'track1') or not passed(identifier, 'track2') for identifier in baseline['selected']):
                raise ValueError('Final checks cannot pass while baseline feature tracks remain incomplete')


def initial():
    return {'schemaVersion': 1, 'revision': 0, 'phase': 'discovery',
            'language': 'en', 'direction': 'ltr', 'title': 'Project Pilot',
            'labels': {}, 'proposal': {'idea': '', 'features': [], 'edges': [], 'decisions': []},
            'questions': [], 'answers': {}, 'baseline': None, 'progress': {},
            'plan2': [], 'plan2Approval': None, 'handoff': {'lastAction': '', 'nextAction': ''},
            'blockers': [], 'finalChecks': {'status': 'pending'}, 'delivery': {}}


def proposal(data):
    return (data.get('baseline') or {}).get('proposal', data.get('proposal', {}))


def selected_features(data):
    selected = (data.get('baseline') or {}).get('selected')
    return [feature for feature in proposal(data).get('features', [])
            if feature.get('kind', 'primary') == 'primary'
            and (selected is None or feature['id'] in selected)]


def dependency_ids(data, identifier):
    features = {feature['id']: feature for feature in proposal(data).get('features', [])}
    def owner(value):
        return features[value].get('parent', value)
    return sorted({owner(edge['to']) for edge in proposal(data).get('edges', [])
                   if owner(edge['from']) == identifier and owner(edge['to']) != identifier})


def passed(data, identifier, track):
    return data.get('progress', {}).get(identifier, {}).get(track, {}).get('status') == 'passed'


def due_checks(data, limit=5):
    local, integrated = [], []
    if not data.get('baseline'):
        return {'track1': [], 'track2': [], 'omitted': {'track1': 0, 'track2': 0}, 'adoptionRequired': True}
    for feature in selected_features(data):
        identifier = feature['id']
        if not passed(data, identifier, 'track1'):
            local.append(identifier)
        elif not passed(data, identifier, 'track2') and all(
                passed(data, dependency, 'track1') for dependency in dependency_ids(data, identifier)):
            integrated.append(identifier)
    return {'track1': local[:limit], 'track2': integrated[:limit],
            'omitted': {'track1': max(0, len(local) - limit), 'track2': max(0, len(integrated) - limit)},
            'adoptionRequired': not bool(data.get('baseline'))}


def brief(data, limit=5):
    features = selected_features(data)
    baseline = data.get('baseline')
    digest = hashlib.sha256(json.dumps(baseline, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16] if baseline else None
    blockers = data.get('blockers', [])
    handoff = data.get('handoff', {})
    approval = data.get('plan2Approval')
    return {'revision': data['revision'], 'phase': data.get('phase'),
            'baseline': {'adopted': bool(baseline), 'digest': digest},
            'counts': {'total': len(features),
                       'track1': sum(passed(data, f['id'], 'track1') for f in features),
                       'both': sum(passed(data, f['id'], 'track1') and passed(data, f['id'], 'track2') for f in features)},
            'handoff': handoff, 'due': due_checks(data, limit),
            'blockers': blockers[:limit], 'omittedBlockers': max(0, len(blockers) - limit),
            'finalChecks': {'status': data.get('finalChecks', {}).get('status', 'pending')},
            'plan2': {'count': len(data.get('plan2', [])), 'approved': bool(approval)},
            'more': 'show --feature ID for scope/evidence; show --section FIELD for complete details'}


def feature_context(data, identifier):
    features = proposal(data).get('features', [])
    feature = next((item for item in features if item['id'] == identifier), None)
    if feature is None:
        raise ValueError('Unknown feature: ' + identifier)
    owner = feature.get('parent', identifier)
    related = {owner, identifier}
    edges = [edge for edge in proposal(data).get('edges', [])
             if edge['from'] in related or edge['to'] in related]
    dependencies = dependency_ids(data, owner)
    return {'revision': data['revision'], 'feature': feature,
            'children': [item for item in features if item.get('parent') == identifier],
            'dependencies': dependencies, 'edges': edges,
            'progress': {key: data.get('progress', {}).get(key, {}) for key in [owner, *dependencies]},
            'adopted': bool(data.get('baseline')),
            'selected': owner in {item['id'] for item in selected_features(data)}}


def apply_update(state, patch, identifier=None):
    if not isinstance(patch, dict):
        raise ValueError('Patch must be a JSON object')
    if identifier:
        if identifier not in {item['id'] for item in selected_features(state)}:
            raise ValueError('Feature update requires a selected primary feature')
        current = state.setdefault('progress', {}).setdefault(identifier, {})
        for key, value in patch.items():
            if key in ('track1', 'track2') and isinstance(value, dict):
                current[key] = {**current.get(key, {}), **value}
            else:
                current[key] = value
    else:
        for protected in ('baseline', 'answers', 'revision', 'plan2Approval', 'userDraft', 'schemaVersion', 'updatedAt'):
            if protected in patch:
                raise ValueError('Cannot overwrite protected field: ' + protected)
        if state['baseline'] and any(key in patch for key in ('proposal', 'questions')):
            raise ValueError('Adopted proposal/questions are immutable; append changes to Plan 2')
        state.update(patch)
    validate(state)


def serve(path, port, auto_open):
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, value, content='application/json'):
            payload = value.encode() if isinstance(value, str) else json.dumps(value, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', content + '; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def authorized(self):
            host = self.headers.get('Host', '')
            expected = f'127.0.0.1:{self.server.server_port}'
            return host == expected and hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + token)

        def do_GET(self):
            if self.headers.get('Host') != f'127.0.0.1:{self.server.server_port}':
                return self.reply(403, {'error': 'Invalid host'})
            if self.path == '/':
                return self.reply(200, ASSET.read_text(encoding='utf-8'), 'text/html')
            if self.path == '/api/state' and self.authorized():
                with LOCK:
                    state = read(path)
                    etag = '"' + str(state['revision']) + '"'
                    if self.headers.get('If-None-Match') == etag:
                        self.send_response(304)
                        self.send_header('ETag', etag)
                        self.send_header('Cache-Control', 'no-store')
                        self.end_headers()
                        return
                    return self.reply(200, state)
            return self.reply(403, {'error': 'Access denied'})

        def do_POST(self):
            origin = self.headers.get('Origin')
            expected = f'http://127.0.0.1:{self.server.server_port}'
            if not self.authorized() or origin != expected:
                return self.reply(403, {'error': 'Access denied'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 1048576:
                    raise ValueError('Invalid request size')
                body = json.loads(self.rfile.read(length))
                with LOCK:
                    state = read(path)
                    if body.get('revision') != state['revision']:
                        return self.reply(409, {'error': 'State changed; refresh and review before submitting'})
                    if self.path == '/api/draft':
                        draft = body.get('draft', {})
                        if not isinstance(draft, dict):
                            raise ValueError('Draft must be an object')
                        state['userDraft'] = draft
                    elif self.path == '/api/adopt':
                        if state['baseline']:
                            raise ValueError('Baseline already adopted; changes belong in Plan 2')
                        proposal = state['proposal']
                        if not proposal.get('features'):
                            raise ValueError('Agent must prepare the feature proposal first')
                        if not state.get('readyForAdoption'):
                            raise ValueError('Agent has not marked the proposal ready for adoption')
                        answers = {}
                        incoming = body.get('answers', {})
                        for question in state['questions']:
                            answer = incoming.get(question['id'])
                            answers[question['id']] = question.get('default') if answer is None or answer == '' else answer
                        primary = [f['id'] for f in proposal['features'] if f.get('kind', 'primary') == 'primary']
                        selected = body.get('selected', primary)
                        if body.get('scopeMode') != 'selected':
                            selected = primary
                        if not selected or not set(selected).issubset(primary):
                            raise ValueError('Select at least one valid primary feature')
                        # Include declared prerequisites; never hide additional required scope.
                        dependencies = {dependency for identifier in selected
                                        for dependency in dependency_ids(state, identifier)}
                        missing = (dependencies.intersection(primary)) - set(selected)
                        if missing:
                            raise ValueError('Required features must also be selected: ' + ', '.join(sorted(missing)))
                        state['answers'] = answers
                        state['baseline'] = {'proposal': copy.deepcopy(proposal), 'questions': copy.deepcopy(state['questions']),
                                             'answers': copy.deepcopy(answers), 'selected': selected,
                                             'adoptedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
                        state['phase'] = 'adopted'
                    elif self.path == '/api/plan2':
                        if state.get('plan2Approval'):
                            raise ValueError('Plan 2 approval is already recorded; use a new execution cycle')
                        if state['finalChecks'].get('status') != 'passed':
                            raise ValueError('Plan 2 execution approval is available after final verification')
                        chosen = body.get('items', [])
                        known = {item['id'] for item in state['plan2']}
                        if not chosen or any(item['id'] not in known for item in chosen):
                            raise ValueError('Select valid Plan 2 items')
                        state['plan2Approval'] = {'items': chosen, 'approvedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
                    else:
                        return self.reply(404, {'error': 'Unknown action'})
                    validate(state)
                    write(path, state)
                    return self.reply(200, state)
            except (ValueError, KeyError, TypeError) as error:
                self.reply(400, {'error': str(error)})

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    url = f'http://127.0.0.1:{server.server_port}/#token={token}'
    print('Portal listening on loopback. The private browser token is not logged.', flush=True)
    if auto_open:
        webbrowser.open(url)
    else:
        # Write launch URL to a private, untracked runtime file, never shared state.
        runtime = path.parent / '.local'
        runtime.mkdir(exist_ok=True)
        os.chmod(runtime, 0o700)
        target = runtime / 'launchUrl'
        target.write_text(url)
        os.chmod(target, 0o600)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init', 'update', 'show', 'brief', 'ready', 'serve'])
    parser.add_argument('--state', required=True, type=Path)
    parser.add_argument('--input', type=Path, help='JSON merge patch for update')
    parser.add_argument('--revision', type=int, help='Required for update; compare-and-swap')
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--section', help='Print only one top-level state field')
    parser.add_argument('--feature', help='Read one feature or update only its progress entry')
    parser.add_argument('--limit', type=int, default=5, help='Maximum entries per brief/ready queue')
    parser.add_argument('--no-open', action='store_true')
    args = parser.parse_args()
    if args.limit < 1:
        parser.error('--limit must be positive')
    if args.feature and args.command not in ('show', 'update'):
        parser.error('--feature is supported by show and update')
    if args.feature and args.section and args.section != 'progress':
        parser.error('--feature with --section supports progress only')
    path = args.state.resolve()
    # A shared lock file serializes CLI writers with the portal across processes on macOS/Linux.
    if os.name == 'nt':
        import msvcrt
    else:
        import fcntl
    # Each request/CLI update holds LOCK; acquire process lock for a complete transaction.
    class FileLock:
        def __enter__(self):
            path.parent.mkdir(parents=True, exist_ok=True)
            self.stream = (path.parent / '.pilot.lock').open('a+b')
            if os.name == 'nt':
                self.stream.seek(0, 2)
                if self.stream.tell() == 0:
                    self.stream.write(b'0')
                    self.stream.flush()
                self.stream.seek(0)
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_LOCK, 1)
            else:
                fcntl.flock(self.stream, fcntl.LOCK_EX)
        def __exit__(self, *unused):
            if os.name == 'nt':
                self.stream.seek(0)
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(self.stream, fcntl.LOCK_UN)
            self.stream.close()
    class CombinedLock:
        def __enter__(self):
            # Shared instance lock, not a fresh lock per request.
            thread_lock.acquire()
            self.file = FileLock()
            self.file.__enter__()
        def __exit__(self, *unused):
            self.file.__exit__()
            thread_lock.release()
    thread_lock = threading.RLock()
    global LOCK
    LOCK = CombinedLock()
    if args.command == 'serve':
        if not path.exists():
            parser.error('Initialize state first')
        return serve(path, args.port, not args.no_open)
    with LOCK:
        if args.command == 'init':
            if path.exists():
                parser.error('State already exists; use update')
            write(path, initial())
        elif args.command in ('show', 'brief', 'ready'):
            state = read(path)
            if args.command == 'brief':
                output = brief(state, args.limit)
            elif args.command == 'ready':
                output = due_checks(state, args.limit)
            elif args.feature:
                context = feature_context(state, args.feature)
                output = state.get('progress', {}).get(args.feature, {}) if args.section else context
            else:
                output = state.get(args.section) if args.section else state
            print(json.dumps(output, ensure_ascii=False, separators=(',', ':') if args.command in ('brief', 'ready') else None,
                             indent=None if args.command in ('brief', 'ready') else 2))
        elif args.command == 'update':
            if not args.input or args.revision is None:
                parser.error('update requires --input and --revision')
            state = read(path)
            if state['revision'] != args.revision:
                parser.error('Revision conflict; read latest state and merge changes')
            patch = read(args.input)
            try:
                apply_update(state, patch, args.feature)
            except ValueError as error:
                parser.error(str(error))
            write(path, state)
            print(json.dumps({'revision': state['revision'], 'updated': 'progress/' + args.feature if args.feature else list(patch)}, separators=(',', ':')))


if __name__ == '__main__':
    main()
