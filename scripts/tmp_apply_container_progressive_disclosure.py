#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry/prompts/spec-architecture-prompts.v1.json"
TEST = ROOT / "tests/test_prompt_registry_expansion_regression_design_teach.py"

OLD = (
    "Compare: managed PaaS/serverless for velocity and low ops; one host with OCI containers via Docker or Podman "
    "for low-cost control; Kubernetes/managed orchestration only for demonstrated horizontal scaling, HA/isolation, "
    "or spiky distributed load. “millions someday” is not proof; keep an upgrade seam. Record chosen/rejected tier "
    "and migration triggers: saturation, p95/p99/SLO, queues/connections, RTO/RPO, toil, and cost."
)
NEW = OLD + (
    " Keep this branch progressive-disclosure: do not preload tier-specific Docker/Podman/Kubernetes or "
    "managed-platform detail; inspect it only after current evidence makes that tier decision-relevant."
)

payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
records = [item for item in payload.get("prompts", []) if item.get("id") == "P95"]
if len(records) != 1:
    raise SystemExit(f"expected exactly one P95 record, found {len(records)}")
record = records[0]
content = record.get("copyContent", "")
if NEW in content:
    pass
elif OLD in content:
    record["copyContent"] = content.replace(OLD, NEW, 1)
else:
    raise SystemExit("P95 deployment operating-model anchor changed; refusing blind mutation")
if len(record["copyContent"]) > 10000:
    raise SystemExit("P95 copyContent exceeds its focused 10k ceiling")
REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

source = TEST.read_text(encoding="utf-8")
needle = '''            "p95/p99/SLO",\n        ):'''
replacement = '''            "p95/p99/SLO",\n            "Keep this branch progressive-disclosure",\n            "do not preload tier-specific Docker/Podman/Kubernetes",\n            "only after current evidence makes that tier decision-relevant",\n        ):'''
if replacement in source:
    pass
elif needle in source:
    source = source.replace(needle, replacement, 1)
else:
    raise SystemExit("focused P95 hosting assertion block changed; refusing blind mutation")
TEST.write_text(source, encoding="utf-8")

print("P95 deployment topology guidance strengthened with demand-loaded progressive disclosure")
