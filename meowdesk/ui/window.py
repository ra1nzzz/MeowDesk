"""
主窗口管理器
"""

import os
import sys
import time
import random
import math
import tkinter as tk
from typing import Optional, Callable, List, Dict
from datetime import datetime
from PIL import Image

from ..core import ConfigManager, FileDatabase, FileClassifier, FileHandler
from .animation import AnimationManager
from .menu import ContextMenu


class MeowWindow:
    """妙喵桌宠主窗口"""
    
    # 常量
    WANDER_SPEED = 1.0
    WANDER_IDLE_DELAY = 5.0
    SLEEP_DELAY = 60.0
    FRAME_DELAY = 80
    
    def __init__(self, config: ConfigManager, db: FileDatabase, assets_dir: str):
        self.config = config
        self.db = db
        self.assets_dir = assets_dir
        
        # 初始化核心模块
        self.classifier = FileClassifier(config.config)
        self.file_handler = FileHandler(
            config.get('archive_dir'),
            config.get('temp_dir')
        )
        
        # 动画管理器
        scale = config.get('scale', 0.5)
        self.animation = AnimationManager(assets_dir, scale)
        
        # 状态
        self.state = AnimationManager.IDLE
        self.frame_index = 0
        self.processing = False
        self.dragging = False
        
        # 定时器
        self.happy_timer = 0
        self.surprised_timer = 0
        self.shy_timer = 0
        self.last_interaction = time.time()
        
        # 气泡
        self.bubble_text = ""
        self.bubble_timer = 0
        
        # 闲逛
        self.wander_target = None
        self.wander_pause_until = 0
        self.wander_bounds = {}
        
        # 拖动
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_start_win_x = 0
        self.drag_start_win_y = 0
        
        # 点击检测
        self.click_times = []
        
        # 窗口尺寸
        self.window_width = 0
        self.window_height = 0
        
        # 平台窗口（延迟初始化）
        self.platform_window = None
        
        # 右键菜单
        self.context_menu = None
        
        # 提醒相关
        self.last_reminder_check = ""  # 上次检查的分钟，避免重复提醒
        self.reminder_check_interval = 30  # 检查间隔（秒）
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
        
        # 创建窗口
        self.platform_window.create()
        
        # 设置回调
        self.platform_window.on_drop(self._on_files_dropped)
        self.platform_window.on_click(self._on_click)
        self.platform_window.on_right_click(self._on_right_click)
        self.platform_window.on_drag_start(self._on_drag_start)
        self.platform_window.on_drag_end(self._on_drag_end)
        
        # 移动到保存的位置
        self._move_to_saved_position()
        
        # 启用拖放
        self.platform_window.enable_drag_drop()
        
        # 显示窗口
        self.platform_window.show()
        
        # 创建右键菜单
        if hasattr(self.platform_window, 'root'):
            self.context_menu = ContextMenu(
                self.platform_window.root,
                self.config,
                on_quit_callback=self.quit,
                on_settings_saved=self._on_settings_saved
            )
        
        # 初始化闲逛
        self._init_wander()
        
        # 开始动画循环（延迟启动）
        if sys.platform == 'win32':
            # Windows: 使用 Tkinter after
            if hasattr(self.platform_window, 'root') and self.platform_window.root:
                self.platform_window.root.after(200, self._animate)
        elif sys.platform == 'darwin':
            # macOS: 使用 NSTimer
            self._start_macos_animation()
    
    def _move_to_saved_position(self):
        """移动到保存的位置"""
        saved_pos = self.config.get('window_position')
        if saved_pos and len(saved_pos) == 2:
            x, y = saved_pos
        else:
            # 默认位置：右上角
            if sys.platform == 'win32':
                if self.platform_window and hasattr(self.platform_window, 'root'):
                    screen_width = self.platform_window.root.winfo_screenwidth()
                    x = screen_width - self.window_width - 100
                    y = 60
                else:
                    x = 1400
                    y = 100
            elif sys.platform == 'darwin':
                if self.platform_window and hasattr(self.platform_window, 'get_screen_size'):
                    screen_width, _ = self.platform_window.get_screen_size()
                    x = screen_width - self.window_width - 100
                    y = 60
                else:
                    x = 1400
                    y = 100
            else:
                x = 1400
                y = 100
        
        self.platform_window.set_position(x, y)
    
    def _init_wander(self):
        """初始化闲逛范围"""
        # 获取屏幕尺寸
        if sys.platform == 'win32':
            if self.platform_window and hasattr(self.platform_window, 'root'):
                screen_width = self.platform_window.root.winfo_screenwidth()
                screen_height = self.platform_window.root.winfo_screenheight()
            else:
                screen_width = 1920
                screen_height = 1080
        elif sys.platform == 'darwin':
            if self.platform_window and hasattr(self.platform_window, 'get_screen_size'):
                screen_width, screen_height = self.platform_window.get_screen_size()
            else:
                screen_width = 1920
                screen_height = 1080
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
        """动画循环（仅 Windows）"""
        if not self.platform_window:
            return
        
        # 检查是否是 Windows 平台
        if not hasattr(self.platform_window, 'root') or not self.platform_window.root:
            return
        
        # 更新状态
        self._update_state()
        
        # 闲逛
        self._wander_tick()
        
        # 检查提醒
        self._check_reminders()
        
        # 获取当前帧
        frame = self.animation.get_frame(self.state, self.frame_index)
        if frame:
            # 如果有气泡文字，绘制到帧上
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
        
        # 下一帧
        frame_count = self.animation.get_frame_count(self.state)
        if frame_count > 0:
            self.frame_index = (self.frame_index + 1) % frame_count
        
        # 继续动画
        delay = self.animation.get_frame_duration(self.state, self.frame_index)
        if hasattr(self.platform_window, 'root') and self.platform_window.root:
            self.platform_window.root.after(int(delay), self._animate)
    
    def _start_macos_animation(self):
        """启动 macOS 动画循环"""
        if sys.platform != 'darwin':
            return
        
        from Foundation import NSTimer, NSRunLoop, NSDefaultRunLoopMode
        
        # 创建定时器
        def animation_tick(timer):
            self._macos_animate()
        
        # 使用 80ms 间隔（约 12.5 FPS）
        self.macos_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.08,  # 80ms
            self.platform_window.view,
            'animationTick:',
            None,
            True
        )
        
        # 将动画方法绑定到视图
        self.platform_window.view.animation_callback = self._macos_animate
    
    def _macos_animate(self):
        """macOS 动画循环"""
        # 更新状态
        self._update_state()
        
        # 闲逛
        self._wander_tick()
        
        # 获取当前帧
        frame = self.animation.get_frame(self.state, self.frame_index)
        if frame:
            # 如果有气泡文字，绘制到帧上
            if self.bubble_text and self.bubble_timer > 0:
                frame = self._draw_bubble(frame, self.bubble_text)
            
            self.platform_window.render(frame)
        
        # 下一帧
        frame_count = self.animation.get_frame_count(self.state)
        if frame_count > 0:
            self.frame_index = (self.frame_index + 1) % frame_count
    
    def _draw_bubble(self, frame: Image.Image, text: str) -> Image.Image:
        """在帧上绘制气泡文字"""
        from PIL import ImageDraw, ImageFont
        
        # 复制帧以避免修改原始缓存
        frame = frame.copy()
        draw = ImageDraw.Draw(frame)
        
        # 尝试加载字体
        try:
            # Windows 系统字体
            font = ImageFont.truetype("msyh.ttc", 12)  # 微软雅黑
        except:
            try:
                font = ImageFont.truetype("arial.ttf", 12)
            except:
                font = ImageFont.load_default()
        
        # 计算文字位置（底部居中）
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (frame.width - text_width) // 2
        y = frame.height - text_height - 10
        
        # 绘制半透明背景
        padding = 5
        draw.rectangle(
            [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
            fill=(0, 0, 0, 180)
        )
        
        # 绘制文字
        draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
        
        return frame
    
    def _update_state(self):
        """更新状态"""
        now = time.time()
        
        # 定时器递减
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
        
        # 睡眠检测
        if (not self.processing and 
            self.state == AnimationManager.IDLE and 
            now - self.last_interaction > self.SLEEP_DELAY):
            self.state = AnimationManager.SLEEPING
            self.frame_index = 0
        
        # 气泡定时器
        if self.bubble_timer > 0:
            self.bubble_timer -= 1
            if self.bubble_timer == 0:
                self.bubble_text = ""
    
    def _wander_tick(self):
        """闲逛逻辑"""
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
        
        # 移动向目标
        tx, ty = self.wander_target
        cx, cy = self.platform_window.get_position()
        dx, dy = tx - cx, ty - cy
        dist = math.hypot(dx, dy)
        
        if dist < 3:
            self.wander_target = None
            self.wander_pause_until = now + random.uniform(2, 6)
            return
        
        # 移动一小步
        new_x = int(cx + dx / dist * self.WANDER_SPEED)
        new_y = int(cy + dy / dist * self.WANDER_SPEED)
        self.platform_window.set_position(new_x, new_y)
    
    def _pick_wander_target(self):
        """选择闲逛目标"""
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
        
        # 获取提醒列表
        reminders = self.config.get('reminders', [])
        if not reminders:
            return
        
        # 检查是否有需要触发的提醒
        for reminder in reminders:
            if not reminder.get('enabled', True):
                continue
            
            reminder_time = reminder.get('time', '')
            if reminder_time == current_time:
                # 检查重复规则
                if self._should_trigger_reminder(reminder):
                    content = reminder.get('content', reminder.get('name', '提醒'))
                    self._show_bubble(content, 120)  # 显示 120 帧（约 10 秒）
                    print(f"[提醒] {reminder.get('name')}: {content}")
        
        self.last_reminder_check = current_time
    
    def _should_trigger_reminder(self, reminder: Dict) -> bool:
        """检查是否应该触发提醒"""
        repeat = reminder.get('repeat', '不重复')
        
        if repeat == '不重复':
            # 检查今天是否已经提醒过
            today = datetime.now().strftime('%Y-%m-%d')
            last_triggered = reminder.get('last_triggered', '')
            if last_triggered == today:
                return False
            # 记录触发时间
            reminder['last_triggered'] = today
            return True
        
        elif repeat == '每天':
            return True
        
        elif repeat == '每周':
            # 检查是否是同一天（周一=0, 周日=6）
            weekday = datetime.now().weekday()
            trigger_days = reminder.get('trigger_days', [weekday])
            return weekday in trigger_days
        
        elif repeat == '每月':
            # 检查是否是同一天
            day = datetime.now().day
            trigger_day = reminder.get('trigger_day', 1)
            return day == trigger_day
        
        elif repeat == '每年':
            # 检查是否是同一天
            now = datetime.now()
            month = reminder.get('trigger_month', now.month)
            day = reminder.get('trigger_day', now.day)
            return now.month == month and now.day == day
        
        return False
    
    def _touch(self):
        """触摸（重置交互时间）"""
        self.last_interaction = time.time()
        self.wander_target = None
    
    def _on_click(self):
        """点击事件（仅在没有移动时触发）"""
        self._touch()
        
        # 多次点击检测
        now = time.time()
        self.click_times.append(now)
        self.click_times = [t for t in self.click_times if now - t < 0.8]
        
        # 3次以上点击 -> 害羞
        if len(self.click_times) >= 3:
            if self.state not in (AnimationManager.RECEIVING, AnimationManager.CARRYING):
                self.state = AnimationManager.SHY
                self.shy_timer = 60
                self.frame_index = 0
                self.click_times.clear()
        
        # TODO: 双击打开 AI 对话
    
    def _on_drag_start(self):
        """拖动开始事件"""
        self._touch()
        self.dragging = True
        
        # 拖动时切换到 SHY 状态
        if self.state not in (AnimationManager.RECEIVING, AnimationManager.CARRYING, AnimationManager.SLEEPING):
            self.state = AnimationManager.SHY
            self.shy_timer = 300  # 长定时器，释放时清除
            self.frame_index = 0
    
    def _on_drag_end(self, x: int, y: int):
        """拖动结束事件"""
        self.dragging = False
        
        # 保存窗口位置
        self.config.set('window_position', [x, y])
        
        # 恢复到 IDLE 状态
        if self.state == AnimationManager.SHY:
            self.state = AnimationManager.IDLE
            self.frame_index = 0
    
    def _on_right_click(self, x: int = None, y: int = None):
        """右键菜单"""
        if not self.context_menu or not self.platform_window:
            return
        
        # 使用传递的位置，或获取当前鼠标位置
        if x is not None and y is not None:
            self.context_menu.show(x, y)
        elif hasattr(self.platform_window, 'root') and self.platform_window.root:
            x = self.platform_window.root.winfo_pointerx()
            y = self.platform_window.root.winfo_pointery()
            self.context_menu.show(x, y)
    
    def _on_files_dropped(self, files: List[str]):
        """文件拖放事件"""
        self._touch()
        print(f"收到 {len(files)} 个文件")
        
        # 收集所有文件
        all_files = []
        folders_to_remove = []
        
        for item in files:
            if os.path.isfile(item):
                all_files.append(item)
            elif os.path.isdir(item):
                folders_to_remove.append(item)
                # 遍历文件夹
                for root, dirs, filenames in os.walk(item):
                    for filename in filenames:
                        filepath = os.path.join(root, filename)
                        if os.path.isfile(filepath):
                            all_files.append(filepath)
        
        if not all_files:
            return
        
        count = len(all_files)
        
        # 大批量文件
        if count >= 10:
            self.state = AnimationManager.SURPRISED
            self.surprised_timer = 10
            self.frame_index = 0
            self._show_bubble(f"收到 {count} 个文件，正在处理...", 120)
            # TODO: 延迟处理
            self._process_files(all_files, folders_to_remove, big_batch=True)
        else:
            self.state = AnimationManager.SURPRISED
            self.surprised_timer = 10
            self.frame_index = 0
            self._show_bubble(f"收到 {count} 个文件", 40)
            # TODO: 延迟处理
            self._process_files(all_files, folders_to_remove)
    
    def _process_files(self, files: List[str], folders_to_remove: List[str] = None, big_batch: bool = False):
        """处理文件"""
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
        
        # 删除文件夹
        if folders_to_remove:
            import shutil
            for folder in folders_to_remove:
                if os.path.exists(folder):
                    try:
                        shutil.rmtree(folder)
                    except Exception as e:
                        print(f"删除文件夹失败 {folder}: {e}")
        
        self.processing = False
        
        # 生成 HTML
        self._update_html()
        
        # 显示结果
        parts = []
        if recycled:
            parts.append(f"{recycled} 截图回收")
        if archived:
            parts.append(f"{archived} 已归档")
        if duplicated:
            parts.append(f"{duplicated} 重复跳过")
        
        message = " · ".join(parts) if parts else "完成"
        print(f"处理完成: {message}")
        
        # 随机表情
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
        """处理单个文件"""
        filename = os.path.basename(filepath)
        file_size = self.file_handler.get_file_size(filepath)
        md5 = self.file_handler.calculate_md5(filepath)
        
        # 检查重复
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
        
        # 分类
        category, action = self.classifier.classify(filepath)
        
        # 创建记录
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
        
        # 处理文件
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
        """更新 HTML 索引"""
        try:
            # 调用原有的 HTML 生成脚本
            import sys
            import importlib.util
            
            # 获取 _gen_html.py 路径
            app_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
            gen_html_path = os.path.join(app_dir, '_gen_html.py')
            
            if os.path.exists(gen_html_path):
                # 动态加载模块
                spec = importlib.util.spec_from_file_location("_gen_html", gen_html_path)
                gen_html = importlib.util.module_from_spec(spec)
                
                # 设置参数
                archive_dir = self.config.get('archive_dir')
                db_file = self.db.db_path
                
                gen_html.DB_FILE = db_file
                gen_html.ARCHIVE_DIR = archive_dir
                gen_html.ARCHIVE_URL = archive_dir.replace("\\", "/")
                
                # 执行生成
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
        scale = self.config.get('scale', 0.5)
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
            self.config.get('archive_dir'),
            self.config.get('temp_dir')
        )
        
        print("设置已更新")
    
    def _show_bubble(self, text: str, duration: int):
        """显示气泡提示"""
        self.bubble_text = text
        self.bubble_timer = duration
    
    def run(self):
        """运行主循环"""
        if self.platform_window:
            self.platform_window.run()
    
    def quit(self):
        """退出"""
        # 保存窗口位置
        if self.platform_window:
            x, y = self.platform_window.get_position()
            self.config.set('window_position', [x, y])
        
        # 回调
        if self.on_quit_callback:
            self.on_quit_callback()
        
        # 退出
        if self.platform_window:
            self.platform_window.quit()
