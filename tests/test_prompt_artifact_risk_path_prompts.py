from __future__ import annotations
import json, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_prompt_kit_registry

class PromptArtifactRiskPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prompts = build_prompt_kit_registry.load_prompt_registry()
        cls.by_id = {p["id"]: p for p in cls.prompts}
    def test_p50_machine_shell_path_and_freshness(self):
        p=self.by_id["P50"]; c=p["copyContent"]
        self.assertEqual(p["name"], "Directory-First Repository Command Guard")
        self.assertEqual(p["copySheet"], "P50_COPY_SAFE")
        for m in ("MACHINE / OS / SHELL GATE","REMOTE FRESHNESS GATE","COMMAND EMISSION GATE","Windows PowerShell, PowerShell 7+, CMD, Git Bash, WSL/Linux, macOS","git fetch --all --prune --tags","refs/remotes/origin/HEAD","git pull --ff-only","P61 Existing Repository Clone + Working-Directory Bootstrapper","Do not infer OS, shell, path separator"):
            self.assertIn(m,c)
        self.assertIn("operating system",p["useWhen"].lower()); self.assertIn("shell",p["proofGate"].lower()); self.assertIn("remote",p["proofGate"].lower())
    def test_p97_bounded_artifact_risk_analysis(self):
        matches=[p for p in self.prompts if p["name"]=="Artifact Risk Review & Triage"]
        self.assertEqual(len(matches),1); p=matches[0]
        self.assertEqual((p["id"],p["seq"],p["copySheet"]),("P97","97","P97_COPY_SAFE"))
        self.assertEqual(p["class"],"ANALYSIS / ARTIFACT RISK TRIAGE")
        for m in ("OBSERVED","INFERRED","UNKNOWN","PASS 2 — CROSS-ARTIFACT / PROVENANCE REVIEW","DO NOT JUMP STRAIGHT INTO REPAIR","P91 Failure-Class Generalization & Repository Audit","P92 Production-Path Proof Gap Auditor","P93 Use-Case Closure Certification","P94 Regression Test & Live Behavior Guard","If no material risk is supported"):
            self.assertIn(m,p["copyContent"])
        self.assertIn("real defect",self.by_id["P91"]["useWhen"].lower()); self.assertNotIn("real defect",p["useWhen"].lower())
    def test_raw_and_generated_parity(self):
        spec=json.loads((ROOT/"registry/prompts/spec-architecture-prompts.v1.json").read_text(encoding="utf-8"))
        raw=next(p for p in spec["prompts"] if p["id"]=="P97")
        self.assertGreaterEqual(len(raw["copyContent"]),3000); self.assertLessEqual(len(raw["copyContent"]),8000)
        site=(ROOT/"web/prompt-kit/index.html").read_text(encoding="utf-8")
        self.assertIn("Artifact Risk Review",site); self.assertIn("MACHINE / OS / SHELL GATE",site)
if __name__ == "__main__": unittest.main()
