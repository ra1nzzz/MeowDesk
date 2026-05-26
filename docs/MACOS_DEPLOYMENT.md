# macOS 部署指南

## 📦 打包方式对比

| 方式 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| PyInstaller | 简单快速，跨平台 | 包体积大 | ⭐⭐⭐⭐ |
| py2app | 原生 .app，体积小 | 配置复杂 | ⭐⭐⭐⭐⭐ |
| 手动打包 | 完全控制 | 工作量大 | ⭐⭐⭐ |

---

## 方法 1：PyInstaller（推荐用于快速测试）

### 1.1 安装 PyInstaller

```bash
pip3 install pyinstaller
```

### 1.2 使用现有 spec 文件

```bash
# 多文件模式（推荐）
pyinstaller meowdesk.spec

# 单文件模式
pyinstaller meowdesk-onefile.spec
```

### 1.3 测试打包结果

```bash
# 多文件模式
./dist/MeowDesk/MeowDesk

# 单文件模式
./dist/MeowDesk
```

### 1.4 创建 .app 包装

```bash
# 创建 .app 目录结构
mkdir -p "MeowDesk.app/Contents/MacOS"
mkdir -p "MeowDesk.app/Contents/Resources"

# 复制可执行文件
cp -r dist/MeowDesk/* "MeowDesk.app/Contents/MacOS/"

# 复制图标（如果有）
# cp assets/icon.icns "MeowDesk.app/Contents/Resources/"

# 创建 Info.plist
cat > "MeowDesk.app/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>MeowDesk</string>
    <key>CFBundleIconFile</key>
    <string>icon</string>
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
    <key>CFBundleVersion</key>
    <string>1.4.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSUIElement</key>
    <false/>
</dict>
</plist>
EOF

# 测试
open MeowDesk.app
```

---

## 方法 2：py2app（推荐用于正式发布）

### 2.1 安装 py2app

```bash
pip3 install py2app
```

### 2.2 使用配置文件

```bash
# 使用提供的 setup_macos.py
python3 setup_macos.py py2app
```

### 2.3 测试

```bash
open dist/MeowDesk.app
```

### 2.4 清理和重新打包

```bash
# 清理
rm -rf build dist

# 重新打包
python3 setup_macos.py py2app
```

---

## 方法 3：创建 DMG 安装包

### 3.1 安装 create-dmg

```bash
# 使用 Homebrew
brew install create-dmg

# 或者从源码安装
git clone https://github.com/create-dmg/create-dmg.git
cd create-dmg
sudo make install
```

### 3.2 创建 DMG

```bash
# 基础版本
create-dmg \
  --volname "MeowDesk" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "MeowDesk.app" 175 120 \
  --hide-extension "MeowDesk.app" \
  --app-drop-link 425 120 \
  "MeowDesk-1.4.0.dmg" \
  "MeowDesk.app"
```

### 3.3 高级 DMG（带背景图）

```bash
# 1. 创建背景图（600x400 像素）
# 2. 保存为 dmg-background.png

# 3. 创建 DMG
create-dmg \
  --volname "MeowDesk" \
  --volicon "assets/icon.icns" \
  --background "dmg-background.png" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "MeowDesk.app" 175 120 \
  --hide-extension "MeowDesk.app" \
  --app-drop-link 425 120 \
  --eula "LICENSE" \
  "MeowDesk-1.4.0.dmg" \
  "MeowDesk.app"
```

---

## 图标制作

### 4.1 从 PNG 创建 ICNS

```bash
# 准备不同尺寸的图标
mkdir icon.iconset
sips -z 16 16     icon.png --out icon.iconset/icon_16x16.png
sips -z 32 32     icon.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32     icon.png --out icon.iconset/icon_32x32.png
sips -z 64 64     icon.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128   icon.png --out icon.iconset/icon_128x128.png
sips -z 256 256   icon.png --out icon.iconset/icon_128x128@2x.png
sips -z 256 256   icon.png --out icon.iconset/icon_256x256.png
sips -z 512 512   icon.png --out icon.iconset/icon_256x256@2x.png
sips -z 512 512   icon.png --out icon.iconset/icon_512x512.png
sips -z 1024 1024 icon.png --out icon.iconset/icon_512x512@2x.png

# 生成 .icns
iconutil -c icns icon.iconset

# 清理
rm -rf icon.iconset
```

### 4.2 使用在线工具

- https://cloudconvert.com/png-to-icns
- https://iconverticons.com/online/

---

## 代码签名（可选）

### 5.1 获取开发者证书

1. 注册 Apple Developer Program ($99/年)
2. 在 Xcode 中下载证书
3. 或使用 Keychain Access 创建证书请求

### 5.2 签名应用

```bash
# 查看可用证书
security find-identity -v -p codesigning

# 签名
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name (TEAM_ID)" \
  MeowDesk.app

# 验证签名
codesign --verify --deep --strict --verbose=2 MeowDesk.app
spctl -a -t exec -vv MeowDesk.app
```

### 5.3 公证（Notarization）

```bash
# 创建 ZIP
ditto -c -k --keepParent MeowDesk.app MeowDesk.zip

# 上传公证
xcrun notarytool submit MeowDesk.zip \
  --apple-id "your@email.com" \
  --password "app-specific-password" \
  --team-id "TEAM_ID" \
  --wait

# 装订公证票据
xcrun stapler staple MeowDesk.app
```

---

## 自动化脚本

### 6.1 完整打包脚本

创建 `build_macos.sh`:

```bash
#!/bin/bash
set -e

echo "🔨 开始构建 MeowDesk for macOS"

# 清理
echo "清理旧文件..."
rm -rf build dist MeowDesk.app *.dmg

# 打包
echo "使用 py2app 打包..."
python3 setup_macos.py py2app

# 测试
echo "测试应用..."
open -a dist/MeowDesk.app --args --test

# 等待用户确认
read -p "测试通过？按 Enter 继续创建 DMG，Ctrl+C 取消..."

# 创建 DMG
echo "创建 DMG..."
create-dmg \
  --volname "MeowDesk" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "MeowDesk.app" 175 120 \
  --hide-extension "MeowDesk.app" \
  --app-drop-link 425 120 \
  "MeowDesk-1.4.0.dmg" \
  "dist/MeowDesk.app"

echo "✅ 构建完成！"
echo "DMG 文件: MeowDesk-1.4.0.dmg"
```

使用：

```bash
chmod +x build_macos.sh
./build_macos.sh
```

---

## 发布清单

### 7.1 发布前检查

- [ ] 所有功能测试通过
- [ ] 在不同 macOS 版本测试
- [ ] 在 Intel 和 Apple Silicon 测试
- [ ] 检查内存泄漏
- [ ] 检查 CPU 使用率
- [ ] 更新版本号
- [ ] 更新 CHANGELOG
- [ ] 准备发布说明

### 7.2 发布渠道

1. **GitHub Releases**
   - 上传 DMG 文件
   - 添加发布说明
   - 标记版本号

2. **官网下载**
   - 提供直接下载链接
   - 提供安装说明

3. **Homebrew Cask**（可选）
   ```ruby
   cask "meowdesk" do
     version "1.4.0"
     sha256 "..."
     
     url "https://github.com/username/meowdesk/releases/download/v#{version}/MeowDesk-#{version}.dmg"
     name "MeowDesk"
     desc "智能桌面文件分类归档工具"
     homepage "https://github.com/username/meowdesk"
     
     app "MeowDesk.app"
   end
   ```

---

## 常见问题

### Q1: "MeowDesk.app 已损坏，无法打开"

**原因**: macOS Gatekeeper 阻止未签名的应用

**解决方案**:
```bash
# 移除隔离属性
xattr -cr MeowDesk.app

# 或者在系统偏好设置中允许
# 系统偏好设置 -> 安全性与隐私 -> 通用 -> 仍要打开
```

### Q2: 打包后找不到资源文件

**原因**: 资源文件路径不正确

**解决方案**:
```python
# 在代码中使用正确的路径
if getattr(sys, 'frozen', False):
    # 打包后
    bundle_dir = sys._MEIPASS  # PyInstaller
    # 或
    bundle_dir = os.path.dirname(sys.executable)  # py2app
else:
    # 开发环境
    bundle_dir = os.path.dirname(os.path.abspath(__file__))
```

### Q3: 打包后体积太大

**解决方案**:
```bash
# 1. 排除不需要的包
# 在 spec 文件中添加 excludes

# 2. 使用 UPX 压缩
brew install upx
upx --best dist/MeowDesk/MeowDesk

# 3. 清理 .pyc 文件
find dist/MeowDesk.app -name "*.pyc" -delete
find dist/MeowDesk.app -name "__pycache__" -type d -delete
```

### Q4: 在 Apple Silicon 上运行 Intel 版本

**解决方案**:
```bash
# 创建通用二进制（Universal Binary）
# 在 setup_macos.py 中添加:
OPTIONS = {
    'arch': 'universal2',  # 同时支持 Intel 和 Apple Silicon
    # ...
}
```

---

## 性能优化

### 8.1 减小包体积

```python
# setup_macos.py
OPTIONS = {
    'excludes': [
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
    ],
    'optimize': 2,  # 优化字节码
    'compressed': True,  # 压缩
}
```

### 8.2 启动速度优化

```python
# 延迟导入大型库
def heavy_function():
    import heavy_library  # 只在需要时导入
    # ...
```

### 8.3 内存优化

```python
# 限制动画缓存
MAX_CACHE_SIZE = 50

# 及时释放资源
def cleanup():
    self.animation.clear_cache()
    gc.collect()
```

---

## 参考资源

- [py2app 文档](https://py2app.readthedocs.io/)
- [PyInstaller 文档](https://pyinstaller.org/)
- [create-dmg](https://github.com/create-dmg/create-dmg)
- [Apple 代码签名指南](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [macOS 应用分发指南](https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases)

---

**Made with ❤️ by ra1nzzz**
