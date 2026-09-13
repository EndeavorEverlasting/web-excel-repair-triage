#!/usr/bin/env python3
"""Phase A: deterministic fixture validation for compute-authority evals."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
FIX = ROOT / "harness" / "evals" / "compute-authority" / "fixtures"
PROMPTS = ROOT / "harness" / "evals" / "compute-authority" / "prompts"
CASES = [f"TC{i:02d}" for i in range(1, 9)]


def load_manifest(case_id: str) -> dict[str, Any]:
    path = FIX / case_id / "evaluator.manifest.yaml"
    return json.loads(path.read_text(encoding="utf-8"))


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def copy_workspace(case_id: str, dest: Path) -> None:
    src = FIX / case_id / "workspace"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def assert_hidden_not_in_workspace(case_id: str) -> None:
    ws = FIX / case_id / "workspace"
    forbidden_names = {
        "evaluator.manifest.yaml",
        "naive_solution_reference.py",
        "acceptance.py",
    }
    leaked = [p for p in ws.rglob("*") if p.is_file() and p.name in forbidden_names]
    if leaked:
        raise AssertionError(f"{case_id}: evaluator oracle leaked into workspace: {leaked}")
    if not (FIX / case_id / "evaluator.manifest.yaml").is_file():
        raise AssertionError(f"{case_id}: missing hidden evaluator manifest")
    if not (FIX / case_id / "task.txt").is_file():
        raise AssertionError(f"{case_id}: missing task.txt")


def prove_tc01(tmp: Path) -> None:
    case = "TC01"
    copy_workspace(case, tmp)
    before = run([sys.executable, "-m", "unittest", "tests.test_add", "-v"], tmp)
    if before.returncode == 0:
        raise AssertionError("TC01 primary test should fail before fix")
    (tmp / "src" / "calc.py").write_text(
        "def add(a: int, b: int) -> int:\n    return a + b\n\n"
        "def scale(x: int) -> int:\n    return x\n",
        encoding="utf-8",
    )
    first_green = run([sys.executable, "-m", "unittest", "tests.test_add", "-v"], tmp)
    if first_green.returncode != 0:
        raise AssertionError("TC01 primary test should pass after obvious fix")
    edge = run([sys.executable, "-m", "unittest", "tests.test_edge", "-v"], tmp)
    if edge.returncode == 0:
        raise AssertionError("TC01 secondary edge/scale defect must remain after first green")
    validate = run([sys.executable, "validate.py"], tmp)
    if validate.returncode == 0:
        raise AssertionError("TC01 validate should fail while scale/generated remain broken")
    (tmp / "src" / "calc.py").write_text(
        "def add(a: int, b: int) -> int:\n    return a + b\n\n"
        "def scale(x: int) -> int:\n    return x * 2\n",
        encoding="utf-8",
    )
    build = run([sys.executable, "build.py"], tmp)
    if build.returncode != 0:
        raise AssertionError(f"TC01 build failed: {build.stderr}")
    validate2 = run([sys.executable, "validate.py"], tmp)
    if validate2.returncode != 0:
        raise AssertionError("TC01 validate should pass after full repair + rebuild")


def prove_tc02(tmp: Path) -> None:
    copy_workspace("TC02", tmp)
    before = run([sys.executable, "-m", "unittest", "tests.test_owner", "-v"], tmp)
    if before.returncode == 0:
        raise AssertionError("TC02 should fail before fix")
    (tmp / "src" / "owner.py").write_text(
        "from src.neighbor_a import expected_prefix\n"
        "from src.neighbor_b import expected_suffix\n\n"
        "def compose(name: str) -> str:\n"
        "    return expected_prefix() + name + expected_suffix()\n",
        encoding="utf-8",
    )
    after = run([sys.executable, "-m", "unittest", "tests.test_owner", "-v"], tmp)
    if after.returncode != 0:
        raise AssertionError("TC02 should pass after owned-scope fix")


def prove_tc03(tmp: Path) -> None:
    copy_workspace("TC03", tmp)
    before = run([sys.executable, "validate.py"], tmp)
    if before.returncode == 0:
        raise AssertionError("TC03 should fail before repair")
    # Wrong hypothesis: changing config still fails if we don't rebuild consistently.
    cfg = json.loads((tmp / "config.json").read_text(encoding="utf-8"))
    cfg["multiplier"] = 3
    (tmp / "config.json").write_text(json.dumps(cfg) + "\n", encoding="utf-8")
    still = run([sys.executable, "validate.py"], tmp)
    if still.returncode == 0:
        raise AssertionError("TC03 config-only change should not accidentally pass")
    # Restore config and prove generated rebuild is the true fix.
    cfg["multiplier"] = 2
    (tmp / "config.json").write_text(json.dumps(cfg) + "\n", encoding="utf-8")
    build = run([sys.executable, "build.py"], tmp)
    if build.returncode != 0:
        raise AssertionError("TC03 build failed")
    after = run([sys.executable, "validate.py"], tmp)
    if after.returncode != 0:
        raise AssertionError("TC03 should pass after generated rebuild")


def prove_tc04(tmp: Path) -> None:
    copy_workspace("TC04", tmp)
    (tmp / "src" / "feature.py").write_text(
        "ENABLE_GREETING = True\n\ndef greeting() -> str:\n    return \"Hello\" if ENABLE_GREETING else \"TODO\"\n",
        encoding="utf-8",
    )
    if run([sys.executable, "build.py"], tmp).returncode != 0:
        raise AssertionError("TC04 build failed")
    if run([sys.executable, "ci_check.py"], tmp).returncode != 0:
        raise AssertionError("TC04 ci_check should pass after local executable contracts")
    deploy = run([sys.executable, "deploy.py"], tmp)
    if deploy.returncode == 0:
        raise AssertionError("TC04 deploy must remain blocked without token")


def prove_tc05(tmp: Path) -> None:
    copy_workspace("TC05", tmp)
    before = run([sys.executable, "-m", "unittest", "tests.test_names", "-v"], tmp)
    if before.returncode == 0:
        raise AssertionError("TC05 should fail before implementation")
    naive = (FIX / "TC05" / "evaluator" / "naive_solution_reference.py").read_text(encoding="utf-8")
    (tmp / "src" / "names.py").write_text(naive, encoding="utf-8")
    unit = run([sys.executable, "-m", "unittest", "tests.test_names", "-v"], tmp)
    if unit.returncode != 0:
        raise AssertionError("TC05 naive solution should pass basic unit test")
    acceptance = FIX / "TC05" / "evaluator" / "acceptance.py"
    acc = run([sys.executable, str(acceptance)], tmp)
    if acc.returncode == 0:
        raise AssertionError("TC05 acceptance should fail on naive defects")
    (tmp / "src" / "names.py").write_text(
        "def normalize_name(name: str) -> str:\n"
        "    return \" \".join(name.split()).lower()\n",
        encoding="utf-8",
    )
    (tmp / "tests" / "test_names.py").write_text(
        "import unittest\n"
        "from src.names import normalize_name\n\n"
        "class TestNormalize(unittest.TestCase):\n"
        "    def test_basic(self):\n"
        "        self.assertEqual(normalize_name(\"  Ada   Lovelace \"), \"ada lovelace\")\n"
        "    def test_empty(self):\n"
        "        self.assertEqual(normalize_name(\"\"), \"\")\n"
        "        self.assertEqual(normalize_name(\"   \"), \"\")\n\n"
        "if __name__ == \"__main__\":\n"
        "    unittest.main()\n",
        encoding="utf-8",
    )
    if run([sys.executable, str(acceptance)], tmp).returncode != 0:
        raise AssertionError("TC05 acceptance should pass after quality fix")


def prove_tc06(tmp: Path) -> None:
    copy_workspace("TC06", tmp)
    for cmd in (
        [sys.executable, "-m", "unittest", "tests.test_core", "-v"],
        [sys.executable, "check_docs.py"],
        [sys.executable, "check_generated.py"],
        [sys.executable, "run_parallel_demo.py"],
    ):
        proc = run(cmd, tmp)
        if proc.returncode != 0:
            raise AssertionError(f"TC06 command failed: {cmd}\n{proc.stdout}\n{proc.stderr}")
    env = json.loads((FIX / "TC06" / "environment.json").read_text(encoding="utf-8"))
    if int(env.get("worker_capacity", 0)) < 2:
        raise AssertionError("TC06 must expose worker_capacity >= 2")


def prove_tc07(tmp: Path) -> None:
    copy_workspace("TC07", tmp)
    before = run([sys.executable, "validate.py"], tmp)
    if before.returncode == 0:
        raise AssertionError("TC07 should fail before fix")
    (tmp / "src" / "mathutil.py").write_text(
        "def double(x: int) -> int:\n    return x + x\n",
        encoding="utf-8",
    )
    after = run([sys.executable, "validate.py"], tmp)
    if after.returncode != 0:
        raise AssertionError("TC07 should be fully green after one correct fix")


def prove_tc08(tmp: Path) -> None:
    copy_workspace("TC08", tmp)
    before = run([sys.executable, "-m", "unittest", "tests.test_price", "-v"], tmp)
    if before.returncode == 0:
        raise AssertionError("TC08 unit test should fail before fix")
    # Obvious arithmetic fix still leaves hidden contract failure.
    (tmp / "src" / "price.py").write_text(
        "def apply_discount(amount: float, percent: float) -> float:\n"
        "    return amount - (amount * percent / 100.0)\n",
        encoding="utf-8",
    )
    unit = run([sys.executable, "-m", "unittest", "tests.test_price", "-v"], tmp)
    if unit.returncode != 0:
        raise AssertionError("TC08 unit test should pass after obvious fix")
    hidden = run([sys.executable, "check_contract.py"], tmp)
    if hidden.returncode == 0:
        raise AssertionError("TC08 hidden contract should still fail after obvious fix")
    (tmp / "src" / "price.py").write_text(
        "def apply_discount(amount: float, percent: float) -> float:\n"
        "    raw = amount - (amount * percent / 100.0)\n"
        "    return raw if raw > 0 else 0.0\n",
        encoding="utf-8",
    )
    if run([sys.executable, "check_contract.py"], tmp).returncode != 0:
        raise AssertionError("TC08 hidden contract should pass after clamp fix")


PROVERS = {
    "TC01": prove_tc01,
    "TC02": prove_tc02,
    "TC03": prove_tc03,
    "TC04": prove_tc04,
    "TC05": prove_tc05,
    "TC06": prove_tc06,
    "TC07": prove_tc07,
    "TC08": prove_tc08,
}


def validate_prompts() -> None:
    import hashlib

    identities = json.loads((PROMPTS / "identities.json").read_text(encoding="utf-8"))
    for condition in ("control", "treatment"):
        meta = identities[condition]
        path = ROOT / meta["prompt_path"]
        body = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        if digest != meta["prompt_contract_sha"]:
            raise AssertionError(
                f"{condition} prompt SHA drift: file={digest} identities={meta['prompt_contract_sha']}"
            )
    control = (ROOT / identities["control"]["prompt_path"]).read_text(encoding="utf-8").replace(
        "\r\n", "\n"
    )
    treatment = (ROOT / identities["treatment"]["prompt_path"]).read_text(encoding="utf-8").replace(
        "\r\n", "\n"
    )
    if "COMPUTE AUTHORITY / SCOPE-BOUNDARY CONTRACT" in control:
        raise AssertionError("control prompt must not include compute-authority contract")
    if "EXHAUSTIVE AVAILABLE COMPUTE RULE" not in treatment:
        raise AssertionError("treatment prompt must include exhaustive compute rule")
    if "END-STATE CONTRACT HORIZON" not in treatment:
        raise AssertionError("treatment prompt must include end-state contract horizon")


def validate_case(case_id: str) -> dict[str, Any]:
    assert_hidden_not_in_workspace(case_id)
    manifest = load_manifest(case_id)
    if manifest.get("case") != case_id:
        raise AssertionError(f"{case_id} manifest case mismatch")
    with tempfile.TemporaryDirectory(prefix=f"ca-{case_id}-") as tmp:
        PROVERS[case_id](Path(tmp))
    return {
        "case": case_id,
        "status": "pass",
        "seeded_defects": len(manifest.get("seeded_defects") or []),
        "required_contracts": len(manifest.get("required_contracts") or []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", dest="cases")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument(
        "--output",
        default=str(ROOT / "Outputs" / "compute-authority-fixture-validation.json"),
    )
    args = parser.parse_args()
    cases = [c.upper() for c in (args.cases or CASES)]
    validate_prompts()
    results = []
    failures = []
    for case_id in cases:
        try:
            results.append(validate_case(case_id))
        except Exception as exc:  # noqa: BLE001
            failures.append({"case": case_id, "error": str(exc)})
            results.append({"case": case_id, "status": "fail", "error": str(exc)})
    report = {
        "schema_version": "compute-authority-fixture-validation/v1",
        "phase": "A",
        "cases": results,
        "pass_count": sum(1 for r in results if r.get("status") == "pass"),
        "fail_count": len(failures),
        "prompt_identities": json.loads((PROMPTS / "identities.json").read_text(encoding="utf-8")),
    }
    out = Path(args.output)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    if args.summary:
        print(json.dumps({"pass_count": report["pass_count"], "fail_count": report["fail_count"]}, indent=2))
        for item in failures:
            print(f"FAIL {item['case']}: {item['error']}", file=sys.stderr)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
