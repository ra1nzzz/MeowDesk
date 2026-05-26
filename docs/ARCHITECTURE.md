# MeowDesk 架构文档

## 项目结构

```
meowdesk/
├── core/                   # 核心功能模块
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── database.py        # 文件数据库
│   ├── classifier.py      # 文件分类器
│   └── file_handler.py    # 文件处理
│
├── agent/                  # AI Agent 集成
│   ├── __init__.py
│   ├── gateway.py         # Agent 网关
│   └── commands.py        # 内置命令
│
├── platform/               # 跨平台抽象层
│   ├── __init__.py
│   ├── base.py            # 平台基类
│   ├── windows.py         # Windows 实现
│   └── macos.py           # macOS 实现
│
├── ui/                     # UI 模块（待实现）
│   ├── __init__.py
│   ├── window.py          # 窗口管理
│   ├── animation.py       # 动画系统
│   ├── tray.py            # 系统托盘
│   └── dialog.py          # 对话框
│
└── utils/                  # 工具模块（待实现）
    ├── __init__.py
    ├── logger.py          # 日志系统
    └── helpers.py         # 辅助函数
```

## 模块说明

### 1. Core 核心模块

#### ConfigManager
- 管理应用配置（config.json）
- 支持默认配置和用户配置合并
- 提供配置读写接口

#### FileDatabase
- 管理文件归档记录
- 支持搜索、统计、查询
- JSON 格式存储（未来可迁移到 SQLite）

#### FileClassifier
- 智能文件分类
- 截图识别（文件名、路径、分辨率）
- 可扩展的分类规则

#### FileHandler
- 文件归档操作
- 回收站管理
- 重名文件处理
- MD5 计算

### 2. Agent AI 集成模块

#### AgentGateway
- 统一接口连接本地 AI Agent
- 支持 OpenClaw、Hermes 等
- 提供对话、命令执行、智能建议

#### CommandRegistry
- 内置命令注册表
- 常用工具命令：
  - `clean_disk`: 磁盘清理
  - `check_date`: 日期查询
  - `check_holidays`: 假期提醒
  - `period_reminder`: 经期提醒
  - `system_info`: 系统信息
  - `open_app`: 打开应用

### 3. Platform 跨平台模块

#### PlatformWindow (基类)
- 定义统一的窗口接口
- 抽象平台差异

#### WindowsWindow
- Windows 平台实现
- 使用 UpdateLayeredWindow 实现透明窗口
- 支持 windnd 拖放

#### MacOSWindow
- macOS 平台实现
- 使用 PyObjC + Cocoa
- 支持原生拖放

## 数据流

```
用户拖入文件
    ↓
PlatformWindow.on_drop
    ↓
FileClassifier.classify (分类)
    ↓
FileHandler.archive_file / recycle_file (处理)
    ↓
FileDatabase.add_record (记录)
    ↓
生成 HTML 索引
```

## Agent 交互流程

```
用户双击宠物
    ↓
显示对话框
    ↓
用户输入 / 选择命令
    ↓
AgentGateway.chat / execute_command
    ↓
本地 Agent 处理
    ↓
返回结果并显示
```

## 配置文件

### config.json
```json
{
  "archive_dir": "D:\\meow-file",
  "temp_dir": "D:\\meow-temp",
  "window_opacity": 0.85,
  "auto_open_html": false,
  "screenshot_action": "recycle",
  "window_position": [1516, 430],
  "categories": { ... },
  "agent": {
    "enabled": true,
    "agent_type": "openclaw",
    "endpoint": "http://localhost:8080",
    "api_key": "",
    "timeout": 30
  },
  "period_reminder": {
    "enabled": false,
    "last_date": "2026-05-01",
    "cycle_days": 28
  }
}
```

## 扩展点

1. **自定义分类器**：继承 `FileClassifier` 实现自定义规则
2. **自定义命令**：通过 `CommandRegistry.register()` 注册
3. **新平台支持**：实现 `PlatformWindow` 接口
4. **Agent 适配器**：实现 `AgentGateway` 的协议转换

## 性能优化

1. **异步文件操作**：使用 `threading` 或 `asyncio`
2. **增量 HTML 生成**：只更新新增记录
3. **APNG 懒加载**：按需解码帧
4. **数据库索引**：迁移到 SQLite 后添加索引

## 安全考虑

1. **路径验证**：防止路径遍历攻击
2. **文件大小限制**：避免处理超大文件
3. **权限检查**：确保有足够权限操作文件
4. **Agent 认证**：API Key 验证
