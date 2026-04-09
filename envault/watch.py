"""Watch .env files for changes and auto-lock/unlock vaults."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Callable, Optional

from envault.exceptions import EnvaultError


class WatchEvent:
    """Represents a file change event."""

    def __init__(self, path: Path, old_hash: str, new_hash: str) -> None:
        self.path = path
        self.old_hash = old_hash
        self.new_hash = new_hash
        self.timestamp = time.time()

    def __repr__(self) -> str:  # pragma: no cover
        return f"WatchEvent(path={self.path}, timestamp={self.timestamp})"


class WatchManager:
    """Polls an .env file and fires a callback when its content changes."""

    def __init__(self, env_path: Path, interval: float = 1.0) -> None:
        self.env_path = Path(env_path)
        self.interval = interval
        self._last_hash: Optional[str] = None
        self._running = False

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def current_hash(self) -> Optional[str]:
        """Return SHA-256 of the env file, or None if missing."""
        if not self.env_path.exists():
            return None
        data = self.env_path.read_bytes()
        return hashlib.sha256(data).hexdigest()

    def has_changed(self) -> bool:
        """Return True if the file changed since last check."""
        new_hash = self.current_hash()
        changed = new_hash != self._last_hash
        self._last_hash = new_hash
        return changed

    def start(self, on_change: Callable[[WatchEvent], None], max_events: int = 0) -> None:
        """Poll the file and invoke *on_change* whenever it changes.

        Args:
            on_change: Callable that receives a :class:`WatchEvent`.
            max_events: Stop after this many events (0 = run forever).
        """
        self._running = True
        self._last_hash = self.current_hash()
        events_fired = 0

        try:
            while self._running:
                time.sleep(self.interval)
                old_hash = self._last_hash
                new_hash = self.current_hash()
                if new_hash != old_hash:
                    self._last_hash = new_hash
                    event = WatchEvent(
                        path=self.env_path,
                        old_hash=old_hash or "",
                        new_hash=new_hash or "",
                    )
                    on_change(event)
                    events_fired += 1
                    if max_events and events_fired >= max_events:
                        break
        except KeyboardInterrupt:  # pragma: no cover
            pass
        finally:
            self._running = False

    def stop(self) -> None:
        """Signal the polling loop to stop."""
        self._running = False
