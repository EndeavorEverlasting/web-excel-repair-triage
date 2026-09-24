"""triage/desktop_iterate.py

Iterative repair loop driven by *desktop Excel* (canonical truth).

Loop:
  open in desktop Excel (try repair) -> collect recovered copy + error*.xml ->
  diff vs repaired copy -> detect patterns -> generate recipe -> apply recipe -> repeat

This is intended for Windows where Excel + pywin32 are available.
"""

from __future__ import annotations

import dataclasses
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from triage.diff import diff_packages
from triage.excel_desktop import ExcelDesktopProbeResult, probe_open_in_desktop_excel_isolated
from triage.gate_checks import run_all as run_gates
from triage.patcher import PatchError, PatchWarning, apply_recipe
from triage.patterns import detect_all
from triage.report import merge_recipes, recipe_from_gates, recipe_from_patterns


def _safe_stem(path: str) -> str:
    s = Path(path).stem
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", s)
    return s.strip("._-") or "workbook"


@dataclass
class DesktopIterStep:
    iteration: int
    input_path: str
    probe_out_dir: str
    opened: bool
    fatal: bool
    dialogs: int
    recovery_logs: int
    repaired_copy_path: Optional[str] = None
    exception: Optional[str] = None
    recipe_patch_count: int = 0
    patched_path: Optional[str] = None
    note: Optional[str] = None


@dataclass
class DesktopIterateResult:
    original_path: str
    final_path: str
    success_clean: bool
    steps: List[DesktopIterStep] = field(default_factory=list)


def _is_clean(probe: ExcelDesktopProbeResult) -> bool:
    return bool(probe.opened) and (not probe.fatal) and (len(probe.dialogs) == 0) and (len(probe.recovery_logs) == 0)


def iterate_until_desktop_clean(
    candidate_path: str,
    out_root: str = "Outputs/desktop_iter",
    max_iters: int = 5,
    timeout_seconds: int = 15,
) -> DesktopIterateResult:
    out_dir = Path(out_root)
    out_dir.mkdir(parents=True, exist_ok=True)

    current = str(Path(candidate_path))
    steps: List[DesktopIterStep] = []

    for i in range(int(max_iters)):
        probe = probe_open_in_desktop_excel_isolated(
            candidate_path=current,
            out_root=str(out_dir / "excel_runs"),
            visible=True,
            try_repair=True,
            save_repaired_copy=True,
            timeout_seconds=int(timeout_seconds),
        )

        step = DesktopIterStep(
            iteration=i + 1,
            input_path=current,
            probe_out_dir=probe.out_dir,
            opened=bool(probe.opened),
            fatal=bool(probe.fatal),
            dialogs=len(probe.dialogs),
            recovery_logs=len(probe.recovery_logs),
            repaired_copy_path=probe.repaired_copy_path,
            exception=probe.exception,
        )
        steps.append(step)

        if _is_clean(probe):
            return DesktopIterateResult(original_path=candidate_path, final_path=current, success_clean=True, steps=steps)

        # Build a patch recipe.
        # Primary path: when Excel produced a repaired copy, diff against it and
        # mine concrete fixes.
        # Fallback path: when Excel cannot produce a repaired copy within the
        # time budget, still apply the deterministic gate-based fixes and retry.
        gate = run_gates(current)
        if probe.repaired_copy_path:
            diff = diff_packages(current, probe.repaired_copy_path)
            patterns = detect_all(diff)
            recipe = merge_recipes(
                recipe_from_gates(gate),
                recipe_from_patterns(current, patterns, diff_report=diff),
            )
        else:
            recipe = recipe_from_gates(gate)
            step.note = "No repaired copy was produced by Excel; applying gate-only patches and retrying."
        step.recipe_patch_count = len(recipe.patches)

        if not recipe.patches:
            step.note = step.note or "No patch operations generated from gates/patterns; stopping."
            break

        patched_path = out_dir / f"{_safe_stem(current)[:50]}_iter{i+1}.xlsx"
        try:
            step.patched_path = apply_recipe(current, recipe.to_dict(), output_path=str(patched_path))
            current = step.patched_path
        except PatchWarning as w:
            # Output is still written; continue.
            step.note = f"PatchWarning: {w}"
            step.patched_path = getattr(w, "output_path", None) or str(patched_path)
            current = step.patched_path
        except (PatchError, Exception) as e:
            step.note = f"Patch failed: {type(e).__name__}: {e}"
            break

    return DesktopIterateResult(original_path=candidate_path, final_path=current, success_clean=False, steps=steps)


def _cli() -> int:  # pragma: no cover
    import argparse

    ap = argparse.ArgumentParser(description="Iterate repairs until desktop Excel opens cleanly")
    ap.add_argument("--file", required=True)
    ap.add_argument("--out", default="Outputs/desktop_iter")
    ap.add_argument("--max-iters", type=int, default=5)
    ap.add_argument("--timeout", type=int, default=15)
    args = ap.parse_args()

    r = iterate_until_desktop_clean(args.file, out_root=args.out, max_iters=args.max_iters, timeout_seconds=args.timeout)
    payload = dataclasses.asdict(r)
    (Path(args.out) / f"{_safe_stem(args.file)}_desktop_iterate.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if r.success_clean else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())

