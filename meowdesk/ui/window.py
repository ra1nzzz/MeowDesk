"""
主窗口管理器
"""

import os
import sys
import time
import random
import math
from typing import Optional, Callable, List
from datetime import datetime
from PIL import Image

from ..core import ConfigManager, FileDatabase, FileClassifier, FileHandler
from .animation import AnimationManager


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
        self.file_handler = FileHandler(
            config.get('archive_dir'),
            config.get('temp_dir')
        )

        scale = config.get('scale', 0.5)
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

        self.on_quit_callback: Optional[Callable] = None

    def create(self):
        idle_w, idle_h = self.animation.get_frame_size(AnimationManager.IDLE)

        if sys.platform == 'win32':
            from ..platform.windows import WindowsWindow
            self.platform_window = WindowsWindow(idle_w, idle_h)
        elif sys.platform == 'darwin':
            from ..platform.macos import MacOSWindow
            self.platform_window = MacOSWindow(idle_w, idle_h)
        else:
            raise NotImplementedError(f"不支持的平台: {sys.platform}")

        self.platform_window.create()

        self.window_width, self.window_height = idle_w, idle_h

        self.platform_window.on_drop(self._on_files_dropped)
        self.platform_window.on_click(self._on_click)
        self.platform_window.on_right_click(self._on_right_click)

        if hasattr(self.platform_window, 'on_mouse_enter'):
            self.platform_window.on_mouse_enter(self._on_mouse_enter)
        if hasattr(self.platform_window, 'on_mouse_exit'):
            self.platform_window.on_mouse_exit(self._on_mouse_exit)
        if hasattr(self.platform_window, 'on_drag_start'):
            self.platform_window.on_drag_start(self._on_drag_start)
        if hasattr(self.platform_window, 'on_drag_end'):
            self.platform_window.on_drag_end(self._on_drag_end)

        self._move_to_saved_position()

        self.platform_window.enable_drag_drop()

        self.platform_window.show()

        if sys.platform == 'win32':
            from .menu import ContextMenu
            if hasattr(self.platform_window, 'root'):
                self.context_menu = ContextMenu(
                    self.platform_window.root,
                    self.config,
                    on_quit_callback=self.quit
                )

        self._init_wander()

        if sys.platform == 'win32':
            if hasattr(self.platform_window, 'root') and self.platform_window.root:
                self.platform_window.root.after(200, self._animate)
        elif sys.platform == 'darwin':
            self._start_macos_animation()

    def _move_to_saved_position(self):
        saved_pos = self.config.get('window_position')
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

        frame = self.animation.get_frame(self.state, self.frame_index)
        if frame:
            if self.bubble_text and self.bubble_timer > 0:
                frame = self._draw_bubble(frame, self.bubble_text)

            self.platform_window.render(frame)

        frame_count = self.animation.get_frame_count(self.state)
        if frame_count > 0:
            self.frame_index = (self.frame_index + 1) % frame_count

        delay = self.animation.get_frame_duration(self.state, self.frame_index)
        if hasattr(self.platform_window, 'root') and self.platform_window.root:
            self.platform_window.root.after(delay, self._animate)

    def _start_macos_animation(self):
        if sys.platform != 'darwin':
            return

        from Foundation import NSTimer

        self.macos_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.08,
            self.platform_window.view,
            'animationTick:',
            None,
            True
        )

        self.platform_window.view.animation_callback = self._macos_animate

    def _macos_animate(self):
        self._update_state()

        self._wander_tick()

        frame = self.animation.get_frame(self.state, self.frame_index)
        if frame:
            if self.bubble_text and self.bubble_timer > 0:
                frame = self._draw_bubble(frame, self.bubble_text)

            self.platform_window.render(frame)

        frame_count = self.animation.get_frame_count(self.state)
        if frame_count > 0:
            self.frame_index = (self.frame_index + 1) % frame_count

    def _draw_bubble(self, frame: Image.Image, text: str) -> Image.Image:
        from PIL import ImageDraw, ImageFont

        frame = frame.copy()
        draw = ImageDraw.Draw(frame)

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
                    font = ImageFont.truetype(fp, 12)
                    break
                except Exception:
                    continue
        if font is None:
            try:
                font = ImageFont.truetype("msyh.ttc", 12)
            except Exception:
                try:
                    font = ImageFont.truetype("arial.ttf", 12)
                except Exception:
                    font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (frame.width - text_width) // 2
        y = frame.height - text_height - 10

        padding = 5
        draw.rectangle(
            [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
            fill=(0, 0, 0, 180)
        )

        draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

        return frame

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

    def _touch(self):
        self.last_interaction = time.time()
        self.wander_target = None

    def _on_click(self):
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

    def _on_mouse_enter(self):
        self._touch()

        if self.state == AnimationManager.SLEEPING:
            self.state = AnimationManager.IDLE
            self.frame_index = 0

    def _on_mouse_exit(self):
        pass

    def _on_drag_start(self):
        self.dragging = True
        self._touch()

        if self.state not in (AnimationManager.RECEIVING, AnimationManager.CARRYING):
            self.state = AnimationManager.SHY
            self.shy_timer = 40
            self.frame_index = 0

    def _on_drag_end(self):
        self.dragging = False
        self._touch()

        if self.state == AnimationManager.SHY and self.shy_timer == 0:
            self.shy_timer = 40

    def _on_right_click(self):
        if not self.platform_window:
            return

        if sys.platform == 'darwin':
            self._show_macos_context_menu()
        elif hasattr(self.platform_window, 'root') and self.platform_window.root:
            if self.context_menu:
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
            ("🎉 假期提醒", self._check_holidays),
            ("💻 系统信息", self._system_info),
            None,
            ("⚙️ 设置", self._open_settings),
            ("ℹ️ 关于", self._show_about),
            None,
            ("❌ 退出", self.quit),
        ]

        self.platform_window.show_context_menu(menu_items)

    def _open_html(self):
        archive_dir = self.config.get('archive_dir')
        html_file = os.path.join(archive_dir, 'index.html')

        if os.path.exists(html_file):
            import webbrowser
            webbrowser.open(f'file://{html_file}')
        else:
            print(f"HTML 文件不存在: {html_file}")

    def _open_archive_dir(self):
        archive_dir = self.config.get('archive_dir')

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
        config_file = os.path.join(
            os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd(),
            'config.json'
        )

        if os.path.exists(config_file):
            import subprocess
            if sys.platform == 'darwin':
                subprocess.Popen(['open', '-t', config_file])
            elif sys.platform == 'win32':
                os.startfile(config_file)

    def _show_about(self):
        from .. import __version__
        self._show_bubble(f"妙喵桌宠 v{__version__}", 80)

    def _on_files_dropped(self, files: List[str]):
        self._touch()
        print(f"收到 {len(files)} 个文件")

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
            self._process_files(all_files, folders_to_remove, big_batch=True)
        else:
            self.state = AnimationManager.SURPRISED
            self.surprised_timer = 10
            self.frame_index = 0
            self._show_bubble(f"收到 {count} 个文件", 40)
            self._process_files(all_files, folders_to_remove)

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

        for filepath in files:
            try:
                result = self._process_single_file(filepath)
                if result == 'recycle':
                    recycled += 1
                elif result == 'duplicate':
                    duplicated += 1
                else:
                    archived += 1
            except Exception as e:
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
            import importlib.util

            app_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
            gen_html_path = os.path.join(app_dir, '_gen_html.py')

            if os.path.exists(gen_html_path):
                spec = importlib.util.spec_from_file_location("_gen_html", gen_html_path)
                gen_html = importlib.util.module_from_spec(spec)

                archive_dir = self.config.get('archive_dir')
                db_file = self.db.db_path

                gen_html.DB_FILE = db_file
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
