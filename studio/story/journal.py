"""Corruption-safe, replay-safe story planning checkpoint receipts.

Creator: ChatGPT GPT-6 · EX-A-0002. A ledger is not a provider result.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .bible import StoryError, identifier, natural, sha256

_STATUSES = frozenset({"PLANNED", "VALIDATED", "WAITING_FOR_REVIEW", "BLOCKED"})
_BRANCH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_./-]{0,159}$")


@dataclass(frozen=True)
class StoryReceipt:
    task_id: str
    branch: str
    sequence: int
    bible_digest_sha256: str
    plan_digest_sha256: str
    previous_receipt_sha256: str | None
    status: str

    def validate(self) -> None:
        identifier(self.task_id, "checkpoint task")
        if type(self.branch) is not str or not _BRANCH.fullmatch(self.branch) or ".." in self.branch or self.branch.endswith("/"):
            raise StoryError("Invalid checkpoint branch")
        natural(self.sequence, "checkpoint sequence")
        sha256(self.bible_digest_sha256, "checkpoint Bible")
        sha256(self.plan_digest_sha256, "checkpoint plan")
        if self.previous_receipt_sha256 is not None:
            sha256(self.previous_receipt_sha256, "previous checkpoint")
        if (self.sequence == 1) != (self.previous_receipt_sha256 is None):
            raise StoryError("Checkpoint chain genesis mismatch")
        if type(self.status) is not str or self.status not in _STATUSES:
            raise StoryError("Unexpected checkpoint status")

    def digest(self) -> str:
        self.validate()
        payload = json.dumps(dataclasses.asdict(self), sort_keys=True,
                             separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


class StoryJournal:
    """One exclusive task receipt file; no auto-replay of ambiguous operations.

    Save requires monotonic sequence and previous digest. Repeating an identical
    receipt is idempotent; conflicting same-sequence receipt fails closed.
    """

    def __init__(self, directory: Path):
        self.directory = Path(directory)

    def _check_dir(self) -> None:
        if self.directory.is_symlink():
            raise StoryError("Symlink journal directory blocked")
        self.directory.mkdir(parents=True, exist_ok=True)
        if self.directory.is_symlink():
            raise StoryError("Symlink journal directory blocked")
        if os.name != "nt":
            os.chmod(self.directory, 0o700)

    def load(self) -> StoryReceipt | None:
        target = self.directory / "story_receipt.json"
        if target.is_symlink():
            raise StoryError("Symlink journal file blocked")
        if not target.exists():
            return None
        try:
            raw = json.loads(target.read_text(encoding="utf-8"))
            if type(raw) is not dict or set(raw) != set(StoryReceipt.__dataclass_fields__):
                raise ValueError("Invalid schema")
            receipt = StoryReceipt(**raw)
            receipt.validate()
            return receipt
        except (OSError, ValueError, TypeError, UnicodeError) as exc:
            raise StoryError("Corrupt journal; preserve exact bytes") from exc

    def save(self, receipt: StoryReceipt) -> str:
        if type(receipt) is not StoryReceipt:
            raise StoryError("Invalid checkpoint object")
        receipt.validate()
        self._check_dir()
        lock = self.directory / "story_receipt.lock"
        try:
            lock.mkdir(mode=0o700)
        except FileExistsError as exc:
            raise StoryError("Story journal is busy/orphaned; manual reconciliation required") from exc
        try:
            existing = self.load()
            if existing == receipt:
                return receipt.digest()
            if existing is None:
                if receipt.sequence != 1 or receipt.previous_receipt_sha256 is not None:
                    raise StoryError("First checkpoint must be a genesis receipt")
            else:
                if existing.task_id != receipt.task_id or existing.branch != receipt.branch:
                    raise StoryError("Cannot take over another checkpoint")
                if receipt.sequence != existing.sequence + 1:
                    raise StoryError("Out of order, duplicate or skipped checkpoint")
                if receipt.previous_receipt_sha256 != existing.digest():
                    raise StoryError("Checkpoint predecessor digest mismatch")
                if receipt.bible_digest_sha256 != existing.bible_digest_sha256 or receipt.plan_digest_sha256 != existing.plan_digest_sha256:
                    raise StoryError("Frozen plan changed without new authorization task")
            payload = json.dumps(dataclasses.asdict(receipt), sort_keys=True,
                                 separators=(",", ":"), ensure_ascii=True).encode("utf-8") + b"\n"
            fd, temp = tempfile.mkstemp(dir=self.directory, prefix=".story.", suffix=".tmp")
            try:
                if os.name != "nt": os.fchmod(fd, 0o600)
                with os.fdopen(fd, "wb") as out:
                    out.write(payload)
                    out.flush()
                    os.fsync(out.fileno())
                os.replace(temp, self.directory / "story_receipt.json")
                if os.name != "nt" and hasattr(os, "O_DIRECTORY"):
                    dfd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY)
                    try: os.fsync(dfd)
                    finally: os.close(dfd)
            finally:
                if os.path.exists(temp): os.unlink(temp)
            return receipt.digest()
        finally:
            lock.rmdir()
