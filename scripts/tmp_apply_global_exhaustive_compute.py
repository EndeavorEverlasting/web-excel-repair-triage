#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

POLICY = Path('registry/prompts/actionable-next-step-policy.v1.json')
ACTION_TEST = Path('tests/test_actionable_prompt_registry.py')
P08_TEST = Path('tests/test_prompt_registry_expansion_regression_design_teach.py')

RULE_MARKER = 'EXHAUSTIVE AVAILABLE COMPUTE RULE'
RULE_BLOCK = '''EXHAUSTIVE AVAILABLE COMPUTE RULE
- Treat exhaustive available compute as authorized by default for Prompt Kit work unless the operator, governing contract, provider quota/cost boundary, safety rule, or execution environment imposes a tighter ceiling. Do not ask for permission to use more reasoning, tool calls, context, retries, variants, validation passes, or worker slots that are already available inside that ceiling.
- Exhaust the decision-relevant safe compute available before stopping. Do not conserve tokens, tool calls, context windows, retries, variants, worker slots, or validation passes on the operator's behalf while another practical pass can close a required contract, test or falsify a live hypothesis, cover an acceptance criterion, reduce material uncertainty, expose a regression, or strengthen proof.
- Exhaust the useful work surface, not arbitrary churn: sweep the acceptance criteria, end-state contract horizon, relevant hypothesis/failure space, affected protected controls, available evidence sources, and applicable proof surfaces. A fixed point is evidence-defined, not attempt-count-defined.
- Examples, minimum pass counts, bounded retries, or an earlier successful check are floors/controls, not ceilings. Do not stop merely because a stated minimum number of passes succeeded or because the first green result looks plausible.
- Order compute economically without minimizing it: run cheap/focused checks early to find defects quickly, then broader, adversarial, integration, and environment-dependent checks when they can materially change confidence or close a contract.
- When at least two meaningful lanes are independent, their writes do not conflict, and at least two usable worker/tool slots exist, dispatch them immediately and execute them concurrently. `Considered parallelism`, `could parallelize`, lane enumeration, or deferred parallelism is not execution evidence. Rejoin through one coordinator, synthesize the returned evidence, and rerun affected combined validation. If usable parallel capacity is absent, continue serially rather than inventing workers; state the exact capability ceiling only when it affects proof or closeout.
- Before declaring fixed point, perform one explicit residual-compute sweep: identify any still-unspent safe action that could materially improve correctness, coverage, evidence, integration, deployment, runtime observation, or operator acceptance. Execute every such action that is authorized and dependency-ready; otherwise classify it BLOCKED, UNSAFE, OUT OF SCOPE, or redundant with evidence.
- Exhaustive compute never expands mutation, safety, privacy, spending, credential, approval, or ownership authority. It increases depth inside the authorized envelope; it does not widen that envelope.
'''.strip()

SUFFIX_APPEND = (
    ' Treat exhaustive available compute as authorized by default unless an explicit operator, governing-contract, provider-quota/cost, safety, or environment ceiling says otherwise. '
    'Do not conserve tokens, tool calls, context, retries, variants, validation passes, or worker slots on the operator\'s behalf while decision-relevant safe work remains. '
    'Exhaust the useful acceptance/contract/hypothesis/proof surface, dispatch independent lanes concurrently when usable capacity exists, and stop only at an evidence-defined fixed point or exact ceiling/blocker—not at an arbitrary pass count or first green.'
)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f'{label}: anchor missing')
    return text.replace(old, new, 1)


def update_policy() -> None:
    policy = json.loads(POLICY.read_text(encoding='utf-8'))
    appendix = policy['copy_content_appendix']
    if RULE_MARKER not in appendix:
        anchor = '\n\nEND-STATE CONTRACT HORIZON\n'
        if anchor not in appendix:
            raise SystemExit('policy: END-STATE CONTRACT HORIZON anchor missing')
        appendix = appendix.replace(anchor, '\n\n' + RULE_BLOCK + anchor, 1)
        policy['copy_content_appendix'] = appendix
    if 'Treat exhaustive available compute as authorized by default' not in policy['next_step_suffix']:
        policy['next_step_suffix'] = policy['next_step_suffix'].rstrip() + SUFFIX_APPEND
    POLICY.write_text(json.dumps(policy, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def update_action_test() -> None:
    text = ACTION_TEST.read_text(encoding='utf-8')
    old = '''            "use as much safe available compute as is materially useful",\n            "first PASS as a checkpoint",\n'''
    new = '''            "use as much safe available compute as is materially useful",\n            "EXHAUSTIVE AVAILABLE COMPUTE RULE",\n            "Treat exhaustive available compute as authorized by default",\n            "Exhaust the decision-relevant safe compute available",\n            "Do not conserve tokens, tool calls, context windows",\n            "fixed point is evidence-defined, not attempt-count-defined",\n            "dispatch them immediately and execute them concurrently",\n            "residual-compute sweep",\n            "first PASS as a checkpoint",\n'''
    text = replace_once(text, old, new, 'actionability phrase tuple')

    old2 = '''                self.assertIn(marker, prompt["copyContent"])\n                self.assertIn(suffix, prompt["nextStep"])\n'''
    new2 = '''                self.assertIn(marker, prompt["copyContent"])\n                self.assertIn("EXHAUSTIVE AVAILABLE COMPUTE RULE", prompt["copyContent"])\n                self.assertIn("Exhaust the decision-relevant safe compute available", prompt["copyContent"])\n                self.assertIn("dispatch them immediately and execute them concurrently", prompt["copyContent"])\n                self.assertIn(suffix, prompt["nextStep"])\n'''
    text = replace_once(text, old2, new2, 'all-prompt inheritance assertions')

    old3 = '''        self.assertIn(\n            "A bounded sprint limits mutation scope, not useful compute volume",\n            self.policy["next_step_suffix"],\n        )\n'''
    new3 = '''        self.assertIn(\n            "A bounded sprint limits mutation scope, not useful compute volume",\n            self.policy["next_step_suffix"],\n        )\n        self.assertIn(\n            "Treat exhaustive available compute as authorized by default",\n            self.policy["next_step_suffix"],\n        )\n        self.assertIn(\n            "stop only at an evidence-defined fixed point or exact ceiling/blocker",\n            self.policy["next_step_suffix"],\n        )\n'''
    text = replace_once(text, old3, new3, 'next-step exhaustive assertions')
    ACTION_TEST.write_text(text, encoding='utf-8')


def update_p08_test() -> None:
    text = P08_TEST.read_text(encoding='utf-8')
    old = '''            "A bounded sprint limits mutation ownership and blast radius",\n            "Treat the first PASS as a checkpoint, not an automatic stop signal",\n'''
    new = '''            "A bounded sprint limits mutation ownership and blast radius",\n            "EXHAUSTIVE AVAILABLE COMPUTE RULE",\n            "Exhaust the decision-relevant safe compute available",\n            "dispatch them immediately and execute them concurrently",\n            "fixed point is evidence-defined, not attempt-count-defined",\n            "Treat the first PASS as a checkpoint, not an automatic stop signal",\n'''
    text = replace_once(text, old, new, 'P08 exhaustive assertions')
    P08_TEST.write_text(text, encoding='utf-8')


def main() -> int:
    update_policy()
    update_action_test()
    update_p08_test()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
