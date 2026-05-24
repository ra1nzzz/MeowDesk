#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
妙喵桌宠 MeowDesk - 安装/卸载工具
用法:
  python install.py install   — 安装（创建快捷方式 + 设置开机自启）
  python install.py uninstall — 卸载
  python install.py status    — 查看状态
"""

import os
import sys
import shutil
import winreg
import subprocess
from pathlib import Path

APP_NAME = "妙喵桌宠 MeowDesk"

# 自动检测 PyQt5 所在的 Python 路径
import shutil as _shutil
_PYTHON_EXE = r"C:\Users\和旭电商\AppData\Roaming\WPS 灵犀\python-env\python.exe"
if not os.path.exists(_PYTHON_EXE):
    _found = _shutil.which("python")
    if _found:
        _PYTHON_EXE = _found
SCRIPT_NAME = "lingxi_droplet.py"
BAT_NAME = "启动妙喵桌宠.bat"
LINK_NAME = "妙喵桌宠 MeowDesk.lnk"
STARTUP_REG = "MeowDesk"

# 安装目录: 用户 AppData\Local
INSTALL_DIR = os.path.join(os.environ.get("LOCALAPPDATA", ""), "MeowDesk")
STARTUP_FOLDER = os.path.join(
    os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
)


def get_script_dir():
    """获取当前脚本所在目录"""
    return os.path.dirname(os.path.abspath(__file__))


def install():
    print(f"\n{'='*50}")
    print(f"  {APP_NAME} - 安装")
    print(f"{'='*50}\n")

    src_dir = get_script_dir()

    # 1. 复制文件到安装目录
    print(f"[1/4] 复制文件到 {INSTALL_DIR}")
    os.makedirs(INSTALL_DIR, exist_ok=True)
    for f in os.listdir(src_dir):
        if f.endswith((".py", ".bat", ".md")):
            src = os.path.join(src_dir, f)
            dst = os.path.join(INSTALL_DIR, f)
            shutil.copy2(src, dst)
            print(f"  + {f}")

    # 2. 创建桌面快捷方式
    print(f"\n[2/4] 创建桌面快捷方式")
    try:
        desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
        create_shortcut(
            os.path.join(INSTALL_DIR, BAT_NAME),
            os.path.join(desktop, LINK_NAME),
            APP_NAME,
            INSTALL_DIR,
        )
        print(f"  + 桌面快捷方式: {LINK_NAME}")
    except Exception as e:
        print(f"  ! 创建快捷方式失败: {e}")

    # 3. 创建开始菜单快捷方式
    print(f"\n[3/4] 创建开始菜单快捷方式")
    try:
        start_menu = os.path.join(
            os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs"
        )
        create_shortcut(
            os.path.join(INSTALL_DIR, BAT_NAME),
            os.path.join(start_menu, LINK_NAME),
            APP_NAME,
            INSTALL_DIR,
        )
        print(f"  + 开始菜单: {LINK_NAME}")
    except Exception as e:
        print(f"  ! 创建开始菜单失败: {e}")

    # 4. 设置开机自启动
    print(f"\n[4/4] 设置开机自启动")
    try:
        bat_path = os.path.join(INSTALL_DIR, BAT_NAME)
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(key, STARTUP_REG, 0, winreg.REG_SZ, f'"{bat_path}"')
        winreg.CloseKey(key)
        print(f"  + 注册表启动项: {STARTUP_REG}")
    except Exception as e:
        print(f"  ! 设置自启动失败: {e}")

    print(f"\n{'='*50}")
    print(f"  安装完成!")
    print(f"{'='*50}")
    print(f"\n  安装目录: {INSTALL_DIR}")
    print(f"  双击桌面「{LINK_NAME}」即可启动")
    print(f"  拖拽文件到右上角悬浮图标即可自动整理\n")


def uninstall():
    print(f"\n{'='*50}")
    print(f"  {APP_NAME} - 卸载")
    print(f"{'='*50}\n")

    # 1. 移除自启动
    print("[1/3] 移除开机自启动")
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE,
        )
        winreg.DeleteValue(key, STARTUP_REG)
        winreg.CloseKey(key)
        print("  + 已移除")
    except FileNotFoundError:
        print("  (不存在)")
    except Exception as e:
        print(f"  ! {e}")

    # 2. 删除快捷方式
    print("\n[2/3] 删除快捷方式")
    locations = [
        os.path.join(os.environ["USERPROFILE"], "Desktop", LINK_NAME),
        os.path.join(
            os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", LINK_NAME
        ),
    ]
    for loc in locations:
        if os.path.exists(loc):
            os.remove(loc)
            print(f"  + 已删除: {loc}")

    # 3. 删除安装目录
    print(f"\n[3/3] 删除安装目录")
    if os.path.exists(INSTALL_DIR):
        try:
            shutil.rmtree(INSTALL_DIR)
            print(f"  + 已删除: {INSTALL_DIR}")
        except Exception as e:
            print(f"  ! 删除失败（可能有文件被占用）: {e}")
            print(f"  请手动删除: {INSTALL_DIR}")
    else:
        print("  (不存在)")

    # 提示是否删除数据目录
    data_dirs = [r"D:\meow-temp", r"D:\meow-file"]
    existing = [d for d in data_dirs if os.path.exists(d)]
    if existing:
        print(f"\n  以下数据目录仍保留（归档文件不受影响）:")
        for d in existing:
            print(f"    - {d}")
        print(f"  如需删除，请手动操作。")

    print(f"\n{'='*50}")
    print(f"  卸载完成!")
    print(f"{'='*50}\n")


def status():
    print(f"\n{'='*50}")
    print(f"  {APP_NAME} - 状态")
    print(f"{'='*50}\n")

    # 检查安装
    installed = os.path.exists(INSTALL_DIR)
    print(f"  安装状态: {'已安装' if installed else '未安装'}")
    if installed:
        print(f"  安装目录: {INSTALL_DIR}")
        files = os.listdir(INSTALL_DIR)
        print(f"  文件列表: {', '.join(files)}")

    # 检查自启动
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
        )
        val, _ = winreg.QueryValueEx(key, STARTUP_REG)
        winreg.CloseKey(key)
        print(f"  开机自启: 已启用 ({val})")
    except FileNotFoundError:
        print(f"  开机自启: 未启用")
    except Exception as e:
        print(f"  开机自启: 查询失败 ({e})")

    # 检查快捷方式
    desktop_link = os.path.join(os.environ["USERPROFILE"], "Desktop", LINK_NAME)
    print(f"  桌面快捷方式: {'存在' if os.path.exists(desktop_link) else '不存在'}")

    # 检查数据目录
    for label, d in [("临时目录", r"D:\meow-temp"), ("归档目录", r"D:\meow-file")]:
        exists = os.path.exists(d)
        size = 0
        count = 0
        if exists:
            for root, dirs, files in os.walk(d):
                for f in files:
                    if not f.startswith("."):
                        fp = os.path.join(root, f)
                        try:
                            size += os.path.getsize(fp)
                            count += 1
                        except Exception:
                            pass
        size_mb = size / (1024 * 1024)
        print(f"  {label} ({d}): {'存在' if exists else '不存在'} | {count} 文件 | {size_mb:.1f} MB")

    # 检查依赖
    deps = ["PyQt5", "send2trash", "Pillow"]
    print(f"\n  依赖检查:")
    for dep in deps:
        try:
            __import__(dep)
            print(f"    {dep}: 已安装")
        except ImportError:
            print(f"    {dep}: 未安装 (pip install {dep})")

    print()


def create_shortcut(target, link_path, description="", working_dir=""):
    """创建 Windows 快捷方式 (.lnk)"""
    from ctypes import windll, wintypes

    # 使用 PowerShell 创建快捷方式（更可靠）
    ps_script = f"""
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut("{link_path}")
$sc.TargetPath = "{target}"
$sc.WorkingDirectory = "{working_dir}"
$sc.Description = "{description}"
$sc.Save()
"""
    result = subprocess.run(
        ["powershell", "-Command", ps_script],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"用法: python {os.path.basename(__file__)} [install|uninstall|status]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "install":
        install()
    elif cmd == "uninstall":
        uninstall()
    elif cmd == "status":
        status()
    else:
        print(f"未知命令: {cmd}")
        print(f"用法: python {os.path.basename(__file__)} [install|uninstall|status]")
