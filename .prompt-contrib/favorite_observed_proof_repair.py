from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_IMPL_COMMIT = "c1a299a6d7c3ad02f7a4ac2868d8cb9fc52341b3"


def replace_exact(path: str, old: str, new: str, expected: int = 1) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"{path}: expected {expected} anchor(s), found {count}: {old[:120]!r}")
    target.write_text(text.replace(old, new), encoding="utf-8", newline="\n")


# Preserve the last known-good implementation/harness prototype, then refine only
# the uncertainties falsified by runtime evidence. The pinned source is part of
# this branch history and checkout uses fetch-depth: 0.
base_script = subprocess.check_output(
    ["git", "show", f"{BASE_IMPL_COMMIT}:.prompt-contrib/favorite_observed_proof_repair.py"],
    cwd=ROOT,
    text=True,
)
exec_globals = {
    "__name__": "favorite_observed_proof_base",
    "__file__": str(ROOT / ".prompt-contrib/favorite_observed_proof_repair.py"),
}
exec(compile(base_script, f"{BASE_IMPL_COMMIT}:favorite_observed_proof_repair.py", "exec"), exec_globals)

# Iteration 2 measurement refinement: smooth scrolling is asynchronous. Observe
# the actual viewport condition instead of assuming a fixed 250 ms delay proves
# success or failure.
replace_exact(
    "tests/prompt_kit_favorite_browser_proof.py",
    """            page.keyboard.press('9')
            page.wait_for_timeout(250)
            toast_text = page.locator('#toast').inner_text()
""",
    """            page.keyboard.press('9')
            try:
                page.wait_for_function(\"\"\"() => {
                  const card=document.querySelector('[data-prompt-id=\\\"P79\\\"]');
                  if(!card)return false;
                  const r=card.getBoundingClientRect();
                  return r.bottom>0 && r.top<innerHeight;
                }\"\"\", timeout=4000)
            except Exception:
                pass
            toast_text = page.locator('#toast').inner_text()
""",
)

# A failure receipt is evidence, but it must never validate as a successful
# proof. This closes the remaining fail-open verdict path found during critique.
replace_exact(
    "scripts/validate_observed_behavior_receipt.py",
    """    if receipt.get(\"verdict\") == \"PASS\" and any(c.get(\"status\") != \"PASS\" for c in claims):
        errors.append(\"overall PASS requires every claim to PASS\")
    return errors
""",
    """    verdict = receipt.get(\"verdict\")
    if verdict != \"PASS\":
        errors.append(f\"receipt verdict is {verdict}, not PASS\")
    elif any(c.get(\"status\") != \"PASS\" for c in claims):
        errors.append(\"overall PASS requires every claim to PASS\")
    return errors
""",
)

replace_exact(
    "tests/test_observed_behavior_proof_harness.py",
    """    def test_prompt_owners_require_observed_outcome_gate(self):
""",
    """    def test_non_pass_receipt_cannot_validate_as_success(self):
        for verdict in (\"FAIL\", \"UNKNOWN\", \"UNPROVEN\", None):
            receipt = self.base_receipt()
            receipt[\"verdict\"] = verdict
            self.assertTrue(any(\"not PASS\" in e for e in MOD.validate(receipt)))

    def test_prompt_owners_require_observed_outcome_gate(self):
""",
)

# Deliberately prove that the refined observer and verdict guard are present
# before the canonical site is certified by the owning workflow.
proof = (ROOT / "tests/prompt_kit_favorite_browser_proof.py").read_text(encoding="utf-8")
if "page.wait_for_function" not in proof or "timeout=4000" not in proof:
    raise SystemExit("browser proof did not adopt observed-destination synchronization")
validator = (ROOT / "scripts/validate_observed_behavior_receipt.py").read_text(encoding="utf-8")
if "receipt verdict is {verdict}, not PASS" not in validator:
    raise SystemExit("receipt validator still permits non-PASS evidence to certify")

print("favorite observed-proof prototype refined from runtime falsification evidence")
