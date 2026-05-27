@echo off
echo ========================================
echo MeowDesk 测试脚本
echo ========================================
echo.

echo 1. 启动 MeowDesk...
start MeowDesk.exe
timeout /t 3 /nobreak >nul

echo.
echo 2. 检查进程...
tasklist | findstr /i "MeowDesk.exe"
if %errorlevel% equ 0 (
    echo ✅ MeowDesk 正在运行
) else (
    echo ❌ MeowDesk 未运行
)

echo.
echo 3. 等待 10 秒观察动画...
echo    请检查:
echo    - 猫猫是否正常显示
echo    - 动画是否流畅
echo    - 是否可以拖动窗口
echo    - 点击是否有反应
timeout /t 10 /nobreak >nul

echo.
echo 4. 关闭程序...
taskkill /F /IM MeowDesk.exe 2>nul
if %errorlevel% equ 0 (
    echo ✅ MeowDesk 已关闭
) else (
    echo ❌ 关闭失败
)

echo.
echo ========================================
echo 测试完成
echo ========================================
pause