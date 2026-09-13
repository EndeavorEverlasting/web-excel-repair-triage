#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

REGISTRY = Path('registry/prompts/correspondence-prompts.v1.json')
TEST = Path('tests/test_correspondence_prompt_registry.py')

SECTION = '''EXHAUSTIVE AVAILABLE EDITING COMPUTE
- Brevity constrains the final output, not internal editing effort. Use all materially useful reasoning and iteration available within the current model/provider ceiling before returning the message.
- Treat the first sendable draft as a checkpoint, not an automatic stop. Silently test and, when useful, compare alternate phrasings against source fidelity, recipient need, factual and quantitative accuracy, actionability, tone, brevity, ambiguity, hidden commitment or question surfaces, and every prompt-specific proof condition.
- Continue until another safe editing pass is unlikely to materially improve an applicable criterion or would merely churn wording. The editing fixed point is evidence-defined, not pass-count-defined.
- Do not reveal scratch work, candidate variants, chain-of-thought, scoring, or edit narration. Exhaustive compute changes the depth of internal review, not the output contract.
- Extra compute never authorizes invented facts, commitments, dates, deadlines, motives, approvals, authority, recipient needs, or disclosure that the source does not support.'''.strip()

NEXT_SUFFIX = (
    " Before returning it, silently exhaust materially useful editing passes to an evidence-defined editing fixed point; "
    "the first sendable draft is a checkpoint, not the stop condition, and candidate variants or process narration must not appear in the output."
)

PROOF_SUFFIX = (
    "; exhaustive editing has reached an evidence-defined fixed point where another safe pass would not materially improve fidelity, recipient need, accuracy, actionability, tone, brevity, or the prompt-specific proof conditions"
)


def insert_before(content: str, anchor: str) -> str:
    if 'EXHAUSTIVE AVAILABLE EDITING COMPUTE' in content:
        return content
    if anchor not in content:
        raise SystemExit(f'missing insertion anchor: {anchor!r}')
    return content.replace(anchor, '\n\n' + SECTION + anchor, 1)


def update_registry() -> None:
    payload = json.loads(REGISTRY.read_text(encoding='utf-8'))
    prompts = payload.get('prompts')
    if not isinstance(prompts, list):
        raise SystemExit('correspondence registry prompts missing')
    by_id = {str(item.get('id')): item for item in prompts}
    if set(by_id) != {'P72', 'P73'}:
        raise SystemExit(f'unexpected correspondence prompt ids: {sorted(by_id)}')

    anchors = {'P72': '\n\nTONE\n', 'P73': '\n\nSTYLE\n'}
    for prompt_id in ('P72', 'P73'):
        prompt = by_id[prompt_id]
        prompt['copyContent'] = insert_before(str(prompt['copyContent']), anchors[prompt_id])
        if 'silently exhaust materially useful editing passes' not in str(prompt['nextStep']):
            prompt['nextStep'] = str(prompt['nextStep']).rstrip() + NEXT_SUFFIX
        if 'exhaustive editing has reached an evidence-defined fixed point' not in str(prompt['proofGate']):
            prompt['proofGate'] = str(prompt['proofGate']).rstrip().rstrip('.') + PROOF_SUFFIX + '.'

    REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def update_test() -> None:
    text = TEST.read_text(encoding='utf-8')
    anchor = '    def test_render_includes_correspondence_runtime_and_profile_tokens(self) -> None:\n'
    method = '''    def test_content_only_prompts_exhaust_editing_compute_without_repo_contract(self) -> None:\n        for prompt_id in ("P72", "P73"):\n            prompt = self.prompts[prompt_id]\n            content = prompt["copyContent"]\n            with self.subTest(prompt=prompt_id):\n                for phrase in (\n                    "EXHAUSTIVE AVAILABLE EDITING COMPUTE",\n                    "Brevity constrains the final output, not internal editing effort",\n                    "Treat the first sendable draft as a checkpoint, not an automatic stop",\n                    "editing fixed point is evidence-defined, not pass-count-defined",\n                    "Do not reveal scratch work, candidate variants, chain-of-thought",\n                    "Extra compute never authorizes invented facts",\n                ):\n                    self.assertIn(phrase, content)\n                self.assertIn(\n                    "silently exhaust materially useful editing passes",\n                    prompt["nextStep"],\n                )\n                self.assertIn(\n                    "exhaustive editing has reached an evidence-defined fixed point",\n                    prompt["proofGate"],\n                )\n                self.assertEqual(\n                    prompt["actionabilityPolicy"],\n                    "not-applicable:content-only",\n                )\n                self.assertNotIn(\n                    "ACTIONABLE NEXT COMMAND AND NEXT STEPS CONTRACT",\n                    content,\n                )\n                self.assertNotIn(\n                    "GREEN BRANCH INTEGRATION CONTRACT",\n                    content,\n                )\n\n'''
    if 'def test_content_only_prompts_exhaust_editing_compute_without_repo_contract' not in text:
        if anchor not in text:
            raise SystemExit('correspondence test insertion anchor missing')
        text = text.replace(anchor, method + anchor, 1)
    TEST.write_text(text, encoding='utf-8')


def main() -> int:
    update_registry()
    update_test()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
