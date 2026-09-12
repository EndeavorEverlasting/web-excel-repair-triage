#!/usr/bin/env python3
"""Offline campaign packet preparation and evidence checks; never publishes ads."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import date, datetime, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "harness/ad-campaign/campaign.v1.json"


def read_json(path: Path) -> dict:
    def reject_constant(value):
        raise ValueError(f"non-finite JSON constant: {value}")

    def exact_float(token):
        value = float(token)
        if not math.isfinite(value) or Decimal(token) != Decimal(str(value)):
            raise ValueError("numeric precision cannot be preserved")
        return value

    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    value = json.loads(path.read_text(encoding="utf-8-sig"),
                       parse_constant=reject_constant, parse_float=exact_float,
                       object_pairs_hook=unique_keys)
    if not isinstance(value, dict):
        raise ValueError("expected a JSON object")
    return value


def contract() -> dict:
    return read_json(CONTRACT_PATH)


def snapshot(packet: dict) -> str:
    fields = contract()["snapshot_fields"]
    encoded = json.dumps({key: packet.get(key) for key in fields},
                         sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def text(value) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value.strip().upper() not in {
        "UNKNOWN", "TBD", "TODO", "N/A"}


def number(value, *, integer=False) -> bool:
    if type(value) is int:
        return value >= 0
    return (type(value) is float and math.isfinite(value) and value >= 0
            and (not integer or value.is_integer()))


def timestamp(value) -> bool:
    try:
        return text(value) and datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def reporting_zone(name):
    return timezone.utc if name == "UTC" else ZoneInfo(name)


def period(value) -> bool:
    try:
        return (isinstance(value, dict) and text(value.get("timezone"))
                and bool(reporting_zone(value["timezone"]))
                and date.fromisoformat(value["start"]) <= date.fromisoformat(value["end"]))
    except (ValueError, KeyError, TypeError, ZoneInfoNotFoundError):
        return False


def not_before(later, earlier) -> bool:
    return (timestamp(later) and timestamp(earlier)
            and datetime.fromisoformat(later.replace("Z", "+00:00"))
            >= datetime.fromisoformat(earlier.replace("Z", "+00:00")))


def metrics(results: dict) -> dict:
    """Return ratios, not percentages; zero/missing denominators are explicit nulls."""
    for key in ("impressions", "clicks", "spend", "conversions", "revenue"):
        value = results.get(key)
        if value is not None and not number(value, integer=key in {"impressions", "clicks"}):
            raise ValueError(f"{key} must be a finite nonnegative number or null")
    definitions = {
        "ctr": ("clicks", "impressions", 1), "cpc": ("spend", "clicks", 1),
        "cpm": ("spend", "impressions", 1000), "cpa": ("spend", "conversions", 1),
        "roas": ("revenue", "spend", 1), "click_conversion_rate": ("conversions", "clicks", 1),
    }
    answer = {}
    for name, (numerator, denominator, scale) in definitions.items():
        top, bottom = results.get(numerator), results.get(denominator)
        reason = "missing input" if top is None or bottom is None else "zero denominator" if bottom == 0 else None
        value = None if reason else float(Decimal(str(top)) * scale / Decimal(str(bottom)))
        if value is not None and not math.isfinite(value):
            raise ValueError(f"{name} exceeds finite numeric range")
        answer[name] = {"value": value, "reason": reason,
                        "numerator": numerator, "denominator": denominator}
    return answer


def validate(packet: dict, target: str) -> dict:
    cfg = contract()
    if target not in cfg["stages"]:
        raise ValueError("unknown campaign stage")
    failures = []
    highest = None

    def require(ok, field):
        if not ok:
            failures.append(field)

    def obj(parent, key):
        value = parent.get(key, {})
        require(isinstance(value, dict), key + ": object required")
        return value if isinstance(value, dict) else {}

    def strings(parent, fields, prefix):
        for field in fields:
            require(text(parent.get(field)), prefix + "." + field)

    def rows(parent, key):
        value = parent.get(key, [])
        require(isinstance(value, list), key + ": array required")
        return value if isinstance(value, list) else []

    def done(stage):
        nonlocal highest
        if not failures:
            highest = stage
        return stage == target

    def report():
        return {"target": target, "status": "PASS" if not failures else "BLOCKED",
                "highest_evidenced_stage": highest, "blockers": failures,
                "proof_ceiling": cfg["proof_ceiling"]}

    require(packet.get("schema_version") == cfg["campaign_schema"], "schema_version")
    require(text(packet.get("campaign_id")), "campaign_id")
    require(type(packet.get("revision")) is int and packet["revision"] > 0, "revision")
    if done("BRIEF"):
        return report()

    brief, doctrine, plan = (obj(packet, key) for key in ("brief", "doctrine", "plan"))
    strings(brief, cfg["brief_text_fields"], "brief")
    require(period(brief.get("period")), "brief.period")
    cap = brief.get("budget_cap")
    require(number(cap), "brief.budget_cap")
    strings(doctrine, ("version", "source"), "doctrine")
    rules = rows(doctrine, "brand_rules")
    require(bool(rules) and all(text(r) for r in rules), "doctrine.brand_rules")
    claim_map = {}
    for claim in rows(doctrine, "claims"):
        if not isinstance(claim, dict):
            require(False, "claims: object required")
            continue
        strings(claim, ("id", "text"), "claim")
        key = claim.get("id")
        if not isinstance(key, str):
            continue
        require(key not in claim_map, "duplicate claim id")
        claim_map[key] = claim
        require(claim.get("status") in ("supported", "unsupported"), "claim.status")
        if claim.get("status") == "supported":
            require(text(claim.get("evidence")), "claim.evidence")
    strings(plan, ("version", "objective"), "plan")
    strings(obj(plan, "metric"), ("name", "numerator", "denominator", "source", "window"), "plan.metric")
    strings(obj(plan, "experiment"), ("hypothesis", "comparison", "decision_rule", "window", "stop_rule"), "plan.experiment")
    allocations = rows(plan, "allocations")
    require(bool(allocations), "plan.allocations")
    amounts = []
    for allocation in allocations:
        if not isinstance(allocation, dict):
            require(False, "allocation: object required")
            continue
        require(text(allocation.get("channel")), "allocation.channel")
        amount = allocation.get("amount")
        require(number(amount), "allocation.amount")
        if number(amount):
            amounts.append(Fraction(Decimal(str(amount))))
    reserve = plan.get("reserve")
    require(number(reserve), "plan.reserve")
    if number(cap) and number(reserve):
        require(sum(amounts) + Fraction(Decimal(str(reserve))) <= Fraction(Decimal(str(cap))), "allocation plus reserve exceeds budget cap")
    if done("PLANNED"):
        return report()

    assets = rows(packet, "assets")
    require(bool(assets), "assets")
    seen = set()
    for asset in assets:
        if not isinstance(asset, dict):
            require(False, "asset: object required")
            continue
        strings(asset, ("id", "version", "channel", "headline", "copy", "cta", "destination",
                        "artifact", "format_evidence", "rights_evidence"), "asset")
        key = asset.get("id")
        if isinstance(key, str):
            require(key not in seen, "duplicate asset id")
            seen.add(key)
        require(asset.get("kind") in ("copy", "rendered"), "asset.kind: a production brief is not a completed asset")
        for claim_id in rows(asset, "claim_ids"):
            claim = claim_map.get(claim_id) if isinstance(claim_id, str) else None
            require(bool(claim) and claim.get("status") == "supported", "asset references unsupported or unknown claim")
    if done("PRODUCED"):
        return report()

    binding = snapshot(packet)
    review = obj(packet, "review")
    require(review.get("snapshot_sha256") == binding, "review snapshot is stale or missing")
    strings(review, ("reviewer",), "review")
    require(timestamp(review.get("at")), "review.at")
    require(text(brief.get("account")), "brief.account")
    checks = rows(review, "checks")
    check_map = {}
    for row in checks:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            require(False, "review check requires a named object")
            continue
        require(row["name"] not in check_map, "duplicate review check")
        check_map[row["name"]] = row
    for name in cfg["review_checks"]:
        row = check_map.get(name, {})
        valid = row.get("status") == "PASS" and text(row.get("evidence"))
        # N/A is accepted only with a reviewer-owned, explicit rationale and evidence.
        valid = valid or (row.get("status") == "NOT APPLICABLE" and text(row.get("reason")) and text(row.get("evidence")))
        require(valid, "review.checks." + name)
    if done("REVIEWED"):
        return report()

    auth = obj(packet, "authorization")
    require(auth.get("snapshot_sha256") == binding, "authorization snapshot is stale or missing")
    strings(auth, ("approver",), "authorization")
    require(timestamp(auth.get("at")), "authorization.at")
    actions = rows(auth, "actions")
    require(cfg["launch_action"] in actions, "authorization.publish")
    if any(amount > 0 for amount in amounts):
        require(cfg["paid_action"] in actions, "authorization.spend")
    if done("AUTHORIZED"):
        return report()

    launch = obj(packet, "launch")
    require(launch.get("snapshot_sha256") == binding, "launch snapshot is stale or missing")
    require(launch.get("observed_state") == "live", "launch.observed_state is not live")
    strings(launch, ("campaign_platform_id", "evidence"), "launch")
    require(timestamp(launch.get("at")), "launch.at")
    require(not_before(launch.get("at"), auth.get("at")), "launch precedes authorization")
    if done("LIVE"):
        return report()

    results = obj(packet, "results")
    require(results.get("snapshot_sha256") == binding, "results snapshot is stale or missing")
    strings(results, ("source", "attribution_model", "attribution_window", "conversion_definition"), "results")
    require(timestamp(results.get("extracted_at")), "results.extracted_at")
    require(period(results.get("period")), "results.period")
    reporting, planned = results.get("period"), brief.get("period")
    if period(reporting) and period(planned):
        require(reporting["timezone"] == planned["timezone"]
                and date.fromisoformat(planned["start"]) <= date.fromisoformat(reporting["start"])
                <= date.fromisoformat(reporting["end"]) <= date.fromisoformat(planned["end"]),
                "results.period must be within campaign period and use its timezone")
    require(not_before(results.get("extracted_at"), launch.get("at")), "results extraction precedes launch")
    if period(reporting) and timestamp(results.get("extracted_at")) and timestamp(launch.get("at")):
        zone = reporting_zone(reporting["timezone"])
        launched = datetime.fromisoformat(launch["at"].replace("Z", "+00:00")).astimezone(zone).date()
        extracted = datetime.fromisoformat(results["extracted_at"].replace("Z", "+00:00")).astimezone(zone).date()
        require(launched <= date.fromisoformat(reporting["start"])
                <= date.fromisoformat(reporting["end"]) <= extracted,
                "results.period falls before launch or after extraction")
    require(results.get("currency") == brief.get("currency"), "results.currency differs from campaign")
    for key in ("impressions", "clicks", "spend", "conversions"):
        require(number(results.get(key), integer=key in {"impressions", "clicks"}), "results." + key)
    try:
        metrics(results)
    except ValueError:
        require(False, "results metrics contain invalid numeric inputs")
    done("MEASURED")
    return report()


def initialize(output: Path, campaign_id: str) -> Path:
    if not text(campaign_id):
        raise ValueError("campaign identity is required")
    # New output identity only; no existing directory/file can be overwritten.
    output.mkdir(parents=True, exist_ok=False)
    packet = read_json(ROOT / contract()["template"])
    packet["campaign_id"] = campaign_id
    destination = output / "campaign.json"
    with destination.open("x", encoding="utf-8") as handle:
        json.dump(packet, handle, indent=2, allow_nan=False)
        handle.write("\n")
    return destination


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="Create a new blank campaign packet; never overwrites.")
    init.add_argument("--output", type=Path, required=True)
    init.add_argument("--campaign", required=True)
    for name in ("validate", "snapshot", "metrics"):
        sub = commands.add_parser(name)
        sub.add_argument("--input", type=Path, required=True)
        if name == "validate":
            sub.add_argument("--target", choices=contract()["stages"], required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            result = {"created": str(initialize(args.output, args.campaign)), "stage": "BRIEF"}
        else:
            packet = read_json(args.input)
            if args.command == "validate":
                result = validate(packet, args.target)
            elif args.command == "snapshot":
                result = {"snapshot_sha256": snapshot(packet)}
            else:
                result = metrics(packet)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 1 if result.get("status") == "BLOCKED" else 0
    except (ValueError, OSError, TypeError, OverflowError) as exc:
        # Do not echo private packet values into logs.
        print(json.dumps({"status": "ERROR", "error_type": type(exc).__name__,
                          "message": "Invalid packet, numeric data, or output path; no advertising action was performed."}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
