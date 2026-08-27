#!/usr/bin/env python3
from pathlib import Path

path = Path('WORKFLOW.md')
text = path.read_text(encoding='utf-8')
replacements = {
    '**Workflow ID:** `prompt-kit-feedback-afk-routing`  \n': '**Workflow ID:** `prompt-kit-feedback-afk-routing`\n',
    '**Trigger:** `prompt-kit-actionable-feedback`  \n': '**Trigger:** `prompt-kit-actionable-feedback`\n',
    '**Capability:** `prompt-kit-feedback-afk-routing`  \n': '**Capability:** `prompt-kit-feedback-afk-routing`\n',
    '**Skill:** `.ai/skills/prompt-kit-feedback-afk-routing/SKILL.md`  \n': '**Skill:** `.ai/skills/prompt-kit-feedback-afk-routing/SKILL.md`\n',
}
for old, new in replacements.items():
    text = text.replace(old, new)
path.write_text(text, encoding='utf-8')
print('normalized AFK workflow markdown whitespace')
