from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


prompts_path = ROOT / "docs/prompts.json"
prompts = load(prompts_path)
by_id = {p["id"]: p for p in prompts}

executable = """EXECUTABLE MANIFEST CONTRACT
- The primary dispatch artifact is JSON at `Outputs/prompt-parallel-dispatch/manifest.json` conforming to `harness/contracts/prompt-parallel-dispatch.v1.json`; prose, a lane table, or copy panels alone do not satisfy this gate.
- Validate it before dispatch: `python scripts/prompt_parallel_dispatch.py validate --manifest Outputs/prompt-parallel-dispatch/manifest.json`.
- For command-addressable `argv` lanes, execute the manifest rather than narrating it: `python scripts/prompt_parallel_dispatch.py run --manifest Outputs/prompt-parallel-dispatch/manifest.json --receipt Outputs/prompt-parallel-dispatch/receipt.json`, then verify with `python scripts/prompt_parallel_dispatch.py verify-receipt --manifest Outputs/prompt-parallel-dispatch/manifest.json --receipt Outputs/prompt-parallel-dispatch/receipt.json`.
- For `runtime_tool` lanes, the active agent runtime must consume the typed tool/operation/arguments records, perform the actual tool/API calls, preserve returned evidence in a compatible receipt, and run `verify-receipt`. The repository CLI must not impersonate an unavailable runtime tool.
- Validation without launch is not dispatch proof. A REQUIRED width >= 2 receipt must prove `observed_parallelism=true`; DEGRADED execution may never do so."""

manifest_tail = "The manifest is the primary orchestration artifact. Copyable chat panels may mirror it for portability, but a plan that requires the operator to launch dependency-ready lanes manually is not automation-complete."
for pid in ("P04", "P59"):
    prompt = by_id[pid]
    if "EXECUTABLE MANIFEST CONTRACT" not in prompt["copyContent"]:
        if manifest_tail not in prompt["copyContent"]:
            raise SystemExit(f"{pid} manifest tail missing")
        prompt["copyContent"] = prompt["copyContent"].replace(
            manifest_tail,
            manifest_tail + "\n\n" + executable,
            1,
        )
    if "real JSON artifact" not in prompt["expectedOutput"]:
        prompt["expectedOutput"] += " The dispatch manifest is a real JSON artifact validated against the repository contract, not prose-only planning."
    if "prompt_parallel_dispatch.py" not in prompt["proofGate"]:
        prompt["proofGate"] += " The JSON manifest validates through `scripts/prompt_parallel_dispatch.py`; command-addressable lanes are actually launched from it or runtime-tool lanes return separately verifiable tool/API receipts."
    if "Validate the JSON manifest" not in prompt["nextStep"]:
        prompt["nextStep"] += " Validate the JSON manifest with `scripts/prompt_parallel_dispatch.py` before P07 consumes it."

p07 = by_id["P07"]
if "EXECUTABLE MANIFEST CONTRACT" not in p07["copyContent"]:
    anchor = "- A fresh P04/P59 dispatch manifest is reusable after refreshing it against the current repository floor. Do not replan merely to satisfy the dispatch gate."
    if anchor not in p07["copyContent"]:
        raise SystemExit("P07 dispatch-manifest anchor missing")
    p07["copyContent"] = p07["copyContent"].replace(anchor, executable + "\n" + anchor, 1)
if "contract-valid manifest plus an observed dispatch receipt" not in p07["expectedOutput"]:
    p07["expectedOutput"] += " Required parallelism closes only with a contract-valid manifest plus an observed dispatch receipt; prose-only lane plans are not execution proof."
if "Before claiming parallel dispatch" not in p07["nextStep"]:
    p07["nextStep"] += " Before claiming parallel dispatch, validate the manifest and execute/verify it through `scripts/prompt_parallel_dispatch.py` for argv lanes or consume typed runtime_tool records through the active agent runtime and verify the resulting receipt."
if "prompt-parallel-dispatch-receipt/v1" not in p07["proofGate"]:
    p07["proofGate"] += " A REQUIRED width >= 2 claim must include a valid `prompt-parallel-dispatch/v1` artifact and a `prompt-parallel-dispatch-receipt/v1` with observed_parallelism=true; manifest validation alone or prose-only lanes are insufficient."
dump(prompts_path, prompts)

overrides_path = ROOT / "registry/prompts/prompt-overrides.v1.json"
overrides = load(overrides_path)
p13 = next(p for p in overrides["overrides"] if p["id"] == "P13")
if "prompt_parallel_dispatch.py" not in p13["copyContent"]:
    anchor = "- P13 remains recurrence/prevention/convergence owner; P07 remains actual execution owner. Do not duplicate P07's full worker protocol here."
    replacement = "- P07 must consume a contract-valid JSON dispatch artifact through `scripts/prompt_parallel_dispatch.py` or the declared runtime_tool adapter; a prose lane list is not dispatch evidence.\n" + anchor
    if anchor not in p13["copyContent"]:
        raise SystemExit("P13 owner anchor missing")
    p13["copyContent"] = p13["copyContent"].replace(anchor, replacement, 1)
dump(overrides_path, overrides)

spec_path = ROOT / "harness/specs/prompt-operations.md"
spec = spec_path.read_text(encoding="utf-8")
marker = "Copyable chat panels are portability/recovery fallback only. Do not make the operator create chats, paste prompts, shuttle context, or act as the scheduler when any autonomous adapter can carry the lane."
addition = """

Canonical executable surfaces:

- contract: `harness/contracts/prompt-parallel-dispatch.v1.json`;
- manifest: `Outputs/prompt-parallel-dispatch/manifest.json` using `prompt-parallel-dispatch/v1`;
- validator/argv dispatcher: `scripts/prompt_parallel_dispatch.py`;
- receipt: `Outputs/prompt-parallel-dispatch/receipt.json` using `prompt-parallel-dispatch-receipt/v1`;
- `validate` must pass before launch; `run` launches command-addressable lanes in deterministic dependency waves; `verify-receipt` rejects REQUIRED width >= 2 claims without observed parallel dispatch evidence;
- `runtime_tool` records remain machine-readable but are executed only by the active agent runtime. The CLI fails closed rather than pretending to own unavailable tool APIs.

A planning response that prints manifest-shaped prose without materializing and validating the JSON artifact is incomplete. A validated manifest without actual launch/receipt evidence is planning/validation proof, not parallel execution proof."""
if "Canonical executable surfaces:" not in spec:
    if marker not in spec:
        raise SystemExit("parallel spec marker missing")
    spec = spec.replace(marker, marker + addition, 1)
spec_path.write_text(spec, encoding="utf-8")

test_path = ROOT / "tests/test_p02_p07_autonomous_iteration.py"
test = test_path.read_text(encoding="utf-8")
needle = '        self.assertIn("paradigm/P128", prompt["proofGate"])\n'
ordering = '''        probe = content.index("Probe execution adapters in order")
        missing_one = content.index("no connected self-hosted workers")
        dispatch = content.index("At the first safe rung")
        degraded = content.index("If graph width is at least two but every safe rung")
        self.assertLess(probe, missing_one)
        self.assertLess(missing_one, dispatch)
        self.assertLess(dispatch, degraded)
        self.assertNotIn("If no usable mechanism exists", content)
        self.assertNotIn("no connected self-hosted workers. Proceeding serially", content)
        self.assertIn("scripts/prompt_parallel_dispatch.py validate", content)
        self.assertIn("scripts/prompt_parallel_dispatch.py run", content)
        self.assertIn("observed_parallelism=true", content)
'''
if 'missing_one = content.index("no connected self-hosted workers")' not in test:
    if needle not in test:
        raise SystemExit("P07 test insertion point missing")
    test = test.replace(needle, needle + ordering, 1)
fallback_needle = '        self.assertIn("User scheduling is never the fallback", prompt["expectedOutput"])\n'
fallback_extra = '''        self.assertNotIn("PARALLEL EXECUTION: unavailable", content)
        self.assertNotIn("proceed serially", content)
        self.assertIn("If graph width is at least two but every safe rung is genuinely unavailable or blocked", content)
        self.assertIn("serial progress may continue only to avoid deadlock", content)
'''
if 'self.assertNotIn("PARALLEL EXECUTION: unavailable", content)' not in test:
    if fallback_needle not in test:
        raise SystemExit("P07 fallback test insertion point missing")
    test = test.replace(fallback_needle, fallback_needle + fallback_extra, 1)
test_path.write_text(test, encoding="utf-8")
