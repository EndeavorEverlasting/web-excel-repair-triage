# AI Harness Prompt Kit V39 — Prompt Segmentation Doctrine

## Mission

V39 extends the operator-accepted V38 workbook without repurposing established prompt IDs or mixing standard-AI prompts into the GNHF harness/runtime section.

The workbook is generated through direct OOXML package edits. It is not loaded or saved through Excel, LibreOffice, `openpyxl`, or another whole-workbook serializer.

## Authoritative distinction

Prompt family is determined by **semantic workflow ownership**, not only by command syntax.

### Standard AI

A standard-AI prompt is ordinary repo-aware AI instruction. It may analyze, implement, return local commands, or guide an operator, but it is not part of the Goodnight, Have Fun execution family.

V39 adds these standard-AI prompts:

- P50 — Directory-First Repository Command Guard
- P51 — Zero-Token Local Test Planner
- P52 — Repository Factoring Analyzer
- P53 — Repository Factoring Builder
- P54 — Local-Only Validation and Closeout
- P55 — GitHub CLI Repository Bootstrapper
- P56 — Context-to-Artifact Generator
- P57 — Portable Harness Discipline Executor

These prompts are physically contiguous and are inserted after P44.

### Goodnight, Have Fun (GNHF)

A GNHF-family prompt belongs to the GNHF compiler, harness, local-runtime, or environment workflow even when the payload does not literally begin with `gnhf`.

The established P45–P49 meanings are preserved:

- P45 — AI-to-GNHF Prompt Compiler
- P46 — GNHF Repo Harness Builder
- P47 — GNHF Harness Workflow Executor
- P48 — Cursor Local GNHF Runtime Executor
- P49 — GNHF and Development Agent Environment Auto-Configurator

P46 and P47 are raw bounded `gnhf` commands. P45, P48, and P49 remain in the GNHF family because of their workflow ownership.

## Workbook placement

The appended V39 order is intentionally:

```text
P50 P51 P52 P53 P54 P55 | P45 P46 P47 P48 P49
standard AI extension   | GNHF harness/runtime
```

Numeric sorting is not allowed to interleave the sections. Prompt IDs are stable contract identifiers, not a command to disregard semantic placement.

## Prompt Library sparse-navigation rule

The Prompt Library must provide navigation links in both the leftmost and rightmost columns without filling every row.

The allowed cadences are every 10, 5, or 2 prompt rows. The generator chooses the **largest cadence that evenly divides the prompt count**, producing the fewest links while keeping a deterministic distribution:

1. use every 10th prompt row when the prompt count is divisible by 10;
2. otherwise use every 5th prompt row when divisible by 5;
3. otherwise use every 2nd prompt row when divisible by 2;
4. fail closed when none of those cadences divides the prompt count.

V39 contains 58 prompts, so it uses a cadence of 2. The selected rows in the upper half of the Prompt Library link to the bottom footer. Selected rows in the lower half link to the top header. The header always links to the bottom and the footer always links to the top. Column A targets column A, and column P targets column P.

Formula links and internal hyperlink metadata must agree. Rows outside the selected cadence remain blank in columns A and P. The footer label must state the current prompt count rather than retaining a stale version range.

## P55 GitHub CLI repository bootstrap

P55 is standard AI because it reasons about and returns or executes reviewed local Git and GitHub CLI commands; it does not launch GNHF.

It supports:

1. Creating a new remote and cloning it under a verified parent directory.
2. Publishing an explicitly selected existing local repository with `--source`, an explicit remote, and optional approved `--push`.

P55 requires:

- explicit owner/name;
- explicit visibility;
- verified parent or source directory;
- `git --version` and `gh --version`;
- `gh auth status --active --hostname github.com` without displaying tokens;
- collision checks through `gh repo view`;
- no automatic overwrite, force-push, deletion, public default, credential capture, release, or deployment;
- post-create remote, branch, commit, status, and visibility evidence.

Artifact generation does not itself create any GitHub repository.

## Directory-first contract

Every P50–P57 prompt contains a directory gate. Repository commands must follow a verified `Set-Location` or `cd` command and `git rev-parse --show-toplevel` evidence.

When no Git repository exists yet, P55 verifies the parent directory for clone mode. For publish-existing mode, it verifies the exact existing root, history, worktree, and remotes.

## Generate V39 locally

```powershell
Set-Location -LiteralPath "C:\path\to\web-excel-repair-triage"
git rev-parse --show-toplevel
.\scripts\Generate-AIPromptKitV39.ps1 `
  -Source "C:\Artifacts\AI_Harness_Prompt_Kit_v38.xlsx"
```

Generated outputs:

- `AI_Harness_Prompt_Kit_v39.xlsx`
- `AI_Harness_Prompt_Kit_v39_manifest.json`
- `AI_Harness_Prompt_Kit_v39_bundle.zip`

## Validation order

1. Parse both prompt contracts.
2. Confirm the source has the exact P00–P44 V38 prompt floor.
3. Validate standard-AI P50–P57 ownership and directory gates.
4. Validate GNHF P45–P49 ownership and execution shapes.
5. Append P50–P57 before P45–P49.
6. Validate Prompt Library order, metadata, exact-range links, backlinks, protection, and sparse edge navigation.
7. Validate workbook relationships, content types, app metadata, formula inventory, and calculation-chain equality.
8. Repeat generation and require byte-identical output.
9. Run focused repository tests and existing prompt-kit compatibility suites.
10. Perform a new Excel for Web field gate because V39 adds worksheets and navigation links.

## Proof ceiling

Repository tests can prove prompt content, family ownership, section placement, directory discipline, GitHub CLI safety, sparse navigation cadence, package topology, formulas, calculation-chain integrity, source immutability, and deterministic generation.

They do not prove:

- Excel for Web opening or interaction;
- actual GNHF execution;
- actual GitHub repository creation;
- clone or push success;
- operator acceptance.


## Whole-row Prompt Library links

Every prompt row uses columns **B:O** as one coherent navigation surface. Each cell preserves its displayed value while linking to the associated `P##_COPY_SAFE` tab and exact `A1:A<n>` copy range. Formula targets and worksheet hyperlink metadata must agree. Columns **A** and **P** remain reserved for deterministic sparse top/bottom navigation.

## Portable artifact and harness prompts

P56 generates the actual requested artifact from supplied context and repository evidence; outline-only, plan-only, and sample-only responses are invalid. P57 installs portable operational harness discipline, including the connected-GitHub mutation fallback, required run context, evidence-before-confidence, artifact proof, sequential prompt routing, and repository commit/PR evidence.

The machine-readable authority is `configs/harness/operational_discipline_v1.json`; `triage.harness_operational_discipline` and CI fail policy drift so external agents and other repositories can adopt the same contract.
