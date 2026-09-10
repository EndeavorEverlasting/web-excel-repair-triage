from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import ad_campaign as campaign

ROOT = Path(__file__).resolve().parents[1]


def synthetic_packet():
    """All facts and evidence labels are synthetic; no live authorization is implied."""
    return campaign.read_json(ROOT / "harness/ad-campaign/fixtures/synthetic-campaign.v1.json")


class AdCampaignTests(unittest.TestCase):
    def assert_blocked(self, packet, target, fragment):
        report = campaign.validate(packet, target)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertTrue(any(fragment in issue for issue in report["blockers"]), report)
        return report

    def test_complete_synthetic_packet_passes_each_stage(self):
        for stage in ("BRIEF", "PLANNED", "PRODUCED", "REVIEWED", "AUTHORIZED", "LIVE", "MEASURED"):
            with self.subTest(stage=stage):
                report = campaign.validate(synthetic_packet(), stage)
                self.assertEqual(report["status"], "PASS", report)
                self.assertEqual(report["highest_evidenced_stage"], stage)

    def test_sparse_brief_is_useful_but_not_planned(self):
        packet = {"schema_version": "ad-campaign/v1", "campaign_id": "example", "revision": 1}
        self.assertEqual(campaign.validate(packet, "BRIEF")["status"], "PASS")
        report = self.assert_blocked(packet, "PLANNED", "brief.brand")
        self.assertEqual(report["highest_evidenced_stage"], "BRIEF")

    def test_budget_counts_reserve_and_does_not_round_away_excess(self):
        packet = synthetic_packet()
        packet["plan"]["allocations"] = [{"channel": "A", "amount": 600}, {"channel": "B", "amount": 500}]
        self.assert_blocked(packet, "PLANNED", "exceeds budget")
        packet["plan"]["allocations"] = [{"channel": "A", "amount": 900.01}]
        self.assert_blocked(packet, "PLANNED", "exceeds budget")
        packet["brief"]["budget_cap"] = 0.3
        packet["plan"]["allocations"] = [{"channel": "A", "amount": 0.1}]
        packet["plan"]["reserve"] = 0.2
        self.assertEqual(campaign.validate(packet, "PLANNED")["status"], "PASS")

    def test_unknown_budget_does_not_become_zero(self):
        packet = synthetic_packet()
        packet["brief"]["budget_cap"] = None
        self.assert_blocked(packet, "PLANNED", "budget_cap")

    def test_large_integer_budget_excess_is_not_rounded_away(self):
        packet = synthetic_packet()
        packet["brief"]["budget_cap"] = 10**28
        packet["plan"]["allocations"][0]["amount"] = 10**28 + 1
        packet["plan"]["reserve"] = 0
        self.assert_blocked(packet, "PLANNED", "exceeds budget")

    def test_json_precision_loss_is_rejected_before_budget_or_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "packet.json"
            for token in ("900.00000000000000001", "1e-999", "1e999"):
                path.write_text('{"amount":' + token + '}', encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "precision"):
                    campaign.read_json(path)
            path.write_text('{"amount":0.1}', encoding="utf-8")
            self.assertEqual(campaign.read_json(path)["amount"], 0.1)

    def test_unsupported_unknown_and_duplicate_claims_fail(self):
        packet = synthetic_packet()
        packet["doctrine"]["claims"][0]["status"] = "unsupported"
        self.assert_blocked(packet, "PRODUCED", "unsupported or unknown")
        packet["assets"][0]["claim_ids"] = ["missing"]
        self.assert_blocked(packet, "PRODUCED", "unsupported or unknown")
        packet["doctrine"]["claims"].append(copy.deepcopy(packet["doctrine"]["claims"][0]))
        self.assert_blocked(packet, "PLANNED", "duplicate claim")

    def test_production_brief_is_not_rendered_asset(self):
        packet = synthetic_packet()
        packet["assets"][0]["kind"] = "brief"
        self.assert_blocked(packet, "PRODUCED", "production brief")

    def test_each_material_input_invalidates_review_and_authority(self):
        for field in ("account", "offer", "audience", "budget_cap", "currency", "period"):
            with self.subTest(field=field):
                packet = synthetic_packet()
                if field == "budget_cap":
                    packet["brief"][field] = 1500
                elif field == "period":
                    packet["brief"][field]["end"] = "2026-10-01"
                else:
                    packet["brief"][field] += " changed"
                self.assert_blocked(packet, "AUTHORIZED", "review snapshot")
                self.assert_blocked(packet, "AUTHORIZED", "authorization snapshot")
        packet = synthetic_packet()
        packet["assets"][0]["destination"] = "https://example.com/changed"
        self.assert_blocked(packet, "AUTHORIZED", "authorization snapshot")

    def test_current_review_cannot_reuse_old_authorization(self):
        packet = synthetic_packet()
        packet["assets"][0]["version"] = "2"
        packet["review"]["snapshot_sha256"] = campaign.snapshot(packet)
        report = self.assert_blocked(packet, "AUTHORIZED", "authorization snapshot")
        self.assertEqual(report["highest_evidenced_stage"], "REVIEWED")

    def test_missing_or_duplicate_tracking_check_blocks_review(self):
        packet = synthetic_packet()
        packet["review"]["checks"] = [row for row in packet["review"]["checks"] if row["name"] != "tracking"]
        self.assert_blocked(packet, "REVIEWED", "checks.tracking")
        packet = synthetic_packet()
        packet["review"]["checks"].append(copy.deepcopy(packet["review"]["checks"][0]))
        self.assert_blocked(packet, "REVIEWED", "duplicate review")

    def test_not_applicable_needs_evidence_and_reason(self):
        packet = synthetic_packet()
        row = packet["review"]["checks"][0]
        row["status"] = "NOT APPLICABLE"
        self.assert_blocked(packet, "REVIEWED", "checks.claims")
        row["reason"] = "Synthetic example has no factual claim"
        self.assertEqual(campaign.validate(packet, "REVIEWED")["status"], "PASS")

    def test_review_is_not_authorization_and_paid_launch_needs_spend_scope(self):
        packet = synthetic_packet()
        packet["authorization"] = {}
        self.assertEqual(campaign.validate(packet, "REVIEWED")["status"], "PASS")
        self.assert_blocked(packet, "AUTHORIZED", "authorization.publish")
        packet = synthetic_packet()
        packet["authorization"]["actions"] = ["publish"]
        self.assert_blocked(packet, "AUTHORIZED", "authorization.spend")

    def test_authorized_and_pending_are_not_live(self):
        packet = synthetic_packet()
        packet["launch"]["observed_state"] = "pending review"
        report = self.assert_blocked(packet, "LIVE", "not live")
        self.assertEqual(report["highest_evidenced_stage"], "AUTHORIZED")

    def test_incompatible_currency_and_missing_attribution_block_results(self):
        packet = synthetic_packet()
        packet["results"]["currency"] = "EUR"
        self.assert_blocked(packet, "MEASURED", "currency")
        packet["results"]["attribution_model"] = ""
        self.assert_blocked(packet, "MEASURED", "attribution_model")

    def test_known_metrics_and_missing_revenue(self):
        data = synthetic_packet()["results"]
        actual = campaign.metrics(data)
        for key, value in {"ctr": .02, "cpc": .5, "cpm": 10, "cpa": 10, "roas": 5, "click_conversion_rate": .05}.items():
            self.assertAlmostEqual(actual[key]["value"], value)
        del data["revenue"]
        self.assertIsNone(campaign.metrics(data)["roas"]["value"])
        self.assertEqual(campaign.metrics(data)["roas"]["reason"], "missing input")

    def test_zero_missing_negative_boolean_and_nonfinite_metrics(self):
        report = campaign.metrics({"spend": 100, "impressions": 0, "clicks": 0, "conversions": 0})
        self.assertTrue(all(value["value"] is None for value in report.values()))
        self.assertEqual(report["ctr"]["reason"], "zero denominator")
        for bad in (-1, True, float("nan"), float("inf"), "100"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                campaign.metrics({"spend": bad})
        with self.assertRaises(ValueError):
            campaign.metrics({"impressions": 1.5})

    def test_init_never_overwrites_and_cli_propagates_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "new-campaign"
            path = campaign.initialize(output, "synthetic-example")
            original = path.read_bytes()
            with self.assertRaises(FileExistsError):
                campaign.initialize(output, "other")
            self.assertEqual(path.read_bytes(), original)
            result = subprocess.run([sys.executable, str(ROOT / "scripts/ad_campaign.py"), "validate", "--input", str(path), "--target", "LIVE"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["highest_evidenced_stage"], "BRIEF")

    def test_json_rejects_duplicate_keys_and_nonfinite_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for source in ('{"spend":1,"spend":2}', '{"spend":NaN}', '[1]'):
                path.write_text(source, encoding="utf-8")
                with self.assertRaises(ValueError):
                    campaign.read_json(path)

    def test_malformed_packet_and_dates_do_not_pass(self):
        packet = synthetic_packet()
        packet["brief"]["period"]["end"] = "2026-08-01"
        self.assert_blocked(packet, "PLANNED", "brief.period")
        packet = synthetic_packet()
        packet["review"]["at"] = "2026-09-01T10:00:00"
        self.assert_blocked(packet, "REVIEWED", "review.at")
        packet = synthetic_packet()
        packet["assets"] = "PRIVATE_DATA_CANARY"
        report = self.assert_blocked(packet, "PRODUCED", "array required")
        self.assertNotIn("PRIVATE_DATA_CANARY", json.dumps(report))


if __name__ == "__main__":
    unittest.main()
