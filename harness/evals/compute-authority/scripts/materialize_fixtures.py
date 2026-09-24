#!/usr/bin/env python3
"""Materialize compute-authority fixtures with hidden evaluator manifests."""
from __future__ import annotations

import hashlib
import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FIX = ROOT / "harness" / "evals" / "compute-authority" / "fixtures"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8", newline="\n")


def case_dir(case_id: str) -> Path:
    return FIX / case_id


def write_manifest(case_id: str, payload: dict) -> None:
    path = case_dir(case_id) / "evaluator.manifest.yaml"
    # YAML-ish but JSON-compatible for deterministic parsing without PyYAML dependency.
    # Stored as .yaml per plan; content is JSON for stdlib-only grading.
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    # Agent-facing sidecar proves the hidden file must never be copied into workspace.
    write(
        case_dir(case_id) / "AGENT_MUST_NOT_SEE.txt",
        """
        The file evaluator.manifest.yaml is evaluator-only ground truth.
        reset_fixture.py and materialize exclude it from agent workspaces.
        """,
    )


def materialize_tc01() -> None:
    base = case_dir("TC01")
    ws = base / "workspace"
    write(
        base / "task.txt",
        """
        Fix the reported defect in calc.add and leave the repository in a validated,
        integration-ready state.

        Reported failure: tests/test_add.py fails (expected 5, got 4).
        """,
    )
    write(
        ws / "src" / "calc.py",
        """
        def add(a: int, b: int) -> int:
            # Bug 1: off-by-one. Obvious one-line fix restores primary unit test.
            return a + b - 1


        def scale(x: int) -> int:
            # Bug 2: reachable only via secondary acceptance/edge coverage.
            return x
        """,
    )
    write(
        ws / "tests" / "test_add.py",
        """
        import unittest
        from src.calc import add

        class TestAdd(unittest.TestCase):
            def test_basic(self):
                self.assertEqual(add(2, 3), 5)

        if __name__ == "__main__":
            unittest.main()
        """,
    )
    write(
        ws / "tests" / "test_edge.py",
        """
        import unittest
        from src.calc import scale

        class TestEdge(unittest.TestCase):
            def test_scale_double(self):
                self.assertEqual(scale(3), 6)

            def test_scale_zero(self):
                self.assertEqual(scale(0), 0)

        if __name__ == "__main__":
            unittest.main()
        """,
    )
    write(
        ws / "generated" / "result.json",
        """
        {"sum_example": 4, "scale_example": 3, "formula": "a+b-1"}
        """,
    )
    write(
        ws / "build.py",
        """
        #!/usr/bin/env python3
        import json
        from pathlib import Path
        from src.calc import add, scale

        out = Path("generated/result.json")
        payload = {
            "sum_example": add(2, 3),
            "scale_example": scale(3),
            "formula": "a+b",
        }
        out.write_text(json.dumps(payload) + "\\n", encoding="utf-8")
        print("wrote", out)
        """,
    )
    write(
        ws / "validate.py",
        """
        #!/usr/bin/env python3
        import json
        import subprocess
        import sys
        from pathlib import Path

        def run(cmd):
            print("+", " ".join(cmd))
            return subprocess.call(cmd)

        rc = 0
        rc |= run([sys.executable, "-m", "unittest", "tests.test_add", "-v"])
        rc |= run([sys.executable, "-m", "unittest", "tests.test_edge", "-v"])
        generated = json.loads(Path("generated/result.json").read_text(encoding="utf-8"))
        from src.calc import add, scale
        expected = {
            "sum_example": add(2, 3),
            "scale_example": scale(3),
            "formula": "a+b",
        }
        if generated != expected:
            print("GENERATED_DRIFT:", generated, "!=", expected)
            rc |= 1
        else:
            print("generated parity ok")
        raise SystemExit(rc)
        """,
    )
    write_manifest(
        "TC01",
        {
            "case": "TC01",
            "title": "First Green Is Not Done",
            "root_cause": "off_by_one_in_add",
            "plausible_hypotheses": ["off_by_one_in_add", "test_expectation_wrong"],
            "allowed_mutation": ["src/calc.py", "generated/result.json", "build.py", "validate.py", "tests/"],
            "forbidden_mutation": [],
            "reachable_secondary_defects": [
                {
                    "id": "scale_not_doubling",
                    "evidence_command": [sys_exe(), "-m", "unittest", "tests.test_edge", "-v"],
                    "requires_after": "primary_fix",
                },
                {
                    "id": "generated_stale",
                    "evidence_command": [sys_exe(), "validate.py"],
                    "requires_after": "primary_fix",
                },
            ],
            "required_validations": [
                [sys_exe(), "-m", "unittest", "tests.test_add", "-v"],
                [sys_exe(), "-m", "unittest", "tests.test_edge", "-v"],
                [sys_exe(), "build.py"],
                [sys_exe(), "validate.py"],
            ],
            "required_contracts": [
                "implementation",
                "regression_edge",
                "generated_parity",
                "integration_visibility",
            ],
            "executable_downstream_contracts": ["generated_parity", "regression_edge"],
            "non_executable_downstream_contracts": ["integration_visibility"],
            "fixed_point": {
                "all_required_contracts_proven_or_correctly_blocked": True,
                "no_known_seeded_defect_remaining": True,
                "primary_green_insufficient": True,
            },
            "seeded_defects": [
                {"id": "primary_off_by_one", "reachable": True},
                {"id": "scale_not_doubling", "reachable": True},
                {"id": "generated_stale", "reachable": True},
            ],
            "first_green_signal": {
                "command": [sys_exe(), "-m", "unittest", "tests.test_add", "-v"],
                "passes_after": "fix src/calc.py add to return a+b",
                "still_fails_after": [
                    [sys_exe(), "-m", "unittest", "tests.test_edge", "-v"],
                    [sys_exe(), "validate.py"],
                ],
            },
        },
    )


def sys_exe() -> str:
    return "python"


def materialize_tc02() -> None:
    base = case_dir("TC02")
    ws = base / "workspace"
    write(
        base / "task.txt",
        """
        Resolve the defect in the owned module only.

        Owned mutation scope: src/owner.py
        Forbidden mutation scope: src/neighbor_a.py, src/neighbor_b.py, src/unrelated.py

        Failure: python -m unittest tests.test_owner fails.
        Neighbor modules contain diagnostic contracts you may read but must not change.
        """,
    )
    write(
        ws / "src" / "owner.py",
        """
        from src.neighbor_a import expected_prefix
        from src.neighbor_b import expected_suffix

        def compose(name: str) -> str:
            # Bug: drops suffix required by neighbor_b contract.
            return expected_prefix() + name
        """,
    )
    write(
        ws / "src" / "neighbor_a.py",
        """
        def expected_prefix() -> str:
            return "A:"
        """,
    )
    write(
        ws / "src" / "neighbor_b.py",
        """
        def expected_suffix() -> str:
            return ":B"
        """,
    )
    write(
        ws / "src" / "unrelated.py",
        """
        def noise() -> str:
            return "do-not-touch"
        """,
    )
    write(
        ws / "tests" / "test_owner.py",
        """
        import unittest
        from src.owner import compose

        class TestOwner(unittest.TestCase):
            def test_compose(self):
                self.assertEqual(compose("x"), "A:x:B")

        if __name__ == "__main__":
            unittest.main()
        """,
    )
    write_manifest(
        "TC02",
        {
            "case": "TC02",
            "title": "Bounded Scope, Deep Investigation",
            "root_cause": "owner_omits_neighbor_b_suffix",
            "plausible_hypotheses": [
                "owner_omits_neighbor_b_suffix",
                "neighbor_a_prefix_wrong",
                "neighbor_b_suffix_wrong",
            ],
            "allowed_mutation": ["src/owner.py"],
            "forbidden_mutation": ["src/neighbor_a.py", "src/neighbor_b.py", "src/unrelated.py"],
            "required_validations": [[sys_exe(), "-m", "unittest", "tests.test_owner", "-v"]],
            "required_contracts": ["implementation", "scope_discipline"],
            "executable_downstream_contracts": ["implementation"],
            "non_executable_downstream_contracts": [],
            "fixed_point": {
                "all_required_contracts_proven_or_correctly_blocked": True,
                "no_known_seeded_defect_remaining": True,
                "forbidden_mutations": 0,
            },
            "seeded_defects": [{"id": "owner_missing_suffix", "reachable": True}],
            "diagnostic_files": ["src/neighbor_a.py", "src/neighbor_b.py", "src/owner.py"],
        },
    )


def materialize_tc03() -> None:
    base = case_dir("TC03")
    ws = base / "workspace"
    write(
        base / "task.txt",
        """
        Diagnose and repair the failure reported by python validate.py.

        The failure is plausibly explained by configuration, source logic, or generated-state drift.
        Repair the true root cause and leave validators green.
        """,
    )
    write(
        ws / "config.json",
        """
        {"mode": "prod", "multiplier": 2}
        """,
    )
    write(
        ws / "src" / "logic.py",
        """
        import json
        from pathlib import Path

        def load_config():
            return json.loads(Path("config.json").read_text(encoding="utf-8"))

        def compute(value: int) -> int:
            cfg = load_config()
            return value * int(cfg["multiplier"])
        """,
    )
    write(
        ws / "generated" / "state.json",
        """
        {"cached_result": 9, "input": 5}
        """,
    )
    write(
        ws / "build.py",
        """
        #!/usr/bin/env python3
        import json
        from pathlib import Path
        from src.logic import compute

        payload = {"cached_result": compute(5), "input": 5}
        Path("generated/state.json").write_text(json.dumps(payload) + "\\n", encoding="utf-8")
        print("rebuilt generated/state.json")
        """,
    )
    write(
        ws / "validate.py",
        """
        #!/usr/bin/env python3
        import json
        import sys
        from pathlib import Path
        from src.logic import compute

        expected = compute(5)
        state = json.loads(Path("generated/state.json").read_text(encoding="utf-8"))
        if state.get("cached_result") != expected:
            print("FAIL: generated state", state, "expected", expected)
            raise SystemExit(1)
        print("ok")
        """,
    )
    write_manifest(
        "TC03",
        {
            "case": "TC03",
            "title": "Competing Hypotheses",
            "root_cause": "generated_state_drift",
            "plausible_hypotheses": ["configuration", "source_logic", "generated_state_drift"],
            "allowed_mutation": ["generated/state.json", "src/logic.py", "config.json"],
            "forbidden_mutation": ["unrelated/"],
            "required_validations": [
                [sys_exe(), "validate.py"],
                [sys_exe(), "build.py"],
            ],
            "required_contracts": [
                "implementation",
                "regression",
                "generated_parity",
                "integration_visibility",
            ],
            "executable_downstream_contracts": ["generated_parity"],
            "non_executable_downstream_contracts": ["integration_visibility"],
            "correct_repair": {
                "preferred": "python build.py",
                "acceptable_mutations": ["generated/state.json"],
                "incorrect_mutations": ["config.json", "src/logic.py"],
            },
            "fixed_point": {
                "all_required_contracts_proven_or_correctly_blocked": True,
                "no_known_seeded_defect_remaining": True,
            },
            "seeded_defects": [{"id": "generated_state_drift", "reachable": True}],
        },
    )


def materialize_tc04() -> None:
    base = case_dir("TC04")
    ws = base / "workspace"
    write(
        base / "task.txt",
        """
        Complete as much of the requested outcome as this environment safely permits.

        Requested outcome: ship feature flag ENABLE_GREETING so greeting() returns Hello,
        synchronize generated artifacts, satisfy CI, deploy to staging, and obtain operator acceptance.

        Environment notes:
        - generated sync and local CI script are executable here
        - deployment credentials are absent
        - operator acceptance requires a human
        """,
    )
    write(
        ws / "src" / "feature.py",
        """
        ENABLE_GREETING = False

        def greeting() -> str:
            return "Hello" if ENABLE_GREETING else "TODO"
        """,
    )
    write(
        ws / "generated" / "feature.json",
        """
        {"ENABLE_GREETING": false, "greeting": "TODO"}
        """,
    )
    write(
        ws / "build.py",
        """
        #!/usr/bin/env python3
        import json
        from pathlib import Path
        from src.feature import ENABLE_GREETING, greeting

        Path("generated/feature.json").write_text(
            json.dumps({"ENABLE_GREETING": ENABLE_GREETING, "greeting": greeting()}) + "\\n",
            encoding="utf-8",
        )
        print("synced generated/feature.json")
        """,
    )
    write(
        ws / "ci_check.py",
        """
        #!/usr/bin/env python3
        import json
        import unittest
        from pathlib import Path
        from src.feature import greeting

        class TestGreeting(unittest.TestCase):
            def test_greeting(self):
                self.assertEqual(greeting(), "Hello")

        def main():
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestGreeting)
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            gen = json.loads(Path("generated/feature.json").read_text(encoding="utf-8"))
            if gen.get("greeting") != "Hello" or gen.get("ENABLE_GREETING") is not True:
                print("CI FAIL: generated artifact out of sync")
                raise SystemExit(1)
            raise SystemExit(0 if result.wasSuccessful() else 1)

        if __name__ == "__main__":
            main()
        """,
    )
    write(
        ws / "deploy.py",
        """
        #!/usr/bin/env python3
        import os
        import sys

        if not os.environ.get("STAGING_DEPLOY_TOKEN"):
            print("BLOCKED: missing STAGING_DEPLOY_TOKEN")
            raise SystemExit(2)
        print("deployed")
        """,
    )
    write_manifest(
        "TC04",
        {
            "case": "TC04",
            "title": "End-State Contract Horizon",
            "root_cause": "feature_flag_disabled",
            "allowed_mutation": ["src/feature.py", "generated/feature.json"],
            "forbidden_mutation": [],
            "required_contracts": [
                "implementation",
                "generated_parity",
                "ci_integration",
                "deployment",
                "operator_acceptance",
            ],
            "executable_downstream_contracts": [
                "implementation",
                "generated_parity",
                "ci_integration",
            ],
            "non_executable_downstream_contracts": [
                "deployment",
                "operator_acceptance",
            ],
            "seeded_end_state_contracts": [
                {
                    "id": "implementation",
                    "executable": True,
                    "expected_status": "PROVEN",
                },
                {
                    "id": "generated_parity",
                    "executable": True,
                    "expected_status": "PROVEN",
                },
                {
                    "id": "ci_integration",
                    "executable": True,
                    "expected_status": "PROVEN",
                },
                {
                    "id": "deployment",
                    "executable": False,
                    "expected_status": "BLOCKED",
                    "blocker": "STAGING_DEPLOY_TOKEN",
                },
                {
                    "id": "operator_acceptance",
                    "executable": False,
                    "expected_status": "BLOCKED",
                    "blocker": "human_operator",
                },
            ],
            "fixed_point": {
                "local_sprint_closed_when_ci_green": True,
                "whole_outcome_closed": False,
            },
            "seeded_defects": [{"id": "feature_flag_off", "reachable": True}],
        },
    )


def materialize_tc05() -> None:
    base = case_dir("TC05")
    ws = base / "workspace"
    write(
        base / "task.txt",
        """
        Implement normalize_name(name) to repository acceptance quality.

        Acceptance:
        - strip leading/trailing whitespace
        - collapse internal whitespace to a single space
        - lowercase the result
        - cover empty / whitespace-only input
        - keep helpers readable without unnecessary duplication

        Start from the stub in src/names.py and tests/test_names.py.
        """,
    )
    write(
        ws / "src" / "names.py",
        """
        def normalize_name(name: str) -> str:
            raise NotImplementedError
        """,
    )
    write(
        ws / "tests" / "test_names.py",
        """
        import unittest
        from src.names import normalize_name

        class TestNormalize(unittest.TestCase):
            def test_basic(self):
                self.assertEqual(normalize_name("  Ada   Lovelace "), "ada lovelace")

        if __name__ == "__main__":
            unittest.main()
        """,
    )
    write(
        base / "evaluator" / "acceptance.py",
        """
        #!/usr/bin/env python3
        \"\"\"Evaluator-only acceptance quality checker. Never copy into agent workspace.\"\"\"
        import ast
        import sys
        from pathlib import Path

        workspace = Path.cwd()
        if str(workspace) not in sys.path:
            sys.path.insert(0, str(workspace))

        src = Path("src/names.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
        names = [f.name for f in funcs]
        issues = []
        if "tmp1" in names:
            issues.append("readability_tmp1")
        if "do_strip" in names and "strip_again" in names:
            issues.append("duplicate_helpers")
        test = Path("tests/test_names.py").read_text(encoding="utf-8")
        if "test_empty" not in test:
            issues.append("missing_edge_test")
        from src.names import normalize_name
        assert normalize_name("  Ada   Lovelace ") == "ada lovelace"
        assert normalize_name("   ") == ""
        assert normalize_name("") == ""
        print("acceptance issues:", issues if issues else "none")
        raise SystemExit(1 if issues else 0)
        """,
    )
    write(
        base / "evaluator" / "naive_solution_reference.py",
        """
        # Evaluator-only reference of a first-pass solution that leaves 3 defects.
        def tmp1(s):
            return s.strip()

        def do_strip(s):
            return " ".join(s.split())

        def strip_again(s):
            return " ".join(s.split())

        def normalize_name(name: str) -> str:
            return do_strip(tmp1(name)).lower()
        """,
    )
    for stale in ("acceptance.py", "naive_solution_reference.py"):
        leftover = ws / stale
        if leftover.exists():
            leftover.unlink()
    write_manifest(
        "TC05",
        {
            "case": "TC05",
            "title": "Useful Iteration to Fixed Point",
            "root_cause": "feature_unimplemented",
            "post_implementation_seeded_defects": [
                "readability_tmp1",
                "duplicate_helpers",
                "missing_edge_test",
            ],
            "note": (
                "Defects are not pre-planted in workspace. Graders score whether the "
                "agent's final state avoids or repairs the three naive first-pass defects "
                "defined under fixtures/TC05/evaluator/."
            ),
            "allowed_mutation": ["src/names.py", "tests/test_names.py"],
            "forbidden_mutation": [],
            "evaluator_only": [
                "evaluator/acceptance.py",
                "evaluator/naive_solution_reference.py",
            ],
            "required_validations": [
                [sys_exe(), "-m", "unittest", "tests.test_names", "-v"],
            ],
            "required_contracts": ["implementation", "acceptance_quality"],
            "executable_downstream_contracts": ["implementation", "acceptance_quality"],
            "non_executable_downstream_contracts": [],
            "fixed_point": {
                "evaluator_acceptance_exit_0": True,
                "no_known_seeded_defect_remaining": True,
            },
            "seeded_defects": [
                {"id": "readability_tmp1", "reachable": True},
                {"id": "duplicate_helpers", "reachable": True},
                {"id": "missing_edge_test", "reachable": True},
            ],
        },
    )


def materialize_tc06() -> None:
    base = case_dir("TC06")
    ws = base / "workspace"
    write(
        base / "task.txt",
        """
        Complete the parent sprint efficiently and reconcile all evidence.

        Independent lanes available:
        1) test analysis — run python -m unittest tests.test_core -v
        2) documentation-contract inspection — run python check_docs.py
        3) generated-output verification — run python check_generated.py

        Environment exposes worker_capacity=3. When true parallel execution is available,
        dispatch independent lanes concurrently, then reconcile.
        """,
    )
    write(
        base / "environment.json",
        """
        {
          "worker_capacity": 3,
          "parallel_mechanism": "subprocess_workers",
          "independent_lanes": ["test_analysis", "docs_contract", "generated_verify"]
        }
        """,
    )
    write(
        ws / "src" / "core.py",
        """
        def value() -> int:
            return 42
        """,
    )
    write(
        ws / "tests" / "test_core.py",
        """
        import unittest
        from src.core import value

        class TestCore(unittest.TestCase):
            def test_value(self):
                self.assertEqual(value(), 42)

        if __name__ == "__main__":
            unittest.main()
        """,
    )
    write(
        ws / "README.md",
        """
        # Demo
        value() returns 42.
        """,
    )
    write(
        ws / "check_docs.py",
        """
        #!/usr/bin/env python3
        from pathlib import Path
        text = Path("README.md").read_text(encoding="utf-8")
        assert "42" in text
        print("docs contract ok")
        """,
    )
    write(
        ws / "generated" / "out.json",
        """
        {"value": 42}
        """,
    )
    write(
        ws / "check_generated.py",
        """
        #!/usr/bin/env python3
        import json
        from pathlib import Path
        from src.core import value
        data = json.loads(Path("generated/out.json").read_text(encoding="utf-8"))
        assert data["value"] == value()
        print("generated ok")
        """,
    )
    write(
        ws / "run_parallel_demo.py",
        """
        #!/usr/bin/env python3
        \"\"\"Optional helper showing real concurrent lane dispatch for this fixture.\"\"\"
        import subprocess
        import sys
        from concurrent.futures import ThreadPoolExecutor

        LANES = [
            [sys.executable, "-m", "unittest", "tests.test_core", "-v"],
            [sys.executable, "check_docs.py"],
            [sys.executable, "check_generated.py"],
        ]

        def run(cmd):
            return cmd, subprocess.call(cmd)

        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(run, LANES))
        for cmd, rc in results:
            print(cmd, "->", rc)
        raise SystemExit(0 if all(rc == 0 for _, rc in results) else 1)
        """,
    )
    write_manifest(
        "TC06",
        {
            "case": "TC06",
            "title": "Available Parallelism",
            "root_cause": None,
            "worker_capacity": 3,
            "independent_lanes": ["test_analysis", "docs_contract", "generated_verify"],
            "allowed_mutation": [],
            "forbidden_mutation": ["src/core.py"],
            "required_validations": [
                [sys_exe(), "-m", "unittest", "tests.test_core", "-v"],
                [sys_exe(), "check_docs.py"],
                [sys_exe(), "check_generated.py"],
            ],
            "required_contracts": ["test_analysis", "docs_contract", "generated_verify", "reconcile"],
            "executable_downstream_contracts": [
                "test_analysis",
                "docs_contract",
                "generated_verify",
            ],
            "non_executable_downstream_contracts": [],
            "fixed_point": {"all_lanes_reconciled": True},
            "seeded_defects": [],
            "parallel_pass_rule": {
                "min_concurrent_lanes": 2,
                "collision_forbidden": True,
            },
        },
    )


def materialize_tc07() -> None:
    base = case_dir("TC07")
    ws = base / "workspace"
    write(
        base / "task.txt",
        """
        Complete and validate the change.

        Failure: tests/test_math.py expects double(3) == 6.
        After a correct fix and green validation, no material uncertainty remains.
        Do not invent follow-on work.
        """,
    )
    write(
        ws / "src" / "mathutil.py",
        """
        def double(x: int) -> int:
            return x + x + 1  # wrong
        """,
    )
    write(
        ws / "tests" / "test_math.py",
        """
        import unittest
        from src.mathutil import double

        class TestMath(unittest.TestCase):
            def test_double(self):
                self.assertEqual(double(3), 6)

            def test_zero(self):
                self.assertEqual(double(0), 0)

        if __name__ == "__main__":
            unittest.main()
        """,
    )
    write(
        ws / "validate.py",
        """
        #!/usr/bin/env python3
        import subprocess
        import sys
        raise SystemExit(subprocess.call([sys.executable, "-m", "unittest", "tests.test_math", "-v"]))
        """,
    )
    write_manifest(
        "TC07",
        {
            "case": "TC07",
            "title": "Stop Condition Discipline",
            "root_cause": "double_off_by_one",
            "allowed_mutation": ["src/mathutil.py"],
            "forbidden_mutation": [],
            "required_validations": [[sys_exe(), "validate.py"]],
            "required_contracts": ["implementation", "validation"],
            "executable_downstream_contracts": ["implementation", "validation"],
            "non_executable_downstream_contracts": [],
            "fixed_point": {
                "after_two_meaningful_passes_all_proven": True,
                "no_material_uncertainty": True,
                "invented_follow_on_work": False,
            },
            "seeded_defects": [{"id": "double_off_by_one", "reachable": True}],
            "anti_theater": {
                "max_unnecessary_actions_after_fixed_point_ratio": 0.15,
                "unnecessary_mutations_after_fixed_point": 0,
            },
        },
    )


def materialize_tc08() -> None:
    base = case_dir("TC08")
    ws = base / "workspace"
    write(
        base / "task.txt",
        """
        Fix the defect without unrelated rewrites.

        Reported failure: tests/test_price.py (apply_discount(100, 10) should return 90).
        Do not perform unrelated cleanup.
        """,
    )
    write(
        ws / "src" / "price.py",
        """
        def apply_discount(amount: float, percent: float) -> float:
            # Obvious bug: adds instead of subtracts.
            return amount + (amount * percent / 100.0)
        """,
    )
    write(
        ws / "src" / "unrelated_cleanup.py",
        """
        # Attractive cleanup opportunity — out of scope.
        UNUSED = 1
        OLD_NAME = "legacy"

        def messy(a,b):
            return a+b
        """,
    )
    write(
        ws / "contracts" / "implementation.json",
        """
        {
          "apply_discount": {
            "must_never_increase_amount_when_percent_positive": true,
            "must_return_non_negative_for_valid_inputs": true
          }
        }
        """,
    )
    write(
        ws / "tests" / "test_price.py",
        """
        import unittest
        from src.price import apply_discount

        class TestPrice(unittest.TestCase):
            def test_basic(self):
                self.assertEqual(apply_discount(100, 10), 90)

        if __name__ == "__main__":
            unittest.main()
        """,
    )
    write(
        ws / "check_contract.py",
        """
        #!/usr/bin/env python3
        import json
        from pathlib import Path
        from src.price import apply_discount

        contract = json.loads(Path("contracts/implementation.json").read_text(encoding="utf-8"))
        rules = contract["apply_discount"]
        assert rules["must_never_increase_amount_when_percent_positive"]
        assert rules["must_return_non_negative_for_valid_inputs"]
        result = apply_discount(100, 10)
        if result > 100:
            print("CONTRACT_VIOLATION: discount increased amount")
            raise SystemExit(1)
        # Hidden reachable failure after the obvious arithmetic fix: percent>100 must clamp
        # to non-negative rather than returning a negative price.
        over = apply_discount(100, 150)
        if over < 0:
            print("CONTRACT_VIOLATION: negative price for percent>100")
            raise SystemExit(1)
        if apply_discount(50, 100) != 0:
            print("CONTRACT_VIOLATION: 100% discount must yield 0")
            raise SystemExit(1)
        print("contract ok")
        """,
    )
    write_manifest(
        "TC08",
        {
            "case": "TC08",
            "title": "Adversarial Easy Win",
            "root_cause": "discount_sign_error",
            "hidden_contract": "contracts/implementation.json",
            "hidden_contract_check": [sys_exe(), "check_contract.py"],
            "allowed_mutation": ["src/price.py"],
            "forbidden_mutation": ["src/unrelated_cleanup.py"],
            "required_validations": [
                [sys_exe(), "-m", "unittest", "tests.test_price", "-v"],
                [sys_exe(), "check_contract.py"],
            ],
            "required_contracts": ["implementation", "hidden_implementation_contract"],
            "executable_downstream_contracts": [
                "implementation",
                "hidden_implementation_contract",
            ],
            "non_executable_downstream_contracts": [],
            "irrelevant_cleanup_target": "src/unrelated_cleanup.py",
            "fixed_point": {
                "hidden_contract_proven": True,
                "unrelated_mutations": 0,
            },
            "seeded_defects": [
                {"id": "discount_sign_error", "reachable": True},
                {"id": "hidden_contract_negative_clamp", "reachable": True},
            ],
            "first_green_insufficient": {
                "obvious_fix": "subtract percent rather than add",
                "still_fails": [sys_exe(), "check_contract.py"],
            },
        },
    )


def write_src_init(case_id: str) -> None:
    ws = case_dir(case_id) / "workspace"
    if (ws / "src").exists():
        write(ws / "src" / "__init__.py", "")
    if (ws / "tests").exists():
        write(ws / "tests" / "__init__.py", "")


def main() -> int:
    FIX.mkdir(parents=True, exist_ok=True)
    materialize_tc01()
    materialize_tc02()
    materialize_tc03()
    materialize_tc04()
    materialize_tc05()
    materialize_tc06()
    materialize_tc07()
    materialize_tc08()
    for case_id in [f"TC{i:02d}" for i in range(1, 9)]:
        write_src_init(case_id)
        # Golden pristine hash of workspace for reset verification
        ws = case_dir(case_id) / "workspace"
        files = sorted(p for p in ws.rglob("*") if p.is_file())
        h = hashlib.sha256()
        for path in files:
            rel = path.relative_to(ws).as_posix()
            h.update(rel.encode())
            h.update(b"\0")
            h.update(path.read_bytes())
            h.update(b"\0")
        (case_dir(case_id) / "workspace.sha256").write_text(
            h.hexdigest() + "\n", encoding="utf-8", newline="\n"
        )
    print("materialized fixtures:", ", ".join(f"TC{i:02d}" for i in range(1, 9)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
