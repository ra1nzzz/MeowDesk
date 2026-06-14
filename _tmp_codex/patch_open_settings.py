from pathlib import Path
p = Path(r"D:\Code\MeowDesk\MeowDesk\meowdesk\ui\menu_actions.py")
s = p.read_text(encoding="utf-8")
old = "def action_open_settings(window: \"MeowWindow\") -> None:\n    \"\"\"Open the graphical settings panel.\"\"\"\n\n    if sys.platform == \"darwin\":\n        _open_macos_settings(window)\n        return\n\n    if hasattr(window, \"parent\"):\n        from .settings import SettingsPanel\n        SettingsPanel(window.parent, window.config, on_save_callback=window._on_settings_saved)\n"
new = "def action_open_settings(window: \"MeowWindow\") -> None:\n    \"\"\"Open the graphical settings panel.\"\"\"\n\n    if sys.platform == \"darwin\":\n        _open_macos_settings(window)\n        return\n\n    parent = getattr(window, \"parent\", None)\n    if parent is None:\n        return\n\n    from .settings import SettingsPanel\n    on_save = getattr(window, \"_on_settings_saved\", None)\n    SettingsPanel(parent, window.config, on_save_callback=on_save)\n"
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("patched action_open_settings")
else:
    print("action_open_settings block not found")