"""
macOS 设置面板启动器 - 使用子进程避免 tkinter 与 PyObjC 冲突
"""

import os
import sys
import subprocess
import tempfile


def open_settings(config_path: str, on_saved_callback=None):
    script = '''
import sys
import json
import os

config_path = sys.argv[1]

class ConfigProxy:
    def __init__(self, path):
        self.path = path
        with open(path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
    def get(self, key, default=None):
        return self.data.get(key, default)
    def set(self, key, value):
        self.data[key] = value
    def save(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

config = ConfigProxy(config_path)

COLORS = {
    'bg': '#121218',
    'fg': '#F0EDE8',
    'entry_bg': '#22222E',
    'accent': '#F4845F',
    'accent_hover': '#F69B7D',
    'danger': '#F87171',
    'success': '#6EE7A0',
    'warning': '#FBBF5C',
    'border': '#2D2D3D',
    'select_bg': '#2A2A38',
    'select_indicator': '#F4845F',
}

FONT = 'PingFang SC'

root = tk.Tk()
root.title("MeowDesk 设置")
root.configure(bg=COLORS['bg'])
root.resizable(False, False)

sw = root.winfo_screenwidth()
sh = root.winfo_screenheight()
ww, wh = 520, 520
root.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")
root.attributes("-topmost", True)

style = ttk.Style()
style.theme_use('default')
style.configure('TNotebook', background=COLORS['bg'])
style.configure('TNotebook.Tab',
               background=COLORS['entry_bg'],
               foreground=COLORS['fg'],
               padding=[12, 4],
               font=(FONT, 9))
style.map('TNotebook.Tab',
         background=[('selected', COLORS['accent'])],
         foreground=[('selected', '#ffffff')])
style.configure('Treeview',
               background=COLORS['entry_bg'],
               foreground=COLORS['fg'],
               fieldbackground=COLORS['entry_bg'],
               font=(FONT, 9))
style.configure('Treeview.Heading',
               background=COLORS['select_bg'],
               foreground=COLORS['fg'],
               font=(FONT, 9, 'bold'))
style.map('Treeview',
         background=[('selected', COLORS['accent'])],
         foreground=[('selected', '#ffffff')])

notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True, padx=10, pady=10)

# === 常规 TAB ===
tab_general = tk.Frame(notebook, bg=COLORS['bg'])
notebook.add(tab_general, text='  常规  ')

row = 0

tk.Label(tab_general, text="归档目录", bg=COLORS['bg'], fg=COLORS['fg'],
         anchor="w", font=(FONT, 10, "bold")).grid(row=row, column=0, sticky="w", padx=20, pady=(20, 4))
row += 1

dir_frame = tk.Frame(tab_general, bg=COLORS['bg'])
dir_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 4))

dir_var = tk.StringVar(value=config.get('archive_dir'))
dir_entry = tk.Entry(dir_frame, textvariable=dir_var, bg=COLORS['entry_bg'],
                    fg=COLORS['fg'], insertbackground=COLORS['fg'],
                    relief="flat", font=(FONT, 10))
dir_entry.pack(side='left', fill='x', expand=True, padx=(0, 8))

def browse_dir():
    d = filedialog.askdirectory(title="选择归档目录", initialdir=dir_var.get())
    if d:
        dir_var.set(d)

tk.Button(dir_frame, text="浏览...", command=browse_dir,
         bg=COLORS['accent'], fg="#fff", relief="flat",
         padx=12).pack(side='right')
row += 1

tk.Label(tab_general, text="宠物大小", bg=COLORS['bg'], fg=COLORS['fg'],
         anchor="w", font=(FONT, 10, "bold")).grid(row=row, column=0, sticky="w", padx=20, pady=(16, 4))
row += 1

scale_frame = tk.Frame(tab_general, bg=COLORS['bg'])
scale_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 4))

scale_var = tk.DoubleVar(value=config.get('scale', 0.5))
scale_label = tk.Label(scale_frame, text=f"{int(scale_var.get()*100)}%",
                       bg=COLORS['bg'], fg=COLORS['accent'],
                       font=(FONT, 10, "bold"), width=6)
scale_label.pack(side='right')

def on_scale_change(v):
    scale_label.config(text=f"{int(float(v)*100)}%")

scale_slider = tk.Scale(scale_frame, from_=0.3, to=1.0, resolution=0.05,
                        orient="horizontal", variable=scale_var,
                        bg=COLORS['bg'], fg=COLORS['fg'],
                        troughcolor=COLORS['entry_bg'],
                        highlightthickness=0, showvalue=False,
                        length=300, command=on_scale_change)
scale_slider.pack(side='left', fill='x', expand=True)
row += 1

tk.Label(tab_general, text="截图处理", bg=COLORS['bg'], fg=COLORS['fg'],
         anchor="w", font=(FONT, 10, "bold")).grid(row=row, column=0, sticky="w", padx=20, pady=(16, 4))
row += 1

ss_var = tk.StringVar(value=config.get('screenshot_action', 'recycle'))
ss_frame = tk.Frame(tab_general, bg=COLORS['bg'])
ss_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 4))

tk.Radiobutton(ss_frame, text="移入回收站", variable=ss_var, value="recycle",
               bg=COLORS['bg'], fg=COLORS['fg'],
               selectcolor=COLORS['select_indicator'], activebackground=COLORS['select_bg'],
               activeforeground=COLORS['fg'],
               font=(FONT, 10), indicatoron=True).pack(side="left", padx=(0, 20))
tk.Radiobutton(ss_frame, text="保留到图片", variable=ss_var, value="archive",
               bg=COLORS['bg'], fg=COLORS['fg'],
               selectcolor=COLORS['select_indicator'], activebackground=COLORS['select_bg'],
               activeforeground=COLORS['fg'],
               font=(FONT, 10), indicatoron=True).pack(side="left")

# === AI 助手 TAB ===
tab_ai = tk.Frame(notebook, bg=COLORS['bg'])
notebook.add(tab_ai, text='  AI 助手  ')

row = 0

ai_enabled_var = tk.BooleanVar(value=config.get('ai_enabled', False))
tk.Checkbutton(tab_ai, text="启用 AI 助手", variable=ai_enabled_var,
              bg=COLORS['bg'], fg=COLORS['fg'],
              selectcolor=COLORS['select_indicator'], activebackground=COLORS['select_bg'],
              activeforeground=COLORS['fg'],
              font=(FONT, 10, "bold"), indicatoron=True).grid(row=row, column=0, sticky="w", padx=20, pady=(20, 8))
row += 1

tk.Label(tab_ai, text="网关类型", bg=COLORS['bg'], fg=COLORS['fg'],
         anchor="w", font=(FONT, 10)).grid(row=row, column=0, sticky="w", padx=20, pady=(8, 4))
row += 1

agent_type_var = tk.StringVar(value=config.get('agent_type', 'openclaw'))
type_frame = tk.Frame(tab_ai, bg=COLORS['bg'])
type_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 4))

for value, text in [('openclaw', 'OpenClaw'), ('hermes', 'Hermes'), ('custom', '自定义')]:
    tk.Radiobutton(type_frame, text=text, variable=agent_type_var, value=value,
                  bg=COLORS['bg'], fg=COLORS['fg'],
                  selectcolor=COLORS['select_indicator'], activebackground=COLORS['select_bg'],
                  activeforeground=COLORS['fg'],
                  font=(FONT, 10), indicatoron=True).pack(side="left", padx=(0, 16))
row += 1

tk.Label(tab_ai, text="网关地址", bg=COLORS['bg'], fg=COLORS['fg'],
         anchor="w", font=(FONT, 10)).grid(row=row, column=0, sticky="w", padx=20, pady=(8, 4))
row += 1

endpoint_var = tk.StringVar(value=config.get('agent_endpoint', 'http://localhost:8080'))
tk.Entry(tab_ai, textvariable=endpoint_var, bg=COLORS['entry_bg'],
        fg=COLORS['fg'], insertbackground=COLORS['fg'],
        relief="flat", font=(FONT, 10)).grid(
    row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 4))
row += 1

tk.Label(tab_ai, text="API Token", bg=COLORS['bg'], fg=COLORS['fg'],
         anchor="w", font=(FONT, 10)).grid(row=row, column=0, sticky="w", padx=20, pady=(8, 4))
row += 1

token_var = tk.StringVar(value=config.get('agent_token', ''))
tk.Entry(tab_ai, textvariable=token_var, bg=COLORS['entry_bg'],
        fg=COLORS['fg'], insertbackground=COLORS['fg'],
        relief="flat", font=(FONT, 10), show="*").grid(
    row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 4))
row += 1

tk.Label(tab_ai, text="请求超时（秒）", bg=COLORS['bg'], fg=COLORS['fg'],
         anchor="w", font=(FONT, 10)).grid(row=row, column=0, sticky="w", padx=20, pady=(8, 4))

timeout_var = tk.IntVar(value=config.get('agent_timeout', 30))
tk.Spinbox(tab_ai, textvariable=timeout_var, from_=5, to=120,
          bg=COLORS['entry_bg'], fg=COLORS['fg'],
          insertbackground=COLORS['fg'], relief="flat",
          font=(FONT, 10), width=10).grid(
    row=row, column=1, sticky="w", padx=20, pady=(8, 4))
row += 1

def test_connection():
    try:
        import requests
        ep = endpoint_var.get().strip()
        response = requests.get(f"{ep}/health", timeout=5)
        if response.status_code == 200:
            messagebox.showinfo("测试连接", "连接成功！")
        else:
            messagebox.showwarning("测试连接", f"连接失败：HTTP {response.status_code}")
    except Exception as e:
        messagebox.showerror("测试连接", f"连接失败：{str(e)}")

tk.Button(tab_ai, text="测试连接", command=test_connection,
         bg=COLORS['accent'], fg="#fff", relief="flat",
         padx=20, pady=4).grid(row=row, column=0, columnspan=2, pady=(20, 4))

# === 定时提醒 TAB ===
tab_reminder = tk.Frame(notebook, bg=COLORS['bg'])
notebook.add(tab_reminder, text='  定时提醒  ')

list_frame = tk.Frame(tab_reminder, bg=COLORS['bg'])
list_frame.pack(fill='both', expand=True, padx=20, pady=(20, 10))

header_frame = tk.Frame(list_frame, bg=COLORS['bg'])
header_frame.pack(fill='x', pady=(0, 8))

tk.Label(header_frame, text="提醒列表", bg=COLORS['bg'], fg=COLORS['fg'],
         font=(FONT, 10, "bold")).pack(side='left')

REPEAT_OPTIONS = ['不重复', '每天', '每周', '每月', '每年']

columns = ('name', 'time', 'repeat', 'enabled')
reminder_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)

reminder_tree.heading('name', text='名称')
reminder_tree.heading('time', text='时间')
reminder_tree.heading('repeat', text='重复')
reminder_tree.heading('enabled', text='状态')

reminder_tree.column('name', width=150)
reminder_tree.column('time', width=100)
reminder_tree.column('repeat', width=100)
reminder_tree.column('enabled', width=60, anchor='center')

scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=reminder_tree.yview)
reminder_tree.configure(yscrollcommand=scrollbar.set)

reminder_tree.pack(side='left', fill='both', expand=True)
scrollbar.pack(side='right', fill='y')

def load_reminders():
    for item in reminder_tree.get_children():
        reminder_tree.delete(item)
    reminders = config.get('reminders', [])
    for r in reminders:
        status = "启用" if r.get('enabled', True) else "禁用"
        reminder_tree.insert('', 'end', values=(
            r.get('name', ''), r.get('time', ''),
            r.get('repeat', '不重复'), status
        ))

load_reminders()

def add_reminder():
    dialog = tk.Toplevel(root)
    dialog.title("添加提醒")
    dialog.configure(bg=COLORS['bg'])
    dialog.resizable(False, False)
    dialog.geometry(f"360x320+{root.winfo_x()+80}+{root.winfo_y()+80}")
    dialog.attributes("-topmost", True)
    dialog.grab_set()

    r = 0
    tk.Label(dialog, text="提醒名称", bg=COLORS['bg'], fg=COLORS['fg'],
             font=(FONT, 10)).grid(row=r, column=0, sticky="w", padx=20, pady=(20, 4))
    r += 1
    name_var = tk.StringVar()
    tk.Entry(dialog, textvariable=name_var, bg=COLORS['entry_bg'], fg=COLORS['fg'],
            insertbackground=COLORS['fg'], relief="flat", font=(FONT, 10)).grid(
        row=r, column=0, sticky="ew", padx=20, pady=(0, 8))
    r += 1

    tk.Label(dialog, text="提醒时间 (HH:MM)", bg=COLORS['bg'], fg=COLORS['fg'],
             font=(FONT, 10)).grid(row=r, column=0, sticky="w", padx=20, pady=(8, 4))
    r += 1
    time_var = tk.StringVar(value="09:00")
    tk.Entry(dialog, textvariable=time_var, bg=COLORS['entry_bg'], fg=COLORS['fg'],
            insertbackground=COLORS['fg'], relief="flat", font=(FONT, 10)).grid(
        row=r, column=0, sticky="ew", padx=20, pady=(0, 8))
    r += 1

    tk.Label(dialog, text="重复方式", bg=COLORS['bg'], fg=COLORS['fg'],
             font=(FONT, 10)).grid(row=r, column=0, sticky="w", padx=20, pady=(8, 4))
    r += 1
    repeat_var = tk.StringVar(value='不重复')
    ttk.Combobox(dialog, textvariable=repeat_var, values=REPEAT_OPTIONS,
                state='readonly', font=(FONT, 10)).grid(
        row=r, column=0, sticky="ew", padx=20, pady=(0, 8))
    r += 1

    tk.Label(dialog, text="提醒内容", bg=COLORS['bg'], fg=COLORS['fg'],
             font=(FONT, 10)).grid(row=r, column=0, sticky="w", padx=20, pady=(8, 4))
    r += 1
    content_var = tk.StringVar()
    tk.Entry(dialog, textvariable=content_var, bg=COLORS['entry_bg'], fg=COLORS['fg'],
            insertbackground=COLORS['fg'], relief="flat", font=(FONT, 10)).grid(
        row=r, column=0, sticky="ew", padx=20, pady=(0, 8))
    r += 1

    enabled_var = tk.BooleanVar(value=True)
    tk.Checkbutton(dialog, text="启用提醒", variable=enabled_var,
                  bg=COLORS['bg'], fg=COLORS['fg'], selectcolor=COLORS['select_indicator'],
                  activebackground=COLORS['select_bg'], activeforeground=COLORS['fg'],
                  font=(FONT, 10), indicatoron=True).grid(row=r, column=0, sticky="w", padx=20, pady=(8, 4))
    r += 1

    def ok():
        name = name_var.get().strip()
        t = time_var.get().strip()
        if not name or not t:
            messagebox.showwarning("提示", "请填写名称和时间", parent=dialog)
            return
        try:
            datetime.strptime(t, '%H:%M')
        except ValueError:
            messagebox.showwarning("提示", "时间格式不正确，请使用 HH:MM", parent=dialog)
            return
        reminders = config.get('reminders', [])
        reminders.append({
            'name': name, 'time': t,
            'repeat': repeat_var.get(),
            'content': content_var.get().strip(),
            'enabled': enabled_var.get()
        })
        config.set('reminders', reminders)
        load_reminders()
        dialog.destroy()

    btn_frame = tk.Frame(dialog, bg=COLORS['bg'])
    btn_frame.grid(row=r, column=0, pady=(16, 20))
    tk.Button(btn_frame, text="确定", command=ok,
             bg=COLORS['accent'], fg="#fff", relief="flat",
             padx=24, pady=4).pack(side='left', padx=8)
    tk.Button(btn_frame, text="取消", command=dialog.destroy,
             bg=COLORS['border'], fg=COLORS['fg'], relief="flat",
             padx=16, pady=4).pack(side='left', padx=8)

tk.Button(header_frame, text="+ 添加提醒", command=add_reminder,
         bg=COLORS['accent'], fg="#fff", relief="flat",
         padx=8, pady=2).pack(side='right')

btn_frame2 = tk.Frame(tab_reminder, bg=COLORS['bg'])
btn_frame2.pack(fill='x', padx=20, pady=(0, 20))

def delete_reminder():
    selected = reminder_tree.selection()
    if not selected:
        return
    item = reminder_tree.item(selected[0])
    name = item['values'][0]
    reminders = config.get('reminders', [])
    reminders = [r for r in reminders if r.get('name') != name]
    config.set('reminders', reminders)
    load_reminders()

tk.Button(btn_frame2, text="删除", command=delete_reminder,
         bg=COLORS['danger'], fg="#fff", relief="flat",
         padx=12, pady=2).pack(side='left', padx=(0, 8))

# === 底部按钮 ===
bottom_frame = tk.Frame(root, bg=COLORS['bg'])
bottom_frame.pack(fill='x', padx=20, pady=(0, 20))

def save():
    config.set('archive_dir', dir_var.get().strip())
    config.set('scale', round(scale_var.get(), 2))
    config.set('screenshot_action', ss_var.get())
    config.set('ai_enabled', ai_enabled_var.get())
    config.set('agent_type', agent_type_var.get())
    config.set('agent_endpoint', endpoint_var.get().strip())
    config.set('agent_token', token_var.get().strip())
    config.set('agent_timeout', timeout_var.get())
    config.save()
    import tempfile
    marker = os.path.join(tempfile.gettempdir(), '.meowdesk_settings_saved')
    with open(marker, 'w') as mf:
        mf.write('saved')
    messagebox.showinfo("设置", "设置已保存！")
    root.destroy()

tk.Button(bottom_frame, text="保存", command=save,
         bg=COLORS['accent'], fg="#fff", relief="flat",
         padx=32, pady=6, font=(FONT, 10, "bold")).pack(side='right', padx=(8, 0))

tk.Button(bottom_frame, text="取消", command=root.destroy,
         bg=COLORS['border'], fg=COLORS['fg'], relief="flat",
         padx=20, pady=6, font=(FONT, 10)).pack(side='right')

root.mainloop()
'''

    marker_file = os.path.join(tempfile.gettempdir(), '.meowdesk_settings_saved')

    if os.path.exists(marker_file):
        try:
            os.remove(marker_file)
        except Exception:
            pass

    proc = subprocess.Popen(
        [sys.executable, '-c', script, config_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    return proc


def check_settings_saved():
    marker_file = os.path.join(tempfile.gettempdir(), '.meowdesk_settings_saved')
    if os.path.exists(marker_file):
        try:
            os.remove(marker_file)
        except Exception:
            pass
        return True
    return False
