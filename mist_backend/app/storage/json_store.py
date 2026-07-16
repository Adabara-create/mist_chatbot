import json
import threading
from pathlib import Path
from typing import Any

_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def _lock_for(path: Path) -> threading.Lock:
    key = str(path)
    with _locks_guard:
        if key not in _locks:
            _locks[key] = threading.Lock()
        return _locks[key]


def read_json(path: Path) -> Any:
    """Read a JSON file. Raises FileNotFoundError if it doesn't exist —
    the data files are seeded at repo setup time, not created on the fly,
    so a missing file usually means a config mistake worth surfacing."""
    lock = _lock_for(path)
    with lock:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


def write_json(path: Path, data: Any) -> None:
    """Write JSON atomically (write to temp file, then rename) so a crash
    mid-write never corrupts the file."""
    lock = _lock_for(path)
    with lock:
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp_path.replace(path)
