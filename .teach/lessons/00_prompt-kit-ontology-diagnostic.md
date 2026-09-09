# Diagnostic — Prompt Kit ontology

Status: DIAGNOSTIC ONLY — no mastery claim.

## Mastery target

Build a first-principles model that separates capability, skill, and prompt by ownership and change boundary rather than by filename or UI label.

## Evidence anchor

The repository currently models `skill-evaluation` as a capability with:
- an operation, inputs, outputs, proof ceiling, triggers, and an implementation kind;
- a linked `.ai/skills/skill-evaluation/SKILL.md` containing reusable procedure and judgment;
- an implementation that may itself be a Prompt Kit prompt.

This means the three labels cannot be safely treated as mutually exclusive file types or synonyms.

## Diagnostic question

Suppose the Prompt Kit has an item that means: **"Evaluate a target skill, create reproducible eval cases, repair valid weaknesses, and emit evidence."**

The repository exposes that operation as a capability, links a reusable `SKILL.md`, and can implement/orchestrate the operation through a Prompt Kit prompt.

Without defining the three terms formally yet, explain what *different responsibility* you think each layer should own. Focus on what would need to change if:
1. the underlying executable mechanism changed;
2. the reusable way an agent reasons through the work changed; or
3. the task-specific instructions handed to an agent changed.

Do not optimize for repository vocabulary. State the model you currently believe is true; the next lesson will test it against the evidence.
