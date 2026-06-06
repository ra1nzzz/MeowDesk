"""Tests for ``meowdesk.ui.animation_loop``."""

from PIL import Image

from meowdesk.ui.animation_loop import AnimationLoop
from meowdesk.ui.window_state import WindowState


class _StubAnimation:
    """Anim that returns one frame of a configurable size, with a
    configurable frame count for advancing."""

    def __init__(self, frame_size=(64, 64), count=4):
        self._size = frame_size
        self._count = count

    def get_frame(self, state, index):
        return Image.new("RGBA", self._size, (0, 0, 0, 0))

    def get_frame_count(self, state):
        return self._count

    def get_frame_duration(self, state, index):
        return 80


def _make_loop(state, animation=None, frame_size=(64, 64),
               on_tick=None, draw_bubble=None, pos=(100, 200)):
    pos_box = {"value": pos}
    size_box = {"value": (64, 64)}
    rendered = []
    bubble_calls = []

    def get_pos():
        return pos_box["value"]

    def set_pos(x, y):
        pos_box["value"] = (x, y)

    def set_size(w, h):
        size_box["value"] = (w, h)

    def render(frame):
        rendered.append(frame.copy())

    def draw_bubble_fn(frame, text):
        bubble_calls.append(text)
        return frame

    loop = AnimationLoop(
        animation=animation or _StubAnimation(frame_size=frame_size),
        state=state,
        initial_size=size_box["value"],
        set_window_size=set_size,
        get_window_position=get_pos,
        set_window_position=set_pos,
        render_frame=render,
        draw_bubble=draw_bubble or draw_bubble_fn,
        on_tick=on_tick,
    )
    return loop, rendered, bubble_calls, pos_box, size_box


def test_tick_renders_one_frame():
    state = WindowState(_StubAnimation())
    loop, rendered, bubbles, _, _ = _make_loop(state)
    loop.tick()
    assert len(rendered) == 1
    assert rendered[0].size == (64, 64)


def test_tick_advances_state_frame_index():
    state = WindowState(_StubAnimation())
    loop, _, _, _, _ = _make_loop(state)
    loop.tick()
    assert state.frame_index == 1
    loop.tick()
    assert state.frame_index == 2


def test_tick_calls_state_update_each_frame():
    state = WindowState(_StubAnimation())
    state.show_bubble("hi", duration=2)
    loop, _, _, _, _ = _make_loop(state)
    loop.tick()
    assert state.bubble_timer == 1
    loop.tick()
    assert state.bubble_timer == 0


def test_tick_calls_on_tick_each_frame():
    state = WindowState(_StubAnimation())
    calls = []

    def on_tick():
        calls.append(1)

    loop, _, _, _, _ = _make_loop(state, on_tick=on_tick)
    loop.tick()
    loop.tick()
    assert len(calls) == 2


def test_tick_swallows_on_tick_exception():
    state = WindowState(_StubAnimation())

    def boom():
        raise RuntimeError("scheduler must keep running")

    loop, rendered, _, _, _ = _make_loop(state, on_tick=boom)
    loop.tick()
    assert len(rendered) == 1


def test_bubble_renderer_called_when_bubble_active():
    state = WindowState(_StubAnimation())
    state.show_bubble("meow", duration=10)
    loop, _, bubbles, _, _ = _make_loop(state)
    loop.tick()
    assert bubbles == ["meow"]


def test_bubble_renderer_skipped_when_no_bubble():
    state = WindowState(_StubAnimation())
    loop, _, bubbles, _, _ = _make_loop(state)
    loop.tick()
    assert bubbles == []


def test_window_resized_when_frame_size_changes():
    anim = _StubAnimation(frame_size=(128, 96))
    state = WindowState(anim)
    loop, _, _, _, size_box = _make_loop(state, animation=anim, frame_size=(64, 64))
    loop.tick()
    assert size_box["value"] == (128, 96)
    assert loop.current_size == (128, 96)


def test_position_offset_when_height_grows():
    anim = _StubAnimation(frame_size=(64, 128))
    state = WindowState(anim)
    pos_box = {"value": (300, 200)}
    size_box = {"value": (64, 64)}

    def get_pos():
        return pos_box["value"]

    def set_pos(x, y):
        pos_box["value"] = (x, y)

    def set_size(w, h):
        size_box["value"] = (w, h)

    def render(_frame):
        return None

    def draw(_f, _t):
        return Image.new("RGBA", (64, 128))

    loop = AnimationLoop(
        animation=anim,
        state=state,
        initial_size=(64, 64),
        set_window_size=set_size,
        get_window_position=get_pos,
        set_window_position=set_pos,
        render_frame=render,
        draw_bubble=draw,
    )
    loop.tick()
    # 高度从 64 → 128 多了 64；y 应当向上补偿 64
    assert pos_box["value"] == (300, 200 - 64)


def test_no_resize_call_when_size_unchanged():
    state = WindowState(_StubAnimation())
    size_box = {"value": (64, 64)}
    resize_calls = []

    def get_pos():
        return (0, 0)

    def set_pos(x, y):
        return None

    def set_size(w, h):
        resize_calls.append((w, h))
        size_box["value"] = (w, h)

    def render(_f):
        return None

    def draw(_f, _t):
        return Image.new("RGBA", (64, 64))

    loop = AnimationLoop(
        animation=_StubAnimation(),
        state=state,
        initial_size=(64, 64),
        set_window_size=set_size,
        get_window_position=get_pos,
        set_window_position=set_pos,
        render_frame=render,
        draw_bubble=draw,
    )
    loop.tick()
    loop.tick()
    assert resize_calls == []


def test_frame_duration_delegates_to_state():
    state = WindowState(_StubAnimation())
    loop, _, _, _, _ = _make_loop(state)
    assert loop.frame_duration() == 80
