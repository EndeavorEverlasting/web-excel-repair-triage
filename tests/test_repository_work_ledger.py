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
    command = ['python3', str(VALIDATOR)]
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
Work item owns progression state.
Branch / PR is execution evidence, not work identity.
READY is AFK-dispatchable only when fully specified and dependency-ready.
PR opened is not completion.
Merged PR alone is not DONE.
DONE is strict.
Canonical terminal action: none; no safe actionable work remains
'''


def task(**overrides):
    values = {
        'Status': 'READY', 'Priority': 'P1', 'Owner': 'unclaimed',
        'Work item': 'ledger:TRQ-900', 'Branch / PR': 'none', 'Scope': 'bounded test scope',
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
        self.assertIn('issue-centered=PASS', result.stdout)
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

    def test_issue_progression_contract_is_local_and_issue_centered(self):
        adoption = json.loads(ADOPTION.read_text(encoding='utf-8'))
        self.assertEqual(
            adoption['local']['issueProgressionContract'],
            '.ai/issue-centered-work-progression.v1.json',
        )
        contract = json.loads((ROOT / adoption['local']['issueProgressionContract']).read_text(encoding='utf-8'))
        self.assertEqual(contract['schema_version'], 'issue-centered-work-progression/v1')
        self.assertEqual(contract['work_identity']['canonical_unit'], 'work_item')
        self.assertEqual(contract['work_identity']['preferred_anchor'], 'issue')
        states = {state['id']: state for state in contract['afk_states']}
        self.assertTrue(states['READY']['afk_dispatchable'])
        self.assertFalse(states['CLAIMED']['afk_dispatchable'])
        self.assertTrue(states['DONE']['terminal'])
        self.assertFalse(contract['done_gate']['merged_pr_alone_sufficient'])

    def test_pr_or_branch_cannot_be_the_work_item_identity(self):
        for work_item in ('pr:#123', 'branch:feat/example', 'commit:1234567', 'merge:1234567'):
            with self.subTest(work_item=work_item):
                result = self.run_temp(task(**{'Work item': work_item}))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Work item must be an issue/ticket/ledger anchor', result.stderr)

    def test_issue_work_item_can_survive_pr_execution_evidence(self):
        result = self.run_temp(task(
            **{
                'Work item': 'issue:#614',
                'Branch / PR': 'feat/example / #615',
                'Next action': 'execute the bounded implementation attached to issue #614',
            }
        ))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_ledger_anchor_must_match_task_identity(self):
        result = self.run_temp(task(**{'Work item': 'ledger:TRQ-899'}))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ledger Work item anchor must match its task id', result.stderr)

    def test_merge_only_proof_cannot_make_work_item_done(self):
        result = self.run_temp(task(
            Status='DONE',
            Owner='agent-session',
            **{
                'Last proof': 'merge:1234567890abcdef1234567890abcdef12345678',
                'Next action': 'none; no safe actionable work remains',
            }
        ))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('merged/committed code alone cannot satisfy DONE', result.stderr)

    def test_validation_without_merge_cannot_make_work_item_done(self):
        result = self.run_temp(task(
            Status='DONE',
            Owner='agent-session',
            **{
                'Last proof': 'workflow:123456789',
                'Next action': 'none; no safe actionable work remains',
            }
        ))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('durable merge integration proof is required', result.stderr)
    def test_done_accepts_merge_plus_validation_evidence(self):
        result = self.run_temp(task(
            Status='DONE',
            Owner='agent-session',
            **{
                'Last proof': 'merge:1234567890abcdef1234567890abcdef12345678; workflow:123456789',
                'Next action': 'none; no safe actionable work remains',
            }
        ))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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
        result = self.run_temp(task(Status='DONE', Owner='agent-session', **{'Last proof': 'merge:1234567890abcdef1234567890abcdef12345678; workflow:123456789', 'Next action': 'none; no safe actionable work remains'}))
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


    def test_trq007_continuation_tracks_integrated_compute_authority_floor(self):
        ledger = (ROOT / '.ai' / 'WORK_QUEUE.md').read_text(encoding='utf-8')
        self.assertIn('merge:43b1953092b518fe3a76b5fe0bfab179f730e849', ledger)
        self.assertIn('merge:300d949fdcf79bbac018440a85052302d575bd2c', ledger)
        self.assertIn('merge:e0038eec048af029f6f27bb2f0dc70f875e09e06', ledger)
        self.assertIn('merge:0733897c0bde4bd0dc48e8aab9b043e9e62bc7aa', ledger)
        self.assertIn('Sprint 1+2+Gen2+ADP-00 INTEGRATED', ledger)
        self.assertIn('Next action:** Execute ADP-04', ledger)
        self.assertIn('ADP-01/02/03 INTEGRATED', ledger)
        self.assertIn('Sprint 2 repository/runtime-harness implementation is SAFE & EXECUTABLE', ledger)
        self.assertIn('PR #450 CLOSED not merged', ledger)
        self.assertNotIn('Sprint 1 is SAFE & EXECUTABLE', ledger)
        self.assertNotIn('build Sprint 1 under `harness/evals/compute-authority/`', ledger)

    def test_ledger_validator_commands_use_python3(self):
        validators = json.loads((ROOT / 'harness' / 'validators.v1.json').read_text(encoding='utf-8'))
        ledger_validators = [v for v in validators['validators']
                            if v['id'].startswith('repository-work-ledger-')]
        self.assertTrue(ledger_validators, 'Expected at least one ledger validator')
        for validator in ledger_validators:
            command = validator['command']
            self.assertTrue(
                command.startswith('python3 ') or ' python3 ' in command,
                f"Validator {validator['id']} must use 'python3', not bare 'python': {command}"
            )
            self.assertNotRegex(
                command,
                r'(?:^| )python (?!-)',
                f"Validator {validator['id']} uses bare 'python' which may not exist on all systems: {command}"
            )

    def test_ledger_workflow_steps_use_python3(self):
        workflow = (ROOT / '.github' / 'workflows' / 'repository-work-ledger-contract.yml').read_text(encoding='utf-8')
        lines = workflow.split('\n')
        for i, line in enumerate(lines):
            if 'run:' in line and 'python ' in line:
                self.assertNotRegex(
                    line,
                    r'python\s+(?!-m\s+pip)',
                    f"Line {i+1} in repository-work-ledger-contract.yml uses bare 'python' instead of 'python3': {line.strip()}"
                )
                if 'repository_work_ledger' in line or 'test_repository_work_ledger' in line:
                    self.assertIn(
                        'python3',
                        line,
                        f"Line {i+1} in repository-work-ledger-contract.yml must use 'python3': {line.strip()}"
                    )


if __name__ == '__main__':
    unittest.main()
