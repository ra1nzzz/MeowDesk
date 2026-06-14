from pathlib import Path

settings = Path(r"D:\Code\MeowDesk\MeowDesk\meowdesk\ui\settings.py")
menu = Path(r"D:\Code\MeowDesk\MeowDesk\meowdesk\ui\menu_actions.py")
tests = Path(r"D:\Code\MeowDesk\MeowDesk\tests\test_regression_menu_drop.py")

old_settings = "        # 创建底部按钮\n        self._create_buttons()\n\n        # 创建选项卡\n        self._create_notebook()\n"
new_settings = "        # 创建选项卡\n        self._create_notebook()\n\n        # 创建底部按钮（必须在 notebook 之后创建并 pack(side='bottom')，\n        # 否则 notebook 先占满窗口会导致按钮被挤出可视区域）\n        self._create_buttons()\n"

menu_rewrites = {
    "    if not window._reminder_checker:\n        window.state.show_bubble(\"暂无提醒，在设置中添加\", 80)\n        return\n    next_reminder = window._reminder_checker.trigger_immediate()\n": "    reminder_checker = getattr(window, \"_reminder_checker\", None)\n    if not reminder_checker:\n        window.state.show_bubble(\"暂无提醒，在设置中添加\", 80)\n        return\n    next_reminder = reminder_checker.trigger_immediate()\n",
    "    if hasattr(window, \"parent\"):\n        SettingsPanel(window.parent, window.config, on_save_callback=window._on_settings_saved)\n": "    parent = getattr(window, \"parent\", None)\n    if parent is None:\n        return\n    on_save = getattr(window, \"_on_settings_saved\", None)\n    SettingsPanel(parent, window.config, on_save_callback=on_save)\n",
    "    if hasattr(window, \"agent_gateway\"):\n        ChatWindow(window.parent, window.config, agent_gateway=window.agent_gateway)\n": "    parent = getattr(window, \"parent\", None)\n    agent_gateway = getattr(window, \"agent_gateway\", None)\n    if parent is None or agent_gateway is None:\n        return\n    ChatWindow(parent, window.config, agent_gateway=agent_gateway)\n",
    "    if result[\"success\"]:\n        data = result[\"result\"]\n        window.state.show_bubble(\n            f\"{data['weekday']} 距周末{data['days_to_weekend']}天\", 80\n        )\n": "    if result[\"success\"]:\n        data = result[\"result\"]\n        window.state.show_bubble(\n            f\"{data.get('weekday', '')} 距周末{data.get('days_to_weekend', '')}天\", 80\n        )\n",
    "        window.state.show_bubble(\n            f\"CPU {data['cpu_count']}核{data['cpu_percent']}% | 内存 {data['memory_percent']}%\",\n            80,\n        )\n": "        window.state.show_bubble(\n            f\"CPU {data.get('cpu_count', '')}核{data.get('cpu_percent', '')}% | 内存 {data.get('memory_percent', '')}%\",\n            80,\n        )\n",
    "    if hasattr(window, \"parent\"):\n        SettingsPanel(window.parent, window.config, on_save_callback=window._on_settings_saved)\n\n\ndef action_open_chat": "    parent = getattr(window, \"parent\", None)\n    if parent is None:\n        return\n    on_save = getattr(window, \"_on_settings_saved\", None)\n    SettingsPanel(parent, window.config, on_save_callback=on_save)\n\n\ndef action_open_chat",
}

def apply_rewrite(src: str, mapping: dict[str, str]) -> tuple[str, int]:
    count = 0
    for old, new in mapping.items():
        if old in src:
            src = src.replace(old, new, 1)
            count += 1
    return src, count


s = settings.read_text(encoding="utf-8")
if old_settings in s:
    s = s.replace(old_settings, new_settings, 1)
    settings.write_text(s, encoding="utf-8")
    print("settings: patched")
else:
    print("settings: already patched")

m = menu.read_text(encoding="utf-8")
m, hits = apply_rewrite(m, menu_rewrites)
menu.write_text(m, encoding="utf-8")
print(f"menu_actions: patched={hits}")

test_code = """import sys
import types
import pytest
import tkinter as tk

from meowdesk.core import ConfigManager
from meowdesk.ui import menu_actions
from meowdesk.ui.menu import _MenuWindowAdapter
from meowdesk.ui.settings import SettingsPanel


class FakeWindow:
    def __init__(self, config, parent, state=None, agent_gateway=None, _reminder_checker=None):
        self.config = config
        self.parent = parent
        self.state = state or types.SimpleNamespace(show_bubble=lambda *_: None)
        self.agent_gateway = agent_gateway
        self._reminder_checker = _reminder_checker
        self._update_html = lambda: None
        self._on_settings_saved = lambda: None

    def quit(self):
        pass


def test_open_settings_survives_missing_parent(monkeypatch):
    calls = []
    monkeypatch.setattr("meowdesk.ui.settings.SettingsPanel", lambda *a, **k: calls.append(True))
    window = FakeWindow(config=object(), parent=None)
    window.parent = None
    menu_actions.action_open_settings(window)
    assert calls == []


def test_open_chat_survives_missing_parent_or_gateway(monkeypatch):
    calls = []
    monkeypatch.setattr("meowdesk.ui.chat.ChatWindow", lambda *a, **k: calls.append(True))
    window = FakeWindow(config=object(), parent="p", agent_gateway=None)
    menu_actions.action_open_chat(window)
    assert calls == []


def test_period_reminder_survives_missing_parent(monkeypatch):
    calls = []
    monkeypatch.setattr("meowdesk.ui.settings.SettingsPanel", lambda *a, **k: calls.append(True))
    window = FakeWindow(config=object(), parent=None)
    menu_actions.action_period_reminder(window)
    assert calls == []


def test_check_date_uses_safe_dict_access(monkeypatch):
    window = FakeWindow(config=object(), parent="p")
    registry = menu_actions.CommandRegistry()
    monkeypatch.setattr(menu_actions, "CommandRegistry", lambda: registry)
    menu_actions.action_check_date(window)


def test_system_info_uses_safe_dict_access(monkeypatch):
    window = FakeWindow(config=object(), parent="p")
    registry = menu_actions.CommandRegistry()
    monkeypatch.setattr(menu_actions, "CommandRegistry", lambda: registry)
    menu_actions.action_system_info(window)


def test_settings_panel_has_period_tab_reference():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk unavailable: {exc}")

    root.withdraw()
    try:
        config = ConfigManager.__new__(ConfigManager)
        config._config = ConfigManager.__class__  # not used
    except Exception:
        pytest.skip("minimal ConfigManager construction not available")

    # Direct attribute existence check on class helpers
    assert hasattr(SettingsPanel, "_create_period_tab")
@'

tests.write_text(test_code, encoding="utf-8")
print("tests: wrote regression file")