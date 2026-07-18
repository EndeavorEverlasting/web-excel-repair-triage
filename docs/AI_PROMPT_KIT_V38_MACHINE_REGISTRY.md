# AI Harness Prompt Kit V38 Machine Registry

## Ownership

`web-excel-repair-triage` is the canonical producer and validator of the prompt registry. The Excel workbook remains the operator-facing view. AgentSwitchboard and other applications consume a pinned JSON snapshot; they do not silently rewrite prompt IDs, prompt text, variable contracts, or execution-surface doctrine.

## Tracked artifacts

- `registry/prompts/v38/prompt-registry.v1.json` — P00-P44 catalog and record-shard manifest extracted from the operator-provided `AI_Harness_Prompt_Kit_v38.xlsx`.
- `registry/prompts/v38/shards/*.json` — bounded full prompt-record shards referenced by the catalog.
- `registry/prompts/prompt-registry.v1.schema.json` — interchange schema for the catalog.
- `registry/prompts/prompt-record-shard.v1.schema.json` — interchange schema for each prompt-record shard.
- `configs/prompt_kit/v38_registry_variable_overrides.json` — definitions for placeholders used by V38 prompts but absent from the workbook's Variables tab.
- `triage/prompt_kit_registry.py` — read-only OOXML extractor and deterministic validator.
- `triage/prompt_kit_registry_store.py` — compact catalog/shard writer and integrity-verifying loader.

The workbook binary is not committed.

## Source evidence

- Source artifact: `AI_Harness_Prompt_Kit_v38.xlsx`
- Source SHA-256: `a9fc45b05669afc94e154f53759a723a5bf5827862fb1e38194926cc8ab3ef5a`
- Prompt IDs: P00-P44
- Prompt count: 45

The registry combines `Prompt_Library`, `Prompt_Sequence`, `Variables`, and each prompt's exact `P##_COPY_SAFE!A1:A<n>` text.

## Generate from a workbook

```powershell
python -m triage.prompt_kit_registry_store extract `
  "C:\Artifacts\AI_Harness_Prompt_Kit_v38.xlsx" `
  --variable-overrides configs/prompt_kit/v38_registry_variable_overrides.json `
  --out Outputs/prompt_kit_v38/registry
```

The extractor reads OOXML directly and does not save or reserialize the workbook.

## Validate a registry

```powershell
python -m triage.prompt_kit_registry_store validate registry/prompts/v38/prompt-registry.v1.json
python -m pytest tests/test_prompt_kit_registry.py -q
```

## Selection boundary

The registry explicitly distinguishes:

- `regular_ai_prompt` — content pasted into an interactive AI or coding-agent conversation;
- `gnhf_launch_artifact` — executable GNHF launch content with its own shell and bounding contract.

Consumers must preserve that distinction. A request for a GNHF prompt cannot be satisfied by selecting ordinary sprint prose.

## Proof ceiling

The tracked snapshot and tests prove deterministic registry structure, prompt identity, text hashes, variable closure, and execution-surface classification for the supplied V38 workbook. They do not prove Excel for Web acceptance, clipboard behavior, prompt quality in every model, provider availability, or successful repository execution.
