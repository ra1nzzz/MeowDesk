#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
灵犀文件精灵 (LingXi Droplet) v2 — tkinter 版
================================================================
用 tkinter 替代 PyQt5，解决无桌面会话环境下 PyQt5 挂死的问题。
tkinter 是 Python 内置库，兼容性更好。

功能:
  1. 桌面右上角悬浮图标，接受文件拖放
  2. 智能分类: 截图→回收站, 其它文件按类型+日期归档
  3. 自动生成 HTML 导航页面用于检索

用法: python lingxi_droplet_tk.py
"""

import os
import sys
import json
import shutil
import hashlib
import datetime
import webbrowser
import math
import tkinter as tk
from tkinter import dnd
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
#  配置
# ═══════════════════════════════════════════════════════════════

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = r"D:\lingxi-temp"
ARCHIVE_DIR = r"D:\lingxi-file"
HTML_INDEX = os.path.join(ARCHIVE_DIR, "index.html")
DB_FILE = os.path.join(ARCHIVE_DIR, ".filedb.json")
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")

DEFAULT_CONFIG = {
    "temp_dir": TEMP_DIR,
    "archive_dir": ARCHIVE_DIR,
    "window_position": None,
    "categories": {
        "截图": {"exts": [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tiff"], "action": "recycle"},
        "文档": {"exts": [".doc", ".docx", ".pdf", ".txt", ".rtf", ".odt", ".md", ".csv", ".xlsx", ".xls", ".ppt", ".pptx"], "action": "archive"},
        "图片": {"exts": [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tiff", ".svg", ".ico"], "action": "archive"},
        "视频": {"exts": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"], "action": "archive"},
        "音频": {"exts": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"], "action": "archive"},
        "代码": {"exts": [".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".java", ".cpp", ".c", ".h", ".go", ".rs", ".rb", ".php", ".sh", ".bat", ".ps1", ".sql", ".yaml", ".yml", ".toml", ".ini", ".cfg"], "action": "archive"},
        "压缩包": {"exts": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"], "action": "archive"},
        "安装包": {"exts": [".exe", ".msi", ".dmg", ".deb", ".rpm", ".appimage"], "action": "archive"},
        "设计稿": {"exts": [".psd", ".ai", ".sketch", ".fig", ".xd", ".eps"], "action": "archive"},
        "电子书": {"exts": [".epub", ".mobi", ".azw", ".azw3", ".djvu"], "action": "archive"},
    }
}


def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    # 同时写入日志文件
    try:
        log_dir = os.path.join(SCRIPT_DIR, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "lingxi_droplet.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            cfg = {**DEFAULT_CONFIG, **saved}
            cfg["categories"] = {**DEFAULT_CONFIG["categories"], **saved.get("categories", {})}
            return cfg
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
#  文件数据库
# ═══════════════════════════════════════════════════════════════

class FileDatabase:
    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_record(self, record):
        self.data.append(record)
        self._save()

    def search(self, keyword=None, category=None):
        results = self.data
        if keyword:
            kw = keyword.lower()
            results = [r for r in results if kw in r.get("original_name", "").lower()]
        if category and category != "全部":
            results = [r for r in results if r.get("category") == category]
        return results

    def get_stats(self):
        stats = {}
        for r in self.data:
            cat = r.get("category", "未分类")
            if cat not in stats:
                stats[cat] = {"count": 0, "size": 0}
            stats[cat]["count"] += 1
            stats[cat]["size"] += r.get("file_size", 0)
        return stats


# ═══════════════════════════════════════════════════════════════
#  文件分类引擎
# ═══════════════════════════════════════════════════════════════

def is_screenshot(filepath):
    name = os.path.basename(filepath).lower()
    dir_path = os.path.dirname(filepath).lower()

    keywords = [
        "screenshot", "截图", "截屏", "screen", "capture", "snap",
        "微信截图", "qq截图", "snipaste", "snip", "paste",
        "屏幕", "screen shot", "printscreen", "prtsc",
    ]
    for kw in keywords:
        if kw in name:
            return True

    temp_markers = ["\\temp\\", "\\tmp\\", "\\appdata\\", "clipboard", "screenshot"]
    for marker in temp_markers:
        if marker in dir_path:
            return True

    # 图片分辨率检测
    try:
        from PIL import Image
        img = Image.open(filepath)
        w, h = img.size
        # 保守判断：用常见的屏幕分辨率范围
        common_screen_widths = [1280, 1366, 1440, 1536, 1600, 1920, 2560, 3440, 3840]
        for sw in common_screen_widths:
            if abs(w - sw) <= 10 and h >= sw * 0.4:
                return True
    except Exception:
        pass

    return False


def classify_file(filepath, config):
    ext = os.path.splitext(filepath)[1].lower()
    categories = config.get("categories", {})

    screenshot_exts = categories.get("截图", {}).get("exts", [])
    if ext in screenshot_exts and is_screenshot(filepath):
        return "截图", "recycle"

    for cat_name, cat_info in categories.items():
        if cat_name == "截图":
            if ext in cat_info.get("exts", []):
                return "图片", "archive"
            continue
        if ext in cat_info.get("exts", []):
            return cat_name, cat_info.get("action", "archive")

    return "其他", "archive"


def get_archive_path(filepath, category, archive_root):
    now = datetime.datetime.now()
    date_folder = now.strftime("%Y-%m")
    cat_dir = os.path.join(archive_root, category, date_folder)
    os.makedirs(cat_dir, exist_ok=True)

    original_name = os.path.basename(filepath)
    target = os.path.join(cat_dir, original_name)

    if os.path.exists(target):
        name, ext = os.path.splitext(original_name)
        timestamp = now.strftime("%H%M%S")
        target = os.path.join(cat_dir, f"{name}_{timestamp}{ext}")
        if os.path.exists(target):
            target = os.path.join(cat_dir, f"{name}_{timestamp}_{os.urandom(4).hex()}{ext}")

    return target


def move_to_recycle(filepath):
    try:
        import send2trash
        send2trash.send2trash(filepath)
        return True
    except ImportError:
        pass
    try:
        from ctypes import windll
        path = os.path.abspath(filepath)
        result = windll.shell32.SHFileOperationW(
            None, 0x0003, path + '\0', None, 0x0040, None, None
        )
        return result == 0
    except Exception:
        pass
    try:
        os.remove(filepath)
        return True
    except Exception:
        return False


def file_md5(filepath):
    h = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════════
#  HTML 导航生成器
# ═══════════════════════════════════════════════════════════════

def generate_html_index(db, archive_dir, config):
    stats = db.get_stats()
    all_records = list(reversed(db.data))

    cat_icons = {
        "截图": "📸", "文档": "📄", "图片": "🖼️", "视频": "🎬",
        "音频": "🎵", "代码": "💻", "压缩包": "📦", "安装包": "💿",
        "设计稿": "🎨", "电子书": "📚", "其他": "📁",
    }
    cat_colors = {
        "截图": "#ef4444", "文档": "#3b82f6", "图片": "#8b5cf6", "视频": "#ec4899",
        "音频": "#f59e0b", "代码": "#10b981", "压缩包": "#f97316", "安装包": "#6366f1",
        "设计稿": "#d946ef", "电子书": "#14b8a6", "其他": "#6b7280",
    }

    cat_options = '<option value="全部">全部分类</option>'
    for cat in sorted(stats.keys()):
        icon = cat_icons.get(cat, "📁")
        count = stats[cat]["count"]
        cat_options += f'<option value="{cat}">{icon} {cat} ({count})</option>'

    file_rows = ""
    for r in all_records:
        cat = r.get("category", "未分类")
        action = r.get("action", "")
        icon = cat_icons.get(cat, "📁")
        color = cat_colors.get(cat, "#6b7280")
        action_badge = '<span class="badge badge-recycle">已回收</span>' if action == "recycle" else '<span class="badge badge-archive">已归档</span>'
        size_mb = r.get("file_size", 0) / (1024 * 1024)
        size_str = f"{size_mb:.2f} MB" if size_mb >= 0.01 else f"{r.get('file_size', 0) / 1024:.1f} KB"
        dest = r.get("destination", "").replace("\\", "/")
        file_rows += f"""<tr>
            <td><span class="cat-dot" style="background:{color}"></span> {icon} {cat}</td>
            <td title="{r.get('original_name', '')}">{r.get('original_name', '')}</td>
            <td>{r.get('date', '')}</td>
            <td>{size_str}</td>
            <td>{action_badge}</td>
            <td class="path-cell" title="{dest}">{os.path.basename(dest) if dest else '-'}</td>
        </tr>"""

    total_count = sum(s["count"] for s in stats.values())
    total_size = sum(s["size"] for s in stats.values())
    total_size_gb = total_size / (1024 ** 3)
    size_display = f"{total_size_gb:.2f} GB" if total_size_gb >= 1 else f"{total_size / (1024**2):.1f} MB"

    stat_cards = ""
    for cat in sorted(stats.keys(), key=lambda x: -stats[x]["count"]):
        icon = cat_icons.get(cat, "📁")
        color = cat_colors.get(cat, "#6b7280")
        cnt = stats[cat]["count"]
        sz = stats[cat]["size"] / (1024**2) if stats[cat]["size"] < 1024**3 else stats[cat]["size"] / (1024**3)
        unit = "MB" if stats[cat]["size"] < 1024**3 else "GB"
        stat_cards += f"""<div class="stat-card" style="border-left: 3px solid {color}">
            <div class="stat-icon">{icon}</div>
            <div class="stat-info">
                <div class="stat-name">{cat}</div>
                <div class="stat-detail">{cnt} 个文件 · {sz:.1f} {unit}</div>
            </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>灵犀文件精灵 - 文件导航</title>
<style>
  :root {{ --bg: #0f1117; --bg2: #1a1d27; --bg3: #242837; --fg: #e2e8f0; --fg2: #94a3b8; --accent: #6366f1; --accent2: #818cf8; --border: #2d3348; --radius: 12px; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, "Microsoft YaHei", "Segoe UI", sans-serif; background: var(--bg); color: var(--fg); line-height: 1.6; min-height: 100vh; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px; }}
  .header {{ text-align: center; margin-bottom: 40px; padding: 40px 0; background: linear-gradient(135deg, var(--bg2), var(--bg3)); border-radius: var(--radius); border: 1px solid var(--border); }}
  .header h1 {{ font-size: 32px; font-weight: 700; background: linear-gradient(135deg, var(--accent), #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px; }}
  .header p {{ color: var(--fg2); font-size: 14px; }}
  .summary {{ display: flex; gap: 24px; margin-bottom: 32px; flex-wrap: wrap; }}
  .summary-card {{ flex: 1; min-width: 180px; background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; text-align: center; }}
  .summary-card .num {{ font-size: 36px; font-weight: 800; color: var(--accent2); }}
  .summary-card .label {{ color: var(--fg2); font-size: 13px; margin-top: 4px; }}
  .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; margin-bottom: 32px; }}
  .stat-card {{ display: flex; align-items: center; gap: 14px; background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px 20px; transition: transform 0.15s, box-shadow 0.15s; }}
  .stat-card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }}
  .stat-icon {{ font-size: 28px; }}
  .stat-name {{ font-weight: 600; font-size: 15px; }}
  .stat-detail {{ color: var(--fg2); font-size: 12px; }}
  .toolbar {{ display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; align-items: center; }}
  .toolbar input, .toolbar select {{ background: var(--bg2); border: 1px solid var(--border); color: var(--fg); padding: 10px 16px; border-radius: 8px; font-size: 14px; outline: none; }}
  .toolbar input:focus, .toolbar select:focus {{ border-color: var(--accent); }}
  .toolbar input {{ flex: 1; min-width: 200px; }}
  .toolbar select {{ min-width: 160px; cursor: pointer; }}
  .toolbar .btn {{ padding: 10px 20px; border-radius: 8px; border: 1px solid var(--accent); background: var(--accent); color: #fff; cursor: pointer; font-size: 14px; font-weight: 500; }}
  .toolbar .btn:hover {{ background: var(--accent2); }}
  .table-wrap {{ background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ background: var(--bg3); padding: 14px 16px; text-align: left; font-weight: 600; font-size: 13px; color: var(--fg2); text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border); }}
  td {{ padding: 12px 16px; font-size: 14px; border-bottom: 1px solid var(--border); max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: rgba(99, 102, 241, 0.06); }}
  .cat-dot {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }}
  .badge {{ display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }}
  .badge-archive {{ background: rgba(16, 185, 129, 0.15); color: #34d399; }}
  .badge-recycle {{ background: rgba(239, 68, 68, 0.15); color: #f87171; }}
  .path-cell {{ color: var(--fg2); font-size: 12px; }}
  .empty {{ text-align: center; padding: 60px 20px; color: var(--fg2); }}
  .empty .icon {{ font-size: 48px; margin-bottom: 16px; }}
  .footer {{ text-align: center; margin-top: 48px; padding: 24px 0; color: var(--fg2); font-size: 12px; border-top: 1px solid var(--border); }}
  @media (max-width: 768px) {{ .summary {{ flex-direction: column; }} .stats-grid {{ grid-template-columns: 1fr; }} .toolbar {{ flex-direction: column; }} }}
</style>
</head>
<body>
<div class="container">
  <div class="header"><h1>灵犀文件精灵</h1><p>智能文件分类归档 · 拖拽即整理</p></div>
  <div class="summary">
    <div class="summary-card"><div class="num">{total_count}</div><div class="label">累计处理文件</div></div>
    <div class="summary-card"><div class="num">{len(stats)}</div><div class="label">文件分类数</div></div>
    <div class="summary-card"><div class="num">{size_display}</div><div class="label">归档总大小</div></div>
  </div>
  <div class="stats-grid">{stat_cards}</div>
  <div class="toolbar">
    <input type="text" id="search" placeholder="搜索文件名..." oninput="filterTable()">
    <select id="catFilter" onchange="filterTable()">{cat_options}</select>
    <button class="btn" onclick="location.reload()">刷新</button>
    <button class="btn" style="background:transparent;border-color:var(--border);color:var(--fg2)" onclick="openDir('{archive_dir}')">打开归档目录</button>
  </div>
  <div class="table-wrap">
    <table><thead><tr><th>分类</th><th>文件名</th><th>日期</th><th>大小</th><th>操作</th><th>归档路径</th></tr></thead>
    <tbody id="fileBody">
      {file_rows if file_rows else '<tr><td colspan="6"><div class="empty"><div class="icon">📂</div><p>暂无文件记录</p><p style="font-size:12px;margin-top:8px">将文件拖拽到悬浮图标即可自动分类归档</p></div></td></tr>'}
    </tbody></table>
  </div>
  <div class="footer">灵犀文件精灵 · LingXi Droplet · 数据存储于本地 {archive_dir}</div>
</div>
<script>
function filterTable() {{ var kw=document.getElementById('search').value.toLowerCase(); var cat=document.getElementById('catFilter').value; document.querySelectorAll('#fileBody tr').forEach(r=>{{ var c=r.querySelectorAll('td'); if(c.length<6)return; var fn=c[1].textContent.toLowerCase(); var rc=c[0].textContent.trim(); r.style.display=(!kw||fn.includes(kw))&&(cat==='全部'||rc.startsWith(cat))?'':'none'; }}); }}
function openDir(p) {{ try {{ var s=new ActiveXObject('Shell.Application'); s.Open(p); }} catch(e) {{ alert('请手动打开: '+p); }} }}
document.addEventListener('keydown',function(e){{ if(e.key==='/'&&document.activeElement.tagName!=='INPUT'){{ e.preventDefault(); document.getElementById('search').focus(); }} }});
</script>
</body></html>"""
    return html


# ═══════════════════════════════════════════════════════════════
#  tkinter 悬浮窗口 + DnD
# ═══════════════════════════════════════════════════════════════

class LingXiDroplet:
    """tkinter 版悬浮拖拽窗口"""

    def __init__(self, config, db):
        self.config = config
        self.db = db
        self.temp_dir = config["temp_dir"]
        self.archive_dir = config["archive_dir"]

        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)

        # 状态
        self._hover = False
        self._processing = False
        self._pulse_phase = 0
        self._notify_text = ""
        self._notify_after_id = None

        # 尝试使用 tkdnd（更好的拖放支持）
        self._has_tkdnd = False

        self._create_window()

    def _create_window(self):
        """创建主窗口"""
        self.root = tk.Tk()
        self.root.title("灵犀文件精灵")
        self.root.overrideredirect(True)  # 无边框
        self.root.attributes("-topmost", True)  # 置顶

        # 尝试设置半透明（Windows 10+）
        try:
            self.root.attributes("-alpha", 0.92)
        except Exception:
            pass

        # 尝试设置 DWM 无阴影（让窗口更干净）
        try:
            from ctypes import windll
            hwnd = windll.user32.GetParent(self.root.winfo_id())
            # DWMWA_NCRENDERING_POLICY = 2, DWMNCRP_DISABLED = 1
            windll.dwmapi.DwmSetWindowAttribute(hwnd, 2, 1, 4)
        except Exception:
            pass

        # 窗口大小
        self.win_size = 80
        self.root.geometry(f"{self.win_size}x{self.win_size}")

        # 移动到右上角
        self._move_to_position()

        # 创建 Canvas（用于绘制图标）
        # 使用背景色来模拟透明
        self.canvas = tk.Canvas(
            self.root,
            width=self.win_size,
            height=self.win_size + 30,
            bg="#1a1d27",
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack()

        # 绑定事件
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        # 拖放支持: 尝试 tkdnd
        self._setup_dnd()

        # 如果没有 tkdnd，用备用方案
        if not self._has_tkdnd:
            self._setup_fallback_dnd()

        # 绑定窗口关闭（只隐藏不退出）
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 绘制
        self._animate()

        # 右键菜单
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="打开文件导航", command=self._open_html)
        self.menu.add_command(label="打开归档目录", command=lambda: os.startfile(self.archive_dir))
        self.menu.add_command(label="打开临时目录", command=lambda: os.startfile(self.temp_dir))
        self.menu.add_separator()
        self.menu.add_command(label="退出", command=self._quit)
        self.canvas.bind("<ButtonPress-3>", self._show_menu)

        log(f"窗口创建完成 ({self.win_size}x{self.win_size}), tkdnd={'有' if self._has_tkdnd else '无(使用备用方案)'}")

    def _move_to_position(self):
        """移动到指定位置"""
        saved = self.config.get("window_position")
        if saved and len(saved) == 2:
            x, y = saved
        else:
            sw = self.root.winfo_screenwidth()
            x = sw - self.win_size - 20
            y = 20
        self.root.geometry(f"+{x}+{y}")

    def _setup_dnd(self):
        """尝试使用 tkdnd 库实现拖放"""
        try:
            self.root.tk.eval("package require tkdnd")
            self.root.tk.call("tkdnd::drop_target", "register", self.root.winfo_pathname(self.root.winfo_id()), "*")
            self.root.drop_target_register("DND_Files")
            self.root.dnd_bind("<<Drop>>", self._on_tkdnd_drop)
            self.root.dnd_bind("<<DragEnter>>", self._on_tkdnd_enter)
            self.root.dnd_bind("<<DragLeave>>", self._on_tkdnd_leave)
            self._has_tkdnd = True
            log("tkdnd 拖放支持: 已启用")
        except Exception as e:
            log(f"tkdnd 不可用: {e}")

    def _setup_fallback_dnd(self):
        """备用拖放方案: 使用 Windows 消息"""
        # tkinter 原生不支持文件拖放，需要用 Win32 消息
        # 注册文件拖放消息
        try:
            import ctypes
            self._user32 = ctypes.windll.user32

            # 获取窗口句柄
            self.root.update_idletasks()
            self._hwnd = self.root.winfo_id()

            # 定义消息常量
            self.WM_DROPFILES = 0x0233

            # 设置接受文件
            self._shell32 = ctypes.windll.shell32
            self._shell32.DragAcceptFiles(self._hwnd, True)

            # 子类化窗口
            self._old_wndproc = None
            try:
                WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, ctypes.c_uint, ctypes.c_int, ctypes.c_int)

                # 先定义回调
                def _wndproc(hwnd, msg, wparam, lparam):
                    if msg == self.WM_DROPFILES:
                        self._on_win32_drop(wparam)
                        return 0
                    if self._old_wndproc:
                        return self._user32.CallWindowProcW(self._old_wndproc, hwnd, msg, wparam, lparam)
                    return self._user32.DefWindowProcW(hwnd, msg, wparam, lparam)

                self._new_wndproc = WNDPROC(_wndproc)
                # 再替换窗口过程
                self._old_wndproc = self._user32.SetWindowLongW(self._hwnd, -4, self._new_wndproc)
                log("Win32 拖放支持: 已启用")
            except Exception as e:
                log(f"Win32 子类化失败: {e}")
                log("备用方案: 请将文件拖入临时目录或使用命令行参数")

        except Exception as e:
            log(f"备用拖放设置失败: {e}")

    def _on_win32_drop(self, wparam):
        """处理 Win32 WM_DROPFILES 消息"""
        try:
            import ctypes
            self._shell32 = ctypes.windll.shell32

            # 获取文件数量
            n_files = self._shell32.DragQueryFileW(wparam, -1, None, 0)
            files = []
            buf = ctypes.create_unicode_buffer(1024)

            for i in range(n_files):
                self._shell32.DragQueryFileW(wparam, i, buf, 1024)
                path = buf.value
                if os.path.isfile(path):
                    files.append(path)

            self._shell32.DragFinish(wparam)

            if files:
                log(f"[拖放] 收到 {len(files)} 个文件")
                self.root.after(10, lambda: self._process_files(files))

        except Exception as e:
            log(f"[拖放] 处理失败: {e}")

    def _on_tkdnd_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        valid_files = [f for f in files if os.path.isfile(f)]
        if valid_files:
            log(f"[拖放] 收到 {len(valid_files)} 个文件")
            self.root.after(10, lambda: self._process_files(valid_files))

    def _on_tkdnd_enter(self, event):
        self._hover = True

    def _on_tkdnd_leave(self, event):
        self._hover = False

    # --- 鼠标事件 ---

    def _on_enter(self, event):
        self._hover = True

    def _on_leave(self, event):
        self._hover = False

    def _on_press(self, event):
        self._drag_offset_x = event.x
        self._drag_offset_y = event.y

    def _on_drag(self, event):
        x = self.root.winfo_x() + event.x - self._drag_offset_x
        y = self.root.winfo_y() + event.y - self._drag_offset_y
        self.root.geometry(f"+{x}+{y}")

    def _on_release(self, event):
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        self.config["window_position"] = [x, y]
        save_config(self.config)
        log(f"位置已保存: ({x}, {y})")

    def _show_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

    def _on_close(self):
        self.root.withdraw()  # 隐藏而不是退出

    def _quit(self):
        log("退出程序")
        self.root.destroy()

    def _open_html(self):
        if os.path.exists(HTML_INDEX):
            webbrowser.open(HTML_INDEX)
        else:
            log("[警告] HTML 导航页不存在，正在生成...")
            self._regenerate_html()
            webbrowser.open(HTML_INDEX)

    # --- 绘制 ---

    def _animate(self):
        """呼吸灯动画 + 重绘"""
        self._pulse_phase = (self._pulse_phase + 3) % 360
        self._draw()
        self.root.after(60, self._animate)  # ~16fps

    def _draw(self):
        """绘制悬浮图标"""
        c = self.canvas
        c.delete("all")

        s = self.win_size
        cx, cy = s // 2, s // 2
        pulse = (math.sin(math.radians(self._pulse_phase)) + 1) / 2

        # 颜色
        if self._processing:
            fill = "#4338ca"
            outline = "#818cf8"
        elif self._hover:
            fill = "#4f46e5"
            outline = "#a5b4fc"
        else:
            fill = "#1e2133"
            outline = "#6366f1"

        # 外圈光晕
        glow_alpha_hex = format(int(30 + 50 * pulse), "02x")
        c.create_oval(cx - 38, cy - 38, cx + 38, cy + 38, fill="", outline=outline, width=1, dash=(2, 4))

        # 主圆
        margin = 8
        c.create_oval(margin, margin, s - margin, s - margin, fill=fill, outline=outline, width=2)

        # 图标文字
        if self._processing:
            icon = "⟳"
        elif self._hover:
            icon = "⬇"
        else:
            icon = "✦"

        c.create_text(cx, cy, text=icon, fill="white", font=("Segoe UI", 22, "bold"))

        # 通知气泡
        if self._notify_text:
            bw = 180
            bh = 24
            bx = cx - bw // 2
            by = s + 2
            c.create_rectangle(bx, by, bx + bw, by + bh, fill="#0f1117", outline="#2d3348")
            c.create_text(cx, by + bh // 2, text=self._notify_text, fill="#e2e8f0", font=("Microsoft YaHei", 9))

    def _show_notify(self, text, duration=3000):
        self._notify_text = text
        if self._notify_after_id:
            self.root.after_cancel(self._notify_after_id)
        self._notify_after_id = self.root.after(duration, self._clear_notify)

    def _clear_notify(self):
        self._notify_text = ""
        self._notify_after_id = None

    # --- 文件处理 ---

    def _process_files(self, file_paths):
        self._processing = True
        recycled = 0
        archived = 0
        errors = []

        for filepath in file_paths:
            try:
                result = self._process_single(filepath)
                if result == "recycle":
                    recycled += 1
                else:
                    archived += 1
            except Exception as e:
                errors.append(f"{os.path.basename(filepath)}: {e}")
                log(f"[错误] {e}")

        self._processing = False

        # 更新 HTML
        self._regenerate_html()

        # 通知
        parts = []
        if recycled:
            parts.append(f"{recycled} 截图已回收")
        if archived:
            parts.append(f"{archived} 文件已归档")
        if errors:
            parts.append(f"{len(errors)} 失败")
        msg = " · ".join(parts) if parts else "处理完成"
        self._show_notify(msg, 4000)
        log(f"[完成] {msg}")

    def _process_single(self, filepath):
        original_name = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)
        now = datetime.datetime.now()

        # 复制到临时目录
        temp_path = os.path.join(self.temp_dir, original_name)
        if os.path.abspath(filepath) != os.path.abspath(temp_path):
            if not os.path.exists(temp_path):
                shutil.copy2(filepath, temp_path)
            work_path = temp_path
        else:
            work_path = filepath

        # 分类
        category, action = classify_file(work_path, self.config)

        timestamp = now.strftime("%Y%m%d%H%M%S%f")
        record = {
            "timestamp": timestamp,
            "original_name": original_name,
            "original_path": filepath,
            "category": category,
            "action": action,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "file_size": file_size,
            "md5": file_md5(work_path),
        }

        if action == "recycle":
            moved = move_to_recycle(work_path)
            record["destination"] = "(已回收)"
            record["recycled"] = moved
            self.db.add_record(record)
            log(f"  [回收] {original_name}")
            return "recycle"
        else:
            target = get_archive_path(work_path, category, self.archive_dir)
            shutil.copy2(work_path, target)
            record["destination"] = target
            self.db.add_record(record)
            log(f"  [归档] {original_name} → {category}/{now.strftime('%Y-%m')}/")
            return "archive"

    def _regenerate_html(self):
        try:
            html = generate_html_index(self.db, self.archive_dir, self.config)
            with open(HTML_INDEX, "w", encoding="utf-8") as f:
                f.write(html)
            log(f"HTML 导航已更新: {HTML_INDEX}")
        except Exception as e:
            log(f"[错误] 生成 HTML 失败: {e}")

    def run(self):
        log("=" * 50)
        log("  灵犀文件精灵已启动!")
        log("  请将文件拖拽到悬浮图标上")
        log("=" * 50)
        log(f"  临时目录: {self.temp_dir}")
        log(f"  归档目录: {self.archive_dir}")
        log(f"  导航页面: {HTML_INDEX}")
        log("  右键图标 → 打开文件导航 / 退出")
        log("")

        # 检查 DnD 状态
        if not self._has_tkdnd:
            log("[提示] tkdnd 未安装，使用 Win32 原生拖放")
            log("  如果拖放不工作，可安装: pip install tkdnd")

        self.root.mainloop()


# ═══════════════════════════════════════════════════════════════
#  主入口
# ═══════════════════════════════════════════════════════════════

def main():
    config = load_config()

    # 初始化数据库和 HTML
    db = FileDatabase(DB_FILE)
    os.makedirs(config["archive_dir"], exist_ok=True)
    html = generate_html_index(db, config["archive_dir"], config)
    with open(HTML_INDEX, "w", encoding="utf-8") as f:
        f.write(html)

    # 创建并运行
    app = LingXiDroplet(config, db)
    app.run()


if __name__ == "__main__":
    main()
