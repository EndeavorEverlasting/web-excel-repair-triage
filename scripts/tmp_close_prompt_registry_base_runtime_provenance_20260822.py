#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUNDING = ROOT / 'scripts' / 'prompt_registry_grounding.py'
TEST = ROOT / 'tests' / 'test_prompt_registry_grounding.py'
SPEC = ROOT / 'harness' / 'specs' / 'prompt-operations.md'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected one anchor, found {count}')
    return text.replace(old, new, 1)

text = GROUNDING.read_text(encoding='utf-8')
text = replace_once(
    text,
    '            ("html_builder", Path(registry_module.build_prompt_kit.__file__).resolve()),\n',
    '            ("runtime:base_prompt_kit", Path(registry_module.build_prompt_kit.JS_PATH)),\n'
    '            ("html_builder", Path(registry_module.build_prompt_kit.__file__).resolve()),\n',
    'base prompt kit runtime source',
)
GROUNDING.write_text(text, encoding='utf-8')

test = TEST.read_text(encoding='utf-8')
test = replace_once(
    test,
    '            "runtime:spec_architecture",\n            "html_builder",\n',
    '            "runtime:spec_architecture",\n            "runtime:base_prompt_kit",\n            "html_builder",\n',
    'base prompt kit runtime regression',
)
TEST.write_text(test, encoding='utf-8')

spec = SPEC.read_text(encoding='utf-8')
spec = replace_once(
    spec,
    'reference data, supplemental runtime JavaScript, the HTML builder module',
    'reference data, base and supplemental runtime JavaScript, the HTML builder module',
    'contract base runtime wording',
)
SPEC.write_text(spec, encoding='utf-8')
print('closed base prompt-kit runtime provenance gap')
