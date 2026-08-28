from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts import prompt_kit_feedback_bridge as bridge


class PromptKitFeedbackBridgeTests(unittest.TestCase):
    def _event(self, **overrides: object) -> dict[str, object]:
        event: dict[str, object] = {
            "event_id": "evt-001",
            "prompt_id": "p115",
            "event_type": "prompt_feedback",
            "value": "comment",
            "timestamp": "2026-08-28T18:00:00Z",
            "schema_version": bridge.EVENT_SCHEMA,
            "source": "browser-profile:personal",
            "sequence": 7,
            "comment": "This route needs a narrower transport boundary.",
            "metadata": {"runtime": "chrome/windows"},
        }
        event.update(overrides)
        return event

    def _payload(self, event: dict[str, object] | None = None, *, authorized: bool = True) -> bytes:
        return json.dumps(
            {
                "schema_version": bridge.PRIVATE_ENVELOPE_SCHEMA,
                "sync_authorized": authorized,
                "event": event or self._event(),
            }
        ).encode("utf-8")

    def test_parse_requires_explicit_sync_authorization(self) -> None:
        with self.assertRaisesRegex(ValueError, "explicit authorization"):
            bridge.parse_envelope(self._payload(authorized=False))

    def test_sensitive_unknown_and_malformed_fields_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "sensitive feedback field"):
            bridge.sanitize_event(self._event(metadata={"token": "nope"}))
        with self.assertRaisesRegex(ValueError, "unsupported feedback fields"):
            bridge.sanitize_event(self._event(extra="nope"))
        with self.assertRaisesRegex(ValueError, "non-negative integer"):
            bridge.sanitize_event(self._event(sequence=True))
        with self.assertRaisesRegex(ValueError, "only allowed"):
            bridge.sanitize_event(
                self._event(event_type="prompt_vote", value="like", comment="not allowed")
            )

    def test_provider_receipt_never_contains_raw_comment_or_raw_source(self) -> None:
        event = bridge.sanitize_event(self._event())
        receipt = bridge.provider_receipt(event)
        self.assertEqual(tuple(receipt), bridge.PROVIDER_RECEIPT_FIELDS)
        self.assertTrue(receipt["has_comment"])
        self.assertNotIn("comment", receipt)
        self.assertNotIn("browser-profile:personal", json.dumps(receipt))
        self.assertTrue(str(receipt["source_hash"]).startswith("bridge-local:"))

    def test_default_acceptance_is_private_and_never_calls_provider(self) -> None:
        calls: list[object] = []

        def forbidden_runner(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
            calls.append((args, kwargs))
            raise AssertionError("provider runner must not be called when wakeup is disabled")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = bridge.accept_private_feedback(
                repo_root=root,
                repository="EndeavorEverlasting/web-excel-repair-triage",
                payload=self._payload(),
                runner=forbidden_runner,
            )
            self.assertEqual(report["status"], "ACCEPTED_PRIVATE")
            self.assertEqual(report["provider_status"], "PROVIDER_WAKEUP_DISABLED")
            self.assertEqual(calls, [])
            pending, sent = bridge.spool_paths(root, "evt-001")
            self.assertTrue(pending.is_file())
            self.assertFalse(sent.exists())
            stored = json.loads(pending.read_text(encoding="utf-8"))
            self.assertIn("comment", stored["event"])
            self.assertNotIn("comment", stored["provider_receipt"])

    def test_explicit_provider_wakeup_dispatches_receipt_only_and_marks_sent(self) -> None:
        observed: dict[str, object] = {}

        def runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            observed["argv"] = argv
            observed["input"] = kwargs.get("input")
            return subprocess.CompletedProcess(argv, 0, "", "")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = bridge.accept_private_feedback(
                repo_root=root,
                repository="EndeavorEverlasting/web-excel-repair-triage",
                payload=self._payload(),
                provider_wakeup=True,
                runner=runner,
            )
            self.assertEqual(report["status"], "ACCEPTED_AND_SIGNALLED")
            body = json.loads(str(observed["input"]))
            self.assertEqual(body["event_type"], "prompt-kit-feedback-receipt")
            provider_payload = body["client_payload"]
            self.assertNotIn("comment", provider_payload)
            self.assertNotIn("This route needs", json.dumps(provider_payload))
            self.assertEqual(
                observed["argv"],
                [
                    "gh",
                    "api",
                    "--method",
                    "POST",
                    "repos/EndeavorEverlasting/web-excel-repair-triage/dispatches",
                    "--input",
                    "-",
                ],
            )
            pending, sent = bridge.spool_paths(root, "evt-001")
            self.assertFalse(pending.exists())
            self.assertTrue(sent.is_file())

    def test_failed_wakeup_keeps_private_pending_spool_for_bounded_retry(self) -> None:
        attempts = 0

        def runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                return subprocess.CompletedProcess(argv, 1, "", "offline")
            return subprocess.CompletedProcess(argv, 0, "", "")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = bridge.accept_private_feedback(
                repo_root=root,
                repository="EndeavorEverlasting/web-excel-repair-triage",
                payload=self._payload(),
                provider_wakeup=True,
                runner=runner,
            )
            self.assertEqual(first["status"], "ACCEPTED_PRIVATE_RETRY_PENDING")
            pending, sent = bridge.spool_paths(root, "evt-001")
            self.assertTrue(pending.is_file())
            retry = bridge.retry_pending_receipts(
                repo_root=root,
                repository="EndeavorEverlasting/web-excel-repair-triage",
                provider_wakeup=True,
                runner=runner,
            )
            self.assertEqual(retry["attempted"], 1)
            self.assertEqual(retry["sent"], 1)
            self.assertFalse(pending.exists())
            self.assertTrue(sent.is_file())

    def test_duplicate_id_is_idempotent_but_conflicting_payload_fails_closed(self) -> None:
        def runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(argv, 0, "", "")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = bridge.accept_private_feedback(
                repo_root=root,
                repository="EndeavorEverlasting/web-excel-repair-triage",
                payload=self._payload(),
                provider_wakeup=True,
                runner=runner,
            )
            self.assertEqual(first["status"], "ACCEPTED_AND_SIGNALLED")
            duplicate = bridge.accept_private_feedback(
                repo_root=root,
                repository="EndeavorEverlasting/web-excel-repair-triage",
                payload=self._payload(),
                provider_wakeup=True,
                runner=runner,
            )
            self.assertEqual(duplicate["status"], "DUPLICATE")
            with self.assertRaisesRegex(ValueError, "event id conflict"):
                bridge.accept_private_feedback(
                    repo_root=root,
                    repository="EndeavorEverlasting/web-excel-repair-triage",
                    payload=self._payload(self._event(comment="different content")),
                    provider_wakeup=True,
                    runner=runner,
                )

    def test_bridge_source_has_no_worker_scheduler_or_merge_authority(self) -> None:
        source = Path(bridge.__file__).read_text(encoding="utf-8")
        for forbidden in (
            "prompt_kit_afk_local_loop",
            "PROMPT_KIT_AFK_WORKER_COMMAND",
            "one_pass(",
            "time.sleep(",
            "--poll-seconds",
            "gh pr",
            '"/merge"',
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("prompt-kit-feedback-receipt", source)
        self.assertIn("PROVIDER_WAKEUP_DISABLED", source)


if __name__ == "__main__":
    unittest.main()
