import types
import pytest

from meowdesk.ui import menu_actions


class FakeWindow:
    def __init__(self, *, parent, config="cfg", agent_gateway="gw", _reminder_checker=None):
        self.config = config
        self.parent = parent
        self.state = types.SimpleNamespace(show_bubble=lambda *_: None)
        self.agent_gateway = agent_gateway
        self._reminder_checker = _reminder_checker
        self._update_html = lambda: None
        self._on_settings_saved = lambda: None

    def quit(self):
        pass


def test_open_settings_survives_missing_parent(monkeypatch):
    calls = []
    monkeypatch.setattr("meowdesk.ui.settings.SettingsPanel", lambda *a, **k: calls.append(True))
    window = FakeWindow(parent=None)
    menu_actions.action_open_settings(window)
    assert calls == []


def test_open_chat_survives_missing_gateway(monkeypatch):
    calls = []
    monkeypatch.setattr("meowdesk.ui.chat.ChatWindow", lambda *a, **k: calls.append(True))
    window = FakeWindow(parent="parent", agent_gateway=None)
    menu_actions.action_open_chat(window)
    assert calls == []


def test_period_reminder_survives_missing_parent(monkeypatch):
    calls = []
    monkeypatch.setattr("meowdesk.ui.settings.SettingsPanel", lambda *a, **k: calls.append(True))
    window = FakeWindow(parent=None)
    menu_actions.action_period_reminder(window)
    assert calls == []


def test_check_date_uses_safe_dict_access(monkeypatch):
    window = FakeWindow(parent="parent")
    registry = menu_actions.CommandRegistry()
    monkeypatch.setattr(menu_actions, "CommandRegistry", lambda: registry)
    menu_actions.action_check_date(window)


def test_system_info_uses_safe_dict_access(monkeypatch):
    window = FakeWindow(parent="parent")
    registry = menu_actions.CommandRegistry()
    monkeypatch.setattr(menu_actions, "CommandRegistry", lambda: registry)
    menu_actions.action_system_info(window)