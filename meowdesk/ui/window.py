"""
主窗口管理器 — 顶层协调者

把状态机、文件 drop、提醒、菜单动作分别拆分到独立的模块，
本类只负责事件路由与平台窗口生命周期。
"""

import sys
import time
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
from .bubble_renderer import draw_bubble
from .macos_animation import MacOSAnimationTimer
from .menu_actions import build_menu_items, ensure_archive_dir_writable
from .platform_factory import create_platform_window
from .win32_animation import Win32AnimationTimer
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
        self.parent = None
        self.context_menu = None
        self._menu_handlers = []
        self.agent_gateway: Optional[AgentGateway] = None

        self.window_width = 0
        self.window_height = 0

        self.click_times: List[float] = []

        self.on_quit_callback: Optional[Callable] = None

        self._drop_handler: Optional[FileDropHandler] = None
        self._reminder_checker: Optional[ReminderChecker] = None
        self._animation_loop: Optional[AnimationLoop] = None
        self._macos_timer: Optional[MacOSAnimationTimer] = None
        self._win32_timer: Optional[Win32AnimationTimer] = None

    def create(self) -> None:
        """Create the platform window and wire up callbacks."""

        self.window_width, self.window_height = self.animation.get_frame_size(AnimationManager.IDLE)

        self.platform_window = create_platform_window(self.window_width, self.window_height)

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
            self.parent = self.platform_window.root
            self.agent_gateway = AgentGateway(self.config.agent_config)
            from .menu import ContextMenu
            self.context_menu = ContextMenu(
                self.platform_window.root,
                self.config,
                window=self,
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
            check_archive_writable=lambda: ensure_archive_dir_writable(self, self.config.archive_dir),
        )
        self._reminder_checker = ReminderChecker(
            config=self.config, show_bubble=self.state.show_bubble
        )
        self._animation_loop = self._build_animation_loop()

        if sys.platform == "win32":
            self._win32_timer = Win32AnimationTimer(self)
            self._win32_timer.start()
        elif sys.platform == "darwin":
            self._macos_timer = MacOSAnimationTimer(self)
            self._macos_timer.start()

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

    def _draw_bubble(self, frame: Image.Image, text: str) -> Image.Image:
        return draw_bubble(frame, text)

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

    def _update_html(self) -> None:
        """Regenerate the HTML index in the archive directory."""

        archive_dir = self.config.archive_dir
        if not ensure_archive_dir_writable(self, archive_dir):
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
