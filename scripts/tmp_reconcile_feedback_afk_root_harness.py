#!/usr/bin/env python3
from pathlib import Path


def add_after(text: str, anchor: str, addition: str, label: str) -> str:
    if addition.strip() in text:
        return text
    if anchor not in text:
        raise SystemExit(f'{label} anchor missing: {anchor!r}')
    return text.replace(anchor, anchor + addition, 1)

validator_path = Path('scripts/validate_harness.py')
validator = validator_path.read_text(encoding='utf-8')
validator = add_after(
    validator,
    '    "prompt-kit-browser-proof-cleanup",\n',
    '    "prompt-kit-feedback-afk-routing",\n',
    'required workflow id',
)
validator = add_after(
    validator,
    '    "app-harness-validation",\n',
    '    "prompt-kit-feedback-afk-routing-audit",\n    "prompt-kit-feedback-afk-routing-tests",\n',
    'required validator ids',
)
validator = add_after(
    validator,
    '    "prompt-kit-responsive-layout",\n',
    '    "prompt-kit-feedback-afk-routing",\n',
    'required capability id',
)
validator = add_after(
    validator,
    '    "prompt-kit-responsive-overlap",\n',
    '    "prompt-kit-actionable-feedback",\n',
    'required trigger id',
)
validator = add_after(
    validator,
    '        "h-prompt-kit-browser-proof-scratch-cleanup",\n',
    '        "i-prompt-kit-feedback-afk-routing",\n',
    'allowed workflow anchor',
)
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
