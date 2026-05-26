"""
内置命令注册表 - 常用工具命令
"""

import os
import sys
import shutil
import subprocess
from typing import Dict, Any, Callable, List
from datetime import datetime, timedelta
from calendar import monthrange


class CommandRegistry:
    """命令注册表"""
    
    def __init__(self):
        self.commands: Dict[str, Callable] = {}
        self._register_builtin_commands()
    
    def register(self, name: str, func: Callable):
        """注册命令"""
        self.commands[name] = func
    
    def execute(self, name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行命令"""
        if name not in self.commands:
            return {
                'success': False,
                'error': f'未知命令: {name}'
            }
        
        try:
            result = self.commands[name](params or {})
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_commands(self) -> List[str]:
        """列出所有可用命令"""
        return list(self.commands.keys())
    
    def _register_builtin_commands(self):
        """注册内置命令"""
        
        # 磁盘清理
        @self.register_command('clean_disk')
        def clean_disk(params):
            if sys.platform == 'darwin':
                temp_dirs = [
                    '/tmp',
                    os.path.expanduser('~/Library/Caches'),
                    os.path.expanduser('~/Library/Logs'),
                ]
            elif sys.platform == 'win32':
                temp_dirs = [
                    os.environ.get('TEMP'),
                    os.environ.get('TMP'),
                    os.path.expanduser('~\\AppData\\Local\\Temp')
                ]
            else:
                temp_dirs = [
                    '/tmp',
                    os.environ.get('TMPDIR'),
                ]
            
            cleaned_size = 0
            cleaned_files = 0
            
            for temp_dir in temp_dirs:
                if not temp_dir or not os.path.exists(temp_dir):
                    continue
                
                try:
                    for item in os.listdir(temp_dir):
                        item_path = os.path.join(temp_dir, item)
                        try:
                            if os.path.isfile(item_path):
                                size = os.path.getsize(item_path)
                                os.remove(item_path)
                                cleaned_size += size
                                cleaned_files += 1
                            elif os.path.isdir(item_path):
                                size = self._get_dir_size(item_path)
                                shutil.rmtree(item_path)
                                cleaned_size += size
                                cleaned_files += 1
                        except Exception:
                            continue
                except Exception:
                    continue
            
            return {
                'cleaned_files': cleaned_files,
                'cleaned_size': cleaned_size,
                'cleaned_size_mb': round(cleaned_size / 1024 / 1024, 2)
            }
        
        # 日期查询
        @self.register_command('check_date')
        def check_date(params):
            """查询日期信息"""
            now = datetime.now()
            
            # 计算距离周末
            days_to_weekend = (4 - now.weekday()) % 7  # 周五
            if days_to_weekend == 0:
                days_to_weekend = 7
            
            # 计算距离月底
            last_day = monthrange(now.year, now.month)[1]
            days_to_month_end = last_day - now.day
            
            return {
                'today': now.strftime('%Y-%m-%d'),
                'weekday': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][now.weekday()],
                'days_to_weekend': days_to_weekend,
                'days_to_month_end': days_to_month_end,
                'week_of_year': now.isocalendar()[1]
            }
        
        # 假期提醒
        @self.register_command('check_holidays')
        def check_holidays(params):
            """查询假期信息"""
            # 2026年中国法定节假日（示例）
            holidays = {
                '2026-01-01': '元旦',
                '2026-01-02': '元旦',
                '2026-01-03': '元旦',
                '2026-02-17': '春节',
                '2026-02-18': '春节',
                '2026-02-19': '春节',
                '2026-02-20': '春节',
                '2026-02-21': '春节',
                '2026-02-22': '春节',
                '2026-02-23': '春节',
                '2026-04-05': '清明节',
                '2026-05-01': '劳动节',
                '2026-05-02': '劳动节',
                '2026-05-03': '劳动节',
                '2026-06-25': '端午节',
                '2026-06-26': '端午节',
                '2026-06-27': '端午节',
                '2026-10-01': '国庆节',
                '2026-10-02': '国庆节',
                '2026-10-03': '国庆节',
                '2026-10-04': '国庆节',
                '2026-10-05': '国庆节',
                '2026-10-06': '国庆节',
                '2026-10-07': '国庆节',
                '2026-10-08': '国庆节',
            }
            
            now = datetime.now()
            upcoming = []
            
            for date_str, name in sorted(holidays.items()):
                holiday_date = datetime.strptime(date_str, '%Y-%m-%d')
                if holiday_date >= now:
                    days_left = (holiday_date - now).days
                    upcoming.append({
                        'date': date_str,
                        'name': name,
                        'days_left': days_left
                    })
                    if len(upcoming) >= 3:
                        break
            
            return {
                'upcoming_holidays': upcoming
            }
        
        # 经期提醒
        @self.register_command('period_reminder')
        def period_reminder(params):
            """女性经期提醒"""
            # 从配置读取上次日期和周期
            last_date_str = params.get('last_date')
            cycle_days = params.get('cycle_days', 28)
            
            if not last_date_str:
                return {
                    'message': '请先设置上次经期日期',
                    'need_setup': True
                }
            
            last_date = datetime.strptime(last_date_str, '%Y-%m-%d')
            now = datetime.now()
            
            days_since = (now - last_date).days
            days_until_next = cycle_days - days_since
            next_date = last_date + timedelta(days=cycle_days)
            
            status = 'normal'
            if days_until_next <= 3:
                status = 'coming_soon'
            elif days_until_next < 0:
                status = 'overdue'
            
            return {
                'last_date': last_date_str,
                'days_since': days_since,
                'days_until_next': days_until_next,
                'next_date': next_date.strftime('%Y-%m-%d'),
                'status': status
            }
        
        # 系统信息
        @self.register_command('system_info')
        def system_info(params):
            import platform

            try:
                import psutil
                has_psutil = True
            except ImportError:
                has_psutil = False

            if has_psutil:
                if sys.platform == 'darwin':
                    disk = psutil.disk_usage('/')
                else:
                    disk = psutil.disk_usage('/')
                memory = psutil.virtual_memory()

                return {
                    'os': platform.system(),
                    'os_version': platform.version(),
                    'cpu_count': psutil.cpu_count(),
                    'cpu_percent': psutil.cpu_percent(interval=0.1),
                    'memory_total_gb': round(memory.total / 1024 / 1024 / 1024, 2),
                    'memory_used_gb': round(memory.used / 1024 / 1024 / 1024, 2),
                    'memory_percent': memory.percent,
                    'disk_total_gb': round(disk.total / 1024 / 1024 / 1024, 2),
                    'disk_used_gb': round(disk.used / 1024 / 1024 / 1024, 2),
                    'disk_percent': disk.percent
                }
            else:
                memory_percent = 0
                cpu_count = os.cpu_count() or 0
                return {
                    'os': platform.system(),
                    'os_version': platform.version(),
                    'cpu_count': cpu_count,
                    'cpu_percent': 0,
                    'memory_total_gb': 0,
                    'memory_used_gb': 0,
                    'memory_percent': memory_percent,
                    'disk_total_gb': 0,
                    'disk_used_gb': 0,
                    'disk_percent': 0
                }
        
        # 打开应用
        @self.register_command('open_app')
        def open_app(params):
            app_name = params.get('app_name', '')

            if sys.platform == 'darwin':
                app_map = {
                    '记事本': ('open', ['-a', 'TextEdit']),
                    '计算器': ('open', ['-a', 'Calculator']),
                    '终端': ('open', ['-a', 'Terminal']),
                    'Finder': ('open', ['-a', 'Finder']),
                }
            else:
                app_map = {
                    '记事本': ('notepad.exe', []),
                    '计算器': ('calc.exe', []),
                    '画图': ('mspaint.exe', []),
                    '资源管理器': ('explorer.exe', []),
                }

            if app_name in app_map:
                cmd, args = app_map[app_name]
                subprocess.Popen([cmd] + args)
                return {'message': f'已打开 {app_name}'}
            else:
                return {'error': f'未知应用: {app_name}'}
    
    def register_command(self, name: str):
        """装饰器：注册命令"""
        def decorator(func: Callable):
            self.commands[name] = func
            return func
        return decorator
    
    @staticmethod
    def _get_dir_size(path: str) -> int:
        """计算目录大小"""
        total = 0
        try:
            for entry in os.scandir(path):
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += CommandRegistry._get_dir_size(entry.path)
        except Exception:
            pass
        return total
