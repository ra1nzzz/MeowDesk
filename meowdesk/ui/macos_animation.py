"""macOS animation timer management.

Handles NSTimer setup and the per-frame animation callback
for the MeowDesk macOS window.
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .window import MeowWindow


class MacOSAnimationTimer:
    """Manages the NSTimer-based animation loop on macOS."""

    def __init__(self, window: "MeowWindow"):
        self.window = window
        self.timer: Optional[object] = None

    def start(self) -> None:
        """Start the animation timer."""

        from Foundation import NSTimer, NSRunLoop
        from AppKit import NSEventTrackingRunLoopMode

        if self.timer is not None:
            self.timer.invalidate()

        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.08, self.window.platform_window.view, "animationTick:", None, True
        )
        NSRunLoop.currentRunLoop().addTimer_forMode_(
            self.timer, NSEventTrackingRunLoopMode
        )
        self.window.platform_window.view.animation_callback = self._on_tick

    def _on_tick(self) -> None:
        """Per-frame callback."""

        from .macos_settings import check_settings_saved

        if check_settings_saved():
            self.window.config.config = self.window.config.load()
            self.window._on_settings_saved()

        if self.window._animation_loop:
            self.window._animation_loop.tick()

    def invalidate(self) -> None:
        """Stop and invalidate the timer."""

        if self.timer is not None:
            self.timer.invalidate()
            self.timer = None
