#!/bin/bash
# MeowDesk macOS 自动化构建脚本

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 版本号
VERSION="1.4.0"

echo -e "${BLUE}🔨 MeowDesk macOS 构建脚本 v${VERSION}${NC}"
echo ""

# 检查系统
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}❌ 此脚本只能在 macOS 上运行${NC}"
    exit 1
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 未安装${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python 版本: $(python3 --version)${NC}"

# 检查依赖
echo ""
echo -e "${YELLOW}📦 检查依赖...${NC}"

DEPS=("Pillow" "send2trash" "pyobjc-framework-Cocoa")
for dep in "${DEPS[@]}"; do
    if python3 -c "import ${dep//-/_}" 2>/dev/null; then
        echo -e "${GREEN}  ✅ ${dep}${NC}"
    else
        echo -e "${RED}  ❌ ${dep} 未安装${NC}"
        echo -e "${YELLOW}  正在安装 ${dep}...${NC}"
        pip3 install "$dep"
    fi
done

# 选择打包方式
echo ""
echo -e "${BLUE}选择打包方式:${NC}"
echo "  1) PyInstaller (快速，适合测试)"
echo "  2) py2app (原生，适合发布)"
echo "  3) 两者都打包"
read -p "请选择 [1-3]: " choice

# 清理旧文件
echo ""
echo -e "${YELLOW}🧹 清理旧文件...${NC}"
rm -rf build dist *.app *.dmg
echo -e "${GREEN}✅ 清理完成${NC}"

# PyInstaller 打包
if [[ "$choice" == "1" ]] || [[ "$choice" == "3" ]]; then
    echo ""
    echo -e "${BLUE}📦 使用 PyInstaller 打包...${NC}"
    
    # 检查 PyInstaller
    if ! command -v pyinstaller &> /dev/null; then
        echo -e "${YELLOW}安装 PyInstaller...${NC}"
        pip3 install pyinstaller
    fi
    
    # 打包
    pyinstaller meowdesk.spec
    
    if [ -d "dist/MeowDesk" ]; then
        echo -e "${GREEN}✅ PyInstaller 打包成功${NC}"
        
        # 创建 .app 包装
        echo -e "${YELLOW}创建 .app 包装...${NC}"
        mkdir -p "MeowDesk-PyInstaller.app/Contents/MacOS"
        mkdir -p "MeowDesk-PyInstaller.app/Contents/Resources"
        
        cp -r dist/MeowDesk/* "MeowDesk-PyInstaller.app/Contents/MacOS/"
        
        cat > "MeowDesk-PyInstaller.app/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>MeowDesk</string>
    <key>CFBundleIdentifier</key>
    <string>com.meowdesk.app</string>
    <key>CFBundleName</key>
    <string>MeowDesk</string>
    <key>CFBundleDisplayName</key>
    <string>妙喵桌宠</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.4.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF
        
        echo -e "${GREEN}✅ .app 包装创建成功${NC}"
    else
        echo -e "${RED}❌ PyInstaller 打包失败${NC}"
    fi
fi

# py2app 打包
if [[ "$choice" == "2" ]] || [[ "$choice" == "3" ]]; then
    echo ""
    echo -e "${BLUE}📦 使用 py2app 打包...${NC}"
    
    # 检查 py2app
    if ! python3 -c "import py2app" 2>/dev/null; then
        echo -e "${YELLOW}安装 py2app...${NC}"
        pip3 install py2app
    fi
    
    # 打包
    python3 setup_macos.py py2app
    
    if [ -d "dist/MeowDesk.app" ]; then
        echo -e "${GREEN}✅ py2app 打包成功${NC}"
    else
        echo -e "${RED}❌ py2app 打包失败${NC}"
    fi
fi

# 显示结果
echo ""
echo -e "${BLUE}📊 构建结果:${NC}"
echo ""

if [ -d "MeowDesk-PyInstaller.app" ]; then
    SIZE=$(du -sh MeowDesk-PyInstaller.app | cut -f1)
    echo -e "${GREEN}✅ MeowDesk-PyInstaller.app (${SIZE})${NC}"
fi

if [ -d "dist/MeowDesk.app" ]; then
    SIZE=$(du -sh dist/MeowDesk.app | cut -f1)
    echo -e "${GREEN}✅ dist/MeowDesk.app (${SIZE})${NC}"
fi

# 询问是否创建 DMG
echo ""
read -p "是否创建 DMG 安装包？[y/N]: " create_dmg

if [[ "$create_dmg" == "y" ]] || [[ "$create_dmg" == "Y" ]]; then
    echo ""
    echo -e "${BLUE}📀 创建 DMG 安装包...${NC}"
    
    # 检查 create-dmg
    if ! command -v create-dmg &> /dev/null; then
        echo -e "${YELLOW}create-dmg 未安装${NC}"
        echo -e "${YELLOW}安装方法: brew install create-dmg${NC}"
        exit 1
    fi
    
    # 选择要打包的 .app
    if [ -d "dist/MeowDesk.app" ]; then
        APP_PATH="dist/MeowDesk.app"
        DMG_NAME="MeowDesk-${VERSION}-py2app.dmg"
    elif [ -d "MeowDesk-PyInstaller.app" ]; then
        APP_PATH="MeowDesk-PyInstaller.app"
        DMG_NAME="MeowDesk-${VERSION}-PyInstaller.dmg"
    else
        echo -e "${RED}❌ 找不到 .app 文件${NC}"
        exit 1
    fi
    
    # 创建 DMG
    create-dmg \
        --volname "MeowDesk" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "MeowDesk.app" 175 120 \
        --hide-extension "MeowDesk.app" \
        --app-drop-link 425 120 \
        "$DMG_NAME" \
        "$APP_PATH"
    
    if [ -f "$DMG_NAME" ]; then
        SIZE=$(du -sh "$DMG_NAME" | cut -f1)
        echo -e "${GREEN}✅ DMG 创建成功: ${DMG_NAME} (${SIZE})${NC}"
    else
        echo -e "${RED}❌ DMG 创建失败${NC}"
    fi
fi

# 完成
echo ""
echo -e "${GREEN}🎉 构建完成！${NC}"
echo ""
echo -e "${BLUE}测试应用:${NC}"
if [ -d "dist/MeowDesk.app" ]; then
    echo "  open dist/MeowDesk.app"
fi
if [ -d "MeowDesk-PyInstaller.app" ]; then
    echo "  open MeowDesk-PyInstaller.app"
fi
echo ""
