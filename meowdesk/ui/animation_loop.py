"""One animation frame, shared between win32 and macOS.

The win32 and macOS platform layers schedule ticks very differently
(``root.after`` vs ``NSTimer``), but the per-frame work — advance the
state machine, wander, tick reminders, draw the current frame with
its bubble, resize the window to match the new frame — is identical.

:class:`AnimationLoop` owns that shared work.  :class:`MeowWindow`
just feeds it ``tick()`` from whichever scheduler the platform
supports.
"""

from typing import Callable, Optional, Tuple

from PIL import Image

from .animation import AnimationManager
from .window_state import WindowState


# Signature: takes a PIL Image, returns a PIL Image with the bubble drawn.
BubbleRenderer = Callable[[Image.Image, str], Image.Image]


class AnimationLoop:
    """Owns the per-frame work that ``MeowWindow._animate`` and
    ``MeowWindow._macos_animate`` used to duplicate.

    The window passes in everything ``tick`` needs through the
    constructor; the platform-specific scheduler simply calls
    ``tick()`` as often as it likes.
    """

    def __init__(
        self,
        animation: AnimationManager,
        state: WindowState,
        initial_size: Tuple[int, int],
        set_window_size: Callable[[int, int], None],
        get_window_position: Callable[[], Tuple[int, int]],
        set_window_position: Callable[[int, int], None],
        render_frame: Callable[[Image.Image], None],
        draw_bubble: BubbleRenderer,
        on_tick: Optional[Callable[[], None]] = None,
    ):
        self._animation = animation
        self._state = state
        self._width, self._height = initial_size
        self._set_size = set_window_size
        self._get_pos = get_window_position
        self._set_pos = set_window_position
        self._render = render_frame
        self._draw_bubble = draw_bubble
        self._on_tick = on_tick

    @property
    def current_size(self) -> Tuple[int, int]:
        return self._width, self._height

    def tick(self) -> None:
        """Advance one frame."""

        if self._on_tick:
            try:
                self._on_tick()
            except Exception:  # noqa: BLE001 — scheduler must keep running
                pass

        self._state.update()
        self._state.wander_tick(self._get_pos, self._set_pos)

        frame = self._animation.get_frame(self._state.state, self._state.frame_index)
        if frame is None:
            return

        if self._state.bubble_text and self._state.bubble_timer > 0:
            frame = self._draw_bubble(frame, self._state.bubble_text)

        fw, fh = frame.size
        if (fw, fh) != (self._width, self._height):
            old_h = self._height
            self._width, self._height = fw, fh
            self._set_size(fw, fh)
            dy = fh - old_h
            if dy:
                x, y = self._get_pos()
                self._set_pos(x, y - dy)

        self._render(frame)
        self._state.advance_frame()

    def frame_duration(self) -> int:
        """How many ms to wait before the next ``tick``."""

        return self._state.frame_duration()
