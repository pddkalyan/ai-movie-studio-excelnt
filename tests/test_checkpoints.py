"""Durable checkpoint failure tests; no background worker inference."""
import dataclasses
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from studio.checkpoints import CheckpointError, CheckpointStore, TaskCheckpoint


def sample(worker="A", status="PLANNED", seq=1, branch=None):
    return TaskCheckpoint(
        worker_alias=worker,
        task_id="EX_0001" if worker == "A" else "EX_0002",
        branch=branch or f"worker/{worker}/foundation",
        head_sha="a" * 40,
        status=status,
        next_action="Review contract tests",
        test_summary="Offline only",
        sequence=seq,
    )


class DurableCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = CheckpointStore(self.root)

    def test_save_and_reopen(self):
        self.store.save(sample())
        store2 = CheckpointStore(self.root)
        self.assertEqual(store2.load("A").status, "PLANNED")

    def test_two_workers_are_isolated(self):
        self.store.save(sample("A"))
        self.store.save(sample("B"))
        self.assertEqual(self.store.load("A").task_id, "EX_0001")
        self.assertEqual(self.store.load("B").task_id, "EX_0002")

    def test_monotonic_update(self):
        self.store.save(sample())
        self.store.save(sample(status="WAITING_FOR_QUOTA", seq=2))
        self.assertEqual(self.store.load("A").sequence, 2)

    def test_duplicate_sequence_refused(self):
        self.store.save(sample())
        with self.assertRaises(CheckpointError):
            self.store.save(sample(status="RUNNING"))

    def test_task_switch_refused(self):
        self.store.save(sample())
        with self.assertRaises(CheckpointError):
            self.store.save(dataclasses.replace(sample(seq=2), task_id="EX_9999"))

    def test_branch_switch_refused(self):
        self.store.save(sample())
        with self.assertRaises(CheckpointError):
            self.store.save(sample(seq=2, branch="worker/A/other"))

    def test_corrupt_json_retained_byte_for_byte(self):
        path = self.root / "worker_A.json"
        path.write_bytes(b'{"broken": ')
        before = path.read_bytes()
        with self.assertRaises(CheckpointError):
            self.store.save(sample())
        self.assertEqual(path.read_bytes(), before)

    def test_corrupt_schema_never_synthesizes_default_fields(self):
        path = self.root / "worker_A.json"
        path.write_text(json.dumps({"task_id": "EX_0001"}))
        before = path.read_bytes()
        with self.assertRaises(CheckpointError):
            self.store.load("A")
        self.assertEqual(path.read_bytes(), before)

    def test_symlink_and_unknown_worker_rejected(self):
        with self.assertRaises(CheckpointError):
            self.store.load("C")

    def test_lock_fails_closed(self):
        (self.root / "worker_A.lock").mkdir()
        with self.assertRaises(CheckpointError):
            self.store.save(sample())

    def test_atomic_replace_fail_keeps_prior_evidence(self):
        self.store.save(sample())
        before = (self.root / "worker_A.json").read_bytes()
        with patch("studio.checkpoints.os.replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.store.save(sample(status="BLOCKED", seq=2))
        self.assertEqual(before, (self.root / "worker_A.json").read_bytes())
        self.assertEqual(list(self.root.glob("*.tmp")), [])

    def test_invalid_sha_and_status_rejected(self):
        for cp in (dataclasses.replace(sample(), head_sha="bad"),
                   dataclasses.replace(sample(), status="SUCCESS"),
                   dataclasses.replace(sample(), next_action="secret\nvalue")):
            with self.assertRaises(CheckpointError):
                self.store.save(cp)


if __name__ == "__main__":
    unittest.main()
