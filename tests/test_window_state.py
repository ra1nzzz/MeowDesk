"""Tests for ``meowdesk.ui.window_state``."""

import time

import pytest

from meowdesk.ui.animation import AnimationManager
from meowdesk.ui.window_state import WindowState


class _DummyAnim:
    """Minimal stand-in for ``AnimationManager`` with predictable frame counts."""

    def __init__(self, count=4):
        self._count = count

    def get_frame_count(self, state):
        return self._count

    def get_frame_duration(self, state, frame_index):
        return 100


@pytest.fixture
def state():
    return WindowState(_DummyAnim())


def test_initial_state_is_idle(state):
    assert state.state == AnimationManager.IDLE
    assert state.frame_index == 0
    assert state.bubble_text == ""
    assert state.bubble_timer == 0


def test_enter_state_resets_frame_index(state):
    state.frame_index = 5
    state.enter_state(AnimationManager.HAPPY, timer=10)
    assert state.state == AnimationManager.HAPPY
    assert state.frame_index == 0
    assert state.happy_timer == 10


def test_happy_state_returns_to_idle_after_timer_expires(state):
    state.enter_state(AnimationManager.HAPPY, timer=2)
    state.update()
    state.update()
    assert state.state == AnimationManager.IDLE


def test_surprised_state_returns_to_idle(state):
    state.enter_state(AnimationManager.SURPRISED, timer=1)
    state.update()
    assert state.state == AnimationManager.IDLE


def test_shy_state_returns_to_idle_when_not_dragging(state):
    state.enter_state(AnimationManager.SHY, timer=1)
    state.update()
    assert state.state == AnimationManager.IDLE


def test_shy_state_holds_while_dragging(state):
    state.enter_state(AnimationManager.SHY, timer=3)
    state.set_dragging(True)
    state.update()  # shy_timer: 3 -> 2, dragging blocks idle
    assert state.state == AnimationManager.SHY
    state.set_dragging(False)
    state.update()  # shy_timer: 2 -> 1, still positive
    assert state.state == AnimationManager.SHY
    state.update()  # shy_timer: 1 -> 0, falls through to IDLE
    assert state.state == AnimationManager.IDLE


def test_sleeping_after_idle_threshold(state, monkeypatch):
    state.last_interaction = time.time() - (WindowState.SLEEP_DELAY + 5)
    state.update()
    assert state.state == AnimationManager.SLEEPING


def test_sleeping_suppressed_while_processing(state, monkeypatch):
    state.set_processing(True)
    state.last_interaction = time.time() - (WindowState.SLEEP_DELAY + 5)
    state.update()
    assert state.state == AnimationManager.IDLE


def test_bubble_decays_to_empty(state):
    state.show_bubble("hi", duration=2)
    state.update()
    state.update()
    assert state.bubble_text == ""


def test_touch_resets_wander_target(state):
    state.wander_target = (10, 10)
    state.wander_pause_until = time.time() + 999
    state.touch()
    assert state.wander_target is None


def test_wander_skipped_while_dragging(state):
    state.init_wander(1920, 1080, 100, 100)
    state.wander_target = (1000, 500)
    state.set_dragging(True)
    positions = []
    state.wander_tick(lambda: (0, 0), lambda x, y: positions.append((x, y)))
    assert positions == []


def test_wander_skipped_while_processing(state):
    state.init_wander(1920, 1080, 100, 100)
    state.set_processing(True)
    state.wander_target = (1000, 500)
    positions = []
    state.wander_tick(lambda: (0, 0), lambda x, y: positions.append((x, y)))
    assert positions == []


def test_wander_picks_target_then_moves(state, monkeypatch):
    state.init_wander(1920, 1080, 100, 100)
    state.last_interaction = time.time() - 999
    state.wander_pause_until = 0

    positions = []
    pos = [900, 500]

    def get_pos():
        return pos[0], pos[1]

    def set_pos(x, y):
        pos[0], pos[1] = x, y
        positions.append((x, y))

    monkeypatch.setattr("meowdesk.ui.window_state.random.uniform", lambda *_: 0)

    state.wander_tick(get_pos, set_pos)
    assert state.wander_target is not None

    state.wander_pause_until = 0
    state.wander_tick(get_pos, set_pos)
    assert positions, "expected at least one move after picking a target"


def test_advance_frame_wraps_around(state):
    state.enter_state(AnimationManager.IDLE)
    for _ in range(5):
        state.advance_frame()
    assert 0 <= state.frame_index < _DummyAnim().get_frame_count(AnimationManager.IDLE)
