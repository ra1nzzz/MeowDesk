# 妙喵桌宠 MeowDesk 🐱

<div align="center">

> 智能桌面文件分类归档工具 + AI 助手

[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-blue)](https://github.com/ra1nzzz/MeowDesk)
[![Python](https://img.shields.io/badge/python-3.8+-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.4.0-red)](https://github.com/ra1nzzz/MeowDesk/releases)

把文件拖到桌面猫猫身上，自动分类归档到对应目录，截图自动回收。

**🎉 v1.4.0 新增 macOS 支持！**

</div>

![screenshot](assets/idle.apng)

---

## ✨ 特性

### 🎯 核心功能
- 🗂️ **智能文件分类** - 自动识别文件类型，分类归档
- 🖼️ **截图自动回收** - 识别截图文件，自动清理到回收站
- 🔍 **MD5 去重** - 避免重复文件占用空间
- 📊 **HTML 索引** - 生成可视化的文件索引页面
- 💾 **数据库记录** - 完整的文件处理历史

### 🎨 桌面宠物
- 🐾 **8 种动画状态** - 闲置、开心、惊讶、害羞、睡眠、接收、搬运、回收
- 🚶 **智能闲逛** - 在屏幕上自然移动
- 💬 **气泡提示** - 实时反馈操作状态
- 🎭 **情绪反应** - 根据交互显示不同表情
- 🖱️ **可拖动** - 位置自动记忆

### 🤖 AI 助手（框架）
- 🔌 **Agent 网关** - 可接入 OpenClaw、Hermes 等
- 📝 **内置命令** - 磁盘清理、日期查询、假期提醒等
- 🔧 **可扩展** - 轻松添加自定义命令

### 🌍 跨平台支持
- ✅ **Windows 10/11** - 完整支持，ULW 透明窗口
- ✅ **macOS 10.15+** - 包括 Apple Silicon，原生 NSWindow
- 🎯 **统一体验** - 两个平台功能对等

---

## 🚀 快速开始

### Windows

#### 方式一：下载 EXE（推荐）
1. 从 [Releases](https://github.com/ra1nzzz/MeowDesk/releases) 下载最新版
2. 解压后双击 `MeowDesk.exe`
3. 开始使用！

#### 方式二：从源码运行
```bash
# 安装依赖
pip install Pillow send2trash windnd

# 运行
python meowdesk_main.py

# 或使用启动脚本
start_meowdesk.bat
```

### macOS

#### 方式一：下载 DMG（推荐）
1. 从 [Releases](https://github.com/ra1nzzz/MeowDesk/releases) 下载 `.dmg`
2. 打开 DMG，拖动到应用程序文件夹
3. 首次运行需要在"系统偏好设置"中允许

#### 方式二：从源码运行
```bash
# 安装依赖
pip3 install Pillow send2trash pyobjc-framework-Cocoa

# 运行测试
python3 test_macos.py

# 运行主程序
python3 meowdesk_main.py

# 或使用启动脚本
chmod +x start_meowdesk_macos.sh
./start_meowdesk_macos.sh
```

---

## 📖 使用说明

### 基本操作
1. **拖入文件** - 将文件拖到猫猫身上
2. **自动分类** - 猫猫会自动分类并归档文件
3. **查看结果** - 右键菜单 → 打开归档目录/HTML 索引

### 交互
- **单击** - 重置闲逛，猫猫会注意你
- **连续点击 3 次** - 猫猫会害羞 😊
- **右键** - 显示菜单
- **拖动** - 移动猫猫位置
- **等待 60 秒** - 猫猫会睡觉 😴

### 文件分类规则

| 类型 | 扩展名 | 归档位置 |
|------|--------|----------|
| 文档 | .doc, .docx, .pdf, .txt, .md | `归档目录/文档/年-月/` |
| 图片 | .jpg, .png, .gif, .bmp | `归档目录/图片/年-月/` |
| 视频 | .mp4, .avi, .mov, .mkv | `归档目录/视频/年-月/` |
| 音频 | .mp3, .wav, .flac | `归档目录/音频/年-月/` |
| 代码 | .py, .js, .java, .cpp | `归档目录/代码/年-月/` |
| 压缩包 | .zip, .rar, .7z | `归档目录/压缩包/年-月/` |
| 设计稿 | .psd, .ai, .sketch | `归档目录/设计稿/年-月/` |
| 电子书 | .epub, .mobi, .azw3 | `归档目录/电子书/年-月/` |
| 截图 | 包含"截图"等关键词 | **回收站** ♻️ |

### 截图识别规则

文件被判定为「临时截图」并自动移入回收站的条件（满足任一即可）：

1. **文件名关键词**：`截图`、`截屏`、`Screenshot`、`Screen Shot`、`微信截图`、`QQ截图`、`Snipaste`、`Capture` 等
2. **临时目录**：位于 `Temp`、`AppData`、`Clipboard` 等
3. **屏幕分辨率**：图片分辨率接近屏幕分辨率（宽 ≥ 80% 且 高 ≥ 50%）

---

## ⚙️ 配置

编辑 `config.json`（首次运行后自动生成）：

```json
{
  "temp_dir": "D:\\meow-temp",           // 临时目录
  "archive_dir": "D:\\meow-file",        // 归档目录
  "window_opacity": 0.85,                // 窗口透明度
  "scale": 0.5,                          // 缩放比例
  "auto_open_html": false,               // 自动打开 HTML
  "window_position": [1400, 100],        // 窗口位置
  "categories": {                        // 分类规则
    "文档": {
      "exts": [".doc", ".docx", ".pdf", ".txt", ".md"],
      "action": "archive"
    },
    "截图": {
      "exts": [".png", ".jpg"],
      "action": "recycle"
    }
  }
}
```

---

## 🏗️ 架构

### 模块化设计

```
meowdesk/
├── core/              # 核心功能
│   ├── config.py          # 配置管理
│   ├── database.py        # 文件数据库
│   ├── classifier.py      # 文件分类器
│   └── file_handler.py    # 文件处理器
├── agent/             # AI Agent 框架
│   ├── gateway.py         # Agent 网关
│   └── commands.py        # 内置命令
├── platform/          # 平台抽象层
│   ├── base.py            # 基类接口
│   ├── windows.py         # Windows 实现
│   └── macos.py           # macOS 实现
└── ui/                # 用户界面
    ├── animation.py       # 动画管理器
    ├── window.py          # 主窗口
    ├── menu.py            # 右键菜单
    └── tray.py            # 系统托盘
```

### 平台支持

| 功能 | Windows | macOS |
|------|---------|-------|
| 透明窗口 | ✅ ULW | ✅ NSWindow |
| 动画渲染 | ✅ DIB | ✅ NSImage |
| 拖放支持 | ✅ windnd | ✅ NSView |
| 鼠标事件 | ✅ Tkinter | ✅ NSView |
| 右键菜单 | ✅ Menu | ✅ 框架 |
| 系统托盘 | ✅ pystray | ✅ 框架 |

---

## 📦 打包

### Windows

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包（多文件）
pyinstaller meowdesk.spec

# 打包（单文件）
pyinstaller meowdesk-onefile.spec

# 输出在 dist/ 目录
```

### macOS

```bash
# 方式一：PyInstaller
pip3 install pyinstaller
pyinstaller meowdesk.spec

# 方式二：py2app（推荐）
pip3 install py2app
python3 setup_macos.py py2app

# 方式三：自动化脚本
chmod +x build_macos.sh
./build_macos.sh

# 创建 DMG
brew install create-dmg
# 按照 docs/MACOS_DEPLOYMENT.md 操作
```

---

## 📚 文档

### 用户文档
- [快速开始](MACOS_QUICKSTART.md) - 5 分钟快速上手
- [使用指南](docs/USER_GUIDE.md) - 详细使用说明
- [常见问题](docs/FAQ.md) - 问题解答

### 开发文档
- [架构设计](docs/ARCHITECTURE.md) - 系统架构
- [Agent 集成](docs/AGENT_INTEGRATION.md) - AI Agent 开发
- [开发路线图](docs/ROADMAP.md) - 未来计划

### macOS 相关
- [macOS 开发](MACOS_DEVELOPMENT.md) - 开发进度
- [macOS 测试](docs/MACOS_TESTING.md) - 测试指南
- [macOS 部署](docs/MACOS_DEPLOYMENT.md) - 打包部署

---

## 🛠️ 开发

### 环境要求
- Python 3.8+
- Windows 10+ 或 macOS 10.15+

### 安装依赖

```bash
# Windows
pip install Pillow send2trash windnd

# macOS
pip3 install Pillow send2trash pyobjc-framework-Cocoa

# 开发依赖
pip install pytest flake8 black
```

### 运行测试

```bash
# Windows
python test_windows_features.py

# macOS
python3 test_macos.py

# 所有测试
pytest
```

### 代码规范

```bash
# 格式化
black meowdesk/

# 检查
flake8 meowdesk/
```

---

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 贡献指南
- 遵循 PEP 8 编码规范
- 添加单元测试
- 更新相关文档
- 提交前运行测试

---

## 📝 更新日志

### v1.4.0 (2026-05-27)
- 🎉 **新增 macOS 支持**（包括 Apple Silicon）
- 🏗️ **模块化重构**，建立清晰的架构
- 🤖 **AI Agent 框架**，支持扩展命令
- ✨ **Windows 功能完善**，右键菜单、系统托盘
- 📚 **完整文档**，15+ 文档文件

### v1.3.0 (2026-05-20)
- 重构代码结构
- 添加配置管理
- 优化动画性能

### v1.2.0 (2026-05-15)
- 添加 HTML 索引
- 支持 MD5 去重
- 优化截图识别

### v1.1.0 (2026-05-10)
- 添加多种动画状态
- 支持闲逛行为
- 添加气泡提示

### v1.0.0 (2026-05-01)
- 首次发布
- 基础文件分类功能

---

## 📄 许可证

[MIT License](LICENSE)

个人和非商业组织免费使用，商业使用需授权。

---

## 💖 赞赏支持

如果觉得好用，欢迎请作者喝杯咖啡 ☕

<p align="left">
  <img src="assets/sponsor-wechat.jpg" width="200" alt="微信赞赏" style="margin-right:20px">
  <img src="assets/sponsor-alipay.jpg" width="200" alt="支付宝赞赏">
</p>

---

## 🙏 致谢

感谢以下开源项目：
- [Pillow](https://python-pillow.org/) - 图像处理
- [PyObjC](https://pyobjc.readthedocs.io/) - macOS 支持
- [PyInstaller](https://pyinstaller.org/) - 打包工具
- [send2trash](https://github.com/arsenetar/send2trash) - 安全删除

---

## 📞 联系方式

- GitHub Issues: [提交问题](https://github.com/ra1nzzz/MeowDesk/issues)
- Discussions: [讨论区](https://github.com/ra1nzzz/MeowDesk/discussions)
- Email: support@meowdesk.com

---

<div align="center">

**Made with ❤️ by ra1nzzz**

⭐ 如果喜欢，请给个 Star！

</div>
