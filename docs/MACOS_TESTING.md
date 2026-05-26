# macOS 测试和部署指南

## 📋 测试前准备

### 1. 系统要求
- macOS 10.15 (Catalina) 或更高版本
- Apple Silicon (M1/M2/M3) 或 Intel 处理器
- Python 3.8 或更高版本

### 2. 安装依赖

```bash
# 安装 Python 依赖
pip install Pillow send2trash pyobjc-framework-Cocoa

# 可选：系统托盘支持
pip install rumps
```

### 3. 权限设置

macOS 10.15+ 需要授予文件访问权限：

1. 打开 **系统偏好设置** → **安全性与隐私**
2. 选择 **隐私** 标签
3. 在左侧列表中选择 **文件和文件夹**
4. 找到 Python 或终端应用，勾选需要访问的文件夹
5. 如果需要拖放功能，还需要授予 **辅助功能** 权限

---

## 🧪 测试步骤

### 阶段 1：基础功能测试

#### 1.1 运行测试脚本

```bash
cd /path/to/desktopet
python test_macos.py
```

**预期输出**：
```
🍎 MeowDesk macOS 平台测试

============================================================
测试 macOS 模块导入
============================================================
✅ macOS 平台模块导入成功

============================================================
测试窗口创建
============================================================
✅ 窗口对象创建成功
✅ macOS 窗口创建成功
✅ 窗口创建成功
✅ 窗口位置设置成功
✅ 窗口位置获取成功: (100, 100)

============================================================
测试动画渲染
============================================================
✅ 窗口创建成功
✅ 动画管理器创建成功
✅ 动画帧获取成功
✅ 动画渲染成功

============================================================
测试拖放功能
============================================================
✅ 拖放功能启用成功

============================================================
✅ 所有测试通过！

可以运行主程序:
  python meowdesk_main.py
============================================================
```

#### 1.2 检查点

- [ ] 所有模块导入成功
- [ ] 窗口创建无错误
- [ ] 动画帧加载成功
- [ ] 拖放功能启用成功

### 阶段 2：主程序测试

#### 2.1 运行主程序

```bash
python meowdesk_main.py
```

**预期输出**：
```
============================================================
🐱 MeowDesk - 妙喵桌宠
============================================================

应用目录: /path/to/desktopet
资源目录: /path/to/desktopet/assets
加载配置: /path/to/desktopet/config.json
数据库: /path/to/archive/.filedb.json
已归档文件: 0 个
总大小: 0.00 MB

创建窗口...
✅ macOS 窗口创建成功
✅ macOS 拖放已启用
✅ 窗口创建成功

============================================================
MeowDesk 正在运行...
拖入文件到猫猫身上即可自动归档
右键点击查看菜单
============================================================
```

#### 2.2 检查点

- [ ] 窗口显示在屏幕上
- [ ] 可以看到透明的猫猫动画
- [ ] 动画正常播放（闲置状态）
- [ ] 窗口保持在最前面

### 阶段 3：交互功能测试

#### 3.1 鼠标交互

**测试项目**：
1. **点击猫猫**
   - [ ] 单击：猫猫有反应（重置闲逛）
   - [ ] 连续点击 3 次：猫猫变害羞（SHY 状态）

2. **拖动猫猫**
   - [ ] 按住鼠标左键可以拖动窗口
   - [ ] 释放后窗口停在新位置
   - [ ] 位置会被保存

3. **右键菜单**
   - [ ] 右键点击显示菜单
   - [ ] 菜单项可以点击
   - [ ] "退出" 可以关闭程序

#### 3.2 拖放功能

**测试项目**：
1. **拖入单个文件**
   - [ ] 从 Finder 拖入一个文件到猫猫身上
   - [ ] 猫猫变惊讶（SURPRISED 状态）
   - [ ] 显示气泡提示 "收到 1 个文件"
   - [ ] 文件被正确分类和归档
   - [ ] 猫猫变开心（HAPPY 状态）

2. **拖入多个文件**
   - [ ] 拖入 5-10 个文件
   - [ ] 猫猫变惊讶
   - [ ] 显示气泡提示 "收到 X 个文件"
   - [ ] 所有文件被处理
   - [ ] 显示处理结果

3. **拖入文件夹**
   - [ ] 拖入一个包含文件的文件夹
   - [ ] 文件夹内所有文件被处理
   - [ ] 空文件夹被删除

4. **拖入截图**
   - [ ] 拖入截图文件（文件名包含 "截图"、"screenshot" 等）
   - [ ] 截图被回收到废纸篓
   - [ ] 显示 "X 截图回收"

#### 3.3 动画状态

**测试项目**：
1. **闲置状态（IDLE）**
   - [ ] 启动后默认是闲置状态
   - [ ] 动画循环播放

2. **闲逛行为**
   - [ ] 等待 5 秒后，猫猫开始在屏幕右上角区域闲逛
   - [ ] 移动平滑自然
   - [ ] 不会移出屏幕

3. **睡眠状态（SLEEPING）**
   - [ ] 60 秒无交互后，猫猫进入睡眠状态
   - [ ] 播放睡眠动画

4. **惊讶状态（SURPRISED）**
   - [ ] 拖入文件时触发
   - [ ] 短暂显示后恢复

5. **开心状态（HAPPY）**
   - [ ] 文件处理完成后触发
   - [ ] 短暂显示后恢复

6. **害羞状态（SHY）**
   - [ ] 连续点击 3 次触发
   - [ ] 短暂显示后恢复

### 阶段 4：文件处理测试

#### 4.1 准备测试文件

```bash
# 创建测试目录
mkdir ~/meowdesk_test
cd ~/meowdesk_test

# 创建各种类型的测试文件
echo "test" > test.txt
echo "test" > test.pdf
echo "test" > test.jpg
echo "test" > test.mp4
echo "test" > test.zip
echo "test" > 截图2024-01-01.png
```

#### 4.2 测试分类规则

**测试项目**：
1. **文档类**
   - [ ] `.txt`, `.pdf`, `.doc`, `.docx` → `文档/`

2. **图片类**
   - [ ] `.jpg`, `.png`, `.gif` → `图片/`

3. **视频类**
   - [ ] `.mp4`, `.avi`, `.mov` → `视频/`

4. **压缩包**
   - [ ] `.zip`, `.rar`, `.7z` → `压缩包/`

5. **截图回收**
   - [ ] 文件名包含 "截图"、"screenshot" → 废纸篓

#### 4.3 检查归档结果

```bash
# 查看归档目录
ls -la ~/Desktop/归档/

# 应该看到：
# 文档/
# 图片/
# 视频/
# 压缩包/
# .filedb.json
# index.html
```

#### 4.4 检查数据库

```bash
# 查看数据库内容
cat ~/Desktop/归档/.filedb.json | python -m json.tool
```

**预期内容**：
```json
{
  "records": [
    {
      "timestamp": "2024-01-01T12:00:00",
      "original_name": "test.txt",
      "category": "文档",
      "action": "archive",
      "destination": "/path/to/文档/test.txt",
      "md5": "...",
      "file_size": 5
    }
  ]
}
```

#### 4.5 检查 HTML 索引

```bash
# 在浏览器中打开
open ~/Desktop/归档/index.html
```

**检查点**：
- [ ] HTML 文件可以打开
- [ ] 显示所有归档记录
- [ ] 可以按分类筛选
- [ ] 可以搜索文件
- [ ] 点击文件名可以打开

---

## 🐛 常见问题

### 问题 1：窗口不显示

**症状**：程序运行但看不到窗口

**解决方案**：
1. 检查是否授予了辅助功能权限
2. 尝试切换到其他桌面空间
3. 检查窗口位置是否在屏幕外：
   ```bash
   # 删除配置文件重置位置
   rm config.json
   ```

### 问题 2：拖放不工作

**症状**：拖入文件没有反应

**解决方案**：
1. 检查终端输出是否有错误
2. 确认已授予文件访问权限
3. 尝试重启程序

### 问题 3：动画不流畅

**症状**：动画卡顿或不播放

**解决方案**：
1. 检查 CPU 使用率
2. 确认 assets 目录存在且包含动画文件
3. 尝试降低动画帧率（修改 `FRAME_DELAY`）

### 问题 4：文件处理失败

**症状**：文件拖入后没有被归档

**解决方案**：
1. 检查终端输出的错误信息
2. 确认归档目录有写入权限
3. 检查磁盘空间是否充足

### 问题 5：PyObjC 导入失败

**症状**：`ImportError: No module named 'Cocoa'`

**解决方案**：
```bash
# 重新安装 PyObjC
pip uninstall pyobjc-framework-Cocoa
pip install pyobjc-framework-Cocoa

# 如果还是失败，尝试安装完整的 PyObjC
pip install pyobjc
```

---

## 📦 打包和分发

### 方法 1：使用 PyInstaller

#### 1. 安装 PyInstaller

```bash
pip install pyinstaller
```

#### 2. 创建 spec 文件

已提供 `meowdesk.spec` 和 `meowdesk-onefile.spec`

#### 3. 打包

```bash
# 多文件模式（推荐）
pyinstaller meowdesk.spec

# 单文件模式
pyinstaller meowdesk-onefile.spec
```

#### 4. 测试打包结果

```bash
# 多文件模式
./dist/MeowDesk/MeowDesk

# 单文件模式
./dist/MeowDesk
```

### 方法 2：创建 .app 包

#### 1. 使用 py2app

```bash
# 安装 py2app
pip install py2app

# 创建 setup.py
python setup.py py2app

# 运行
open dist/MeowDesk.app
```

#### 2. 手动创建 .app 包

```bash
# 创建目录结构
mkdir -p MeowDesk.app/Contents/MacOS
mkdir -p MeowDesk.app/Contents/Resources

# 复制可执行文件
cp dist/MeowDesk MeowDesk.app/Contents/MacOS/

# 复制资源
cp -r assets MeowDesk.app/Contents/Resources/
cp icon.icns MeowDesk.app/Contents/Resources/

# 创建 Info.plist
cat > MeowDesk.app/Contents/Info.plist << 'EOF'
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
```

### 方法 3：创建 DMG 安装包

```bash
# 安装 create-dmg
brew install create-dmg

# 创建 DMG
create-dmg \
  --volname "MeowDesk" \
  --volicon "assets/icon.icns" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "MeowDesk.app" 175 120 \
  --hide-extension "MeowDesk.app" \
  --app-drop-link 425 120 \
  "MeowDesk-1.4.0.dmg" \
  "MeowDesk.app"
```

---

## 🚀 性能优化

### 1. 减少内存使用

```python
# 在 animation.py 中启用帧缓存限制
MAX_CACHE_SIZE = 50  # 限制缓存帧数
```

### 2. 优化动画帧率

```python
# 在 window.py 中调整帧延迟
FRAME_DELAY = 100  # 增加到 100ms（10 FPS）
```

### 3. 异步文件处理

```python
# 使用线程处理大批量文件
import threading

def process_files_async(files):
    thread = threading.Thread(target=self._process_files, args=(files,))
    thread.start()
```

---

## 📊 性能基准

### 预期性能指标

| 指标 | 目标值 | 测试方法 |
|------|--------|----------|
| CPU 使用率 | < 5% | Activity Monitor |
| 内存使用 | < 100 MB | Activity Monitor |
| 启动时间 | < 2 秒 | 计时 |
| 动画帧率 | 12-15 FPS | 目测 |
| 文件处理速度 | > 10 文件/秒 | 批量测试 |

### 测试方法

```bash
# 监控 CPU 和内存
top -pid $(pgrep -f meowdesk_main)

# 测试启动时间
time python meowdesk_main.py

# 测试文件处理速度
# 拖入 100 个文件，记录处理时间
```

---

## ✅ 测试清单

### 基础功能
- [ ] 程序可以启动
- [ ] 窗口正常显示
- [ ] 动画正常播放
- [ ] 可以拖动窗口
- [ ] 可以点击交互

### 拖放功能
- [ ] 可以拖入单个文件
- [ ] 可以拖入多个文件
- [ ] 可以拖入文件夹
- [ ] 文件被正确分类
- [ ] 截图被正确回收

### 动画状态
- [ ] 闲置状态正常
- [ ] 闲逛行为正常
- [ ] 睡眠状态正常
- [ ] 惊讶状态正常
- [ ] 开心状态正常
- [ ] 害羞状态正常

### 数据管理
- [ ] 数据库正确记录
- [ ] HTML 索引正确生成
- [ ] 配置正确保存
- [ ] 窗口位置被记住

### 性能
- [ ] CPU 使用率正常
- [ ] 内存使用正常
- [ ] 动画流畅
- [ ] 文件处理快速

### 打包
- [ ] PyInstaller 打包成功
- [ ] .app 包可以运行
- [ ] DMG 安装包正常

---

## 📝 测试报告模板

```markdown
# MeowDesk macOS 测试报告

**测试日期**: 2024-XX-XX
**测试人员**: XXX
**系统版本**: macOS XX.X (XXX)
**处理器**: Apple M1/M2/Intel
**Python 版本**: 3.X.X

## 测试结果

### 基础功能
- [x] 程序启动: ✅ 通过
- [x] 窗口显示: ✅ 通过
- [x] 动画播放: ✅ 通过
- [ ] 拖动窗口: ❌ 失败 - 原因：XXX

### 拖放功能
- [x] 单个文件: ✅ 通过
- [x] 多个文件: ✅ 通过
- [x] 文件夹: ✅ 通过

### 性能
- CPU 使用率: 3.5%
- 内存使用: 85 MB
- 启动时间: 1.8 秒

## 问题列表

1. **问题描述**: XXX
   - **严重程度**: 高/中/低
   - **复现步骤**: XXX
   - **预期结果**: XXX
   - **实际结果**: XXX

## 总体评价

- **功能完整性**: 95%
- **稳定性**: 良好
- **性能**: 优秀
- **用户体验**: 良好

## 建议

1. XXX
2. XXX
```

---

**Made with ❤️ by ra1nzzz**
