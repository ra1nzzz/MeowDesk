@echo off
chcp 65001 >nul
title 妙喵桌宠 MeowDesk

:: 切换到脚本所在目录
cd /d "%~dp0"

:: 自动检测 Python（优先 WPS 灵犀环境）
set "PYTHON_EXE=C:\Users\和旭电商\AppData\Roaming\WPS 灵犀\python-env\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

echo.
echo  ========================================
echo    妙喵桌宠 MeowDesk
echo  ========================================
echo.
echo  Python: %PYTHON_EXE%
echo  启动中...
echo.

:: 优先使用 tkinter 版（兼容性更好）
if exist "%~dp0lingxi_droplet_tk.py" (
    "%PYTHON_EXE%" "%~dp0lingxi_droplet_tk.py"
) else (
    "%PYTHON_EXE%" "%~dp0lingxi_droplet.py"
)

if %errorlevel% neq 0 (
    echo.
    echo  [启动失败] 请查看 logs\meow_desk.log
    echo.
    pause
)
