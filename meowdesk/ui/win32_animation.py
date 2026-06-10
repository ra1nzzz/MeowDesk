"""Windows animation timer management.

Handles the Tkinter after() based animation loop for the
MeowDesk Windows window.
"""

import sys
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .window import MeowWindow


class Win32AnimationTimer:
    """Manages the Tkinter after() based animation loop on Windows."""

    def __init__(self, window: "MeowWindow"):
        self.window = window
        self.timer_id: Optional[str] = None
        self._running = False

    def start(self, delay_ms: int = 200) -> None:
        """Start the animation timer."""

        if not hasattr(self.window.platform_window, "root"):
            return
        if not self.window.platform_window.root:
            return

        self._running = True
        self._schedule_tick(delay_ms)

    def _schedule_tick(self, delay_ms: int) -> None:
        """Schedule the next animation tick."""

        if not self._running:
            return
        if not hasattr(self.window.platform_window, "root"):
            return
        if not self.window.platform_window.root:
            return

        root = self.window.platform_window.root
        self.timer_id = root.after(delay_ms, self._on_tick)

    def _on_tick(self) -> None:
        """Per-frame callback."""

        if self.window._animation_loop:
            self.window._animation_loop.tick()

        if self._running and hasattr(self.window.platform_window, "root"):
            delay = int(self.window._animation_loop.frame_duration())
            self._schedule_tick(delay)

    def stop(self) -> None:
        """Stop the animation timer."""

        self._running = False
        if self.timer_id is not None and hasattr(self.window.platform_window, "root"):
            if self.window.platform_window.root:
                self.window.platform_window.root.after_cancel(self.timer_id)
                self.timer_id = None
