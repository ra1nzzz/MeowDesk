"""Tests for ``meowdesk.ui.window_reminders``."""

from datetime import datetime


from meowdesk.core.types import Reminder
from meowdesk.ui.window_reminders import ReminderChecker


class _StubConfig:
    def __init__(self, reminders=None, period=None):
        self._reminders = reminders or []
        self._period = period

    @property
    def reminders(self):
        return self._reminders

    @property
    def config(self):
        return _StubPeriodConfig(self._period)


class _StubPeriodConfig:
    def __init__(self, period):
        self.period = period or _StubPeriod()


class _StubPeriod:
    def __init__(self, enabled=False, prediction=None, mode="self"):
        self.enabled = enabled
        self._prediction = prediction
        self.mode = mode

    def get_predicted_dates(self):
        return self._prediction


def _reminder(name="r1", time=None, enabled=True, repeat="每天", last_triggered=None, content=None):
    return Reminder(
        name=name,
        time=time or datetime.now().strftime("%H:%M"),
        enabled=enabled,
        repeat=repeat,
        last_triggered=last_triggered,
        content=content or name,
    )


def test_fires_when_current_time_matches_enabled_reminder():
    bubbles = []
    now_str = datetime.now().strftime("%H:%M")
    config = _StubConfig(reminders=[_reminder(time=now_str)])

    checker = ReminderChecker(config, lambda text, dur: bubbles.append((text, dur)))
    checker.tick()
    assert bubbles and bubbles[0][0] == "r1"


def test_skips_disabled_reminders():
    bubbles = []
    now_str = datetime.now().strftime("%H:%M")
    config = _StubConfig(reminders=[_reminder(time=now_str, enabled=False)])

    checker = ReminderChecker(config, lambda text, dur: bubbles.append((text, dur)))
    checker.tick()
    assert bubbles == []


def test_no_repeat_does_not_fire_twice_on_same_day():
    bubbles = []
    today = datetime.now().strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%H:%M")
    reminder = _reminder(time=now_str, repeat="不重复", last_triggered=today)
    config = _StubConfig(reminders=[reminder])

    checker = ReminderChecker(config, lambda text, dur: bubbles.append((text, dur)))
    checker.tick()
    assert bubbles == []


def test_rate_limiting_prevents_rapid_repeat():
    bubbles = []
    now_str = datetime.now().strftime("%H:%M")
    config = _StubConfig(reminders=[_reminder(time=now_str)])

    checker = ReminderChecker(config, lambda text, dur: bubbles.append((text, dur)))
    checker.check_interval = 999
    checker.tick()
    checker.tick()
    assert len(bubbles) == 1


def test_period_reminder_two_days_out():
    bubbles = []
    period = _StubPeriod(
        enabled=True,
        prediction={"days_until": 2, "predicted_start": "07-15", "predicted_end": "07-19"},
    )
    config = _StubConfig(period=period)

    checker = ReminderChecker(config, lambda text, dur: bubbles.append(text))
    checker._check_period()
    assert bubbles and "后天" in bubbles[0]


def test_period_reminder_disabled_is_silent():
    bubbles = []
    period = _StubPeriod(
        enabled=False,
        prediction={"days_until": 0, "predicted_start": "07-15", "predicted_end": "07-19"},
    )
    config = _StubConfig(period=period)

    checker = ReminderChecker(config, lambda text, dur: bubbles.append(text))
    checker._check_period()
    assert bubbles == []


def test_period_reminder_outside_window_is_silent():
    bubbles = []
    period = _StubPeriod(
        enabled=True,
        prediction={"days_until": 5, "predicted_start": "07-15", "predicted_end": "07-19"},
    )
    config = _StubConfig(period=period)

    checker = ReminderChecker(config, lambda text, dur: bubbles.append(text))
    checker._check_period()
    assert bubbles == []


def test_trigger_immediate_finds_next_reminder():
    reminders = [
        _reminder(name="earlier", time="00:00"),
        _reminder(name="later", time="23:59"),
    ]
    config = _StubConfig(reminders=reminders)
    checker = ReminderChecker(config, lambda *_: None)
    next_one = checker.trigger_immediate()
    assert next_one is not None
    assert next_one["name"] in {"earlier", "later"}


def test_trigger_immediate_empty_when_no_reminders():
    config = _StubConfig(reminders=[])
    checker = ReminderChecker(config, lambda *_: None)
    assert checker.trigger_immediate() is None
