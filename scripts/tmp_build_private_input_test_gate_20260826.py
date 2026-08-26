#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


manifest_path = ROOT / "harness/test-floor.v1.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["private_input_requirements"] = [
    {
        "id": "neuron-real-roster",
        "input_path": "Candidates/attendacne artifacts 6-1-2026/INTERNAL_May_Billing_Active_Roster_Log_2026-06-01-update so that partial hours are flagged before submission.xlsx",
        "test_selector": "tests/test_nw_prj_neuron_track_hours.py::test_neuron_track_totals_match_reference_targets",
        "missing_reason": "Real roster log not present"
    },
    {
        "id": "one-marcus-real-recon",
        "input_path": "Candidates/inventory recon/WEBSAFE_Tab-Linked_1_Marcus_Compiled_Recon_Integrated_5-28-2026_PARTNUMBERS_LINKED_CANDIDATE_v2.xlsx",
        "test_selector": "tests/test_one_marcus_recon.py::test_real_workbook_idempotent_regression",
        "missing_reason": "private real workbook not present"
    },
    {
        "id": "one-marcus-operator-reference",
        "input_path": "Candidates/inventory recon/1M_Recon_READY.xlsx",
        "test_selector": "tests/test_one_marcus_generate.py::test_generate_from_operator_reference",
        "missing_reason": "private operator reference workbook not present"
    }
]
manifest["proof_ceiling"] = (
    "Deterministic clean-checkout Python, pinned direct CI dependencies, test-floor self-contract, "
    "convention-covered Prompt Kit semantic regressions with explicit low-cost execution registration, "
    "public/synthetic artifact-engine tests with fail-closed registered private-input skips, harness, "
    "Prompt Kit static/generated-parity, repository hygiene, and exact-candidate provider-workflow proof on the observed SHA. "
    "The separate canonical private-input gate fails closed when its three registered operator inputs are absent and runs the exact "
    "real-input regressions when they are supplied. Public CI does not claim a private-input PASS, production, privileged-device, "
    "secret-bearing, or operator acceptance proof."
)
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

private_runner = r'''#!/usr/bin/env python3
"""Run the registered private-input regressions without treating missing operator files as green."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "harness" / "test-floor.v1.json"
DEFAULT_REPORT = REPO_ROOT / "Outputs" / "private-input-test-floor-report.json"


class ContractError(RuntimeError):
    pass


def _git_value(*args: str) -> str | None:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def load_requirements(manifest_path: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot load private-input manifest: {exc}") from exc
    if manifest.get("schema_version") != "deterministic-test-floor/v1":
        raise ContractError("unsupported deterministic test-floor schema")
    allowed = manifest.get("allowed_artifact_skip_reasons")
    artifact_tests = manifest.get("artifact_tests")
    raw = manifest.get("private_input_requirements")
    if not isinstance(allowed, list) or not isinstance(artifact_tests, list):
        raise ContractError("test-floor skip/test owners are malformed")
    if not isinstance(raw, list) or not raw:
        raise ContractError("private_input_requirements must be a non-empty list")

    records: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_selectors: set[str] = set()
    seen_reasons: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            raise ContractError("private input requirement must be an object")
        record = {key: str(item.get(key, "")).strip() for key in ("id", "input_path", "test_selector", "missing_reason")}
        if any(not value for value in record.values()):
            raise ContractError("private input requirement has an empty required field")
        rel = PurePosixPath(record["input_path"])
        if rel.is_absolute() or ".." in rel.parts:
            raise ContractError(f"private input path must stay repository-relative: {record['input_path']}")
        test_file = record["test_selector"].split("::", 1)[0]
        if "::" not in record["test_selector"] or test_file not in artifact_tests:
            raise ContractError(f"private test selector is not owned by artifact_tests: {record['test_selector']}")
        if record["missing_reason"] not in allowed:
            raise ContractError(f"private input reason is not registered: {record['missing_reason']}")
        if record["id"] in seen_ids or record["test_selector"] in seen_selectors or record["missing_reason"] in seen_reasons:
            raise ContractError("private input ids, selectors, and reasons must be unique")
        seen_ids.add(record["id"])
        seen_selectors.add(record["test_selector"])
        seen_reasons.add(record["missing_reason"])
        records.append(record)
    if seen_reasons != set(allowed):
        raise ContractError("private input requirements must exactly own the registered private skip reasons")
    return manifest, records


def missing_requirements(records: list[dict[str, str]], repo_root: Path = REPO_ROOT) -> list[dict[str, str]]:
    return [record for record in records if not (repo_root / record["input_path"]).is_file()]


def pytest_argv(records: list[dict[str, str]]) -> list[str]:
    return [sys.executable, "-m", "pytest", *[record["test_selector"] for record in records], "-q", "-rs"]


def run(manifest_path: Path, report_path: Path) -> int:
    try:
        manifest, records = load_requirements(manifest_path)
    except ContractError as exc:
        report = {
            "schema_version": "private-input-test-floor-report/v1",
            "status": "FAIL",
            "failed_step": "contract",
            "error": str(exc),
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"PRIVATE INPUT CONTRACT FAIL: {exc}", file=sys.stderr)
        return 2

    missing = missing_requirements(records)
    report: dict[str, Any] = {
        "schema_version": "private-input-test-floor-report/v1",
        "status": "BLOCKED" if missing else "PASS",
        "failed_step": "private-input-readiness" if missing else None,
        "commit_sha": _git_value("rev-parse", "HEAD"),
        "branch": _git_value("rev-parse", "--abbrev-ref", "HEAD"),
        "required_input_ids": [record["id"] for record in records],
        "missing_input_ids": [record["id"] for record in missing],
        "test_selectors": [record["test_selector"] for record in records],
        "proof_ceiling": (
            "Private-input regression PASS is available only when all registered operator inputs are present. "
            "This gate never proves production, privileged-device, secret-bearing, or operator acceptance behavior."
        ),
        "test": None,
    }
    if missing:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("PRIVATE INPUT TEST FLOOR: BLOCKED")
        print("Missing registered input ids: " + ", ".join(report["missing_input_ids"]))
        print(f"Receipt: {report_path}")
        return 3

    env = os.environ.copy()
    for key, value in manifest.get("environment", {}).items():
        env[str(key)] = str(value)
    result = subprocess.run(
        pytest_argv(records), cwd=REPO_ROOT, env=env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    if stdout:
        print(stdout, end="" if stdout.endswith("\n") else "\n")
    if stderr:
        print(stderr, file=sys.stderr, end="" if stderr.endswith("\n") else "\n")
    skipped = " skipped" in stdout or any(line.startswith("SKIPPED [") for line in stdout.splitlines())
    status = "PASS" if result.returncode == 0 and not skipped else "FAIL"
    report["status"] = status
    report["failed_step"] = None if status == "PASS" else "private-input-regressions"
    report["test"] = {
        "argv": pytest_argv(records),
        "returncode": result.returncode,
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-4000:],
        "skip_detected": skipped,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PRIVATE INPUT TEST FLOOR: {status}")
    print(f"Receipt: {report_path}")
    return 0 if status == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run registered private-input regressions fail-closed.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    manifest = args.manifest if args.manifest.is_absolute() else REPO_ROOT / args.manifest
    report = args.report if args.report.is_absolute() else REPO_ROOT / args.report
    return run(manifest.resolve(), report.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
'''
write("scripts/run_private_input_test_floor.py", private_runner)

# Strengthen deterministic floor regression without creating a competing test owner.
test_path = ROOT / "tests/test_deterministic_test_floor.py"
test_text = test_path.read_text(encoding="utf-8")
if "run_private_input_test_floor as private_floor" not in test_text:
    test_text = test_text.replace(
        "from scripts import run_deterministic_test_floor as floor\n",
        "from scripts import run_deterministic_test_floor as floor\nfrom scripts import run_private_input_test_floor as private_floor\n",
    )
methods = r'''
    def test_private_input_requirements_exactly_own_registered_skips(self) -> None:
        manifest, records = private_floor.load_requirements(MANIFEST)
        self.assertEqual(len(records), 3)
        self.assertEqual(
            {record["missing_reason"] for record in records},
            set(manifest["allowed_artifact_skip_reasons"]),
        )
        self.assertEqual(
            {record["id"] for record in records},
            {"neuron-real-roster", "one-marcus-real-recon", "one-marcus-operator-reference"},
        )
        for record in records:
            self.assertIn(record["test_selector"].split("::", 1)[0], manifest["artifact_tests"])

    def test_private_input_gate_is_fail_closed_and_can_become_ready(self) -> None:
        _manifest, records = private_floor.load_requirements(MANIFEST)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(len(private_floor.missing_requirements(records, root)), 3)
            for record in records:
                target = root / record["input_path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"fixture")
            self.assertEqual(private_floor.missing_requirements(records, root), [])
            argv = private_floor.pytest_argv(records)
            self.assertEqual(argv[0], private_floor.sys.executable)
            for record in records:
                self.assertIn(record["test_selector"], argv)

    def test_private_input_contract_rejects_path_escape(self) -> None:
        broken = dict(self.manifest)
        broken["private_input_requirements"] = [dict(item) for item in self.manifest["private_input_requirements"]]
        broken["private_input_requirements"][0]["input_path"] = "../secret.xlsx"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(broken), encoding="utf-8")
            with self.assertRaisesRegex(private_floor.ContractError, "repository-relative"):
                private_floor.load_requirements(path)

    def test_public_workflow_proves_private_gate_blocks_without_acquiring_secrets(self) -> None:
        workflow = FLOOR_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Private-input gate must block on clean public runner", workflow)
        self.assertIn("scripts/run_private_input_test_floor.py", workflow)
        self.assertIn("private-input-blocked-report.json", workflow)
        self.assertIn("report.get('status') != 'BLOCKED'", workflow)
        self.assertIn("contents: read", workflow)
        self.assertNotIn("secrets.", workflow)
'''
if "test_private_input_requirements_exactly_own_registered_skips" not in test_text:
    test_text = test_text.replace("\n\nif __name__ == \"__main__\":\n", "\n" + methods + "\nif __name__ == \"__main__\":\n")
test_path.write_text(test_text, encoding="utf-8")

workflow_path = ROOT / ".github/workflows/deterministic-test-floor.yml"
workflow = workflow_path.read_text(encoding="utf-8")
private_step = r'''
      - name: Private-input gate must block on clean public runner
        shell: bash
        run: |
          set -euo pipefail
          set +e
          python scripts/run_private_input_test_floor.py \
            --report "$RUNNER_TEMP/private-input-blocked-report.json"
          status=$?
          set -e
          if [ "$status" -ne 3 ]; then
            echo "Expected private-input readiness blocker (exit 3), observed $status" >&2
            exit 1
          fi
          python - "$RUNNER_TEMP/private-input-blocked-report.json" <<'PY'
          import json
          import sys
          from pathlib import Path
          report = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
          if report.get('status') != 'BLOCKED' or report.get('failed_step') != 'private-input-readiness':
              raise SystemExit(f"unexpected private-input gate receipt: {report}")
          missing = report.get('missing_input_ids') or []
          if len(missing) != 3:
              raise SystemExit(f"expected three unavailable private inputs, observed {missing!r}")
          print("private-input gate proved fail-closed on clean public runner: " + ", ".join(missing))
          PY

'''
if "Private-input gate must block on clean public runner" not in workflow:
    marker = "      - name: Run clean deterministic test floor\n"
    workflow = workflow.replace(marker, private_step + marker)
    workflow = workflow.replace(
        "            ${{ runner.temp }}/negative-canary-report.json\n            ${{ runner.temp }}/deterministic-test-floor-report.json\n",
        "            ${{ runner.temp }}/negative-canary-report.json\n            ${{ runner.temp }}/private-input-blocked-report.json\n            ${{ runner.temp }}/deterministic-test-floor-report.json\n",
    )
workflow_path.write_text(workflow, encoding="utf-8")

# Patch test expectations that intentionally count test-floor runner calls.
test_text = test_path.read_text(encoding="utf-8")
test_text = test_text.replace(
    'self.assertEqual(workflow.count("scripts/run_deterministic_test_floor.py"), 2)',
    'self.assertEqual(workflow.count("scripts/run_deterministic_test_floor.py"), 2)\n        self.assertEqual(workflow.count("scripts/run_private_input_test_floor.py"), 1)',
)
test_path.write_text(test_text, encoding="utf-8")

# Validate focused contract, expected public blocker, then the canonical floor.
subprocess.run(["python", "-m", "pytest", "tests/test_deterministic_test_floor.py", "-q"], cwd=ROOT, check=True)
blocked_report = ROOT / "Outputs/private-input-provider-canary.json"
blocked = subprocess.run(
    ["python", "scripts/run_private_input_test_floor.py", "--report", str(blocked_report)],
    cwd=ROOT,
)
if blocked.returncode != 3:
    raise SystemExit(f"private-input canary expected exit 3, got {blocked.returncode}")
receipt = json.loads(blocked_report.read_text(encoding="utf-8"))
if receipt.get("status") != "BLOCKED" or len(receipt.get("missing_input_ids", [])) != 3:
    raise SystemExit(f"unexpected private-input canary receipt: {receipt}")
subprocess.run(
    ["python", "scripts/run_deterministic_test_floor.py", "--report", "Outputs/deterministic-test-floor-private-gate-build.json"],
    cwd=ROOT,
    check=True,
)
subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)

# Temporary carrier must not survive the durable branch.
(ROOT / "scripts/tmp_build_private_input_test_gate_20260826.py").unlink(missing_ok=True)
(ROOT / ".github/workflows/tmp-private-input-test-gate-20260826.yml").unlink(missing_ok=True)
subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
subprocess.run(["git", "diff", "--cached", "--check"], cwd=ROOT, check=True)
subprocess.run(
    ["git", "commit", "-m", "feat(test): add fail-closed private-input proof gate"],
    cwd=ROOT,
    check=True,
)
subprocess.run(["git", "push", "origin", "HEAD"], cwd=ROOT, check=True)
