# AI Harness Prompt Kit V38 Self-Service Generation

## Mission

Generate `AI_Harness_Prompt_Kit_v38.xlsx` from the field-open V37 workbook without rebuilding or reserializing the package.

V38 owns one bounded workbook repair: every `P##_COPY_SAFE` tab receives clickable copy-range cells at `C1` and `C<last prompt row>`, and the existing calculation chain is synchronized. The Prompt Library already supplies the exact canonical `A1:A<n>` targets.

V38 also generates a separately validated local-agent prompt support file for converting a sprint into an executable local runtime build. The prompt is geared toward Cosmos by Augment, Cursor, Codex, and comparable coding agents with local filesystem and terminal access.

## Canonical commands

PowerShell:

```powershell
.\scripts\Generate-AIPromptKitV38.ps1 `
  -Source "C:\Artifacts\AI_Harness_Prompt_Kit_v37.xlsx"
```

Double-click-compatible CMD:

```text
scripts\Generate-AIPromptKitV38.cmd "C:\Artifacts\AI_Harness_Prompt_Kit_v37.xlsx"
```

Direct Python:

```powershell
python -m triage.prompt_kit_v38_generator `
  --source "C:\Artifacts\AI_Harness_Prompt_Kit_v37.xlsx" `
  --out-dir "Outputs\prompt_kit_v38" `
  --expected-prompt-count 45 `
  --json
```

Prompt asset only:

```powershell
python -m triage.prompt_kit_v38_prompt_assets `
  --out-dir "Outputs\prompt_kit_v38" `
  --json
```

## Source contract

The workbook source may be:

- the field-open V37 `.xlsx`; or
- a delivery `.zip` containing exactly one V37 workbook.

The workbook source is never overwritten. The default output root is `Outputs/prompt_kit_v38/`.

The local-runtime prompt source is tracked at:

```text
prompts/v38/local-runtime-build.md
```

The source prompt is validated before it is copied into the generated delivery artifacts.

## Generated artifacts

```text
AI_Harness_Prompt_Kit_v38.xlsx
AI_Harness_Prompt_Kit_v38_local_runtime_build.md
AI_Harness_Prompt_Kit_v38_manifest.json
AI_Harness_Prompt_Kit_v38_bundle.zip
```

Support files from an input bundle are preserved in the output bundle unless their names collide with canonical generated artifacts. Workbook binaries and operator-local reports remain generated outputs and must not be committed.

## Local runtime build prompt contract

The generated prompt is distinct from a factoring or prompt-authoring prompt. It instructs a local coding agent to turn an attached sprint into a real repository runtime and execute it.

The contract requires the agent to:

- identify and enter the correct local repository before commands are issued;
- prove the directory using `Get-Location` or `pwd` and `git rev-parse --show-toplevel`;
- recover missing or placeholder paths from workspace and Git evidence;
- name repo, branch/worktree, sprint, lane, owned scope, forbidden scope, artifacts, validation order, proof target, and proof ceiling;
- implement the runtime surface rather than only factoring or describing it;
- run the runtime locally after creating scripts;
- use disposable proof when real execution would expose credentials, private data, production systems, or destructive actions;
- run targeted validation, repository validators, hygiene checks, `git diff --check`, and final Git checks;
- commit, push, and open or update the PR when permitted;
- fail closed instead of claiming success from process exit, static validation, or uncommitted artifacts.

The prompt remains agent-neutral while explicitly naming Cosmos by Augment, Cursor, and Codex as intended local-agent surfaces. It does not rely on focus automation, product-specific UI control, provider authentication, or hidden chat context.

## Package boundary

The canonical V38 generator delegates workbook mutation to `triage.prompt_kit_copy_range_links`.

Allowed workbook changes:

- the 45 prompt worksheet parts;
- `xl/calcChain.xml`, when it already exists and needs the new formula entries.

Forbidden workbook changes include workbook metadata, relationships, content types, styles, shared strings, theme, properties, sheet order, protection, ZIP member set, and ZIP member order.

Excel automation, LibreOffice, `openpyxl`, and any other whole-workbook serializer are forbidden for this conversion.

The new local-runtime prompt is a delivery-bundle support file. It does not add a worksheet, change workbook topology, or weaken the accepted V37-to-V38 package boundary.

## Fail-closed gates

Generation fails when:

- the workbook source is missing or is not an `.xlsx`/single-workbook bundle;
- the Prompt Library exact range links are missing or malformed;
- the prompt-tab copy-label cells are absent;
- the discovered prompt count differs from 45 by default;
- fewer or more than 90 links are produced;
- a non-prompt worksheet part changes;
- calculation-chain identities are stale or incomplete;
- a second workbook generation pass is not byte-identical;
- the local-runtime prompt omits correct-directory discipline;
- the local-runtime prompt does not distinguish runtime construction from factoring;
- the local-runtime prompt does not require local execution after script creation;
- required commit, push, validation, safety, or proof-ceiling language is absent;
- deferred-work language such as `sit tight` is introduced.

## Validation

```powershell
python -m py_compile `
  triage/prompt_kit_v38_prompt_assets.py `
  triage/prompt_kit_v38_generator.py `
  tests/test_prompt_kit_v38_prompt_assets.py `
  tests/test_prompt_kit_v38_generator.py

python -m pytest `
  tests/test_prompt_kit_copy_range_links.py `
  tests/test_prompt_kit_v38_prompt_assets.py `
  tests/test_prompt_kit_v38_generator.py `
  -q

python -m triage.prompt_kit_v38_prompt_assets --help
python -m triage.prompt_kit_v38_generator --help
```

Then run the existing package, worksheet, copy-surface, operability, and Web Excel compatibility validators against the generated workbook.

## Compatibility posture

The older `prompt_kit_v33_*` modules remain compatibility internals on the stacked branch. They are not the canonical operator entrypoint for the accepted V37-to-V38 conversion.

The V38 runtime prompt is emitted outside the workbook because the field-open V37 package has 45 prompt worksheets and V38 is intentionally topology-preserving. A later explicitly versioned workbook-expansion sprint may promote this support prompt into a new prompt tab after Excel for Web acceptance and package-topology requirements are separately defined.

## Proof ceiling

Repository tests and the V38 manifest may prove exact formula generation, package boundaries, calculation-chain integrity, output naming, bundle construction, local-runtime prompt validation, and byte idempotence. They do not prove that Cosmos by Augment, Cursor, Codex, or another local agent successfully executed a real repository sprint. Local agent execution, Excel for Web opening, and click-selection behavior remain separate runtime and field gates.
