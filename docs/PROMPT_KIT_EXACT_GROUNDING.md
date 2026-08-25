# Prompt Kit JIT Exact Grounding Gate

## Owner and boundary

This is a narrow host-side extension of the existing Prompt Kit `CommandKernel` program seam. It protects **agent-generated command proposals** immediately before the existing kernel can perform clipboard, preference, or other registered command side effects.

The model proposes. The host retrieves current structure, validates provenance and exact values, runs a second deterministic consistency pass, and alone authorizes execution.

## Exactness-critical fields

| Field | Current authority | Why exact |
| --- | --- | --- |
| `type` | live `CommandKernel.handlers` registry | invented command names must never reach dispatch |
| `promptId` | live `PromptCatalog.byId` registry | invented/stale identifiers must never reach a handler |
| `source` | `harness/exact-grounding/agent-command-boundary.v1.json` | the agent gateway may not impersonate another entrypoint |

Open-ended prose, route choice, and whether an otherwise valid command is a good idea remain outside this deterministic gate.

## Grounding packet

`CommandKernelGroundingSource.buildPacket()` reads the current kernel/catalog maps and the versioned boundary contract just in time. The packet contains only the packet schema version; source ID, structural SHA-256 version, contract version/path; selected operation/source key; and the three required exact fields with resolvable source keys and current const/enum constraints.

The structural version hashes the current command names, prompt IDs, allowed boundary sources, and contract schema version. A catalog/registry change therefore invalidates an older proposal without loading the whole repository into model context.

## Fail-closed outcomes

- `GROUNDED_PASS` — all exact fields are current and attributed; only then may the host call `CommandKernel.execute()`.
- `UNSOURCED_BLOCK` — operation/provenance is absent or cannot resolve to the packet.
- `CONTRADICTION_BLOCK` — an attributed value contradicts the current registry/enum.
- `SCHEMA_MISMATCH` — proposal or grounding shape differs from the versioned boundary contract.
- `GROUNDING_FAILURE` — canonical structure/contract is malformed, unavailable, or stale; refresh is required.

No model critic can override one of these deterministic failures.

## Two-pass execution gate

`AgentCommandGroundingInterceptor.execute()` validates the proposal against a fresh grounding packet, then immediately repeats the validation and requires the same packet digest/source version before delegating exactly once to the existing command kernel. This is the adversarial consistency pass. A structure change between preparation and execution is a `GROUNDING_FAILURE`, not a warning.

## Proof ceiling

The fixture proves the Prompt Kit prototype boundary for current registered command names, prompt IDs, source enum, provenance, schema shape, stale structure, malformed grounding input, and exactly-once delegation. It does not prove arbitrary external API schemas, semantic wisdom of a valid action, production browser wiring, retry/idempotency after a valid side effect, or context-budget strategy.
