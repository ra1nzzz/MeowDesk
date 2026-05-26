#!/bin/bash
# MeowDesk macOS 启动脚本

# 获取脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装"
    echo "请访问 https://www.python.org/downloads/ 下载安装"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
python3 -c "import PIL" 2>/dev/null || {
    echo "安装 Pillow..."
    pip3 install Pillow
}

python3 -c "import send2trash" 2>/dev/null || {
    echo "安装 send2trash..."
    pip3 install send2trash
}

python3 -c "from Cocoa import NSApplication" 2>/dev/null || {
    echo "安装 PyObjC..."
    pip3 install pyobjc-framework-Cocoa
}

# 启动程序
echo ""
echo "🐱 启动 MeowDesk..."
echo ""
python3 meowdesk_main.py
