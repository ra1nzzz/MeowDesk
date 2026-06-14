from pathlib import Path

settings = Path(r"D:\Code\MeowDesk\MeowDesk\meowdesk\ui\settings.py")
menu = Path(r"D:\Code\MeowDesk\MeowDesk\meowdesk\ui\menu_actions.py")

old_settings = "        # 创建底部按钮\n        self._create_buttons()\n\n        # 创建选项卡\n        self._create_notebook()\n"
new_settings = "        # 创建选项卡\n        self._create_notebook()\n\n        # 创建底部按钮（必须在 notebook 之后创建并 pack(side='bottom')，\n        # 否则 notebook 先占满窗口会导致按钮被挤出可视区域）\n        self._create_buttons()\n"

menu_rewrites = {
    "    if not window._reminder_checker:\n        window.state.show_bubble(\"暂无提醒，在设置中添加\", 80)\n        return\n    next_reminder = window._reminder_checker.trigger_immediate()\n": "    reminder_checker = getattr(window, \"_reminder_checker\", None)\n    if not reminder_checker:\n        window.state.show_bubble(\"暂无提醒，在设置中添加\", 80)\n        return\n    next_reminder = reminder_checker.trigger_immediate()\n",
    "    if hasattr(window, \"parent\"):\n        SettingsPanel(window.parent, window.config, on_save_callback=window._on_settings_saved)\n": "    parent = getattr(window, \"parent\", None)\n    if parent is None:\n        return\n    on_save = getattr(window, \"_on_settings_saved\", None)\n    SettingsPanel(parent, window.config, on_save_callback=on_save)\n",
    "    if hasattr(window, \"agent_gateway\"):\n        ChatWindow(window.parent, window.config, agent_gateway=window.agent_gateway)\n": "    parent = getattr(window, \"parent\", None)\n    agent_gateway = getattr(window, \"agent_gateway\", None)\n    if parent is None or agent_gateway is None:\n        return\n    ChatWindow(parent, window.config, agent_gateway=agent_gateway)\n",
    "    if result[\"success\"]:\n        data = result[\"result\"]\n        window.state.show_bubble(\n            f\"{data['weekday']} 距周末{data['days_to_weekend']}天\", 80\n        )\n": "    if result[\"success\"]:\n        data = result[\"result\"]\n        window.state.show_bubble(\n            f\"{data.get('weekday', '')} 距周末{data.get('days_to_weekend', '')}天\", 80\n        )\n",
    "        window.state.show_bubble(\n            f\"CPU {data['cpu_count']}核{data['cpu_percent']}% | 内存 {data['memory_percent']}%\",\n            80,\n        )\n": "        window.state.show_bubble(\n            f\"CPU {data.get('cpu_count', '')}核{data.get('cpu_percent', '')}% | 内存 {data.get('memory_percent', '')}%\",\n            80,\n        )\n",
}

s = settings.read_text(encoding="utf-8")
if old_settings in s:
    s = s.replace(old_settings, new_settings, 1)
    settings.write_text(s, encoding="utf-8")
    print("settings: patched")
else:
    print("settings: already patched")

m = menu.read_text(encoding="utf-8")
hits = 0
for old, new in menu_rewrites.items():
    if old in m:
        m = m.replace(old, new, 1)
        hits += 1
menu.write_text(m, encoding="utf-8")
print(f"menu_actions: patched={hits}")