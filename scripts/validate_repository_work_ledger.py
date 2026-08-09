#!/usr/bin/env python3
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / '.ai' / 'WORK_QUEUE.md'
ADOPTION = ROOT / '.ai' / 'work-ledger-adoption.json'
STATUSES = {'READY', 'CLAIMED', 'VERIFY', 'REVIEW', 'MERGE', 'OPERATOR', 'BLOCKED', 'DONE'}
CONTINUATION = {'READY', 'CLAIMED', 'VERIFY', 'REVIEW', 'MERGE'}
PRIORITIES = {'P0', 'P1', 'P2', 'P3'}
REQUIRED = [
    'Status', 'Priority', 'Owner', 'Branch / PR', 'Scope', 'Forbidden',
    'Dependencies', 'References', 'Acceptance gate', 'Gate', 'Last proof',
    'Next action', 'Updated',
]
TERMINAL = 'none; no safe actionable work remains'
UNASSIGNED_OWNERS = {'unclaimed', 'none', 'unknown', 'tbd', 'n/a'}
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


def durable_proof(value):
    return any(re.search(pattern, value, re.I) for pattern in (
        r'\b(?:commit|merge):[0-9a-f]{7,40}\b',
        r'\b(?:workflow|run):#?\d+\b',
        r'\bartifact:\S+',
        r'\boperator-proof:\S+',
    ))


def validate(ledger_path):
    errors = []
    if not ADOPTION.is_file():
        return ['missing adoption manifest: .ai/work-ledger-adoption.json']
    adoption = json.loads(ADOPTION.read_text(encoding='utf-8'))
    if adoption.get('canonicalContract', {}).get('id') != 'agentswitchboard.repository-work-ledger.v1':
        errors.append('unexpected canonical contract id')
    if adoption.get('canonicalContract', {}).get('version') != '1.0.0':
        errors.append('unexpected canonical contract version')
    if not re.fullmatch(r'[0-9a-f]{40}', adoption.get('canonicalContract', {}).get('pinnedCommit', '')):
        errors.append('canonical contract pinnedCommit must be a full SHA')
    if adoption.get('originalDonor', {}).get('repository') != 'EndeavorEverlasting/AxTask':
        errors.append('unexpected original donor repository')
    if not ledger_path.is_file():
        return errors + [f'missing ledger: {ledger_path}']
    source = ledger_path.read_text(encoding='utf-8')
    for phrase in (
        'contractRef: agentswitchboard.repository-work-ledger.v1@1.0.0',
        f"canonicalContractCommit: {adoption['canonicalContract']['pinnedCommit']}",
        'Continuation states are not stopping states.',
        'PR opened is not completion.',
        'DONE is strict.',
        TERMINAL,
    ):
        if phrase not in source:
            errors.append(f'missing ledger contract phrase: {phrase}')
    malformed = re.findall(r'^##[ \t]+(TRQ-[^\r\n]+)\r?$', source, re.M)
    canonical = list(re.finditer(r'^##[ \t]+(TRQ-\d{3,})[ \t]+—[ \t]+([^\r\n]+)\r?$', source, re.M))
    for heading in malformed:
        if not re.fullmatch(r'TRQ-\d{3,}[ \t]+—[ \t]+[^\r\n]+', heading):
            errors.append(f'malformed TRQ heading: {heading}')
    if not canonical:
        errors.append('ledger must contain at least one canonical TRQ task block')
        return errors
    seen = set()
    for index, match in enumerate(canonical):
        task_id = match.group(1)
        if task_id in seen:
            errors.append(f'{task_id}: duplicate task id')
        seen.add(task_id)
        end = canonical[index + 1].start() if index + 1 < len(canonical) else len(source)
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
        gate = fields.get('Gate', '')
        proof = fields.get('Last proof', '')
        next_action = fields.get('Next action', '')
        if status and status not in STATUSES:
            errors.append(f"{task_id}: invalid status '{status}'")
        if priority and priority not in PRIORITIES:
            errors.append(f"{task_id}: invalid priority '{priority}'")
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


def main():
    parser = argparse.ArgumentParser(description='Validate the repository-local shared work ledger.')
    parser.add_argument('--file', default=str(DEFAULT_LEDGER))
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args()
    ledger = pathlib.Path(args.file)
    if not ledger.is_absolute():
        ledger = ROOT / ledger
    errors = validate(ledger)
    if errors:
        print(f'[repository-work-ledger] FAIL ({len(errors)})', file=sys.stderr)
        for error in errors:
            print(f'- {error}', file=sys.stderr)
        return 1
    print(f'[repository-work-ledger] PASS {ledger.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
