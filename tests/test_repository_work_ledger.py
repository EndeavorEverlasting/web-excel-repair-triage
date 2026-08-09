import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / 'scripts' / 'validate_repository_work_ledger.py'


def run_validator(path=None):
    command = ['python', str(VALIDATOR)]
    if path:
        command += ['--file', str(path)]
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True)


HEADER = '''contractRef: agentswitchboard.repository-work-ledger.v1@1.0.0
canonicalContractCommit: caa32133e67ed2fed7ed643e4bb05570a2ef392f
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

    def run_temp(self, content):
        with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, dir=ROOT, encoding='utf-8') as handle:
            handle.write(content)
            relative = pathlib.Path(handle.name).relative_to(ROOT)
        try:
            return run_validator(relative)
        finally:
            pathlib.Path(handle.name).unlink(missing_ok=True)

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


if __name__ == '__main__':
    unittest.main()
