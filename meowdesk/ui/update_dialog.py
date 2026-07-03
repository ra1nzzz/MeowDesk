"""OTA 更新对话框 — 显示新版本信息、下载进度并触发应用。

样式与 SettingsPanel 保持一致(深色/浅色主题,圆角,无边框)。
"""

import os
import threading
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from ..utils import get_logger

if TYPE_CHECKING:
    from ..updater import UpdateManager, UpdateInfo

_log = get_logger(__name__)

# 复用 settings.py 的配色方案
from .settings import resolve_colors


def _format_size(size: int) -> str:
    """字节数 → 人类可读字符串。"""
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / 1024 / 1024:.1f} MB"


class UpdateDialog:
    """更新对话框(模态 Toplevel)。

    显示版本号、Release Notes、下载进度,提供
    [立即更新] [稍后] [跳过此版本] 三个操作。
    """

    def __init__(self, parent: tk.Misc, mgr: "UpdateManager", info: "UpdateInfo",
                 on_applied=None):
        self.parent = parent
        self.mgr = mgr
        self.info = info
        self.on_applied = on_applied
        self.COLORS = resolve_colors(mgr.config.get("color_mode", "dark"))
        self._downloading = False

        self.window = tk.Toplevel(parent)
        self.window.title("发现新版本")
        self.window.configure(bg=self.COLORS["bg"])
        self.window.resizable(False, False)

        # 窗口图标
        _set_window_icon(self.window)

        # 居中
        ww, wh = 480, 420
        self.window.update_idletasks()
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        self.window.geometry(f"{ww}x{wh}+{(sw - ww) // 2}+{(sh - wh) // 2}")
        self.window.attributes("-topmost", True)
        self.window.grab_set()

        self._build_ui()

    def _build_ui(self):
        C = self.COLORS
        w = self.window

        # 标题
        tk.Label(w, text=f"🆕 发现新版本 v{self.info.version}",
                 bg=C["bg"], fg=C["fg"],
                 font=("Microsoft YaHei UI", 14, "bold")).pack(pady=(20, 5))

        tk.Label(w, text=f"当前版本 v{self.info.tag_name.lstrip('vV')}",
                 bg=C["bg"], fg=C["text_muted"],
                 font=("Microsoft YaHei UI", 9)).pack(pady=(0, 10))

        # 文件信息
        size_str = _format_size(self.info.asset_size) if self.info.asset_size else "未知"
        tk.Label(w, text=f"📦 {self.info.asset_name}  ({size_str})",
                 bg=C["bg"], fg=C["text_secondary"],
                 font=("Microsoft YaHei UI", 9)).pack(pady=(0, 10))

        # Release Notes
        notes_frame = tk.Frame(w, bg=C["entry_bg"], relief="flat", bd=0)
        notes_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        notes_text = tk.Text(notes_frame, wrap="word", relief="flat",
                             bg=C["entry_bg"], fg=C["fg"],
                             font=("Microsoft YaHei UI", 9),
                             padx=10, pady=8, height=8,
                             highlightthickness=0, cursor="arrow")
        notes_text.pack(side="left", fill="both", expand=True)

        notes_scroll = tk.Scrollbar(notes_frame, command=notes_text.yview,
                                    troughcolor=C["entry_bg"], bg=C["border"])
        notes_scroll.pack(side="right", fill="y")
        notes_text.config(yscrollcommand=notes_scroll.set)

        # 填充 release notes(截断过长的内容)
        notes = self.info.release_notes.strip()
        if len(notes) > 2000:
            notes = notes[:2000] + "\n\n...(完整内容请查看 GitHub Release 页面)"
        notes_text.insert("1.0", notes or "暂无更新说明")
        notes_text.config(state="disabled")

        # 进度条(初始隐藏)
        self.progress = ttk.Progressbar(w, length=440, mode="determinate")
        self.progress_label = tk.Label(w, text="", bg=C["bg"], fg=C["text_secondary"],
                                       font=("Microsoft YaHei UI", 8))

        # 按钮区域
        btn_frame = tk.Frame(w, bg=C["bg"])
        btn_frame.pack(pady=(5, 20))

        self.btn_update = tk.Button(
            btn_frame, text="立即更新", width=12,
            bg=C["accent"], fg="white", relief="flat",
            font=("Microsoft YaHei UI", 10, "bold"),
            activebackground=C["accent_hover"], activeforeground="white",
            cursor="hand2", command=self._on_update)
        self.btn_update.pack(side="left", padx=5)

        tk.Button(
            btn_frame, text="稍后", width=8,
            bg=C["entry_bg"], fg=C["fg"], relief="flat",
            font=("Microsoft YaHei UI", 10),
            activebackground=C["border"], cursor="hand2",
            command=self.window.destroy).pack(side="left", padx=5)

        tk.Button(
            btn_frame, text="跳过此版本", width=10,
            bg=C["entry_bg"], fg=C["text_muted"], relief="flat",
            font=("Microsoft YaHei UI", 9),
            activebackground=C["border"], cursor="hand2",
            command=self._on_skip).pack(side="left", padx=5)

    def _on_skip(self):
        """跳过当前版本。"""
        self.mgr.skip_version(self.info.version)
        self.window.destroy()

    def _on_update(self):
        """开始下载并应用更新。"""
        if self._downloading:
            return
        self._downloading = True
        self.btn_update.config(text="正在下载...", state="disabled")

        # 显示进度条
        self.progress.pack(pady=(0, 5))
        self.progress_label.pack(pady=(0, 5))
        self.progress["value"] = 0

        def _progress_cb(downloaded: int, total: int):
            if total > 0:
                pct = downloaded * 100 / total
                self.window.after(0, lambda: self._update_progress(pct, downloaded, total))

        def _worker():
            try:
                local_path = self.mgr.download_update(self.info, progress_cb=_progress_cb)
                if local_path is None:
                    self.window.after(0, lambda: self._on_download_failed())
                    return
                self.window.after(0, lambda: self._on_download_done(local_path))
            except Exception:
                _log.exception("download failed")
                self.window.after(0, lambda: self._on_download_failed())

        threading.Thread(target=_worker, daemon=True, name="ota-download").start()

    def _update_progress(self, pct: float, downloaded: int, total: int):
        self.progress["value"] = pct
        self.progress_label.config(text=f"下载中... {pct:.0f}%  ({_format_size(downloaded)} / {_format_size(total)})")

    def _on_download_failed(self):
        """下载失败处理。"""
        from tkinter import messagebox
        self.progress.pack_forget()
        self.progress_label.pack_forget()
        self.btn_update.config(text="立即更新", state="normal")
        self._downloading = False
        messagebox.showwarning("更新失败", "下载更新包失败,请检查网络连接后重试。\n\n你也可以前往 GitHub Release 页面手动下载。",
                               parent=self.window)

    def _on_download_done(self, local_path: str):
        """下载完成,应用更新。"""
        self.progress["value"] = 100
        self.progress_label.config(text="正在应用更新,应用将自动重启...")

        # 延迟一下让用户看到进度
        self.window.after(800, lambda: self._apply(local_path))

    def _apply(self, local_path: str):
        """应用更新并退出。"""
        try:
            ok = self.mgr.apply_update(local_path)
        except Exception:
            _log.exception("apply_update failed")
            ok = False

        if not ok:
            from tkinter import messagebox
            self.progress.pack_forget()
            self.progress_label.pack_forget()
            self.btn_update.config(text="立即更新", state="normal")
            self._downloading = False
            messagebox.showerror("更新失败", "应用更新时发生错误,请手动下载替换。",
                                 parent=self.window)
            return

        # 更新脚本已启动,关闭对话框并退出主程序
        self.window.destroy()
        if self.on_applied:
            self.on_applied()
        else:
            # 默认行为:退出主程序(让 updater.bat 完成 EXE 替换)
            self.parent.after(500, self._quit_app)

    def _quit_app(self):
        """退出应用程序。"""
        try:
            self.parent.quit()
        except Exception:
            pass


def _set_window_icon(window: tk.Toplevel):
    """设置窗口图标(打包/开发模式兼容)。"""
    import sys
    bundle = getattr(sys, "_MEIPASS", None)
    base = bundle if bundle else os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    icon = os.path.join(base, "assets", "icon.ico")
    if os.path.exists(icon):
        try:
            window.iconbitmap(icon)
        except Exception:
            pass


def show_update_dialog(parent, mgr, info, on_applied=None):
    """创建并显示更新对话框。"""
    UpdateDialog(parent, mgr, info, on_applied=on_applied)


def check_update_manually(parent, config, app_dir):
    """手动检查更新(由菜单项调用)。

    显示气泡提示进度,在后台线程检查,发现新版本后弹出对话框。
    """
    from ..updater import UpdateManager

    mgr = UpdateManager(config, app_dir)

    # 尝试获取 show_bubble 来显示状态
    show_bubble = None
    if hasattr(parent, "state") and hasattr(parent.state, "show_bubble"):
        show_bubble = parent.state.show_bubble
    elif hasattr(parent, "show_bubble"):
        show_bubble = parent.show_bubble

    if not mgr.is_frozen:
        if show_bubble:
            show_bubble("开发模式不支持自动更新", 60)
        return

    if show_bubble:
        show_bubble("正在检查更新...", 40)

    def _worker():
        try:
            info = mgr.check_for_update()
            mgr.record_check()
            if not info:
                if show_bubble:
                    parent.after(0, lambda: show_bubble("已是最新版本", 40))
                return
            if mgr.should_skip_version(info.version):
                if show_bubble:
                    parent.after(0, lambda: show_bubble(f"已跳过 v{info.version}", 40))
                return
            parent.after(0, lambda: show_update_dialog(parent, mgr, info,
                                                        on_applied=lambda: parent.after(300, parent.quit)))
        except Exception:
            _log.exception("manual update check failed")
            if show_bubble:
                parent.after(0, lambda: show_bubble("检查更新失败", 40))

    threading.Thread(target=_worker, daemon=True, name="ota-manual-check").start()
