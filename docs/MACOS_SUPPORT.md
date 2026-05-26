# macOS 支持指南

## 概述

MeowDesk 通过平台抽象层支持 macOS（Apple Silicon），使用 PyObjC 实现原生透明窗口和拖放功能。

## 系统要求

- macOS 11.0 (Big Sur) 或更高版本
- Apple Silicon (M1/M2/M3) 或 Intel
- Python 3.9+

## 安装依赖

```bash
# 安装 PyObjC（macOS Cocoa 框架绑定）
pip install pyobjc-framework-Cocoa

# 安装其他依赖
pip install Pillow send2trash
```

## 平台差异

### 1. 窗口系统
- **Windows**: Win32 API + UpdateLayeredWindow
- **macOS**: Cocoa + NSWindow

### 2. 坐标系
- **Windows**: 原点在左上角
- **macOS**: 原点在左下角（需要转换）

### 3. 拖放
- **Windows**: windnd 库
- **macOS**: NSView 原生拖放

### 4. 系统托盘
- **Windows**: win32gui
- **macOS**: NSStatusBar

## 代码示例

### 创建窗口
```python
from meowdesk.platform import get_platform_window

# 自动选择平台实现
WindowClass = get_platform_window()
window = WindowClass(width=128, height=128)

# 创建和显示
window.create()
window.set_position(100, 100)
window.show()

# 设置回调
window.on_drop(lambda files: print(f"拖入文件: {files}"))
window.on_click(lambda: print("点击"))

# 运行
window.run()
```

### 渲染动画
```python
from PIL import Image

# 加载图片
image = Image.open("assets/idle.apng")

# 渲染到窗口
window.render(image)
```

## 打包 macOS 应用

### 使用 PyInstaller
```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包（Apple Silicon）
pyinstaller --onefile \
    --windowed \
    --name MeowDesk \
    --icon assets/icon.icns \
    --add-data "assets:assets" \
    --target-arch arm64 \
    meowdesk_main.py

# 打包（Universal Binary - 同时支持 Intel 和 Apple Silicon）
pyinstaller --onefile \
    --windowed \
    --name MeowDesk \
    --icon assets/icon.icns \
    --add-data "assets:assets" \
    --target-arch universal2 \
    meowdesk_main.py
```

### 创建 .app 包
```bash
# 打包后会生成 dist/MeowDesk.app
# 可以直接拖到 Applications 文件夹

# 或者创建 DMG 安装包
hdiutil create -volname "MeowDesk" \
    -srcfolder dist/MeowDesk.app \
    -ov -format UDZO \
    MeowDesk.dmg
```

## 权限配置

### Info.plist
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>MeowDesk</string>
    
    <key>CFBundleDisplayName</key>
    <string>妙喵桌宠</string>
    
    <key>CFBundleIdentifier</key>
    <string>com.meowdesk.app</string>
    
    <key>CFBundleVersion</key>
    <string>1.3.0</string>
    
    <key>LSUIElement</key>
    <true/>  <!-- 不显示在 Dock -->
    
    <key>NSAppleEventsUsageDescription</key>
    <string>MeowDesk 需要访问文件以进行归档</string>
    
    <key>NSFileProviderDomainUsageDescription</key>
    <string>MeowDesk 需要访问文件系统</string>
</dict>
</plist>
```

## 已知问题

### 1. 透明度问题
- macOS 的窗口透明度处理与 Windows 不同
- 需要正确设置 `NSWindow.setOpaque_(False)`

### 2. 拖放权限
- macOS 10.15+ 需要用户授权文件访问
- 首次拖放时会弹出权限请求

### 3. 开机自启
```python
import os
import plistlib

def add_to_login_items():
    """添加到登录项"""
    app_path = os.path.abspath(__file__)
    plist_path = os.path.expanduser(
        "~/Library/LaunchAgents/com.meowdesk.plist"
    )
    
    plist_data = {
        'Label': 'com.meowdesk',
        'ProgramArguments': ['/usr/bin/python3', app_path],
        'RunAtLoad': True,
        'KeepAlive': False
    }
    
    with open(plist_path, 'wb') as f:
        plistlib.dump(plist_data, f)
    
    os.system(f'launchctl load {plist_path}')
```

## 测试

### 单元测试
```bash
# 在 macOS 上运行测试
python -m pytest tests/ -v
```

### 手动测试清单
- [ ] 窗口创建和显示
- [ ] 拖放文件
- [ ] 动画播放
- [ ] 右键菜单
- [ ] 系统托盘
- [ ] 文件归档
- [ ] HTML 生成

## 性能优化

### 1. 减少重绘
```python
# 只在需要时更新
if image_changed:
    window.render(image)
```

### 2. 使用 Metal 加速（可选）
```python
# 未来可以考虑使用 Metal 进行硬件加速
```

## 发布

### App Store
如果要发布到 App Store，需要：
1. 注册 Apple Developer 账号
2. 代码签名
3. 沙盒化
4. 提交审核

### 独立分发
```bash
# 签名（需要开发者证书）
codesign --force --deep --sign "Developer ID Application: Your Name" \
    dist/MeowDesk.app

# 公证（可选，推荐）
xcrun notarytool submit MeowDesk.dmg \
    --apple-id your@email.com \
    --password app-specific-password \
    --team-id TEAM_ID
```

## 参考资源

- [PyObjC 文档](https://pyobjc.readthedocs.io/)
- [Cocoa 编程指南](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/CocoaFundamentals/)
- [macOS Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/macos)
