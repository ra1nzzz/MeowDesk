"""
主窗口管理器 — 顶层协调者

把状态机、文件 drop、提醒、菜单动作分别拆分到独立的模块，
本类只负责事件路由与平台窗口生命周期。
"""

import os
import sys
import time
import webbrowser
from datetime import datetime
from typing import Callable, List, Optional

from PIL import Image

from ..agent import AgentGateway
from ..core import (
    ConfigManager,
    FileClassifier,
    FileDatabase,
    FileHandler,
)
from ..utils import get_logger
from .animation import AnimationManager
from .animation_loop import AnimationLoop
from .menu_actions import build_menu_items
from .window_drop import FileDropHandler
from .window_reminders import ReminderChecker
from .window_state import WindowState


_log = get_logger(__name__)


class MeowWindow:
    """Top-level window controller.

    Owns the platform window, the animation manager, the
    :class:`WindowState`, the :class:`FileDropHandler` and the
    :class:`ReminderChecker`, and wires them together through
    platform callbacks (drop / click / drag / right-click).
    """

    FRAME_DELAY_MS = 80

    def __init__(self, config: ConfigManager, db: FileDatabase, assets_dir: str):
        self.config = config
        self.db = db
        self.assets_dir = assets_dir

        self.classifier = FileClassifier(config.config)
        self.file_handler = FileHandler(config.archive_dir, config.temp_dir)

        scale = config.config.scale
        self.animation = AnimationManager(assets_dir, scale)
        self.state = WindowState(self.animation)

        self.platform_window = None
        self.context_menu = None
        self._menu_handlers = []
        self.agent_gateway: Optional[AgentGateway] = None

        self.window_width = 0
        self.window_height = 0

        self.click_times: List[float] = []
        self.macos_timer = None

        self.on_quit_callback: Optional[Callable] = None

        self._drop_handler: Optional[FileDropHandler] = None
        self._reminder_checker: Optional[ReminderChecker] = None
        self._animation_loop: Optional[AnimationLoop] = None

    def create(self) -> None:
        """Create the platform window and wire up callbacks."""

        self.window_width, self.window_height = self.animation.get_frame_size(AnimationManager.IDLE)

        if sys.platform == "win32":
            from ..platform.windows import WindowsWindow
            self.platform_window = WindowsWindow(self.window_width, self.window_height)
        elif sys.platform == "darwin":
            from ..platform.macos import MacOSWindow
            self.platform_window = MacOSWindow(self.window_width, self.window_height)
        else:
            raise NotImplementedError(f"不支持的平台: {sys.platform}")

        self.platform_window.create()
        self.platform_window.on_drop(self._on_files_dropped)
        self.platform_window.on_click(self._on_click)
        self.platform_window.on_right_click(self._on_right_click)
        self.platform_window.on_drag_start(self._on_drag_start)
        self.platform_window.on_drag_end(self._on_drag_end)

        for event in ("on_mouse_enter", "on_mouse_exit", "on_drag_enter", "on_drag_exit"):
            if hasattr(self.platform_window, event):
                getattr(self.platform_window, event)(getattr(self, f"_{event}"))

        self._move_to_saved_position()
        self.platform_window.enable_drag_drop()
        self.platform_window.show()

        if hasattr(self.platform_window, "root") and self.platform_window.root:
            self.agent_gateway = AgentGateway(self.config.agent_config)
            from .menu import ContextMenu
            self.context_menu = ContextMenu(
                self.platform_window.root,
                self.config,
                agent_gateway=self.agent_gateway,
                on_quit_callback=self.quit,
                on_settings_saved=self._on_settings_saved,
            )

        self._init_wander()

        self._drop_handler = FileDropHandler(
            config=self.config,
            db=self.db,
            classifier=self.classifier,
            file_handler=self.file_handler,
            state=self.state,
            show_bubble=self.state.show_bubble,
            on_finished=self._update_html,
            check_archive_writable=self._ensure_archive_dir_writable,
        )
        self._reminder_checker = ReminderChecker(
            config=self.config, show_bubble=self.state.show_bubble
        )
        self._animation_loop = self._build_animation_loop()

        if sys.platform == "win32":
            if hasattr(self.platform_window, "root") and self.platform_window.root:
                self.platform_window.root.after(200, self._animate)
        elif sys.platform == "darwin":
            self._start_macos_animation()

    def run(self) -> None:
        if self.platform_window:
            self.platform_window.run()

    def quit(self) -> None:
        if self.platform_window:
            x, y = self.platform_window.get_position()
            self.config.set("window_position", [x, y])
        if self.on_quit_callback:
            self.on_quit_callback()
        if self.platform_window:
            self.platform_window.quit()

    def _move_to_saved_position(self) -> None:
        saved_pos = self.config.config.window_position
        if saved_pos and len(saved_pos) == 2:
            x, y = saved_pos
        else:
            if self.platform_window and hasattr(self.platform_window, "get_screen_size"):
                screen_width, _ = self.platform_window.get_screen_size()
                x = screen_width - self.window_width - 100
                y = 60
            else:
                x, y = 1400, 100
        self.platform_window.set_position(x, y)

    def _init_wander(self) -> None:
        if self.platform_window and hasattr(self.platform_window, "get_screen_size"):
            sw, sh = self.platform_window.get_screen_size()
        else:
            sw, sh = 1920, 1080
        self.state.init_wander(sw, sh, self.window_width, self.window_height)

    def _build_animation_loop(self) -> AnimationLoop:
        return AnimationLoop(
            animation=self.animation,
            state=self.state,
            initial_size=(self.window_width, self.window_height),
            set_window_size=self.platform_window.set_size,
            get_window_position=self.platform_window.get_position,
            set_window_position=self.platform_window.set_position,
            render_frame=self.platform_window.render,
            draw_bubble=self._draw_bubble,
            on_tick=self._reminder_checker.tick if self._reminder_checker else None,
        )

    def _animate(self) -> None:
        if not self.platform_window:
            return
        if not getattr(self.platform_window, "root", None):
            return

        loop = self._animation_loop
        loop.tick()

        if getattr(self.platform_window, "root", None):
            self.platform_window.root.after(int(loop.frame_duration()), self._animate)

    def _start_macos_animation(self) -> None:
        if sys.platform != "darwin":
            return
        from Foundation import NSTimer, NSRunLoop
        from AppKit import NSEventTrackingRunLoopMode

        if getattr(self, "macos_timer", None):
            self.macos_timer.invalidate()
            self.macos_timer = None

        self.macos_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.08, self.platform_window.view, "animationTick:", None, True
        )
        NSRunLoop.currentRunLoop().addTimer_forMode_(
            self.macos_timer, NSEventTrackingRunLoopMode
        )
        self.platform_window.view.animation_callback = self._macos_animate

    def _macos_animate(self) -> None:
        if sys.platform == "darwin":
            from .macos_settings import check_settings_saved
            if check_settings_saved():
                self.config.config = self.config.load()
                self._on_settings_saved()
        self._animation_loop.tick()

    def _draw_bubble(self, frame: Image.Image, text: str) -> Image.Image:
        from PIL import ImageDraw, ImageFont

        font = None
        if sys.platform == "darwin":
            for fp in (
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/Library/Fonts/Arial Unicode.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
            ):
                try:
                    font = ImageFont.truetype(fp, 14)
                    break
                except OSError:
                    continue
        if font is None:
            for fp in ("msyh.ttc", "arial.ttf"):
                try:
                    font = ImageFont.truetype(fp, 14)
                    break
                except OSError:
                    continue
        if font is None:
            font = ImageFont.load_default()

        dummy_draw = ImageDraw.Draw(frame)
        bbox = dummy_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        padding = 8
        bubble_height = text_height + padding * 2
        bubble_width = text_width + padding * 2 + 20

        new_width = max(frame.width, bubble_width)
        new_height = frame.height + bubble_height + 8
        new_frame = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))
        cat_x = (new_width - frame.width) // 2
        new_frame.paste(frame, (cat_x, bubble_height + 8))

        draw = ImageDraw.Draw(new_frame)
        bubble_x = (new_width - bubble_width) // 2
        bubble_y = 0
        draw.rounded_rectangle(
            [bubble_x, bubble_y, bubble_x + bubble_width, bubble_y + bubble_height],
            radius=8,
            fill=(30, 30, 50, 220),
            outline=(100, 100, 180, 180),
            width=1,
        )
        text_x = bubble_x + padding + 10
        text_y = bubble_y + padding
        draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)

        arrow_cx = new_width // 2
        arrow_top = bubble_y + bubble_height
        draw.polygon(
            [(arrow_cx - 6, arrow_top), (arrow_cx + 6, arrow_top), (arrow_cx, arrow_top + 8)],
            fill=(30, 30, 50, 220),
        )
        return new_frame

    def _on_click(self) -> None:
        self.state.touch()
        if self.state.state == AnimationManager.SLEEPING:
            self.state.reset_to_idle()

        now = time.time()
        self.click_times.append(now)
        self.click_times = [t for t in self.click_times if now - t < 0.8]

        if len(self.click_times) >= 3:
            if self.state.state not in (AnimationManager.RECEIVING, AnimationManager.CARRYING):
                self.state.enter_state(AnimationManager.SHY, timer=60)
                self.click_times.clear()

    def _on_mouse_enter(self) -> None:
        self.state.touch()
        self.state.reset_to_idle()

    def _on_mouse_exit(self) -> None:
        pass

    def _on_drag_enter(self) -> None:
        if self.state.state not in (AnimationManager.RECEIVING, AnimationManager.CARRYING):
            self.state.enter_state(AnimationManager.SURPRISED, timer=30)

    def _on_drag_exit(self) -> None:
        if self.state.state == AnimationManager.SURPRISED and not self.state.processing:
            self.state.enter_state(AnimationManager.IDLE)

    def _on_drag_start(self) -> None:
        self.state.set_dragging(True)
        self.state.touch()
        if self.state.state not in (AnimationManager.RECEIVING, AnimationManager.CARRYING):
            self.state.enter_state(AnimationManager.SHY, timer=300)

    def _on_drag_end(self, x: int, y: int) -> None:
        self.state.set_dragging(False)
        self.state.touch()
        self.config.set("window_position", [x, y])
        if self.state.state == AnimationManager.SHY:
            self.state.reset_shy(40)

    def _on_files_dropped(self, files: List[str]) -> None:
        self.state.touch()
        if self._drop_handler:
            self._drop_handler.receive(files)

    def _on_right_click(self, x: int = None, y: int = None) -> None:
        if not self.platform_window:
            return
        if sys.platform == "darwin":
            self._show_macos_context_menu()
        elif self.context_menu:
            if x is not None and y is not None:
                self.context_menu.show(x, y)
            elif hasattr(self.platform_window, "root") and self.platform_window.root:
                cx = self.platform_window.root.winfo_pointerx()
                cy = self.platform_window.root.winfo_pointery()
                self.context_menu.show(cx, cy)

    def _show_macos_context_menu(self) -> None:
        menu_items = build_menu_items(self)
        self.platform_window.show_context_menu(menu_items)

    def _on_settings_saved(self) -> None:
        scale = self.config.config.scale
        if abs(scale - self.animation.scale) > 0.01:
            self.animation = AnimationManager(self.assets_dir, scale)
            w, h = self.animation.get_frame_size(self.state.state)
            self.window_width, self.window_height = w, h
            if self.platform_window:
                self.platform_window.set_size(w, h)
        self.file_handler = FileHandler(self.config.archive_dir, self.config.temp_dir)
        if self.platform_window:
            self._animation_loop = self._build_animation_loop()
        _log.info("settings reloaded")

    def _ensure_archive_dir_writable(self, archive_dir: str = None) -> bool:
        archive_dir = archive_dir or self.config.archive_dir
        if sys.platform == "darwin" and hasattr(self.platform_window, "check_directory_writable"):
            if not self.platform_window.check_directory_writable(archive_dir):
                granted = self.platform_window.request_directory_access(archive_dir)
                if not granted:
                    self.state.show_bubble("请将 Python.app 添加到完全磁盘访问权限", 120)
                    return False
                if not self.platform_window.check_directory_writable(archive_dir):
                    self.state.show_bubble("授权未生效，请重启应用后重试", 120)
                    return False
            return True
        if not os.path.exists(archive_dir):
            try:
                os.makedirs(archive_dir, exist_ok=True)
            except OSError as e:
                self.state.show_bubble(f"归档目录无法创建: {e}", 120)
                return False
        if not os.access(archive_dir, os.W_OK):
            self.state.show_bubble(f"归档目录不可写: {archive_dir}", 120)
            return False
        return True

    def _update_html(self) -> None:
        """Regenerate the HTML index in the archive directory."""

        archive_dir = self.config.archive_dir
        if not os.path.exists(archive_dir) or not os.access(archive_dir, os.W_OK):
            _log.warning("archive dir not writable, skipping html generation")
            return

        from ..index_gen import write_html_index
        records = [r.to_dict() for r in self.db.records]
        out = write_html_index(
            records=records,
            archive_dir=archive_dir,
            archive_url=archive_dir.replace("\\", "/"),
        )
        if out:
            _log.info("html index written: %s", out)
