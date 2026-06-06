"""Reminder scheduling: time-of-day reminders + period reminders.

Pulled out of the window module so the reminder cadence can be unit
tested without spinning up a platform window.
"""

from datetime import datetime
from typing import Optional

from ..core import ConfigManager
from ..utils import get_logger


_log = get_logger(__name__)


class ReminderChecker:
    """Drives time-of-day and period reminders for the desktop pet.

    Owner is responsible for calling :meth:`tick` once per animation
    frame (or at a throttled cadence).  When a reminder fires the
    checker invokes ``show_bubble`` so the cat can speak the message.
    """

    def __init__(self, config: ConfigManager, show_bubble):
        self._config = config
        self._show_bubble = show_bubble

        self.check_interval = 30  # seconds between reminder checks
        self._last_check_time = 0.0
        self._last_check_label = ""

    def tick(self) -> None:
        """Run one check; rate-limited internally."""

        now = datetime.now()
        if now.timestamp() - self._last_check_time < self.check_interval:
            return
        self._last_check_time = now.timestamp()

        current_time = now.strftime("%H:%M")
        if current_time == self._last_check_label:
            return

        for reminder in self._config.reminders:
            if not getattr(reminder, "enabled", False):
                continue
            if reminder.time == current_time:
                if self._should_trigger(reminder):
                    content = reminder.content or reminder.name or "提醒"
                    self._show_bubble(content, 120)
                    _log.info("reminder fired: %s — %s", reminder.name, content)

        self._check_period()
        self._last_check_label = current_time

    def trigger_immediate(self) -> Optional[dict]:
        """Return the next reminder the user has scheduled.

        Used by the right-click "查看提醒" action so the bubble can
        show what's coming up without waiting for the next minute.
        """

        reminders = self._config.reminders
        if not reminders:
            return None
        current_time = datetime.now().strftime("%H:%M")
        for r in reminders:
            if getattr(r, "enabled", True) and getattr(r, "time", "") >= current_time:
                return {"name": r.name, "time": r.time}
        return None

    def _check_period(self) -> None:
        period = self._config.config.period
        if not period.enabled:
            return

        prediction = period.get_predicted_dates()
        if not prediction:
            return

        days_until = prediction["days_until"]
        if days_until not in (0, 1, 2):
            return

        mode_text = "您的" if period.mode == "self" else "伴侣的"
        predicted_start = prediction["predicted_start"]
        predicted_end = prediction["predicted_end"]
        if days_until == 2:
            self._show_bubble(
                f"{mode_text}预计经期将在后天到来 ({predicted_start}~{predicted_end})", 180
            )
        elif days_until == 1:
            self._show_bubble(
                f"{mode_text}预计经期明天到来 ({predicted_start}~{predicted_end})", 180
            )
        else:
            self._show_bubble(
                f"提醒: {mode_text}预计经期今天开始 ({predicted_start}~{predicted_end})", 180
            )

    def _should_trigger(self, reminder) -> bool:
        """Apply the repeat-rule gating for a reminder at its trigger time."""

        repeat = getattr(reminder, "repeat", "不重复")
        if repeat == "不重复":
            today = datetime.now().strftime("%Y-%m-%d")
            if getattr(reminder, "last_triggered", None) == today:
                return False
            reminder.last_triggered = today
            return True
        # 每天 / 每周 / 每月 / 每年 — currently fire every time the
        # configured ``time`` matches, which is good enough for the
        # bundled rule set.
        return True
