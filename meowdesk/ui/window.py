"""
主窗口管理器
"""

import os
import sys
import time
import random
import math
from typing import Optional, Callable, List, Dict
from datetime import datetime
from PIL import Image

from ..core import (
    ConfigManager, FileDatabase, FileClassifier, FileHandler,
    ProcessResult, ClassifyResult, FileAction
)
from ..agent import AgentGateway
from .animation import AnimationManager
from .menu import ContextMenu


class MeowWindow:

    WANDER_SPEED = 1.0
    WANDER_IDLE_DELAY = 5.0
    SLEEP_DELAY = 60.0
    FRAME_DELAY = 80

    def __init__(self, config: ConfigManager, db: FileDatabase, assets_dir: str):
        self.config = config
        self.db = db
        self.assets_dir = assets_dir

        self.classifier = FileClassifier(config.config)
        self.file_handler = FileHandler(config.archive_dir, config.temp_dir)

        scale = config.config.scale
        self.animation = AnimationManager(assets_dir, scale)

        self.state = AnimationManager.IDLE
        self.frame_index = 0
        self.processing = False
        self.dragging = False

        self.happy_timer = 0
        self.surprised_timer = 0
        self.shy_timer = 0
        self.last_interaction = time.time()

        self.bubble_text = ""
        self.bubble_timer = 0

        self.wander_target = None
        self.wander_pause_until = 0
        self.wander_bounds = {}

        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_start_win_x = 0
        self.drag_start_win_y = 0

        self.click_times = []

        self.window_width = 0
        self.window_height = 0

        self.platform_window = None

        self.context_menu = None
        self._menu_handlers = []

        # 提醒相关
        self.last_reminder_check = ""
        self.reminder_check_interval = 30
        self.last_reminder_check_time = 0

        # 回调
        self.on_quit_callback: Optional[Callable] = None

    def create(self):
        """创建窗口"""
        # 先初始化动画管理器获取尺寸
        self.window_width, self.window_height = self.animation.get_frame_size(AnimationManager.IDLE)

        # 导入平台窗口
        if sys.platform == 'win32':
            from ..platform.windows import WindowsWindow
            self.platform_window = WindowsWindow(self.window_width, self.window_height)
        elif sys.platform == 'darwin':
            from ..platform.macos import MacOSWindow
            self.platform_window = MacOSWindow(self.window_width, self.window_height)
        else:
            raise NotImplementedError(f"不支持的平台: {sys.platform}")

        self.platform_window.create()

        # 设置回调
        self.platform_window.on_drop(self._on_files_dropped)
        self.platform_window.on_click(self._on_click)
        self.platform_window.on_right_click(self._on_right_click)
        self.platform_window.on_drag_start(self._on_drag_start)
        self.platform_window.on_drag_end(self._on_drag_end)

        if hasattr(self.platform_window, 'on_mouse_enter'):
            self.platform_window.on_mouse_enter(self._on_mouse_enter)
        if hasattr(self.platform_window, 'on_mouse_exit'):
            self.platform_window.on_mouse_exit(self._on_mouse_exit)
        if hasattr(self.platform_window, 'on_drag_enter'):
            self.platform_window.on_drag_enter(self._on_drag_enter)
        if hasattr(self.platform_window, 'on_drag_exit'):
            self.platform_window.on_drag_exit(self._on_drag_exit)

        # 移动到保存的位置
        self._move_to_saved_position()

        self.platform_window.enable_drag_drop()

        self.platform_window.show()

        # 创建右键菜单
        if hasattr(self.platform_window, 'root'):
            # 创建 Agent Gateway
            from ..agent import AgentGateway
            self.agent_gateway = AgentGateway(self.config.agent_config)
            
            self.context_menu = ContextMenu(
                self.platform_window.root,
                self.config,
                agent_gateway=self.agent_gateway,
                on_quit_callback=self.quit,
                on_settings_saved=self._on_settings_saved
            )

        # 初始化闲逛
        self._init_wander()

        # 开始动画循环（延迟启动）
        if sys.platform == 'win32':
            if hasattr(self.platform_window, 'root') and self.platform_window.root:
                self.platform_window.root.after(200, self._animate)
        elif sys.platform == 'darwin':
            self._start_macos_animation()

    def _move_to_saved_position(self):
        saved_pos = self.config.config.window_position
        if saved_pos and len(saved_pos) == 2:
            x, y = saved_pos
        else:
            if self.platform_window and hasattr(self.platform_window, 'get_screen_size'):
                screen_width, _ = self.platform_window.get_screen_size()
                x = screen_width - self.window_width - 100
                y = 60
            else:
                x = 1400
                y = 100

        self.platform_window.set_position(x, y)

    def _init_wander(self):
        if self.platform_window and hasattr(self.platform_window, 'get_screen_size'):
            screen_width, screen_height = self.platform_window.get_screen_size()
        else:
            screen_width = 1920
            screen_height = 1080

        self.wander_bounds = {
            'x_min': screen_width - 300,
            'x_max': screen_width - self.window_width - 10,
            'y_min': 10,
            'y_max': screen_height - self.window_height - 60,
        }

    def _animate(self):
        if not self.platform_window:
            return

        if not hasattr(self.platform_window, 'root') or not self.platform_window.root:
            return

        self._update_state()

        self._wander_tick()

        # 检查提醒
        self._check_reminders()

        # 获取当前帧
        frame = self.animation.get_frame(self.state, self.frame_index)
        if frame:
            if self.bubble_text and self.bubble_timer > 0:
                frame = self._draw_bubble(frame, self.bubble_text)

            # 检查帧尺寸是否变化，动态调整窗口大小
            fw, fh = frame.size
            if fw != self.window_width or fh != self.window_height:
                old_h = self.window_height
                self.window_width = fw
                self.window_height = fh
                self.platform_window.set_size(fw, fh)
                # 补偿 y 使猫咪保持在同一位置（气泡向上扩展）
                dy = fh - old_h
                if dy != 0:
                    x, y = self.platform_window.get_position()
                    self.platform_window.set_position(x, y - dy)

            self.platform_window.render(frame)

        frame_count = self.animation.get_frame_count(self.state)
        if frame_count > 0:
            self.frame_index = (self.frame_index + 1) % frame_count

        delay = self.animation.get_frame_duration(self.state, self.frame_index)
        if hasattr(self.platform_window, 'root') and self.platform_window.root:
            self.platform_window.root.after(int(delay), self._animate)

    def _start_macos_animation(self):
        if sys.platform != 'darwin':
            return

        from Foundation import NSTimer, NSRunLoop
        from AppKit import NSEventTrackingRunLoopMode

        if hasattr(self, 'macos_timer') and self.macos_timer:
            self.macos_timer.invalidate()
            self.macos_timer = None

        self.macos_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.08,
            self.platform_window.view,
            'animationTick:',
            None,
            True
        )
        NSRunLoop.currentRunLoop().addTimer_forMode_(
            self.macos_timer, NSEventTrackingRunLoopMode
        )

        self.platform_window.view.animation_callback = self._macos_animate

    def _macos_animate(self):
        if sys.platform == 'darwin':
            from .macos_settings import check_settings_saved
            if check_settings_saved():
                self.config.config = self.config.load()
                self._on_settings_saved()

        self._update_state()

        self._wander_tick()

        self._check_reminders()

        frame = self.animation.get_frame(self.state, self.frame_index)
        if frame:
            if self.bubble_text and self.bubble_timer > 0:
                frame = self._draw_bubble(frame, self.bubble_text)

            fw, fh = frame.size
            if fw != self.window_width or fh != self.window_height:
                self.window_width = fw
                self.window_height = fh
                if self.platform_window:
                    self.platform_window.set_size(fw, fh)

            self.platform_window.render(frame)

        frame_count = self.animation.get_frame_count(self.state)
        if frame_count > 0:
            self.frame_index = (self.frame_index + 1) % frame_count

    def _draw_bubble(self, frame: Image.Image, text: str) -> Image.Image:
        from PIL import ImageDraw, ImageFont

        font = None
        if sys.platform == 'darwin':
            font_paths = [
                '/System/Library/Fonts/PingFang.ttc',
                '/System/Library/Fonts/STHeiti Light.ttc',
                '/Library/Fonts/Arial Unicode.ttf',
                '/System/Library/Fonts/Helvetica.ttc',
            ]
            for fp in font_paths:
                try:
                    font = ImageFont.truetype(fp, 14)
                    break
                except Exception:
                    continue
        if font is None:
            try:
                font = ImageFont.truetype("msyh.ttc", 14)
            except Exception:
                try:
                    font = ImageFont.truetype("arial.ttf", 14)
                except Exception:
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

        new_frame = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))

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
            width=1
        )

        text_x = bubble_x + padding + 10
        text_y = bubble_y + padding
        draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)

        arrow_cx = new_width // 2
        arrow_top = bubble_y + bubble_height
        draw.polygon(
            [(arrow_cx - 6, arrow_top), (arrow_cx + 6, arrow_top), (arrow_cx, arrow_top + 8)],
            fill=(30, 30, 50, 220)
        )

        return new_frame

    def _update_state(self):
        now = time.time()

        if self.happy_timer > 0:
            self.happy_timer -= 1
            if self.happy_timer == 0 and self.state == AnimationManager.HAPPY:
                self.state = AnimationManager.IDLE
                self.frame_index = 0

        if self.surprised_timer > 0:
            self.surprised_timer -= 1
            if self.surprised_timer == 0 and self.state == AnimationManager.SURPRISED:
                self.state = AnimationManager.IDLE
                self.frame_index = 0

        if self.shy_timer > 0:
            self.shy_timer -= 1
            if self.shy_timer == 0 and self.state == AnimationManager.SHY:
                if not self.dragging:
                    self.state = AnimationManager.IDLE
                    self.frame_index = 0

        if (not self.processing and
            self.state == AnimationManager.IDLE and
            now - self.last_interaction > self.SLEEP_DELAY):
            self.state = AnimationManager.SLEEPING
            self.frame_index = 0

        if self.bubble_timer > 0:
            self.bubble_timer -= 1
            if self.bubble_timer == 0:
                self.bubble_text = ""

    def _wander_tick(self):
        if not self.wander_bounds:
            return

        if self.dragging or self.processing or self.state == AnimationManager.SLEEPING:
            return

        now = time.time()
        if now - self.last_interaction < self.WANDER_IDLE_DELAY:
            return

        if now < self.wander_pause_until:
            return

        if self.wander_target is None:
            self._pick_wander_target()
            return

        tx, ty = self.wander_target
        cx, cy = self.platform_window.get_position()
        dx, dy = tx - cx, ty - cy
        dist = math.hypot(dx, dy)

        if dist < 3:
            self.wander_target = None
            self.wander_pause_until = now + random.uniform(2, 6)
            return

        new_x = int(cx + dx / dist * self.WANDER_SPEED)
        new_y = int(cy + dy / dist * self.WANDER_SPEED)
        self.platform_window.set_position(new_x, new_y)

    def _pick_wander_target(self):
        b = self.wander_bounds
        self.wander_target = (
            random.randint(b['x_min'], b['x_max']),
            random.randint(b['y_min'], b['y_max'])
        )
        self.wander_pause_until = time.time() + random.uniform(3, 8)

    def _check_reminders(self):
        """检查定时提醒"""
        now = time.time()

        # 控制检查频率
        if now - self.last_reminder_check_time < self.reminder_check_interval:
            return
        self.last_reminder_check_time = now

        # 获取当前时间
        current_time = datetime.now().strftime('%H:%M')

        # 避免同一分钟内重复提醒
        if current_time == self.last_reminder_check:
            return

        # 检查普通提醒
        reminders = self.config.reminders
        for reminder in reminders:
            if not reminder.enabled:
                continue

            if reminder.time == current_time:
                if self._should_trigger_reminder(reminder):
                    content = reminder.content or reminder.name or '提醒'
                    self._show_bubble(content, 120)
                    print(f"[提醒] {reminder.name}: {content}")

        # 检查经期提醒
        self._check_period_reminder()

        self.last_reminder_check = current_time

    def _check_period_reminder(self):
        """检查经期提醒"""
        period = self.config.config.period
        if not period.enabled:
            return

        prediction = period.get_predicted_dates()
        if not prediction:
            return

        days_until = prediction['days_until']
        predicted_start = prediction['predicted_start']
        predicted_end = prediction['predicted_end']

        # 提前2天、1天、0天提醒
        if days_until == 2:
            mode_text = "您的" if period.mode == "self" else "伴侣的"
            self._show_bubble(f"{mode_text}预计经期将在后天到来 ({predicted_start}~{predicted_end})", 180)
        elif days_until == 1:
            mode_text = "您的" if period.mode == "self" else "伴侣的"
            self._show_bubble(f"{mode_text}预计经期明天到来 ({predicted_start}~{predicted_end})", 180)
        elif days_until == 0:
            mode_text = "您的" if period.mode == "self" else "伴侣的"
            self._show_bubble(f"提醒: {mode_text}预计经期今天开始 ({predicted_start}~{predicted_end})", 180)

    def _should_trigger_reminder(self, reminder) -> bool:
        """检查是否应该触发提醒"""
        repeat = reminder.repeat

        if repeat == '不重复':
            today = datetime.now().strftime('%Y-%m-%d')
            if reminder.last_triggered == today:
                return False
            reminder.last_triggered = today
            return True

        elif repeat == '每天':
            return True

        elif repeat == '每周':
            weekday = datetime.now().weekday()
            return True  # 简化处理

        elif repeat == '每月':
            return True  # 简化处理

        elif repeat == '每年':
            return True  # 简化处理

        return False

    def _touch(self):
        self.last_interaction = time.time()
        self.wander_target = None

    def _on_click(self):
        """点击事件（仅在没有移动时触发）"""
        self._touch()

        if self.state == AnimationManager.SLEEPING:
            self.state = AnimationManager.IDLE
            self.frame_index = 0

        now = time.time()
        self.click_times.append(now)
        self.click_times = [t for t in self.click_times if now - t < 0.8]

        if len(self.click_times) >= 3:
            if self.state not in (AnimationManager.RECEIVING, AnimationManager.CARRYING):
                self.state = AnimationManager.SHY
                self.shy_timer = 60
                self.frame_index = 0
                self.click_times.clear()

        # TODO: 双击打开 AI 对话

    def _on_mouse_enter(self):
        self._touch()

        if self.state == AnimationManager.SLEEPING:
            self.state = AnimationManager.IDLE
            self.frame_index = 0

    def _on_mouse_exit(self):
        pass

    def _on_drag_enter(self):
        if self.state not in (AnimationManager.RECEIVING, AnimationManager.CARRYING):
            self.state = AnimationManager.SURPRISED
            self.surprised_timer = 30
            self.frame_index = 0

    def _on_drag_exit(self):
        if self.state == AnimationManager.SURPRISED and not self.processing:
            self.state = AnimationManager.IDLE
            self.frame_index = 0

    def _on_drag_start(self):
        """拖动开始事件"""
        self.dragging = True
        self._touch()

        if self.state not in (AnimationManager.RECEIVING, AnimationManager.CARRYING):
            self.state = AnimationManager.SHY
            self.shy_timer = 300
            self.frame_index = 0

    def _on_drag_end(self, x: int, y: int):
        """拖动结束事件"""
        self.dragging = False
        self._touch()

        self.config.set('window_position', [x, y])

        if self.state == AnimationManager.SHY:
            self.shy_timer = 40

    def _on_right_click(self, x: int = None, y: int = None):
        """右键菜单"""
        if not self.platform_window:
            return

        if sys.platform == 'darwin':
            self._show_macos_context_menu()
        elif self.context_menu:
            if x is not None and y is not None:
                self.context_menu.show(x, y)
            elif hasattr(self.platform_window, 'root') and self.platform_window.root:
                x = self.platform_window.root.winfo_pointerx()
                y = self.platform_window.root.winfo_pointery()
                self.context_menu.show(x, y)

    def _show_macos_context_menu(self):
        menu_items = [
            ("📄 打开导航页", self._open_html),
            ("📁 打开归档目录", self._open_archive_dir),
            None,
            ("🧹 清理磁盘", self._clean_disk),
            ("📅 查看日期", self._check_date),
            ("🔔 定期提醒", self._check_reminders_now),
            ("💻 系统信息", self._system_info),
            None,
            ("⚙️ 设置", self._open_settings),
            ("ℹ️ 关于", self._show_about),
            None,
            ("❌ 退出", self.quit),
        ]

        self.platform_window.show_context_menu(menu_items)

    def _open_html(self):
        archive_dir = self.config.archive_dir

        if not self._ensure_archive_dir_writable(archive_dir):
            return

        html_file = os.path.join(archive_dir, 'index.html')

        if not os.path.exists(html_file):
            self._update_html()

        if os.path.exists(html_file):
            import webbrowser
            webbrowser.open(f'file://{html_file}')
        else:
            self._show_bubble("导航页生成失败", 60)

    def _open_archive_dir(self):
        archive_dir = self.config.archive_dir

        if os.path.exists(archive_dir):
            import subprocess
            if sys.platform == 'darwin':
                subprocess.Popen(['open', archive_dir])
            elif sys.platform == 'win32':
                os.startfile(archive_dir)
            else:
                subprocess.Popen(['xdg-open', archive_dir])
        else:
            print(f"归档目录不存在: {archive_dir}")

    def _clean_disk(self):
        from ..agent import CommandRegistry
        registry = CommandRegistry()
        result = registry.execute('clean_disk')
        if result['success']:
            data = result['result']
            self._show_bubble(f"清理: {data['cleaned_files']} 文件, {data['cleaned_size_mb']} MB", 80)
        else:
            self._show_bubble("清理失败", 40)

    def _check_date(self):
        from ..agent import CommandRegistry
        registry = CommandRegistry()
        result = registry.execute('check_date')
        if result['success']:
            data = result['result']
            msg = f"{data['weekday']} 距周末{data['days_to_weekend']}天"
            self._show_bubble(msg, 80)

    def _check_holidays(self):
        from ..agent import CommandRegistry
        registry = CommandRegistry()
        result = registry.execute('check_holidays')
        if result['success']:
            holidays = result['result']['upcoming_holidays']
            if holidays:
                h = holidays[0]
                self._show_bubble(f"{h['name']}: 还有{h['days_left']}天", 80)

    def _system_info(self):
        from ..agent import CommandRegistry
        registry = CommandRegistry()
        result = registry.execute('system_info')
        if result['success']:
            data = result['result']
            msg = f"CPU {data['cpu_count']}核 {data['cpu_percent']}% | 内存 {data['memory_percent']}%"
            self._show_bubble(msg, 80)

    def _open_settings(self):
        if sys.platform == 'darwin':
            self._open_macos_settings()
        else:
            config_file = os.path.join(
                os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd(),
                'config.json'
            )

            if os.path.exists(config_file):
                import subprocess
                if sys.platform == 'win32':
                    os.startfile(config_file)

    def _open_macos_settings(self):
        try:
            from .macos_settings import open_settings
            open_settings(self.config.config_path)
        except Exception as e:
            print(f"打开设置面板失败: {e}")
            import traceback
            traceback.print_exc()

    def _check_reminders_now(self):
        reminders = self.config.reminders
        if not reminders:
            self._show_bubble("暂无提醒，在设置中添加", 80)
            return
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        next_reminder = None
        for r in reminders:
            if r.get('enabled', True) and r.get('time', '') >= current_time:
                next_reminder = r
                break
        if next_reminder:
            name = next_reminder.get('name', '提醒')
            t = next_reminder.get('time', '')
            self._show_bubble(f"下一提醒: {name} ({t})", 80)
        else:
            self._show_bubble(f"今日 {len(reminders)} 个提醒已完成", 80)

    def _show_about(self):
        from .. import __version__
        self._show_bubble(f"妙喵桌宠 v{__version__}", 80)

    def _on_files_dropped(self, files: List[str]):
        self._touch()
        print(f"收到 {len(files)} 个文件")

        archive_dir = self.config.archive_dir
        if not self._ensure_archive_dir_writable(archive_dir):
            return

        all_files = []
        folders_to_remove = []

        for item in files:
            if os.path.isfile(item):
                all_files.append(item)
            elif os.path.isdir(item):
                folders_to_remove.append(item)
                for root, dirs, filenames in os.walk(item):
                    for filename in filenames:
                        filepath = os.path.join(root, filename)
                        if os.path.isfile(filepath):
                            all_files.append(filepath)

        if not all_files:
            return

        count = len(all_files)

        if count >= 10:
            self.state = AnimationManager.SURPRISED
            self.surprised_timer = 10
            self.frame_index = 0
            self._show_bubble(f"收到 {count} 个文件，正在处理...", 120)
        else:
            self.state = AnimationManager.SURPRISED
            self.surprised_timer = 10
            self.frame_index = 0
            self._show_bubble(f"收到 {count} 个文件", 40)

        import threading
        t = threading.Thread(target=self._process_files_async, args=(all_files, folders_to_remove, count >= 10), daemon=True)
        t.start()

    def _ensure_archive_dir_writable(self, archive_dir: str) -> bool:
        if sys.platform == 'darwin' and hasattr(self.platform_window, 'check_directory_writable'):
            if not self.platform_window.check_directory_writable(archive_dir):
                granted = self.platform_window.request_directory_access(archive_dir)
                if not granted:
                    self._show_bubble("请将 Python.app 添加到完全磁盘访问权限", 120)
                    return False
                if not self.platform_window.check_directory_writable(archive_dir):
                    self._show_bubble("授权未生效，请重启应用后重试", 120)
                    return False
        else:
            if not os.path.exists(archive_dir):
                try:
                    os.makedirs(archive_dir, exist_ok=True)
                except OSError as e:
                    self._show_bubble(f"归档目录无法创建: {e}", 120)
                    return False
            if not os.access(archive_dir, os.W_OK):
                self._show_bubble(f"归档目录不可写: {archive_dir}", 120)
                return False
        return True

    def _process_files(self, files: List[str], folders_to_remove: List[str] = None, big_batch: bool = False):
        self.processing = True

        if big_batch:
            self.state = AnimationManager.RECEIVING
        else:
            self.state = AnimationManager.CARRYING

        self.frame_index = 0

        recycled = 0
        archived = 0
        duplicated = 0
        errors = 0

        for filepath in files:
            try:
                result = self._process_single_file(filepath)
                if result == 'recycle':
                    recycled += 1
                elif result == 'duplicate':
                    duplicated += 1
                elif result == 'error':
                    errors += 1
                else:
                    archived += 1
            except Exception as e:
                errors += 1
                print(f"处理文件失败 {os.path.basename(filepath)}: {e}")

        if folders_to_remove:
            import shutil
            for folder in folders_to_remove:
                if os.path.exists(folder):
                    try:
                        shutil.rmtree(folder)
                    except Exception as e:
                        print(f"删除文件夹失败 {folder}: {e}")

        self.processing = False

        self._update_html()

        parts = []
        if recycled:
            parts.append(f"{recycled} 截图回收")
        if archived:
            parts.append(f"{archived} 已归档")
        if duplicated:
            parts.append(f"{duplicated} 重复跳过")
        if errors:
            parts.append(f"{errors} 失败")

        message = " · ".join(parts) if parts else "完成"
        print(f"处理完成: {message}")

        if random.random() < 0.25:
            self.state = AnimationManager.SHY
            self.shy_timer = 50
        else:
            self.state = AnimationManager.HAPPY
            self.happy_timer = 80

        self.frame_index = 0
        self.click_times.clear()
        self._show_bubble(message, 80)

    def _process_files_async(self, files: List[str], folders_to_remove: List[str], big_batch: bool):
        try:
            self._process_files(files, folders_to_remove, big_batch)
        except Exception as e:
            self.processing = False
            print(f"文件处理异常: {e}")
            import traceback
            traceback.print_exc()

    def _process_single_file(self, filepath: str) -> str:
        filename = os.path.basename(filepath)
        file_size = self.file_handler.get_file_size(filepath)
        md5 = self.file_handler.calculate_md5(filepath)

        existing_records = self.db.search()
        for record in existing_records:
            if (record.get('md5') == md5 and
                record.get('action') != 'recycle'):
                dest = record.get('destination', '')
                if dest and dest != '(已回收)' and os.path.exists(dest):
                    print(f"  [跳过] {filename} (重复)")
                    try:
                        os.remove(filepath)
                    except Exception:
                        pass
                    return 'duplicate'

        category, action = self.classifier.classify(filepath)

        now = datetime.now()
        record = {
            'timestamp': now.isoformat(),
            'original_name': filename,
            'original_path': filepath,
            'category': category,
            'action': action,
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M:%S'),
            'file_size': file_size,
            'md5': md5,
        }

        if action == 'recycle':
            success, error = self.file_handler.recycle_file(filepath)
            if success:
                record['destination'] = '(已回收)'
                self.db.add_record(record)
                print(f"  [回收] {filename}")
                return 'recycle'
            else:
                print(f"  [回收失败] {filename}: {error}")
                return 'error'
        else:
            success, dest, error = self.file_handler.archive_file(filepath, category)
            if success:
                record['destination'] = dest
                self.db.add_record(record)
                print(f"  [归档] {filename} -> {category}/")
                return 'archive'
            else:
                print(f"  [归档失败] {filename}: {error}")
                return 'error'

    def _update_html(self):
        try:
            archive_dir = self.config.archive_dir
            if not os.path.exists(archive_dir) or not os.access(archive_dir, os.W_OK):
                print("⚠️ 归档目录不可写，跳过 HTML 生成")
                return

            import importlib.util

            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

            gen_html_path = os.path.join(app_dir, '_gen_html.py')

            if os.path.exists(gen_html_path):
                spec = importlib.util.spec_from_file_location("_gen_html", gen_html_path)
                gen_html = importlib.util.module_from_spec(spec)

                gen_html.DB_FILE = self.db.db_path
                gen_html.ARCHIVE_DIR = archive_dir
                gen_html.ARCHIVE_URL = archive_dir.replace("\\", "/")

                spec.loader.exec_module(gen_html)
                gen_html.main()

                print("✅ HTML 索引已更新")
            else:
                print(f"⚠️  HTML 生成脚本不存在: {gen_html_path}")

        except Exception as e:
            print(f"❌ HTML 生成失败: {e}")
            import traceback
            traceback.print_exc()

    def _on_settings_saved(self):
        """设置保存后的回调"""
        # 重新加载动画（如果 scale 变化）
        scale = self.config.config.scale
        if abs(scale - self.animation.scale) > 0.01:
            self.animation = AnimationManager(self.assets_dir, scale)
            # 更新窗口尺寸
            w, h = self.animation.get_frame_size(self.state)
            self.window_width = w
            self.window_height = h
            if self.platform_window:
                self.platform_window.set_size(w, h)

        # 更新文件处理器
        self.file_handler = FileHandler(
            self.config.archive_dir,
            self.config.temp_dir
        )

        print("设置已更新")

    def _show_bubble(self, text: str, duration: int):
        self.bubble_text = text
        self.bubble_timer = duration

    def run(self):
        if self.platform_window:
            self.platform_window.run()

    def quit(self):
        if self.platform_window:
            x, y = self.platform_window.get_position()
            self.config.set('window_position', [x, y])

        if self.on_quit_callback:
            self.on_quit_callback()

        if self.platform_window:
            self.platform_window.quit()
