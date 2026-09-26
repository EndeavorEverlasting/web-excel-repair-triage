#!/usr/bin/env python3
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / '.ai' / 'WORK_QUEUE.md'
ADOPTION = ROOT / '.ai' / 'work-ledger-adoption.json'
ISSUE_PROGRESSION = ROOT / '.ai' / 'issue-centered-work-progression.v1.json'
ISSUE_PROGRESSION_SCHEMA = 'issue-centered-work-progression/v1'
ISSUE_PROGRESSION_ID = 'web-excel-repair-triage.issue-centered-work-progression.v1'
PORTABLE_REPOSITORY = 'EndeavorEverlasting/BlacksmithGuild'
PORTABLE_ID = 'repo-ledger-interoperability'
PORTABLE_VERSION = 'RepoLedgerInteroperability.v1'
PORTABLE_COMMIT = '429237aa41d8712d71859865c9be407ca23d8580'
PORTABLE_PATH = '.tbg/workflows/repo-ledger-interoperability.contract.json'
PORTABLE_SCHEMA_PATH = '.tbg/harness/schemas/repo-ledger-adoption.schema.json'
DONOR_REPOSITORY = 'EndeavorEverlasting/AxTask'
DONOR_COMMIT = '9351c952b057ae4520b1ea0d388e1d8908f4c093'
DONOR_PATHS = [
    '.ai/README.md',
    '.ai/WORK_QUEUE.md',
    '.ai/authority.json',
    'scripts/ai-harness/validate-work-queue.mjs',
]
STATUSES = {'READY', 'CLAIMED', 'VERIFY', 'REVIEW', 'MERGE', 'OPERATOR', 'BLOCKED', 'DONE'}
CONTINUATION = {'READY', 'CLAIMED', 'VERIFY', 'REVIEW', 'MERGE'}
PRIORITIES = {'P0', 'P1', 'P2', 'P3'}
REQUIRED = [
    'Status', 'Priority', 'Owner', 'Work item', 'Branch / PR', 'Scope', 'Forbidden',
    'Dependencies', 'References', 'Acceptance gate', 'Gate', 'Last proof',
    'Next action', 'Updated',
]
TERMINAL = 'none; no safe actionable work remains'
UNASSIGNED_OWNERS = {'unclaimed', 'none', 'unknown', 'tbd', 'n/a'}
INVALID_ACCEPTANCE_GATES = {'none', 'unknown', 'tbd', 'pending', 'n/a'}
NON_ACTIONS = {
    TERMINAL, 'none', 'tbd', 'status unchanged', 'pr opened', 'tests passed',
    'ci green', 'wait', 'wait for review', 'review later', 'merge later', 'test later',
}
ACTIONABLE_NEXT = re.compile(
    r'^(?:(?:after|once)\b.+?,\s*)?(?:operator\s+)?'
    r'(?:run|execute|create|update|repair|resolve|merge|fetch|inspect|open|verify|'
    r'validate|test|commit|push|rebase|retarget|compare|generate|record|obtain|'
    r'install|apply|build|launch|deploy|restore|export|import|review|reconcile|'
    r'invoke|edit|write|move|copy|sync|check)\b',
    re.I,
)
EXACT_COMMIT = re.compile(r'^[0-9a-f]{40}$')
WORK_ITEM_PATTERNS = (
    re.compile(r'^issue:#\d+$'),
    re.compile(r'^ticket:[A-Za-z0-9._/-]+$'),
    re.compile(r'^ledger:TRQ-\d{3,}$'),
)
FORBIDDEN_WORK_ITEM_PREFIXES = (
    'pr:', 'branch:', 'worktree:', 'commit:', 'workflow:', 'run:', 'artifact:', 'merge:',
)
EXPECTED_AFK_STATES = {
    'READY': (False, True),
    'CLAIMED': (False, False),
    'VERIFY': (False, False),
    'REVIEW': (False, False),
    'MERGE': (False, False),
    'OPERATOR': (False, False),
    'BLOCKED': (False, False),
    'DONE': (True, False),
}


def durable_proof(value):
    return any(re.search(pattern, value, re.I) for pattern in (
        r'\b(?:commit|merge):[0-9a-f]{7,40}\b',
        r'\b(?:workflow|run):#?\d+\b',
        r'\bartifact:\S+',
        r'\boperator-proof:\S+',
    ))


def _repository_proof_path(candidate):
    normalized = candidate.rstrip(').')
    candidate_path = (ROOT / normalized).resolve()
    try:
        candidate_path.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return candidate_path


def non_merge_acceptance_proof(value, references):
    if re.search(r'\b(?:workflow|run):#?\d+\b', value, re.I):
        return True
    candidates = []
    candidates.extend(re.findall(r'\bartifact:([^\s;,]+)', value, re.I))
    candidates.extend(re.findall(r'\boperator-proof:([^\s;,]+)', value, re.I))
    for candidate in candidates:
        normalized = candidate.rstrip(').')
        proof_path = _repository_proof_path(normalized)
        if normalized in references and proof_path is not None and proof_path.exists():
            return True
    return False

def merge_integration_proof(value):
    return re.search(r'\bmerge:[0-9a-f]{7,40}\b', value, re.I) is not None


def validate_issue_progression_contract(path):
    errors = []
    if not path.is_file():
        return [f'missing issue progression contract: {path}']
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        return [f'invalid issue progression contract: {exc}']
    if payload.get('schema_version') != ISSUE_PROGRESSION_SCHEMA:
        errors.append('issue progression schema drifted')
    if payload.get('contract_id') != ISSUE_PROGRESSION_ID:
        errors.append('issue progression contract id drifted')
    if payload.get('owner') != '.ai/WORK_QUEUE.md':
        errors.append('issue progression owner must remain .ai/WORK_QUEUE.md')
    identity = payload.get('work_identity', {})
    if identity.get('canonical_unit') != 'work_item':
        errors.append('issue progression canonical unit must remain work_item')
    if identity.get('preferred_anchor') != 'issue':
        errors.append('issue progression preferred anchor must remain issue')
    if identity.get('allowed_anchor_patterns') != [
        r'^issue:#\d+$',
        r'^ticket:[A-Za-z0-9._/-]+$',
        r'^ledger:TRQ-\d{3,}$',
    ]:
        errors.append('issue progression allowed anchor patterns drifted')
    if tuple(identity.get('forbidden_anchor_prefixes', [])) != FORBIDDEN_WORK_ITEM_PREFIXES:
        errors.append('issue progression forbidden work-item prefixes drifted')
    ready_gate = payload.get('ready_gate', {})
    if ready_gate.get('gate_must_equal') != 'none':
        errors.append('READY gate must remain none')
    if ready_gate.get('dependencies_must_equal') != 'none':
        errors.append('READY dependencies must remain none')
    if 'BLOCKED or OPERATOR' not in str(ready_gate.get('unresolved_dependency_rule', '')):
        errors.append('READY unresolved dependency routing rule drifted')
    evidence = payload.get('execution_evidence', {})
    if evidence.get('ledger_field') != 'Branch / PR':
        errors.append('execution evidence must remain bound to Branch / PR')
    if evidence.get('role') != 'attempt_evidence_only':
        errors.append('Branch / PR must remain attempt evidence only')
    if evidence.get('may_change_without_changing_work_identity') is not True:
        errors.append('execution attempts must be replaceable without changing work identity')
    states = payload.get('afk_states')
    if not isinstance(states, list):
        errors.append('issue progression afk_states must be a list')
    else:
        observed = {}
        for state in states:
            if not isinstance(state, dict) or not state.get('id'):
                errors.append('issue progression contains malformed AFK state')
                continue
            observed[state['id']] = (state.get('terminal'), state.get('afk_dispatchable'))
        if observed != EXPECTED_AFK_STATES:
            errors.append('issue progression AFK state semantics drifted')
    done_gate = payload.get('done_gate', {})
    if done_gate.get('merged_pr_alone_sufficient') is not False:
        errors.append('merged PR alone must never satisfy DONE')
    required = done_gate.get('required')
    if not isinstance(required, list) or 'acceptance_gate_non_placeholder' not in required:
        errors.append('DONE gate must require a non-placeholder acceptance gate')
    if not isinstance(required, list) or 'durable_non_merge_validation_or_acceptance_proof' not in required:
        errors.append('DONE gate must require durable non-merge validation or acceptance proof')
    if not isinstance(required, list) or 'durable_merge_integration_proof' not in required:
        errors.append('DONE gate must require durable merge integration proof')
    return errors


def validate(ledger_path, adoption_path=ADOPTION):
    errors = []
    if not adoption_path.is_file():
        return [f'missing adoption manifest: {adoption_path}']
    try:
        adoption = json.loads(adoption_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        return [f'invalid adoption manifest: {exc}']

    canonical = adoption.get('canonicalContract', {})
    if canonical.get('repository') != PORTABLE_REPOSITORY:
        errors.append('canonical contract repository must be BlacksmithGuild')
    if canonical.get('id') != PORTABLE_ID:
        errors.append('unexpected canonical contract id')
    if canonical.get('version') != PORTABLE_VERSION:
        errors.append('unexpected canonical contract version')
    if canonical.get('pinnedCommit') != PORTABLE_COMMIT:
        errors.append('canonical contract pinnedCommit drifted; explicit compatibility update required')
    if not EXACT_COMMIT.fullmatch(canonical.get('pinnedCommit', '')):
        errors.append('canonical contract pinnedCommit must be a full exact SHA')
    if canonical.get('contractPath') != PORTABLE_PATH:
        errors.append('canonical contract path drifted')
    if canonical.get('schemaPath') != PORTABLE_SCHEMA_PATH:
        errors.append('canonical contract schema path drifted')

    local = adoption.get('local', {})
    issue_progression_ref = local.get('issueProgressionContract')
    expected_issue_progression = ISSUE_PROGRESSION.relative_to(ROOT).as_posix()
    if issue_progression_ref != expected_issue_progression:
        errors.append('local issueProgressionContract path drifted')
    errors.extend(validate_issue_progression_contract(ISSUE_PROGRESSION))

    donor = adoption.get('originalDonor', {})
    if donor.get('repository') != DONOR_REPOSITORY:
        errors.append('unexpected original donor repository')
    if donor.get('pinnedCommit') != DONOR_COMMIT:
        errors.append('original donor pinnedCommit drifted')
    if not EXACT_COMMIT.fullmatch(donor.get('pinnedCommit', '')):
        errors.append('original donor pinnedCommit must be a full exact SHA')
    if donor.get('authoritativePaths') != DONOR_PATHS:
        errors.append('original donor authoritativePaths drifted')

    for bad_ref in ('main', 'master', 'HEAD', 'v1.0.0', '429237aa41d8'):
        if EXACT_COMMIT.fullmatch(bad_ref):
            errors.append(f'symbolic/short contract ref unexpectedly accepted: {bad_ref}')

    if not ledger_path.is_file():
        return errors + [f'missing ledger: {ledger_path}']
    source = ledger_path.read_text(encoding='utf-8')
    for phrase in (
        f'portableContractRef: {PORTABLE_VERSION}@{PORTABLE_COMMIT}',
        f'canonicalContractCommit: {PORTABLE_COMMIT}',
        'Continuation states are not stopping states.',
        'Work item owns progression state.',
        'Branch / PR is execution evidence, not work identity.',
        'READY is AFK-dispatchable only when fully specified and dependency-ready.',
        'PR opened is not completion.',
        'Merged PR alone is not DONE.',
        'DONE is strict.',
        TERMINAL,
    ):
        if phrase not in source:
            errors.append(f'missing ledger contract phrase: {phrase}')
    malformed = re.findall(r'^##[ \t]+(TRQ-[^\r\n]+)\r?$', source, re.M)
    canonical_tasks = list(re.finditer(r'^##[ \t]+(TRQ-\d{3,})[ \t]+—[ \t]+([^\r\n]+)\r?$', source, re.M))
    for heading in malformed:
        if not re.fullmatch(r'TRQ-\d{3,}[ \t]+—[ \t]+[^\r\n]+', heading):
            errors.append(f'malformed TRQ heading: {heading}')
    if not canonical_tasks:
        errors.append('ledger must contain at least one canonical TRQ task block')
        return errors
    seen = set()
    for index, match in enumerate(canonical_tasks):
        task_id = match.group(1)
        if task_id in seen:
            errors.append(f'{task_id}: duplicate task id')
        seen.add(task_id)
        end = canonical_tasks[index + 1].start() if index + 1 < len(canonical_tasks) else len(source)
        block = source[match.start():end]
        fields = {}
        for field_match in re.finditer(r'^- \*\*([^*]+):\*\*[ \t]*([^\r\n]*)\r?$', block, re.M):
            field_name = field_match.group(1).strip()
            if field_name in fields:
                errors.append(f"{task_id}: duplicate field '{field_name}'")
                continue
            fields[field_name] = field_match.group(2).strip()
        for field in REQUIRED:
            if field not in fields:
                errors.append(f"{task_id}: missing field '{field}'")
            elif not fields[field]:
                errors.append(f"{task_id}: required field '{field}' must not be blank")
        status = fields.get('Status', '')
        priority = fields.get('Priority', '')
        owner = fields.get('Owner', '')
        work_item = fields.get('Work item', '')
        gate = fields.get('Gate', '')
        dependencies = fields.get('Dependencies', '')
        acceptance = fields.get('Acceptance gate', '')
        references = fields.get('References', '')
        proof = fields.get('Last proof', '')
        next_action = fields.get('Next action', '')
        if status and status not in STATUSES:
            errors.append(f"{task_id}: invalid status '{status}'")
        if priority and priority not in PRIORITIES:
            errors.append(f"{task_id}: invalid priority '{priority}'")
        if work_item:
            lowered_work_item = work_item.lower()
            if lowered_work_item.startswith(FORBIDDEN_WORK_ITEM_PREFIXES):
                errors.append(f'{task_id}: Work item must be an issue/ticket/ledger anchor, not execution evidence')
            elif not any(pattern.fullmatch(work_item) for pattern in WORK_ITEM_PATTERNS):
                errors.append(f'{task_id}: invalid Work item anchor')
            elif work_item.startswith('ledger:') and work_item != f'ledger:{task_id}':
                errors.append(f'{task_id}: ledger Work item anchor must match its task id')
        if status == 'READY':
            if gate != 'none':
                errors.append(f'{task_id}: READY is AFK-dispatchable only with Gate: none; use BLOCKED or OPERATOR for unresolved prerequisites')
            if dependencies != 'none':
                errors.append(f'{task_id}: READY is AFK-dispatchable only with Dependencies: none; move resolved dependency evidence to References/Last proof and use BLOCKED or OPERATOR for unresolved dependencies')
        if status == 'CLAIMED' and (not owner or owner.strip().lower() in UNASSIGNED_OWNERS):
            errors.append(f'{task_id}: CLAIMED requires a concrete owner')
        if status in CONTINUATION:
            normalized_next = next_action.strip().lower()
            if not next_action or normalized_next in NON_ACTIONS or not ACTIONABLE_NEXT.match(next_action):
                errors.append(f'{task_id}: continuation state requires an executable next action beginning with a concrete action verb')
        if status in {'BLOCKED', 'OPERATOR'} and (not gate or gate == 'none'):
            errors.append(f'{task_id}: {status} requires an exact Gate')
        if status == 'DONE':
            if not durable_proof(proof):
                errors.append(f'{task_id}: DONE requires durable Last proof')
            if acceptance.strip().lower() in INVALID_ACCEPTANCE_GATES:
                errors.append(f'{task_id}: DONE requires a non-placeholder Acceptance gate')
            if durable_proof(proof) and not non_merge_acceptance_proof(proof, references):
                errors.append(f'{task_id}: merged/committed code alone cannot satisfy DONE; durable validation/acceptance proof must be a workflow/run receipt or a declared existing artifact/operator-proof')
            if durable_proof(proof) and not merge_integration_proof(proof):
                errors.append(f'{task_id}: validation/acceptance proof alone cannot satisfy DONE; durable merge integration proof is required')
            if gate != 'none':
                errors.append(f'{task_id}: DONE requires Gate: none')
            if next_action != TERMINAL:
                errors.append(f'{task_id}: DONE requires canonical terminal Next action')
        for reference in re.findall(r'`([^`]+)`', fields.get('References', '')):
            if reference.startswith(('http://', 'https://', '#')) or any(ch in reference for ch in '*?'):
                continue
            if not (ROOT / reference).exists():
                errors.append(f'{task_id}: stale local reference: {reference}')
    return errors


def resolve_path(value):
    path = pathlib.Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def main():
    parser = argparse.ArgumentParser(description='Validate the repository-local shared work ledger.')
    parser.add_argument('--file', default=str(DEFAULT_LEDGER))
    parser.add_argument('--adoption', default=str(ADOPTION))
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args()
    ledger = resolve_path(args.file)
    adoption = resolve_path(args.adoption)
    errors = validate(ledger, adoption)
    if errors:
        print(f'[repository-work-ledger] FAIL ({len(errors)})', file=sys.stderr)
        for error in errors:
            print(f'- {error}', file=sys.stderr)
        return 1
    try:
        display_path = ledger.relative_to(ROOT)
    except ValueError:
        display_path = ledger
    print(
        f'[repository-work-ledger] PASS {display_path} '
        f'portable={PORTABLE_VERSION}@{PORTABLE_COMMIT[:12]} donor={DONOR_COMMIT[:12]} issue-centered=PASS stale-ref-probes=PASS'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
