#!/usr/bin/env python3
from pathlib import Path


def ensure_set_item(text: str, header: str, item: str) -> str:
    start = text.find(header)
    if start < 0:
        raise SystemExit(f'set header missing: {header!r}')
    close = text.find('\n}', start)
    if close < 0:
        raise SystemExit(f'set closing brace missing after: {header!r}')
    block = text[start:close]
    marker = f'    "{item}",'
    if marker in block:
        return text
    return text[:close] + f'\n{marker}' + text[close:]


def ensure_nested_set_item(text: str, header: str, item: str) -> str:
    start = text.find(header)
    if start < 0:
        raise SystemExit(f'nested set header missing: {header!r}')
    close = text.find('\n    }', start)
    if close < 0:
        raise SystemExit(f'nested set closing brace missing after: {header!r}')
    block = text[start:close]
    marker = f'        "{item}",'
    if marker in block:
        return text
    return text[:close] + f'\n{marker}' + text[close:]

validator_path = Path('scripts/validate_harness.py')
validator = validator_path.read_text(encoding='utf-8')
validator = ensure_set_item(validator, 'REQUIRED_WORKFLOW_IDS = {', 'prompt-kit-feedback-afk-routing')
validator = ensure_set_item(validator, 'REQUIRED_VALIDATOR_IDS = {', 'prompt-kit-feedback-afk-routing-audit')
validator = ensure_set_item(validator, 'REQUIRED_VALIDATOR_IDS = {', 'prompt-kit-feedback-afk-routing-tests')
validator = ensure_set_item(validator, 'REQUIRED_CAPABILITY_IDS = {', 'prompt-kit-feedback-afk-routing')
validator = ensure_set_item(validator, 'REQUIRED_TRIGGER_IDS = {', 'prompt-kit-actionable-feedback')
validator = ensure_nested_set_item(validator, '    allowed_anchors = {', 'i-prompt-kit-feedback-afk-routing')
validator_path.write_text(validator, encoding='utf-8')

hook_path = Path('.githooks/pre-push')
hook = hook_path.read_text(encoding='utf-8')
commands = (
    'python scripts/validate_prompt_kit_feedback_afk_routing.py --summary\n',
    'python -m unittest tests.test_prompt_kit_feedback_afk_routing -v\n',
)
anchor = 'python -m unittest tests.test_skill_prompt_registry -v\n'
if not all(command in hook for command in commands):
    if anchor not in hook:
        raise SystemExit('pre-push insertion anchor missing')
    missing = ''.join(command for command in commands if command not in hook)
    hook = hook.replace(anchor, anchor + missing, 1)
hook_path.write_text(hook, encoding='utf-8')

print('reconciled root harness pinned IDs, workflow anchor, and pre-push execution')
