@echo off
echo ========================================
echo MeowDesk EXE 测试
echo ========================================
echo.
echo 正在启动 MeowDesk...
echo.
cd dist\MeowDesk
start MeowDesk.exe
echo.
echo ✅ MeowDesk 已启动！
echo.
echo 测试项目：
echo   1. 窗口是否正常显示
echo   2. 动画是否正常播放
echo   3. 拖入文件测试
echo   4. 右键菜单测试
echo   5. 闲逛行为测试
echo.
echo 按任意键关闭此窗口...
pause > nul
