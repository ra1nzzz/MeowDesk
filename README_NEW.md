# 妙喵桌宠 MeowDesk 🐱

> 智能桌面文件分类归档工具 + AI 助手

把文件拖到桌面猫猫身上，自动分类归档；双击对话，AI 助手帮你处理日常任务。

![screenshot](assets/idle.apng)

---

## ✨ 特性

### 📁 智能文件管理
- **悬浮拖拽区** — 桌面猫猫图标，拖入文件即自动整理
- **智能分类** — 截图自动回收，其它文件按类型归档（文档/图片/视频/音频/代码等）
- **日期归档** — 按 `类型/年-月/` 目录结构存放
- **HTML 导航** — 自动生成暗色主题文件索引页面，支持搜索、筛选、定位

### 🤖 AI 助手集成
- **本地 Agent** — 连接 OpenClaw、Hermes 等本地 AI
- **智能对话** — 双击宠物即可对话
- **快捷命令** — 磁盘清理、日期查询、假期提醒、经期提醒等
- **工作助手** — TODO 管理、旅行规划、系统监控

### 🎨 跨平台支持
- **Windows** — 完整支持，透明窗口 + 拖放
- **macOS** — Apple Silicon 原生支持（v1.4.0+）
- **动画丰富** — idle / happy / shy / surprised / sleeping 等状态

---

## 🚀 快速开始

### Windows

#### 方式一：下载 EXE（推荐）
1. 从 [Releases](https://github.com/ra1nzzz/MeowDesk/releases) 下载最新版
2. 解压或直接运行 `MeowDesk-standalone.exe`
3. 首次运行会生成配置文件

#### 方式二：Python 运行
```bash
# 安装依赖
pip install Pillow send2trash windnd

# 运行
python lingxi_droplet.py
```

### macOS

```bash
# 安装依赖
pip install Pillow send2trash pyobjc-framework-Cocoa

# 运行
python meowdesk_main.py
```

或下载 `.dmg` 安装包（v1.4.0+）

---

## 📖 使用指南

### 基础操作
1. **拖入文件** — 拖到猫猫身上自动归档
2. **双击对话** — 与 AI 助手交流
3. **右键菜单** — 打开导航页、设置、退出
4. **拖动位置** — 猫猫可拖到任意位置，自动记忆

### AI 助手命令
- `清理磁盘` — 清理临时文件
- `今天星期几` — 查询日期信息
- `下个假期` — 查看即将到来的假期
- `经期提醒` — 女性健康提醒（需配置）
- `系统信息` — 查看 CPU、内存、磁盘使用

### 配置 AI Agent

编辑 `config.json`：
```json
{
  "agent": {
    "enabled": true,
    "agent_type": "openclaw",
    "endpoint": "http://localhost:8080",
    "api_key": "",
    "timeout": 30
  }
}
```

---

## 🏗️ 架构

```
meowdesk/
├── core/           # 核心功能（配置、数据库、分类、文件处理）
├── agent/          # AI Agent 集成（网关、命令）
├── platform/       # 跨平台抽象（Windows、macOS）
├── ui/             # UI 模块（窗口、动画、托盘）
└── utils/          # 工具模块（日志、辅助函数）
```

详见 [架构文档](docs/ARCHITECTURE.md)

---

## 📚 文档

- [架构设计](docs/ARCHITECTURE.md)
- [macOS 支持](docs/MACOS_SUPPORT.md)
- [AI Agent 集成](docs/AGENT_INTEGRATION.md)
- [开发路线图](docs/ROADMAP.md)

---

## 🛠️ 开发

### 环境要求
- Python 3.9+
- Windows 10+ 或 macOS 11+

### 安装开发依赖
```bash
pip install -r requirements-dev.txt
```

### 运行测试
```bash
pytest tests/ -v
```

### 代码检查
```bash
flake8 meowdesk/
black meowdesk/
```

---

## 🗺️ 路线图

- [x] v1.0 - 基础文件归档
- [x] v1.1 - HTML 导航页
- [x] v1.2 - 截图识别
- [x] v1.3 - 模块化重构
- [ ] v1.4 - macOS 支持
- [ ] v1.5 - AI Agent 集成
- [ ] v1.6 - 性能优化
- [ ] v2.0 - 插件系统

详见 [ROADMAP.md](docs/ROADMAP.md)

---

## 🤝 贡献

欢迎贡献代码、报告 Bug、提出建议！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 许可证

[非商业免费使用许可证](LICENSE) — 个人和非商业组织免费使用，商业使用需授权。

---

## 💖 赞赏支持

如果觉得好用，欢迎请作者喝杯咖啡 ☕

<p align="left">
  <img src="assets/sponsor-wechat.jpg" width="200" alt="微信赞赏" style="margin-right:20px">
  <img src="assets/sponsor-alipay.jpg" width="200" alt="支付宝赞赏">
</p>

---

## 🔗 相关链接

- [GitHub 仓库](https://github.com/ra1nzzz/MeowDesk)
- [问题反馈](https://github.com/ra1nzzz/MeowDesk/issues)
- [讨论区](https://github.com/ra1nzzz/MeowDesk/discussions)

---

**Made with ❤️ by ra1nzzz**
