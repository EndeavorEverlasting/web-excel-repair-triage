from __future__ import annotations

import json
from pathlib import Path


def load(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump(path: str, obj) -> None:
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one target in {path}; found {count}: {old[:100]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# Durable receipt retention before overwrite.
replace_once(
    "scripts/Clear-PromptKitBrowserProofScratch.ps1",
    """New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ResolvedReportPath) | Out-Null
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ResolvedReportPath -Encoding UTF8

Write-Host (\"Prompt Kit browser-proof cleanup: mode={0} candidates={1} eligible={2} deleted={3} preserved={4} failed={5}\" -f $report.mode, $report.candidate_count, $report.eligible_count, $report.deleted_count, $report.preserved_count, $report.failed_count)
""",
    """New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ResolvedReportPath) | Out-Null
$previousReceiptBackup = $null
if (Test-Path -LiteralPath $ResolvedReportPath -PathType Leaf) {
    $backupRoot = Join-Path $OutputsRoot 'backups/prompt-kit-browser-proof-cleanup'
    New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
    $stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
    $backupName = '{0}_backup_{1}{2}' -f [System.IO.Path]::GetFileNameWithoutExtension($ResolvedReportPath), $stamp, [System.IO.Path]::GetExtension($ResolvedReportPath)
    $previousReceiptBackup = Join-Path $backupRoot $backupName
    Copy-Item -LiteralPath $ResolvedReportPath -Destination $previousReceiptBackup -Force -ErrorAction Stop
}
$report.previous_receipt_backup = $previousReceiptBackup
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ResolvedReportPath -Encoding UTF8

Write-Host (\"Prompt Kit browser-proof cleanup: mode={0} candidates={1} eligible={2} deleted={3} preserved={4} failed={5}\" -f $report.mode, $report.candidate_count, $report.eligible_count, $report.deleted_count, $report.preserved_count, $report.failed_count)
""",
)

# Domain contract now requires retained previous receipts.
domain_manifest = load("harness/browser-proof-cleanup/manifest.v1.json")
domain_manifest["scratch_contract"]["retain_previous_report_before_overwrite"] = True
dump("harness/browser-proof-cleanup/manifest.v1.json", domain_manifest)

domain_artifacts = load("harness/browser-proof-cleanup/artifacts.v1.json")
domain_artifacts["artifacts"][0]["overwrite_policy"] = "backup_previous_then_latest"
dump("harness/browser-proof-cleanup/artifacts.v1.json", domain_artifacts)
replace_once(
    "harness/browser-proof-cleanup/ARTIFACT_REGISTRY.md",
    "**Naming:** The default report path is stable so the newest operator run is easy to find. Historical retention is operator-owned; this harness does not create timestamped repository clutter automatically.",
    "**Naming:** The default report path is stable so the newest operator run is easy to find. Before overwriting an existing receipt, the runner preserves it under `Outputs/backups/prompt-kit-browser-proof-cleanup/` with a UTC timestamp.",
)

# Canonical skill structure.
Path(".ai/skills/prompt-kit-browser-proof-cleanup/SKILL.md").write_text(
    """---
name: prompt-kit-browser-proof-cleanup
description: Safely classify and remove detached Prompt Kit browser-proof scratch directories without touching canonical repositories, browser profile data, or Favorites.
---

# Prompt Kit Browser-Proof Cleanup

## Trigger

Use when the operator supplies a `prompt-kit-browser-proof-*` path under the OS temp directory or asks to classify/remove detached Prompt Kit browser-proof copies.

## Required inputs

- current repository checkout and governance;
- optional exact scratch path;
- preview versus explicit deletion intent;
- minimum age requirement when deletion is requested.

## Outputs

- classified candidate list;
- retained prior receipt when the stable report already exists;
- `Outputs/prompt-kit-browser-proof-cleanup-report.json`;
- exact eligible/preserved/deleted/failed counts and proof ceiling.

## Procedure

1. Read `AGENTS.md`, `harness/browser-proof-cleanup/manifest.v1.json`, and `harness/browser-proof-cleanup/WORKFLOW.md`.
2. Run `scripts/Clear-PromptKitBrowserProofScratch.ps1` without `-Apply` first.
3. Confirm each candidate is a direct child of the OS temp root, matches the exact browser-proof regex, is not a reparse point, contains `web/prompt-kit/index.html`, and meets minimum age.
4. Preserve every rejected candidate.
5. If deletion is explicitly requested, close browser tabs still using the file URL and rerun only the exact eligible target with `-Apply`.
6. Read the JSON receipt and report eligible/preserved/deleted/failed counts.
7. Do not claim browser site-data or Favorites cleanup.

## Guardrails

- Preview is the default; `-Apply` is explicit.
- Never widen an exact target into wildcard `%TEMP%` cleanup.
- Never delete a canonical checkout, `Outputs/` evidence, a reparse point, an unexpected name, or a directory missing the Prompt Kit marker.
- Never clear browser cookies/cache/history/profile, localStorage, or Prompt Kit Favorites.
- Preserve the previous stable cleanup receipt under `Outputs/backups/` before replacing it.

## Validation

```powershell
python scripts/validate_prompt_kit_browser_proof_cleanup.py --summary
python -m unittest tests.test_prompt_kit_browser_proof_cleanup_harness -v
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\Clear-PromptKitBrowserProofScratch.ps1
```

Exact apply after a successful preview:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\Clear-PromptKitBrowserProofScratch.ps1 -TargetPath "<exact path>" -MinimumAgeMinutes 0 -Apply
```

## Proof ceiling

Repository/static/CI proof plus the filesystem result recorded by the operator command. This skill does not prove browser localStorage, Favorites, or browser-profile cleanup.
""",
    encoding="utf-8",
)

# Root manifest and domain authority.
root_manifest = load("harness/manifest.v1.json")
root_manifest["domain_contracts"]["prompt_kit_browser_proof_cleanup"] = {
    "contract": "harness/browser-proof-cleanup/manifest.v1.json",
    "validator": "scripts/validate_prompt_kit_browser_proof_cleanup.py",
    "contract_tests": "tests/test_prompt_kit_browser_proof_cleanup_harness.py",
    "workflow": "WORKFLOW.md#h-prompt-kit-browser-proof-scratch-cleanup",
    "harness_gate": "python scripts/validate_prompt_kit_browser_proof_cleanup.py --summary",
    "skill": ".ai/skills/prompt-kit-browser-proof-cleanup/SKILL.md",
    "cleanup_runner": "scripts/Clear-PromptKitBrowserProofScratch.ps1",
    "artifact_registry": "harness/browser-proof-cleanup/artifacts.v1.json",
    "operator_report": "harness/browser-proof-cleanup/reports/CURRENT_STATE.md",
}
skill = ".ai/skills/prompt-kit-browser-proof-cleanup/SKILL.md"
if skill not in root_manifest["skills"]:
    root_manifest["skills"].append(skill)
dump("harness/manifest.v1.json", root_manifest)

# Capability and trigger.
caps = load("harness/capabilities.v1.json")
if not any(item["id"] == "prompt-kit-browser-proof-scratch-cleanup" for item in caps["capabilities"]):
    caps["capabilities"].append({
        "id": "prompt-kit-browser-proof-scratch-cleanup",
        "version": "1.0.0",
        "status": "canonical",
        "skill": skill,
        "trigger_ids": ["prompt-kit-browser-proof-temp-path"],
        "operation": "Preview, classify, retain receipts for, and explicitly remove only eligible detached Prompt Kit browser-proof scratch directories under the OS temp root.",
        "inputs": ["optional exact prompt-kit-browser-proof path", "OS temp root", "minimum age", "explicit apply intent"],
        "outputs": ["prompt-kit-browser-proof-cleanup-report", "preserved prior receipt when present", "eligible/preserved/deleted/failed counts"],
        "implementation": {"kind": "script", "path": "scripts/Clear-PromptKitBrowserProofScratch.ps1"},
        "proof_ceiling": "Filesystem classification and cleanup receipt only; browser profile/localStorage/Favorites state remains separate.",
    })
dump("harness/capabilities.v1.json", caps)

triggers = load("harness/triggers.v1.json")
if not any(item["id"] == "prompt-kit-browser-proof-temp-path" for item in triggers["triggers"]):
    triggers["triggers"].append({
        "id": "prompt-kit-browser-proof-temp-path",
        "capability_id": "prompt-kit-browser-proof-scratch-cleanup",
        "skill": skill,
        "workflow": "WORKFLOW.md#h-prompt-kit-browser-proof-scratch-cleanup",
        "conditions": ["operator supplies a prompt-kit-browser-proof-* path under the OS temp directory", "operator asks to classify or clear detached Prompt Kit browser-proof scratch copies"],
        "forbidden_conditions": ["broad OS temp cleanup is requested", "browser profile/localStorage/Favorites deletion is the actual request", "target is a canonical repository checkout or durable Outputs evidence"],
    })
dump("harness/triggers.v1.json", triggers)

# Workflow, artifact, validator registries.
workflows = load("harness/workflows.v1.json")
if not any(item["id"] == "prompt-kit-browser-proof-cleanup" for item in workflows["workflows"]):
    workflows["workflows"].append({
        "id": "prompt-kit-browser-proof-cleanup",
        "document": "WORKFLOW.md#h-prompt-kit-browser-proof-scratch-cleanup",
        "trigger": "An operator presents a detached prompt-kit-browser-proof-* Temp path or requests safe Prompt Kit browser-proof scratch classification/cleanup.",
        "owned_scope": ["browser-proof scratch classification", "preview/apply cleanup runner", "cleanup receipts and retained receipt backups", "focused validator/tests/skill/report"],
        "forbidden_scope": ["AGENTS.md", "Prompt Kit product behavior", "browser profile/localStorage/Favorites deletion", "broad temp deletion", "canonical checkout deletion"],
        "entry_points": ["scripts/Clear-PromptKitBrowserProofScratch.ps1", "scripts/validate_prompt_kit_browser_proof_cleanup.py", "harness/browser-proof-cleanup/manifest.v1.json"],
        "validation_profile": "target-repository",
        "failure_policy": "Fail closed and preserve the candidate when temp-root, name, marker, age, reparse-point, report-path, or deletion gates fail. Never widen cleanup scope to recover from a failure.",
        "handoff_fields": ["target path", "preview/apply mode", "eligible/preserved/deleted/failed counts", "receipt and backup paths", "proof ceiling", "next executable action"],
    })
dump("harness/workflows.v1.json", workflows)

artifacts = load("harness/artifacts.v1.json")
if not any(item["id"] == "prompt-kit-browser-proof-cleanup-report" for item in artifacts["artifacts"]):
    artifacts["artifacts"].append({
        "id": "prompt-kit-browser-proof-cleanup-report",
        "kind": "runtime",
        "canonical_path": "Outputs/prompt-kit-browser-proof-cleanup-report.json",
        "producer": "scripts/Clear-PromptKitBrowserProofScratch.ps1",
        "validator": "prompt-kit-browser-proof-cleanup-completeness",
        "naming": "Stable latest receipt; previous receipt is preserved under Outputs/backups/prompt-kit-browser-proof-cleanup/ with UTC timestamp.",
        "tracking_policy": "Gitignored operator evidence; never commit scratch directories or cleanup receipts.",
        "proof_ceiling": "Filesystem classification and cleanup receipt only; no browser-profile/localStorage/Favorites proof.",
    })
dump("harness/artifacts.v1.json", artifacts)

validators = load("harness/validators.v1.json")
validator_ids = {item["id"] for item in validators["validators"]}
new_validators = [
    {"id": "prompt-kit-browser-proof-cleanup-completeness", "class": "contract", "command": "python scripts/validate_prompt_kit_browser_proof_cleanup.py --summary", "blocking": True, "output": "process log", "proof_ceiling": "Static focused cleanup-harness completeness and safety-marker proof."},
    {"id": "prompt-kit-browser-proof-cleanup-tests", "class": "test", "command": "python -m unittest tests.test_prompt_kit_browser_proof_cleanup_harness -v", "blocking": True, "output": "process log", "proof_ceiling": "Executable focused cleanup contract regression proof."},
    {"id": "prompt-kit-browser-proof-cleanup-powershell-smoke", "class": "test", "command": "pwsh -NoLogo -NoProfile -File scripts/Clear-PromptKitBrowserProofScratch.ps1", "blocking": True, "output": "Outputs/prompt-kit-browser-proof-cleanup-report.json", "proof_ceiling": "PowerShell preview execution on the current host; not P-Top cleanup proof."},
]
for item in new_validators:
    if item["id"] not in validator_ids:
        validators["validators"].append(item)
dump("harness/validators.v1.json", validators)

# Root validator exact-ID authority and workflow anchor.
replace_once("scripts/validate_harness.py", '    "skill-evaluation",\n}', '    "skill-evaluation",\n    "prompt-kit-browser-proof-cleanup",\n}')
replace_once("scripts/validate_harness.py", '    "workbook-engine-output",\n}', '    "workbook-engine-output",\n    "prompt-kit-browser-proof-cleanup-report",\n}')
replace_once("scripts/validate_harness.py", '    "patch-hygiene-staged",\n}', '    "patch-hygiene-staged",\n    "prompt-kit-browser-proof-cleanup-completeness",\n    "prompt-kit-browser-proof-cleanup-tests",\n    "prompt-kit-browser-proof-cleanup-powershell-smoke",\n}')
replace_once("scripts/validate_harness.py", '    "technician-prompt-kit-acquisition",\n}', '    "technician-prompt-kit-acquisition",\n    "prompt-kit-browser-proof-scratch-cleanup",\n}')
replace_once("scripts/validate_harness.py", '    "technician-needs-latest-prompt-kit",\n}', '    "technician-needs-latest-prompt-kit",\n    "prompt-kit-browser-proof-temp-path",\n}')
replace_once("scripts/validate_harness.py", '        "g-skill-evaluation-build",\n    }', '        "g-skill-evaluation-build",\n        "h-prompt-kit-browser-proof-scratch-cleanup",\n    }')

# Human indexes and workflow.
replace_once("SKILLS.md", "## Required skill-file sections", """### Prompt Kit browser-proof cleanup

- **Path:** `.ai/skills/prompt-kit-browser-proof-cleanup/SKILL.md`
- **Trigger:** `prompt-kit-browser-proof-temp-path`
- **Capability:** `prompt-kit-browser-proof-scratch-cleanup`
- **Use when:** An operator presents a detached `prompt-kit-browser-proof-*` directory under the OS temp root or requests safe classification/removal of those browser-proof copies.
- **Forbidden scope:** Browser profile/localStorage/Favorites deletion, broad temp cleanup, canonical checkout deletion, product behavior changes.
- **Outputs:** Preview/apply receipt, retained prior receipt backup, classified candidates, and bounded filesystem proof.
- **Primary validation:** `python scripts/validate_prompt_kit_browser_proof_cleanup.py --summary` and `python -m unittest tests.test_prompt_kit_browser_proof_cleanup_harness -v`.

## Required skill-file sections""")
replace_once("CAPABILITIES.md", "| `technician-prompt-kit-acquisition` | `.ai/skills/technician-prompt-kit-acquisition/SKILL.md` | Existing public/Windows/Git acquisition surfaces | Device-aware access mode: public use, phone install, Windows local app, editable checkout, or ZIP snapshot. |", "| `technician-prompt-kit-acquisition` | `.ai/skills/technician-prompt-kit-acquisition/SKILL.md` | Existing public/Windows/Git acquisition surfaces | Device-aware access mode: public use, phone install, Windows local app, editable checkout, or ZIP snapshot. |\n| `prompt-kit-browser-proof-scratch-cleanup` | `.ai/skills/prompt-kit-browser-proof-cleanup/SKILL.md` | `scripts/Clear-PromptKitBrowserProofScratch.ps1` | Preview/apply cleanup receipt for exact eligible detached browser-proof scratch. |")
replace_once("CAPABILITIES.md", "## Proof boundaries", """## Browser-proof scratch cleanup capability

`prompt-kit-browser-proof-scratch-cleanup` owns only detached `prompt-kit-browser-proof-*` directories directly under the OS temp root. Preview is default; apply is explicit; rejected paths are preserved; prior stable receipts are backed up. Browser profile data, localStorage, Favorites, canonical repositories, public Pages, and unrelated Temp contents are outside this capability.

## Proof boundaries""")
replace_once("TRIGGERS.md", "| `technician-needs-latest-prompt-kit` | A user needs to open/use the Prompt Kit in a browser, install it on a phone/tablet, launch the Windows stable local app, obtain a source snapshot, or create/update an editable checkout for edit/commit/push work. | `technician-prompt-kit-acquisition` | Destructive Git cleanup or credential automation is proposed; or an editable checkout update is unsafe because the checkout is dirty, divergent, non-main, or has the wrong origin. |", "| `technician-needs-latest-prompt-kit` | A user needs to open/use the Prompt Kit in a browser, install it on a phone/tablet, launch the Windows stable local app, obtain a source snapshot, or create/update an editable checkout for edit/commit/push work. | `technician-prompt-kit-acquisition` | Destructive Git cleanup or credential automation is proposed; or an editable checkout update is unsafe because the checkout is dirty, divergent, non-main, or has the wrong origin. |\n| `prompt-kit-browser-proof-temp-path` | An operator supplies a `prompt-kit-browser-proof-*` path under OS Temp or asks to classify/remove detached Prompt Kit browser-proof scratch. | `prompt-kit-browser-proof-scratch-cleanup` | The real request is browser-site data/Favorites deletion, broad Temp cleanup, canonical-repo cleanup, or durable evidence deletion. |")
replace_once("TRIGGERS.md", "## Routing procedure", """## Browser-proof cleanup routing rule

A `file:///.../Temp/prompt-kit-browser-proof-<hex>/web/prompt-kit/index.html` path routes to the cleanup capability only after filesystem classification. Preview first. Do not translate this trigger into browser localStorage/Favorites deletion or generic Temp cleanup.

## Routing procedure""")
replace_once("WORKFLOW.md", "## 3. Validate before committing", """### H. Prompt Kit browser-proof scratch cleanup

**Workflow ID:** `prompt-kit-browser-proof-cleanup`  
**Trigger:** `prompt-kit-browser-proof-temp-path`  
**Capability:** `prompt-kit-browser-proof-scratch-cleanup`  
**Skill:** `.ai/skills/prompt-kit-browser-proof-cleanup/SKILL.md`

1. Treat `prompt-kit-browser-proof-*` folders as untrusted until the focused runner classifies them.
2. Run preview first; never broaden an exact target into `%TEMP%` deletion.
3. Require direct-child OS-temp location, exact leaf regex, non-reparse-point status, `web/prompt-kit/index.html`, and minimum age.
4. Preserve browser profile data, localStorage/Favorites, canonical repositories, public Pages, portable-loopback state, and unrelated evidence.
5. Before replacing the stable receipt, preserve the previous receipt under `Outputs/backups/prompt-kit-browser-proof-cleanup/`.
6. Run `python scripts/validate_prompt_kit_browser_proof_cleanup.py --summary` and `python -m unittest tests.test_prompt_kit_browser_proof_cleanup_harness -v`; native workstation deletion remains a separate runtime gate.

## 3. Validate before committing""")
replace_once("ARTIFACT_REGISTRY.md", "| Prompt Kit preview | `Outputs/prompt-kit-preview.html` or temp | builder preview mode | stable preview name | Never replace canonical site without parity. |", "| Prompt Kit preview | `Outputs/prompt-kit-preview.html` or temp | builder preview mode | stable preview name | Never replace canonical site without parity. |\n| Browser-proof cleanup receipt | `Outputs/prompt-kit-browser-proof-cleanup-report.json` | `scripts/Clear-PromptKitBrowserProofScratch.ps1` | stable latest receipt; previous copy under `Outputs/backups/prompt-kit-browser-proof-cleanup/` with UTC timestamp | Gitignored runtime evidence; scratch inputs are never canonical. |")
replace_once("CODEBASE_MAP.md", "## Build, test, and launch commands", """## Prompt Kit browser-proof scratch lifecycle

- `harness/browser-proof-cleanup/manifest.v1.json` — focused lifecycle authority for detached `prompt-kit-browser-proof-*` Temp copies.
- `scripts/Clear-PromptKitBrowserProofScratch.ps1` — preview-first, explicit-apply cleanup runner.
- `Outputs/prompt-kit-browser-proof-cleanup-report.json` — latest cleanup receipt; prior receipt retained under `Outputs/backups/prompt-kit-browser-proof-cleanup/`.
- Browser profile/localStorage/Favorites are intentionally separate from filesystem scratch cleanup.

## Build, test, and launch commands""")

# Focused validator must enforce retention too.
replace_once("scripts/validate_prompt_kit_browser_proof_cleanup.py", '        "favorites_local_storage_out_of_scope": True,\n', '        "favorites_local_storage_out_of_scope": True,\n        "retain_previous_report_before_overwrite": True,\n')
replace_once("scripts/validate_prompt_kit_browser_proof_cleanup.py", '            "browser localStorage and Prompt Kit Favorites",\n', '            "browser localStorage and Prompt Kit Favorites",\n            "backups/prompt-kit-browser-proof-cleanup",\n            "Copy-Item -LiteralPath $ResolvedReportPath",\n            "previous_receipt_backup",\n')

# Focused regression coverage for retention + root routing.
p = Path("tests/test_prompt_kit_browser_proof_cleanup_harness.py")
t = p.read_text(encoding="utf-8")
anchor = "    def test_artifact_registry_keeps_scratch_noncanonical(self) -> None:\n"
addition = '''    def test_cleanup_runner_retains_previous_receipt_before_overwrite(self) -> None:\n        text = (ROOT / "scripts/Clear-PromptKitBrowserProofScratch.ps1").read_text(encoding="utf-8")\n        self.assertIn("backups/prompt-kit-browser-proof-cleanup", text)\n        self.assertIn("Copy-Item -LiteralPath $ResolvedReportPath", text)\n        self.assertIn("previous_receipt_backup", text)\n\n    def test_root_harness_registers_cleanup_capability_and_trigger(self) -> None:\n        manifest = json.loads((ROOT / "harness/manifest.v1.json").read_text(encoding="utf-8"))\n        self.assertIn("prompt_kit_browser_proof_cleanup", manifest["domain_contracts"])\n        caps = json.loads((ROOT / "harness/capabilities.v1.json").read_text(encoding="utf-8"))["capabilities"]\n        triggers = json.loads((ROOT / "harness/triggers.v1.json").read_text(encoding="utf-8"))["triggers"]\n        self.assertIn("prompt-kit-browser-proof-scratch-cleanup", {item["id"] for item in caps})\n        self.assertIn("prompt-kit-browser-proof-temp-path", {item["id"] for item in triggers})\n\n'''
if addition not in t:
    if anchor not in t:
        raise SystemExit("focused test anchor missing")
    p.write_text(t.replace(anchor, addition + anchor, 1), encoding="utf-8")

# Dedicated CI proves backup retention and actual test-owned deletion.
replace_once(
    ".github/workflows/prompt-kit-browser-proof-cleanup.yml",
    """          & ./scripts/Clear-PromptKitBrowserProofScratch.ps1 -TargetPath $Scratch -MinimumAgeMinutes 0 -ReportPath ./Outputs/browser-proof-preview.json
          if ($LASTEXITCODE) { exit $LASTEXITCODE }
          if (-not (Test-Path -LiteralPath $Scratch)) { throw 'Preview deleted the test-owned scratch directory.' }
          & ./scripts/Clear-PromptKitBrowserProofScratch.ps1 -TargetPath $Scratch -MinimumAgeMinutes 0 -Apply -ReportPath ./Outputs/browser-proof-apply.json
""",
    """          & ./scripts/Clear-PromptKitBrowserProofScratch.ps1 -TargetPath $Scratch -MinimumAgeMinutes 0 -ReportPath ./Outputs/browser-proof-preview.json
          if ($LASTEXITCODE) { exit $LASTEXITCODE }
          if (-not (Test-Path -LiteralPath $Scratch)) { throw 'Preview deleted the test-owned scratch directory.' }
          & ./scripts/Clear-PromptKitBrowserProofScratch.ps1 -TargetPath $Scratch -MinimumAgeMinutes 0 -ReportPath ./Outputs/browser-proof-preview.json
          if ($LASTEXITCODE) { exit $LASTEXITCODE }
          $Backup = @(Get-ChildItem ./Outputs/backups/prompt-kit-browser-proof-cleanup -File -Filter 'browser-proof-preview_backup_*.json' -ErrorAction Stop)
          if ($Backup.Count -lt 1) { throw 'Repeated preview did not preserve the previous durable receipt.' }
          & ./scripts/Clear-PromptKitBrowserProofScratch.ps1 -TargetPath $Scratch -MinimumAgeMinutes 0 -Apply -ReportPath ./Outputs/browser-proof-apply.json
""",
)
