"""Behavioral checks for compact context, durable updates, and portal approvals."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from urllib import request, error, parse

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


portal = load('portal')
fingerprints = load('fingerprint')
benchmark = load('benchmark_context')


def feature(identifier, **extra):
    return {'id': identifier, 'title': identifier.title(), 'kind': 'primary',
            'acceptance': ['Create and read ' + identifier], **extra}


def adopted(features=None, edges=None):
    state = portal.initial()
    state['proposal']['features'] = features or [feature('orders'), feature('products')]
    state['proposal']['edges'] = edges if edges is not None else [
        {'from': 'orders', 'to': 'products', 'reason': 'Order lines use products', 'operations': ['create order']}]
    state['baseline'] = {'proposal': copy.deepcopy(state['proposal']), 'questions': [], 'answers': {},
                         'selected': [f['id'] for f in state['proposal']['features'] if f['kind'] == 'primary']}
    state['phase'] = 'adopted'
    return state


class ContextTests(unittest.TestCase):
    def test_resume_context_stays_small_without_losing_feature_acceptance(self):
        result = benchmark.measure()
        self.assertLess(result['briefAndFeature'], result['fullState'] / 10)
        state = benchmark.sample_state()
        self.assertEqual(portal.feature_context(state, 'feature0')['feature']['acceptance'],
                         state['baseline']['proposal']['features'][0]['acceptance'])

    def test_no_work_is_authorized_before_adoption(self):
        state = portal.initial()
        state['proposal']['features'] = [feature('orders')]
        self.assertEqual(portal.due_checks(state)['track1'], [])
        self.assertTrue(portal.brief(state)['due']['adoptionRequired'])

    def test_integration_waits_for_all_direct_local_passes(self):
        state = adopted()
        state['progress']['orders'] = {'track1': {'status': 'passed'}}
        self.assertEqual(portal.due_checks(state)['track2'], [])
        state['progress']['products'] = {'track1': {'status': 'passed'}}
        self.assertEqual(portal.due_checks(state)['track2'], ['orders', 'products'])
        state['progress']['orders']['track2'] = {'status': 'passed'}
        self.assertEqual(portal.due_checks(state)['track2'], ['products'])

    def test_cycles_wait_only_for_local_passes(self):
        state = adopted(edges=[{'from': 'orders', 'to': 'products', 'reason': 'use'},
                               {'from': 'products', 'to': 'orders', 'reason': 'use'}])
        for key in ('orders', 'products'):
            state['progress'][key] = {'track1': {'status': 'passed'}}
        self.assertEqual(portal.due_checks(state)['track2'], ['orders', 'products'])

    def test_child_dependencies_resolve_to_primary_owner(self):
        state = adopted([feature('orders'), feature('products'),
                         feature('checkout', kind='secondary', parent='orders')],
                        [{'from': 'checkout', 'to': 'products', 'reason': 'price lookup'}])
        self.assertEqual(portal.dependency_ids(state, 'orders'), ['products'])
        state['progress']['orders'] = {'track1': {'status': 'passed'}, 'track2': {'status': 'passed'}}
        with self.assertRaisesRegex(ValueError, 'Track 2'):
            portal.validate(state)

    def test_feature_packet_excludes_unrelated_acceptance(self):
        state = adopted([feature('orders'), feature('products'), feature('reports')])
        packet = portal.feature_context(state, 'orders')
        self.assertEqual(packet['feature']['id'], 'orders')
        self.assertEqual(packet['dependencies'], ['products'])
        self.assertNotIn('reports', json.dumps(packet))
        with self.assertRaisesRegex(ValueError, 'Unknown feature'):
            portal.feature_context(state, 'missing')

    def test_queue_limit_reports_omissions_without_truncating_contracts(self):
        state = adopted([feature('f' + str(i)) for i in range(20)], [])
        result = portal.due_checks(state, 3)
        self.assertEqual(len(result['track1']), 3)
        self.assertEqual(result['omitted']['track1'], 17)
        self.assertEqual(portal.feature_context(state, 'f19')['feature']['acceptance'], ['Create and read f19'])

    def test_feature_update_preserves_other_features_and_tracks(self):
        state = adopted()
        state['progress'] = {'orders': {'track1': {'status': 'pending', 'evidence': ['log.txt']},
                                        'track2': {'status': 'pending'}},
                             'products': {'status': 'blocked'}}
        portal.apply_update(state, {'track1': {'status': 'passed'}}, 'orders')
        self.assertEqual(state['progress']['products'], {'status': 'blocked'})
        self.assertEqual(state['progress']['orders']['track1']['evidence'], ['log.txt'])
        self.assertEqual(state['progress']['orders']['track2']['status'], 'pending')

    def test_baseline_and_user_owned_fields_are_protected(self):
        for field in ('baseline', 'answers', 'revision', 'userDraft', 'plan2Approval', 'schemaVersion', 'updatedAt'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                portal.apply_update(adopted(), {field: {}})
        with self.assertRaisesRegex(ValueError, 'immutable'):
            portal.apply_update(adopted(), {'proposal': {}})

    def test_final_pass_requires_adoption_and_complete_tracks(self):
        state = portal.initial()
        state['finalChecks']['status'] = 'passed'
        with self.assertRaisesRegex(ValueError, 'adopted'):
            portal.validate(state)
        state = adopted()
        state['finalChecks']['status'] = 'passed'
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            portal.validate(state)

    def test_brief_digest_is_stable_across_progress_updates(self):
        state = adopted()
        digest = portal.brief(state)['baseline']['digest']
        state['progress']['orders'] = {'status': 'inProgress'}
        self.assertEqual(portal.brief(state)['baseline']['digest'], digest)
        state['baseline']['answers']['currency'] = 'USD'
        self.assertNotEqual(portal.brief(state)['baseline']['digest'], digest)


class FingerprintTests(unittest.TestCase):
    def test_inputs_not_commit_or_unrelated_files_define_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'source.py').write_text('one')
            (root / 'test.py').write_text('check')
            (root / 'unrelated.py').write_text('other')
            def digest(files=('source.py', 'test.py'), command='test', context=('python=3.12',)):
                return fingerprints.fingerprint(root, files, command, context)['digest']
            original = digest()
            self.assertEqual(digest(('test.py', 'source.py')), original)
            (root / 'unrelated.py').write_text('changed')
            self.assertEqual(digest(), original)
            self.assertNotEqual(digest(command='different'), original)
            self.assertNotEqual(digest(context=('python=3.13',)), original)
            (root / 'source.py').write_text('two')
            self.assertNotEqual(digest(), original)
            with self.assertRaises(ValueError):
                fingerprints.fingerprint(root, ['missing.py'])
            with self.assertRaises(ValueError):
                fingerprints.fingerprint(root, [Path(directory).parent])


class CommandTests(unittest.TestCase):
    def test_revision_conflict_does_not_overwrite_state(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / 'state.json'
            script = [sys.executable, str(ROOT / 'scripts/portal.py')]
            subprocess.run([*script, 'init', '--state', str(state)], check=True, capture_output=True)
            patch = Path(directory) / 'patch.json'
            patch.write_text(json.dumps({'handoff': {'lastAction': 'Checked', 'nextAction': 'Continue'}}))
            update = [*script, 'update', '--state', str(state), '--revision', '1', '--input', str(patch)]
            first = subprocess.run(update, check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(first.stdout)['revision'], 2)
            stale = subprocess.run(update, capture_output=True, text=True)
            self.assertNotEqual(stale.returncode, 0)
            self.assertEqual(json.loads(state.read_text())['revision'], 2)
            brief = subprocess.run([*script, 'brief', '--state', str(state)], check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(brief.stdout)['handoff']['nextAction'], 'Continue')


class PortalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'state.json'
        state = portal.initial()
        state['proposal']['features'] = [feature('orders'), feature('products'),
                                         feature('checkout', kind='secondary', parent='orders')]
        state['proposal']['edges'] = [{'from': 'checkout', 'to': 'products', 'reason': 'price lookup'}]
        state['questions'] = [{'id': 'currency', 'default': 'USD'}]
        state['readyForAdoption'] = True
        portal.write(self.path, state)
        self.process = subprocess.Popen([sys.executable, str(ROOT / 'scripts/portal.py'), 'serve',
                                         '--state', str(self.path), '--no-open'],
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        launch = self.path.parent / '.local/launchUrl'
        for _ in range(100):
            if launch.exists() and launch.stat().st_size:
                break
            if self.process.poll() is not None:
                self.fail('Portal process exited during startup')
            time.sleep(.03)
        self.assertTrue(launch.exists())
        url = parse.urlsplit(launch.read_text())
        self.origin = f'{url.scheme}://{url.netloc}'
        self.token = parse.parse_qs(url.fragment)['token'][0]

    def tearDown(self):
        self.process.terminate()
        self.process.wait(timeout=5)
        self.temp.cleanup()

    def call(self, path='/api/state', body=None, authorized=True, origin=True, extra=None):
        headers = dict(extra or {})
        if authorized:
            headers['Authorization'] = 'Bearer ' + self.token
        if origin:
            headers['Origin'] = self.origin
        payload = json.dumps(body).encode() if body is not None else None
        req = request.Request(self.origin + path, data=payload, headers=headers)
        try:
            response = request.urlopen(req, timeout=5)
        except error.HTTPError as result:
            response = result
        with response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None

    def test_authentication_and_origin_remain_required(self):
        self.assertEqual(self.call(authorized=False)[0], 403)
        self.assertEqual(self.call('/api/draft', {'revision': 1, 'draft': {}}, origin=False)[0], 403)
        self.assertEqual(self.call('/api/state', extra={'Host': 'untrusted.example'})[0], 403)
        self.assertEqual(self.call()[0], 200)

    def test_unchanged_poll_has_no_body_and_changed_state_is_returned(self):
        self.assertEqual(self.call(extra={'If-None-Match': '"1"'}), (304, None))
        status, state = self.call('/api/draft', {'revision': 1, 'draft': {'answers': {'currency': 'EUR'}}})
        self.assertEqual(status, 200)
        self.assertEqual(state['revision'], 2)
        self.assertEqual(self.call(extra={'If-None-Match': '"1"'})[0], 200)

    def test_adoption_defaults_and_immutable_snapshot(self):
        status, state = self.call('/api/adopt', {'revision': 1})
        self.assertEqual(status, 200)
        self.assertEqual(state['baseline']['answers']['currency'], 'USD')
        self.assertEqual(state['baseline']['selected'], ['orders', 'products'])
        self.assertEqual(self.call('/api/adopt', {'revision': 2})[0], 400)
        self.assertEqual(self.call('/api/draft', {'revision': 1, 'draft': {}})[0], 409)
        self.assertEqual(self.call()[1]['baseline'], state['baseline'])

    def test_selected_scope_requires_secondary_owners_dependencies(self):
        status, result = self.call('/api/adopt', {'revision': 1, 'scopeMode': 'selected', 'selected': ['orders']})
        self.assertEqual(status, 400)
        self.assertIn('products', result['error'])
        self.assertIsNone(self.call()[1]['baseline'])

    def test_plan2_cannot_be_approved_early(self):
        self.assertEqual(self.call('/api/plan2', {'revision': 1, 'items': [{'id': 'extra'}]})[0], 400)

    def test_verified_baseline_allows_explicit_plan2_approval_once(self):
        status, state = self.call('/api/adopt', {'revision': 1})
        self.assertEqual(status, 200)
        patch = self.path.parent / 'patch.json'
        patch.write_text(json.dumps({
            'progress': {key: {'track1': {'status': 'passed'}, 'track2': {'status': 'passed'}}
                         for key in ('orders', 'products')},
            'finalChecks': {'status': 'passed'},
            'plan2': [{'id': 'extra', 'title': 'Export'}]}))
        subprocess.run([sys.executable, str(ROOT / 'scripts/portal.py'), 'update',
                        '--state', str(self.path), '--revision', str(state['revision']),
                        '--input', str(patch)], check=True, capture_output=True)
        revision = self.call()[1]['revision']
        status, state = self.call('/api/plan2', {'revision': revision,
                                               'items': [{'id': 'extra', 'proposal': 'Export CSV'}]})
        self.assertEqual(status, 200)
        self.assertEqual(state['plan2Approval']['items'][0]['proposal'], 'Export CSV')
        self.assertEqual(self.call('/api/plan2', {'revision': state['revision'],
                                                'items': [{'id': 'extra'}]})[0], 400)


if __name__ == '__main__':
    unittest.main()
