import json
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / 'scripts' / 'validate_repository_work_ledger.py'
ADOPTION = ROOT / '.ai' / 'work-ledger-adoption.json'
PORTABLE_COMMIT = '429237aa41d8712d71859865c9be407ca23d8580'


def run_validator(path=None, adoption=None):
    command = ['python', str(VALIDATOR)]
    if path:
        command += ['--file', str(path)]
    if adoption:
        command += ['--adoption', str(adoption)]
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True)


HEADER = f'''portableContractRef: RepoLedgerInteroperability.v1@{PORTABLE_COMMIT}
canonicalContractCommit: {PORTABLE_COMMIT}
localAuthority: AGENTS.md

# Test ledger

Continuation states are not stopping states.
PR opened is not completion.
DONE is strict.
Canonical terminal action: none; no safe actionable work remains
'''


def task(**overrides):
    values = {
        'Status': 'READY', 'Priority': 'P1', 'Owner': 'unclaimed',
        'Branch / PR': 'none', 'Scope': 'bounded test scope',
        'Forbidden': 'production mutation', 'Dependencies': 'none',
        'References': '`AGENTS.md`', 'Acceptance gate': 'observable proof exists',
        'Gate': 'none', 'Last proof': 'none',
        'Next action': 'create the bounded artifact and validate it',
        'Updated': '2026-08-09',
    }
    values.update(overrides)
    body = '\n'.join(f'- **{key}:** {value}' for key, value in values.items())
    return f'{HEADER}\n## TRQ-900 — Test task\n\n{body}\n'


class RepositoryWorkLedgerTests(unittest.TestCase):
    def test_repository_ledger_passes(self):
        result = run_validator()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('portable=RepoLedgerInteroperability.v1@429237aa41d8', result.stdout)
        self.assertIn('stale-ref-probes=PASS', result.stdout)

    def test_canonical_contract_is_blacksmith_and_exact(self):
        adoption = json.loads(ADOPTION.read_text(encoding='utf-8'))
        canonical = adoption['canonicalContract']
        self.assertEqual(canonical['repository'], 'EndeavorEverlasting/BlacksmithGuild')
        self.assertEqual(canonical['id'], 'repo-ledger-interoperability')
        self.assertEqual(canonical['version'], 'RepoLedgerInteroperability.v1')
        self.assertEqual(canonical['pinnedCommit'], PORTABLE_COMMIT)
        self.assertRegex(canonical['pinnedCommit'], r'^[0-9a-f]{40}$')
        self.assertEqual(canonical['contractPath'], '.tbg/workflows/repo-ledger-interoperability.contract.json')
        self.assertEqual(canonical['schemaPath'], '.tbg/harness/schemas/repo-ledger-adoption.schema.json')

    def run_temp(self, content):
        with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, dir=ROOT, encoding='utf-8') as handle:
            handle.write(content)
            relative = pathlib.Path(handle.name).relative_to(ROOT)
        try:
            return run_validator(relative)
        finally:
            pathlib.Path(handle.name).unlink(missing_ok=True)

    def run_temp_adoption(self, mutator):
        adoption = json.loads(ADOPTION.read_text(encoding='utf-8'))
        mutator(adoption)
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, dir=ROOT, encoding='utf-8') as handle:
            json.dump(adoption, handle)
            relative = pathlib.Path(handle.name).relative_to(ROOT)
        try:
            return run_validator(adoption=relative)
        finally:
            pathlib.Path(handle.name).unlink(missing_ok=True)

    def test_symbolic_contract_pin_fails_closed(self):
        result = self.run_temp_adoption(lambda adoption: adoption['canonicalContract'].__setitem__('pinnedCommit', 'main'))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('canonical contract pinnedCommit drifted', result.stderr)
        self.assertIn('canonical contract pinnedCommit must be a full exact SHA', result.stderr)

    def test_wrong_contract_owner_fails_closed(self):
        result = self.run_temp_adoption(lambda adoption: adoption['canonicalContract'].__setitem__('repository', 'EndeavorEverlasting/AgentSwitchboard'))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('canonical contract repository must be BlacksmithGuild', result.stderr)

    def test_done_rejects_prose_proof(self):
        result = self.run_temp(task(Status='DONE', **{'Last proof': 'completed successfully', 'Next action': 'merge later'}))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('DONE requires durable Last proof', result.stderr)
        self.assertIn('DONE requires canonical terminal Next action', result.stderr)

    def test_done_accepts_durable_proof(self):
        result = self.run_temp(task(Status='DONE', Owner='agent-session', **{'Last proof': 'commit:1234567', 'Next action': 'none; no safe actionable work remains'}))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_operator_requires_gate(self):
        result = self.run_temp(task(Status='OPERATOR', Owner='operator', Gate='none'))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('OPERATOR requires an exact Gate', result.stderr)

    def test_stale_reference_fails(self):
        result = self.run_temp(task(References='`does/not/exist.txt`'))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('stale local reference', result.stderr)

    def test_malformed_task_heading_is_rejected(self):
        result = self.run_temp(HEADER + '\n## TRQ-9 - Hidden task\n\n- **Status:** READY\n' + task().split('# Test ledger\n', 1)[1])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('malformed TRQ heading', result.stderr)

    def test_duplicate_fields_are_rejected(self):
        content = task().replace('- **Status:** READY', '- **Status:** DONE\n- **Status:** READY', 1)
        result = self.run_temp(content)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate field 'Status'", result.stderr)

    def test_claimed_rejects_unassigned_owner_sentinels(self):
        for owner in ('unclaimed', 'none', 'unknown', 'tbd', 'n/a'):
            with self.subTest(owner=owner):
                result = self.run_temp(task(Status='CLAIMED', Owner=owner))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('CLAIMED requires a concrete owner', result.stderr)

    def test_continuation_rejects_non_action_next_steps(self):
        for next_action in ('status unchanged', 'PR opened', 'CI green', 'wait', 'merge later'):
            with self.subTest(next_action=next_action):
                result = self.run_temp(task(**{'Next action': next_action}))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('continuation state requires an executable next action', result.stderr)

    def test_continuation_accepts_concrete_action(self):
        result = self.run_temp(task(Status='VERIFY', Owner='agent-session', **{'Next action': 'run the local validator and record its workflow receipt'}))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_external_absolute_ledger_path_reports_success(self):
        with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8') as handle:
            handle.write(task())
            path = pathlib.Path(handle.name)
        try:
            result = run_validator(path)
        finally:
            path.unlink(missing_ok=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(str(path), result.stdout)


if __name__ == '__main__':
    unittest.main()
