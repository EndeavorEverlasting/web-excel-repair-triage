# AI Harness Prompt Kit V38 Self-Service Generation

## Mission

Generate `AI_Harness_Prompt_Kit_v38.xlsx` from the field-open V37 workbook without rebuilding or reserializing the package.

V38 owns one bounded workbook repair: every `P##_COPY_SAFE` tab receives clickable copy-range cells at `C1` and `C<last prompt row>`, and the existing calculation chain is synchronized. The Prompt Library already supplies the exact canonical `A1:A<n>` targets.

V38 also generates a separately validated local-agent prompt support file for converting a sprint into an executable local runtime build. The prompt is geared toward Cosmos by Augment, Cursor, Codex, and comparable coding agents with local filesystem and terminal access.

## Operator launchers

Users should not need to request commandlets or terminal snippets from an AI to generate or validate V38 assets.

### Generate the V38 assets

Double-click the repository-root launcher:

```text
Run-AIPromptKitV38.cmd
```

The launcher:

- resolves the repository from its own `%~dp0` location;
- accepts a V37 workbook or bundle by drag-and-drop, command-line argument, or interactive path prompt;
- invokes the committed V38 generator;
- preserves the generator exit code;
- prints the exact workbook, prompt, manifest, and bundle paths;
- pauses for Explorer users unless `WEB_EXCEL_NO_PAUSE` is set.

### Sync and validate the V38 implementation

Double-click:

```text
Sync-Validate-AIPromptKitV38.cmd
```

The launcher refuses a dirty worktree, fetches origin, switches to the canonical V38 branch, fast-forwards only, and runs the focused V38 contract suite. This replaces the former multi-command PowerShell handoff.

### Automation and advanced use

The root asset launcher also accepts optional arguments:

```text
Run-AIPromptKitV38.cmd <V37-workbook-or-bundle> [output-directory] [expected-prompt-count]
```

The implementation-level entrypoints remain available under `scripts/` and `triage/`, but they are not the normal operator path.

## Source contract

The workbook source may be:

- the field-open V37 `.xlsx`; or
- a delivery `.zip` containing exactly one V37 workbook.

The workbook source is never overwritten. The default output root is `Outputs/prompt_kit_v38/`.

The local-runtime prompt source and declarative registry are tracked at:

```text
prompts/v38/local-runtime-build.md
configs/prompt_kit/v38_prompt_assets.json
```

The registry and source prompt are validated before generated delivery artifacts are written.

## Generated artifacts

```text
AI_Harness_Prompt_Kit_v38.xlsx
AI_Harness_Prompt_Kit_v38_local_runtime_build.md
AI_Harness_Prompt_Kit_v38_manifest.json
AI_Harness_Prompt_Kit_v38_bundle.zip
```

Support files from an input bundle are preserved unless their names collide with canonical generated artifacts. Workbook binaries and operator-local reports remain generated outputs and must not be committed.

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

The local-runtime prompt is a delivery-bundle support file. It does not add a worksheet, change workbook topology, or weaken the accepted V37-to-V38 package boundary.

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
- the declarative prompt registry is malformed or inconsistent;
- the local-runtime prompt omits correct-directory discipline;
- the local-runtime prompt does not distinguish runtime construction from factoring;
- the local-runtime prompt does not require local execution after script creation;
- required commit, push, validation, safety, or proof-ceiling language is absent;
- deferred-work language such as `sit tight` is introduced.

The sync launcher also fails closed before fetching when the worktree contains local changes.

## Validation

The normal Windows validation surface is:

```text
Sync-Validate-AIPromptKitV38.cmd
```

CI additionally runs the prompt registry, CMD launcher contracts, copy-range links, V38 prompt assets, V38 generator, V33 compatibility, remaining prompt-kit validators, and CLI smoke checks.

## Compatibility posture

The older `prompt_kit_v33_*` modules remain compatibility internals on the stacked branch. They are not the canonical operator entrypoint for the accepted V37-to-V38 conversion.

The V38 runtime prompt is emitted outside the workbook because the field-open V37 package has 45 prompt worksheets and V38 is intentionally topology-preserving. A later explicitly versioned workbook-expansion sprint may promote this support prompt into a new prompt tab after Excel for Web acceptance and package-topology requirements are separately defined.

## Proof ceiling

Repository tests and the V38 manifest may prove exact formula generation, package boundaries, calculation-chain integrity, output naming, bundle construction, prompt-registry validation, CMD launcher contracts, local-runtime prompt validation, and byte idempotence. They do not prove that Cosmos by Augment, Cursor, Codex, or another local agent successfully executed a real repository sprint. Local agent execution, Excel for Web opening, and click-selection behavior remain separate runtime and field gates.
