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

Every P50–P55 prompt contains a directory gate. Repository commands must follow a verified `Set-Location` or `cd` command and `git rev-parse --show-toplevel` evidence.

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
3. Validate standard-AI P50–P55 ownership and directory gates.
4. Validate GNHF P45–P49 ownership and execution shapes.
5. Append P50–P55 before P45–P49.
6. Validate Prompt Library order, metadata, exact-range links, backlinks, and protection.
7. Validate workbook relationships, content types, app metadata, formula inventory, and calculation-chain equality.
8. Repeat generation and require byte-identical output.
9. Run focused repository tests and existing prompt-kit compatibility suites.
10. Perform a new Excel for Web field gate because V39 adds worksheets.

## Proof ceiling

Repository tests can prove prompt content, family ownership, section placement, directory discipline, GitHub CLI safety, package topology, formulas, calculation-chain integrity, source immutability, and deterministic generation.

They do not prove:

- Excel for Web opening or interaction;
- actual GNHF execution;
- actual GitHub repository creation;
- clone or push success;
- operator acceptance.
