"""Cat state, timers and idle wandering.

Holds the per-frame state machine that drives animations: IDLE /
HAPPY / SHY / SURPRISED / SLEEPING transitions, the timers that
return the cat to IDLE, the bubble lifetime counter and the random
wander behaviour that nudges the pet around the screen when idle.
"""

import math
import random
import time
from typing import Optional

from .animation import AnimationManager


class WindowState:
    """State machine and per-frame timers for the desktop pet.

    The owning window feeds it the high-level inputs (mouse, drag,
    file drops) and reads back the resulting animation state plus the
    bubble text.  The wander logic is invoked once per animation tick.
    """

    WANDER_SPEED = 1.0
    WANDER_IDLE_DELAY = 5.0
    SLEEP_DELAY = 60.0

    def __init__(self, animation: AnimationManager):
        self._animation = animation

        self.state = AnimationManager.IDLE
        self.frame_index = 0

        self.processing = False
        self.dragging = False

        self.happy_timer = 0
        self.surprised_timer = 0
        self.shy_timer = 0
        self.last_interaction = time.time()

        self.bubble_text = ""
        self.bubble_timer = 0

        self.wander_target: Optional[tuple] = None
        self.wander_pause_until = 0.0
        self.wander_bounds: dict = {}

    def touch(self) -> None:
        """Mark user activity — interrupts wandering and resets sleep timer."""

        self.last_interaction = time.time()
        self.wander_target = None

    def show_bubble(self, text: str, duration: int) -> None:
        self.bubble_text = text
        self.bubble_timer = duration

    def set_processing(self, processing: bool) -> None:
        self.processing = processing

    def set_dragging(self, dragging: bool) -> None:
        self.dragging = dragging

    def init_wander(self, screen_width: int, screen_height: int, window_w: int, window_h: int) -> None:
        self.wander_bounds = {
            "x_min": max(0, screen_width - 300),
            "x_max": max(0, screen_width - window_w - 10),
            "y_min": 10,
            "y_max": max(10, screen_height - window_h - 60),
        }

    def update(self) -> None:
        """Decrement timers and resolve state transitions for one tick."""

        now = time.time()

        if self.happy_timer > 0:
            self.happy_timer -= 1
            if self.happy_timer == 0 and self.state == AnimationManager.HAPPY:
                self._enter(AnimationManager.IDLE)

        if self.surprised_timer > 0:
            self.surprised_timer -= 1
            if self.surprised_timer == 0 and self.state == AnimationManager.SURPRISED:
                self._enter(AnimationManager.IDLE)

        if self.shy_timer > 0:
            self.shy_timer -= 1
            if self.shy_timer == 0 and self.state == AnimationManager.SHY and not self.dragging:
                self._enter(AnimationManager.IDLE)

        if (
            not self.processing
            and self.state == AnimationManager.IDLE
            and now - self.last_interaction > self.SLEEP_DELAY
        ):
            self._enter(AnimationManager.SLEEPING)

        if self.bubble_timer > 0:
            self.bubble_timer -= 1
            if self.bubble_timer == 0:
                self.bubble_text = ""

    def enter_state(self, state: str, timer: int = 0) -> None:
        """Public hook used by drop / click handlers to override the state."""

        self._enter(state)
        if timer:
            if state == AnimationManager.HAPPY:
                self.happy_timer = timer
            elif state == AnimationManager.SURPRISED:
                self.surprised_timer = timer
            elif state == AnimationManager.SHY:
                self.shy_timer = timer

    def reset_shy(self, timer: int) -> None:
        """Refresh the shy timer without re-entering SHY (used after drag)."""

        if self.state == AnimationManager.SHY:
            self.shy_timer = timer

    def reset_to_idle(self) -> None:
        """Wake the cat from sleep if it's currently sleeping."""

        if self.state == AnimationManager.SLEEPING:
            self._enter(AnimationManager.IDLE)

    def wander_tick(self, get_position, set_position) -> None:
        """Advance the wander behaviour by one tick.

        ``get_position``/``set_position`` are callables because the
        owning window owns the platform window and we want to keep
        that boundary clean.
        """

        if not self.wander_bounds:
            return
        if self.dragging or self.processing or self.state == AnimationManager.SLEEPING:
            return

        now = time.time()
        if now - self.last_interaction < self.WANDER_IDLE_DELAY:
            return
        if now < self.wander_pause_until:
            return

        if self.wander_target is None:
            self._pick_wander_target()
            return

        tx, ty = self.wander_target
        cx, cy = get_position()
        dx, dy = tx - cx, ty - cy
        dist = math.hypot(dx, dy)

        if dist < 3:
            self.wander_target = None
            self.wander_pause_until = now + random.uniform(2, 6)
            return

        new_x = int(cx + dx / dist * self.WANDER_SPEED)
        new_y = int(cy + dy / dist * self.WANDER_SPEED)
        set_position(new_x, new_y)

    def advance_frame(self) -> None:
        """Bump ``frame_index`` modulo the current state's frame count."""

        frame_count = self._animation.get_frame_count(self.state)
        if frame_count > 0:
            self.frame_index = (self.frame_index + 1) % frame_count

    def frame_duration(self) -> int:
        return int(self._animation.get_frame_duration(self.state, self.frame_index))

    def _enter(self, state: str) -> None:
        self.state = state
        self.frame_index = 0

    def _pick_wander_target(self) -> None:
        b = self.wander_bounds
        self.wander_target = (
            random.randint(b["x_min"], b["x_max"]),
            random.randint(b["y_min"], b["y_max"]),
        )
        self.wander_pause_until = time.time() + random.uniform(3, 8)
