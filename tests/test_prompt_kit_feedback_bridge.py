from __future__ import annotations

import json
import os
import stat
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

    @staticmethod
    def _register_consumer(repo_root: Path) -> None:
        workflow = repo_root / ".github" / "workflows" / "prompt-kit-feedback-hook.yml"
        workflow.parent.mkdir(parents=True, exist_ok=True)
        workflow.write_text(
            "on:\n  repository_dispatch:\n    types: [prompt-kit-feedback-receipt]\n",
            encoding="utf-8",
        )

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

    def test_unknown_prompt_and_invalid_timestamp_fail_before_spooling(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown prompt identity"):
            bridge.sanitize_event(self._event(prompt_id="P999999"))
        with self.assertRaisesRegex(ValueError, "invalid timestamp"):
            bridge.sanitize_event(self._event(timestamp="not-a-time"))

    def test_provider_receipt_never_contains_raw_comment_or_raw_source(self) -> None:
        event = bridge.sanitize_event(self._event())
        receipt = bridge.provider_receipt(event)
        self.assertEqual(tuple(receipt), bridge.PROVIDER_RECEIPT_FIELDS)
        self.assertTrue(receipt["has_comment"])
        self.assertNotIn("comment", receipt)
        self.assertNotIn("browser-profile:personal", json.dumps(receipt))
        self.assertTrue(str(receipt["source_hash"]).startswith("bridge-local:"))

    def test_spool_key_preserves_distinct_ids_with_digest_suffix(self) -> None:
        first = bridge._spool_key("a/b")
        second = bridge._spool_key("a?b")
        self.assertNotEqual(first, second)
        self.assertTrue(first.startswith("a_b-"))
        self.assertTrue(second.startswith("a_b-"))

    def test_default_acceptance_is_private_and_owner_only_on_posix(self) -> None:
        calls: list[object] = []

        def forbidden_runner(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
            calls.append((args, kwargs))
            raise AssertionError("provider runner must not be called when wakeup is disabled")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spool = root / "private-spool"
            report = bridge.accept_private_feedback(
                repo_root=root,
                repository="EndeavorEverlasting/web-excel-repair-triage",
                payload=self._payload(),
                spool_root=spool,
                runner=forbidden_runner,
            )
            self.assertEqual(report["status"], "ACCEPTED_PRIVATE")
            self.assertEqual(report["provider_status"], "PROVIDER_WAKEUP_DISABLED")
            self.assertEqual(calls, [])
            accepted, pending, sent = bridge.spool_paths(spool, "evt-001")
            self.assertTrue(accepted.is_file())
            self.assertFalse(pending.exists())
            self.assertFalse(sent.exists())
            stored = json.loads(accepted.read_text(encoding="utf-8"))
            self.assertIn("comment", stored["event"])
            self.assertNotIn("comment", stored["provider_receipt"])
            if os.name != "nt":
                self.assertEqual(stat.S_IMODE(accepted.stat().st_mode), 0o600)
                self.assertEqual(stat.S_IMODE(accepted.parent.stat().st_mode), 0o700)

    def test_wakeup_without_registered_consumer_stays_pending_and_keeps_raw_event(self) -> None:
        calls: list[object] = []

        def forbidden_runner(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
            calls.append((args, kwargs))
            raise AssertionError("unregistered provider consumer must prevent dispatch")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spool = root / "private-spool"
            report = bridge.accept_private_feedback(
                repo_root=root,
                repository="EndeavorEverlasting/web-excel-repair-triage",
                payload=self._payload(),
                spool_root=spool,
                provider_wakeup=True,
                runner=forbidden_runner,
            )
            self.assertEqual(report["status"], "ACCEPTED_PRIVATE_RETRY_PENDING")
            self.assertEqual(report["provider_status"], "PROVIDER_CONSUMER_UNREGISTERED")
            self.assertEqual(calls, [])
            accepted, pending, sent = bridge.spool_paths(spool, "evt-001")
            self.assertTrue(accepted.is_file())
            self.assertTrue(pending.is_file())
            self.assertFalse(sent.exists())
            self.assertIn("comment", json.loads(accepted.read_text(encoding="utf-8"))["event"])
            self.assertNotIn("comment", json.loads(pending.read_text(encoding="utf-8"))["provider_receipt"])

    def test_registered_consumer_dispatches_receipt_only_and_retains_private_event(self) -> None:
        observed: dict[str, object] = {}

        def runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            observed["argv"] = argv
            observed["input"] = kwargs.get("input")
            observed["timeout"] = kwargs.get("timeout")
            return subprocess.CompletedProcess(argv, 0, "", "")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spool = root / "private-spool"
            self._register_consumer(root)
            report = bridge.accept_private_feedback(
                repo_root=root,
                repository="EndeavorEverlasting/web-excel-repair-triage",
                payload=self._payload(),
                spool_root=spool,
                provider_wakeup=True,
                runner=runner,
            )
            self.assertEqual(report["status"], "ACCEPTED_AND_SIGNALLED")
            body = json.loads(str(observed["input"]))
            self.assertEqual(body["event_type"], bridge.PROVIDER_EVENT_TYPE)
            self.assertNotIn("comment", body["client_payload"])
            self.assertNotIn("This route needs", json.dumps(body["client_payload"]))
            self.assertEqual(observed["timeout"], bridge.PROVIDER_TIMEOUT_SECONDS)
            accepted, pending, sent = bridge.spool_paths(spool, "evt-001")
            self.assertTrue(accepted.is_file())
            self.assertFalse(pending.exists())
            self.assertTrue(sent.is_file())
            self.assertIn("comment", json.loads(accepted.read_text(encoding="utf-8"))["event"])

    def test_provider_timeout_keeps_receipt_pending(self) -> None:
        def runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            raise subprocess.TimeoutExpired(argv, kwargs.get("timeout", 0))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spool = root / "private-spool"
            self._register_consumer(root)
            report = bridge.accept_private_feedback(
                repo_root=root,
                repository="EndeavorEverlasting/web-excel-repair-triage",
                payload=self._payload(),
                spool_root=spool,
                provider_wakeup=True,
                runner=runner,
            )
            self.assertEqual(report["status"], "ACCEPTED_PRIVATE_RETRY_PENDING")
            self.assertEqual(report["provider_status"], "PROVIDER_WAKEUP_TIMEOUT")
            _, pending, sent = bridge.spool_paths(spool, "evt-001")
            self.assertTrue(pending.is_file())
            self.assertFalse(sent.exists())

    def test_retry_rejects_repository_drift_and_uses_stored_destination(self) -> None:
        observed: list[str] = []

        def runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            observed.append(argv[4])
            return subprocess.CompletedProcess(argv, 0, "", "")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spool = root / "private-spool"
            self._register_consumer(root)
            event = bridge.parse_envelope(self._payload())
            bridge.write_accepted(spool, event, "EndeavorEverlasting/web-excel-repair-triage")
            bridge.queue_provider_receipt(spool, event, "EndeavorEverlasting/web-excel-repair-triage")
            with self.assertRaisesRegex(ValueError, "repository mismatch"):
                bridge.retry_pending_receipts(
                    repo_root=root,
                    repository="EndeavorEverlasting/wrong-repo",
                    spool_root=spool,
                    provider_wakeup=True,
                    runner=runner,
                )
            retry = bridge.retry_pending_receipts(
                repo_root=root,
                repository="EndeavorEverlasting/web-excel-repair-triage",
                spool_root=spool,
                provider_wakeup=True,
                runner=runner,
            )
            self.assertEqual(retry["sent"], 1)
            self.assertEqual(observed, ["repos/EndeavorEverlasting/web-excel-repair-triage/dispatches"])

    def test_duplicate_id_is_idempotent_but_conflicting_payload_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spool = root / "private-spool"
            first = bridge.accept_private_feedback(
                repo_root=root,
                repository="EndeavorEverlasting/web-excel-repair-triage",
                payload=self._payload(),
                spool_root=spool,
            )
            self.assertEqual(first["status"], "ACCEPTED_PRIVATE")
            duplicate = bridge.accept_private_feedback(
                repo_root=root,
                repository="EndeavorEverlasting/web-excel-repair-triage",
                payload=self._payload(),
                spool_root=spool,
            )
            self.assertEqual(duplicate["status"], "DUPLICATE")
            with self.assertRaisesRegex(ValueError, "event id conflict"):
                bridge.accept_private_feedback(
                    repo_root=root,
                    repository="EndeavorEverlasting/web-excel-repair-triage",
                    payload=self._payload(self._event(comment="different content")),
                    spool_root=spool,
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
        self.assertIn("PROVIDER_CONSUMER_UNREGISTERED", source)
        self.assertIn("PROVIDER_TIMEOUT_SECONDS", source)
        self.assertIn("default_spool_root", source)


if __name__ == "__main__":
    unittest.main()
