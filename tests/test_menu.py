"""Tests for shared context-menu wiring."""

import tempfile
from pathlib import Path

import pytest

from meowdesk.core import ConfigManager
from meowdesk.core.types import AgentType, FileAction
from meowdesk.ui import menu_actions
from meowdesk.ui.menu_actions import build_menu_items

try:
    from meowdesk.ui.menu import _MenuWindowAdapter
except ImportError:
    _MenuWindowAdapter = None


def test_menu_window_adapter_provides_quit_callback():
    if _MenuWindowAdapter is None:
        pytest.skip("tkinter not available")
    called = []
    window = _MenuWindowAdapter(
        config=object(),
        parent=object(),
        on_quit_callback=lambda: called.append("quit"),
    )

    menu_items = build_menu_items(window)
    quit_item = next(item for item in reversed(menu_items) if item is not None)
    quit_item[1]()

    assert called == ["quit"]


def test_open_settings_uses_settings_panel(monkeypatch):
    calls = []

    class FakeSettingsPanel:
        def __init__(self, parent, config, on_save_callback=None):
            calls.append((parent, config, on_save_callback))

    monkeypatch.setattr(menu_actions.sys, "platform", "win32")
    monkeypatch.setattr("meowdesk.ui.settings.SettingsPanel", FakeSettingsPanel)

    window = _MenuWindowAdapter(
        config="config",
        parent="parent",
        on_settings_saved="saved",
    )

    menu_actions.action_open_settings(window)

    assert calls == [("parent", "config", "saved")]


def test_settings_panel_has_period_tab_helpers():
    from meowdesk.ui.settings import SettingsPanel

    assert hasattr(SettingsPanel, "_create_period_tab")
    assert hasattr(SettingsPanel, "_adjust_calibration")


def test_settings_panel_keeps_footer_buttons_visible():
    from meowdesk.ui.settings import SettingsPanel

    with tempfile.TemporaryDirectory() as td:
        config = ConfigManager(str(Path(td) / "config.json"))
        try:
            import tkinter as tk
        except ImportError:
            pytest.skip("Tk unavailable: tkinter not installed")
            return

        try:
            root = tk.Tk()
        except tk.TclError as exc:
            pytest.skip(f"Tk unavailable: {exc}")

        root.withdraw()
        panel = None
        try:
            panel = SettingsPanel(root, config)
            panel.window.update_idletasks()

            assert len(panel.notebook.tabs()) == 4

            children = panel.button_frame.winfo_children()
            assert len(children) >= 2

            footer_bottom = panel.button_frame.winfo_y() + panel.button_frame.winfo_height()
            assert footer_bottom <= panel.window.winfo_height()
            assert panel.button_frame.winfo_y() >= 0
        finally:
            if panel is not None:
                panel.window.destroy()
            root.destroy()


def test_settings_panel_save_persists_typed_values(monkeypatch):
    from meowdesk.ui.settings import SettingsPanel

    try:
        import tkinter
    except ImportError:
        pytest.skip("Tk unavailable: tkinter not installed")
        return
    monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *_, **__: None)

    with tempfile.TemporaryDirectory() as td:
        config_path = Path(td) / "config.json"
        config = ConfigManager(str(config_path))
        try:
            import tkinter as tk
        except ImportError:
            pytest.skip("Tk unavailable: tkinter not installed")
            return

        try:
            root = tk.Tk()
        except tk.TclError as exc:
            pytest.skip(f"Tk unavailable: {exc}")

        root.withdraw()
        panel = None
        saved = []
        try:
            panel = SettingsPanel(root, config, on_save_callback=lambda: saved.append(True))
            panel.dir_var.set(str(Path(td) / "archive"))
            panel.scale_var.set(0.7)
            panel.ss_var.set("archive")
            panel.ai_enabled_var.set(True)
            panel.agent_type_var.set("hermes")
            panel.endpoint_var.set("http://example.com")
            panel.token_var.set("token")
            panel.timeout_var.set(12)

            panel._save()

            reloaded = ConfigManager(str(config_path))
            assert reloaded.config.screenshot_action == FileAction.ARCHIVE
            assert reloaded.agent_config.agent_type == AgentType.HERMES
            assert reloaded.agent_config.enabled is True
            assert reloaded.agent_config.endpoint == "http://example.com"
            assert saved == [True]
        finally:
            if panel is not None and panel.window.winfo_exists():
                panel.window.destroy()
            root.destroy()


def test_settings_panel_save_persists_launch_at_startup(monkeypatch):
    from meowdesk.ui.settings import SettingsPanel

    try:
        import tkinter
    except ImportError:
        pytest.skip("Tk unavailable: tkinter not installed")
        return
    monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *_, **__: None)

    with tempfile.TemporaryDirectory() as td:
        config_path = Path(td) / "config.json"
        config = ConfigManager(str(config_path))
        try:
            import tkinter as tk
        except ImportError:
            pytest.skip("Tk unavailable: tkinter not installed")
            return

        try:
            root = tk.Tk()
        except tk.TclError as exc:
            pytest.skip(f"Tk unavailable: {exc}")

        root.withdraw()
        panel = None
        try:
            panel = SettingsPanel(root, config)
            panel.launch_var.set(True)
            panel._save()

            reloaded = ConfigManager(str(config_path))
            assert reloaded.config.launch_at_startup is True
        finally:
            if panel is not None and panel.window.winfo_exists():
                panel.window.destroy()
            root.destroy()
