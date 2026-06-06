"""Tests for ``meowdesk.agent.commands.CommandRegistry`` pure-logic commands.

Only commands that don't touch the filesystem, network, or external
processes are exercised here.  ``clean_disk`` and ``open_app`` are
covered separately by smoke tests because they perform real side
effects.
"""

from datetime import datetime

import pytest

from meowdesk.agent.commands import CommandRegistry


class _FrozenDateTime:
    """Wrap ``datetime`` so that ``.now()`` returns a fixed value.

    All other attributes are passed through to the real ``datetime``
    class so ``strptime``/``strftime`` keep working inside the command.
    """

    def __init__(self, fixed):
        self._fixed = fixed
        self._real = datetime

    def now(self):
        return self._fixed

    def __getattr__(self, name):
        return getattr(self._real, name)


@pytest.fixture
def registry():
    return CommandRegistry()


def test_list_commands_contains_expected_builtin_names(registry):
    names = set(registry.list_commands())
    assert {
        "clean_disk",
        "check_date",
        "check_holidays",
        "period_reminder",
        "system_info",
        "open_app",
    } <= names


def test_execute_unknown_command_returns_error(registry):
    result = registry.execute("nope")
    assert result["success"] is False
    assert "未知命令" in result["error"]


def test_check_date_returns_today_and_weekday(registry):
    result = registry.execute("check_date")
    assert result["success"] is True
    data = result["result"]
    today = datetime.now().strftime("%Y-%m-%d")
    assert data["today"] == today
    assert data["weekday"] in {
        "周一", "周二", "周三", "周四", "周五", "周六", "周日"
    }
    assert 0 <= data["days_to_weekend"] <= 7
    assert isinstance(data["week_of_year"], int)


def test_check_holidays_returns_upcoming_entries(registry):
    result = registry.execute("check_holidays")
    assert result["success"] is True
    upcoming = result["result"]["upcoming_holidays"]
    # Only future holidays are returned, capped at 3
    assert len(upcoming) <= 3
    for entry in upcoming:
        assert {"date", "name", "days_left"} <= entry.keys()
        assert entry["days_left"] >= 0


def test_period_reminder_requires_last_date(registry):
    result = registry.execute("period_reminder", {"last_date": ""})
    assert result["success"] is True
    assert result["result"]["need_setup"] is True


def test_period_reminder_coming_soon_status(registry, monkeypatch):
    # Freeze "now" at 12:00 to avoid off-by-one issues around midnight
    from datetime import datetime, timedelta
    fixed_now = datetime(2026, 6, 1, 12, 0, 0)
    monkeypatch.setattr(
        "meowdesk.agent.commands.datetime",
        _FrozenDateTime(fixed_now),
    )
    # 26 days ago with a 28-day cycle -> days_until_next = 2
    last = (fixed_now - timedelta(days=26)).strftime("%Y-%m-%d")
    result = registry.execute(
        "period_reminder",
        {"last_date": last, "cycle_days": 28},
    )
    assert result["success"] is True
    data = result["result"]
    assert data["last_date"] == last
    assert data["days_until_next"] == 2
    assert data["status"] == "coming_soon"
    assert data["next_date"] == (fixed_now + timedelta(days=2)).strftime("%Y-%m-%d")


def test_period_reminder_overdue_status(registry, monkeypatch):
    from datetime import datetime, timedelta
    fixed_now = datetime(2026, 6, 1, 12, 0, 0)
    monkeypatch.setattr(
        "meowdesk.agent.commands.datetime",
        _FrozenDateTime(fixed_now),
    )
    last = (fixed_now - timedelta(days=50)).strftime("%Y-%m-%d")
    result = registry.execute(
        "period_reminder",
        {"last_date": last, "cycle_days": 28},
    )
    assert result["success"] is True
    data = result["result"]
    assert data["days_until_next"] == -22
    assert data["status"] == "overdue"


def test_period_reminder_normal_status(registry, monkeypatch):
    """A date 10 days into a 28-day cycle sits in the 'normal' band."""
    from datetime import datetime, timedelta
    fixed_now = datetime(2026, 6, 1, 12, 0, 0)
    monkeypatch.setattr(
        "meowdesk.agent.commands.datetime",
        _FrozenDateTime(fixed_now),
    )
    last = (fixed_now - timedelta(days=10)).strftime("%Y-%m-%d")
    result = registry.execute(
        "period_reminder",
        {"last_date": last, "cycle_days": 28},
    )
    assert result["success"] is True
    data = result["result"]
    assert data["days_until_next"] == 18
    assert data["status"] == "normal"


def test_register_custom_command(registry):
    @registry.register_command("echo")
    def echo(params):
        return params.get("msg", "")

    result = registry.execute("echo", {"msg": "hi"})
    assert result["success"] is True
    assert result["result"] == "hi"
