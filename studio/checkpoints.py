"""Atomic, read-only-to-outsiders worker task checkpoints; no model dispatch.

Provenance: ChatGPT GPT-6, EX-0001.
"""
from dataclasses import asdict, dataclass
from pathlib import Path
import contextlib
import json
import os
import re
import tempfile


class CheckpointError(RuntimeError):
    pass


STATUSES = frozenset({"PLANNED", "RUNNING", "WAITING_FOR_QUOTA",
                      "WAITING_FOR_REVIEW", "BLOCKED", "NEEDS_RECONCILIATION", "COMPLETE"})
_SHA = re.compile(r"^[a-f0-9]{40}$")
_TASK = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
_BRANCH = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_./-]{0,159}$")


@dataclass(frozen=True)
class TaskCheckpoint:
    worker_alias: str
    task_id: str
    branch: str
    head_sha: str
    status: str
    next_action: str
    test_summary: str
    sequence: int

    def validate(self) -> None:
        if self.worker_alias not in ("A", "B"):
            raise CheckpointError("Only A/B worker aliases permitted")
        if not isinstance(self.task_id, str) or not _TASK.fullmatch(self.task_id):
            raise CheckpointError("Invalid task ID")
        if (not isinstance(self.branch, str) or not _BRANCH.fullmatch(self.branch) or
                self.branch.endswith("/") or ".." in self.branch or
                self.branch.startswith("/")):
            raise CheckpointError("Invalid branch")
        if not isinstance(self.head_sha, str) or not _SHA.fullmatch(self.head_sha):
            raise CheckpointError("Expected a 40-digit Git SHA")
        if self.status not in STATUSES:
            raise CheckpointError("Unknown status")
        if type(self.sequence) is not int or self.sequence < 1:
            raise CheckpointError("Sequence must be positive")
        for field in ("next_action", "test_summary"):
            value = getattr(self, field)
            if (not isinstance(value, str) or not value.strip() or
                    len(value) > 500 or any(ord(ch) < 32 for ch in value)):
                raise CheckpointError("Invalid public checkpoint note")


class CheckpointStore:
    """Local private-state journal. A worker owns a unique branch/task.

    Do not confuse a checkpoint with persistent code: commit tested source on
    the worker's own branch; never delete or rewrite user's other worktrees.
    """

    def __init__(self, root: Path):
        self.root = Path(root)

    def _dir(self) -> None:
        if self.root.is_symlink():
            raise CheckpointError("Symlink checkpoint root blocked")
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink():
            raise CheckpointError("Symlink checkpoint root blocked")
        if os.name != "nt":
            os.chmod(self.root, 0o700)

    def _path(self, alias: str) -> Path:
        if alias not in ("A", "B"):
            raise CheckpointError("Unknown worker alias")
        return self.root / f"worker_{alias}.json"

    @contextlib.contextmanager
    def _lock(self, alias: str):
        self._dir()
        lock = self.root / f"worker_{alias}.lock"
        try:
            lock.mkdir(mode=0o700)
        except FileExistsError as exc:
            raise CheckpointError("Worker checkpoint busy or orphaned lock") from exc
        try:
            yield
        finally:
            lock.rmdir()

    def load(self, alias: str) -> TaskCheckpoint | None:
        path = self._path(alias)
        if path.is_symlink():
            raise CheckpointError("Symlink checkpoint blocked")
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            fields = set(TaskCheckpoint.__dataclass_fields__)
            if not isinstance(data, dict) or set(data) != fields:
                raise ValueError("Invalid checkpoint schema")
            cp = TaskCheckpoint(**data)
            cp.validate()
            if cp.worker_alias != alias:
                raise ValueError("Cross-account checkpoint file")
            return cp
        except (OSError, UnicodeError, ValueError, TypeError, CheckpointError) as exc:
            raise CheckpointError("Corrupt checkpoint; original bytes preserved") from exc

    def save(self, checkpoint: TaskCheckpoint) -> None:
        checkpoint.validate()
        with self._lock(checkpoint.worker_alias):
            previous = self.load(checkpoint.worker_alias)
            if previous:
                if (previous.task_id != checkpoint.task_id or
                        previous.branch != checkpoint.branch):
                    raise CheckpointError("Cannot silently reassign another task or branch")
                if checkpoint.sequence != previous.sequence + 1:
                    raise CheckpointError("Checkpoint must have next monotonic sequence")
            elif checkpoint.sequence != 1:
                raise CheckpointError("First checkpoint must have sequence 1")
            path = self._path(checkpoint.worker_alias)
            if path.is_symlink():
                raise CheckpointError("Symlink checkpoint blocked")
            payload = (json.dumps(asdict(checkpoint), sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
            fd, temporary = tempfile.mkstemp(dir=self.root, prefix=".checkpoint.", suffix=".tmp")
            try:
                if os.name != "nt":
                    os.fchmod(fd, 0o600)
                with os.fdopen(fd, "wb") as output:
                    output.write(payload)
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, path)
                if os.name != "nt" and hasattr(os, "O_DIRECTORY"):
                    dirfd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
                    try:
                        os.fsync(dirfd)
                    finally:
                        os.close(dirfd)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
