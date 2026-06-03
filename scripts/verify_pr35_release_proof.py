"""Recompute PR #35 delivery release verdict from on-disk preflight/compare JSON."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from triage.release_status import compute_release_status, enrich_variant_output


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _variant_verdict(
    preflight_path: Path,
    compare_path: Path | None,
    *,
    delivery: bool,
    reference_supplied: bool,
) -> dict:
    pf = _load(preflight_path)
    variant_out = {
        "websafe_preflight_pass": pf.get("preflight_pass"),
        "semantic_integrity": pf.get("semantic_integrity", "FAIL"),
        "excel_for_web_manual_check": pf.get("excel_for_web_manual_check", "NOT_PROVEN"),
    }
    if compare_path and compare_path.is_file():
        cmp = _load(compare_path)
        variant_out["artifact_compare_pass"] = cmp.get("compare_pass")
        variant_out["artifact_compare_json"] = str(compare_path)
    enrich_variant_output(
        variant_out,
        delivery_artifact=delivery,
        variant="client",
        reference_supplied=reference_supplied,
    )
    return variant_out


def verify_bonita(out_dir: Path) -> dict:
    pf = out_dir / "Neuron_Track_Hours_April_May_2026_preflight.json"
    cmp = out_dir / "Bonita_Neuron_Track_Hours_artifact_compare.json"
    if not pf.is_file():
        return {"error": "missing preflight", "release_candidate": False}
    pre = _load(pf)
    cmp_pass = None
    cmp_status = "NOT_RUN"
    if cmp.is_file():
        c = _load(cmp)
        cmp_pass = c.get("compare_pass")
        cmp_status = "PASS" if cmp_pass else "FAIL"
    release = compute_release_status(
        delivery_artifact=True,
        websafe_preflight_pass=pre.get("preflight_pass"),
        semantic_integrity=pre.get("semantic_integrity", "FAIL"),
        excel_for_web_manual_check=pre.get("excel_for_web_manual_check", "NOT_PROVEN"),
        artifact_compare_status=cmp_status,
        artifact_compare_pass=cmp_pass,
    )
    return release


def verify_admin(out_dir: Path) -> dict:
    manifest_path = out_dir / "admin_billing_summary_manifest.json"
    if not manifest_path.is_file():
        return {"error": "missing manifest", "release_candidate": False}
    manifest = _load(manifest_path)
    rows = []
    all_client_ok = True
    for mk, mo in manifest.get("per_month", {}).items():
        client = mo.get("outputs", {}).get("client", {})
        pf_path = Path(client.get("preflight_json", ""))
        cmp_path = Path(client["artifact_compare_json"]) if client.get("artifact_compare_json") else None
        ref_used = client.get("reference_used", "")
        ref_supplied = bool(ref_used)
        v = _variant_verdict(
            pf_path,
            cmp_path,
            delivery=True,
            reference_supplied=ref_supplied,
        )
        rows.append({
            "month": mk,
            "workbook": client.get("workbook"),
            "reference_used": ref_used,
            **v,
        })
        if not v.get("release_candidate"):
            all_client_ok = False
    return {
        "release_candidate": all_client_ok,
        "per_month_client": rows,
        "manifest_stale_top_level": manifest.get("release_candidate"),
    }


def main() -> int:
    root = _REPO_ROOT
    bonita = root / "Outputs" / "proof_pr35_bonita"
    admin = root / "Outputs" / "proof_pr35_admin_billing"
    report = {
        "bonita": verify_bonita(bonita),
        "admin_billing": verify_admin(admin),
    }
    blockers = []
    if not report["bonita"].get("release_candidate"):
        blockers.extend(report["bonita"].get("release_blockers", ["bonita_not_ready"]))
    if not report["admin_billing"].get("release_candidate"):
        blockers.append("admin_client_delivery_not_ready")
        for row in report["admin_billing"].get("per_month_client", []):
            blockers.extend(
                f"{row['month']}:{b}" for b in row.get("release_blockers", [])
            )
    report["recommendation"] = "MERGE" if not blockers else "HOLD"
    report["blockers"] = blockers
    out = admin / "final_proof_verdict.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["recommendation"] == "MERGE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
