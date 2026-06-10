# MeowDesk 架构文档

## 项目结构

```
meowdesk/
├── __init__.py
│
├── core/                       # 与平台无关的核心逻辑
│   ├── __init__.py
│   ├── types.py                # 共享 dataclass / enum（AppConfig、FileRecord、...）
│   ├── config.py               # ConfigManager：配置加载/合并/保存
│   ├── database.py             # FileDatabase：JSON 文件形式的记录库
│   ├── classifier.py           # FileClassifier：分类与截图识别
│   └── file_handler.py         # FileHandler：归档/回收/MD5
│
├── agent/                      # AI Agent 集成
│   ├── __init__.py
│   ├── gateway.py              # AgentGateway：HTTP + CLI 适配
│   └── commands.py             # CommandRegistry：内置命令注册表
│
├── platform/                   # 平台抽象层
│   ├── __init__.py
│   ├── base.py                 # PlatformWindow 抽象基类
│   ├── windows.py              # WindowsWindow（windnd + UpdateLayeredWindow）
│   └── macos.py                # MacOSWindow（PyObjC + Cocoa）
│
├── ui/                         # Tk 风格 UI 组件
│   ├── __init__.py             # 顶层导出（ContextMenu / Tray / Settings 等按需懒加载）
│   ├── window.py               # MeowWindow：主控制器（事件路由 + 平台窗口生命周期）
│   ├── window_state.py         # WindowState：状态机 + timer + 闲逛行为
│   ├── window_drop.py          # FileDropHandler：拖入文件 → 分类 → 归档/回收
│   ├── window_reminders.py     # ReminderChecker：定时提醒 + 经期提醒
│   ├── animation.py            # AnimationManager：APNG 帧解析
│   ├── animation_loop.py       # AnimationLoop：单帧 tick（state/wander/render），win32 与 macOS 共享
│   ├── tray.py                 # SystemTray：系统托盘
│   ├── menu.py                 # ContextMenu：右键菜单
│   ├── settings.py             # SettingsPanel：设置面板
│   ├── chat.py                 # ChatWindow：AI 对话窗口
│   └── macos_settings.py       # macOS 专属设置面板
│
├── utils/                      # 跨模块工具
│   ├── __init__.py             # 导出 get_logger / atomic_write_* / load_json_with_backup
│   ├── logger.py               # 配置 meowdesk.* 日志器
│   └── io.py                   # atomic_write_text / atomic_write_json / load_json_with_backup
│
└── （入口）meowdesk_main.py    # 启动主程序
```

> `ui/dialog.py` 与 `utils/` 子目录已合并入上面的结构。`window.py` 在 P1 重构里
> 拆成了 `MeowWindow + WindowState + FileDropHandler + ReminderChecker`，每个模块
> 都可独立单元测试。

## 模块说明

### 1. Core 核心模块

#### ConfigManager
- 管理应用配置（`config.json`）
- 默认配置与用户配置合并
- 兼容旧接口 `get` / `set`
- 见 `meowdesk/core/config.py`

#### FileDatabase
- 文件归档记录管理
- 支持搜索、统计、最近记录
- JSON 格式存储（计划迁移到 SQLite）
- 见 `meowdesk/core/database.py`

#### FileClassifier
- 智能文件分类（按扩展名）
- 截图识别（文件名 / 路径 / 屏幕分辨率）
- 可扩展的分类规则
- 见 `meowdesk/core/classifier.py`

#### FileHandler
- 文件归档（按 `类型/年-月/`）
- 回收站（`send2trash`）
- 重名文件加序号
- MD5 / 文件大小工具方法
- 见 `meowdesk/core/file_handler.py`

#### types
- 共享 dataclass：`AppConfig`、`CategoryConfig`、`AgentConfig`、`Reminder`、`PeriodConfig`、`PeriodRecord`、`ClassifyResult`、`FileRecord`、`ArchiveResult`、`ProcessResult`
- 共享 enum：`FileAction`、`AgentType`、`Platform`
- 平台检测工具 `get_platform()`
- 见 `meowdesk/core/types.py`

### 2. Agent AI 集成模块

#### AgentGateway
- 统一接口连接本地 AI Agent
- 优先 HTTP，回退到 CLI（OpenClaw）
- 健康检查自动尝试多路径
- 见 `meowdesk/agent/gateway.py`

#### CommandRegistry
- 内置命令注册表
- 装饰器 API：`@registry.register_command('name')`
- 常用命令：
  - `clean_disk`：清理超过 7 天的临时文件
  - `check_date`：日期 / 距离周末 / 距离月底
  - `check_holidays`：假期倒计时
  - `period_reminder`：经期提醒
  - `system_info`：系统信息（依赖 psutil）
  - `open_app`：打开应用
- 见 `meowdesk/agent/commands.py`

### 3. Platform 跨平台模块

#### PlatformWindow (基类)
- 定义统一的窗口接口
- 抽象平台差异
- 见 `meowdesk/platform/base.py`

#### WindowsWindow
- Windows 平台实现
- `windnd` 拖放
- `UpdateLayeredWindow` 透明渲染
- 见 `meowdesk/platform/windows.py`

#### MacOSWindow
- macOS 平台实现
- `PyObjC + Cocoa` 透明窗口
- 原生拖放（`draggingEntered` / `performDragOperation_`）
- 见 `meowdesk/platform/macos.py`

## 数据流

```
用户拖入文件
    ↓
PlatformWindow.on_drop (Windows: windnd | macOS: draggingEntered)
    ↓
MeowWindow._on_files_dropped
    ↓
FileDropHandler.receive (utils/logger 记录条数)
    ↓
后台线程 → FileDropHandler._process
    ↓
FileDropHandler._process_one
    ↓
FileClassifier.classify (分类)
    ↓
FileHandler.archive_file / recycle_file (处理)
    ↓
FileDatabase.add_record (记录；保存走 atomic_write_json)
    ↓
on_finished 回调 → _update_html → 生成 HTML 索引（_gen_html.py 脚本）
```

## 状态机

`MeowWindow` 不再直接持有 `state` / `frame_index` / `timer` 字段 —— 这些都被
`WindowState` 收编。每个动画 tick 由 `MeowWindow._animate` 触发一次
`WindowState.update()` + `WindowState.wander_tick()`，再由
`ReminderChecker.tick()` 决定要不要弹气泡。`WindowState.enter_state(SHY, timer=N)`
是各事件（点击、拖入、拖动结束）切换状态与设置 timer 的统一入口。

## 动画循环

`AnimationLoop` 抽出了 `_animate` 与 `_macos_animate` 共享的每帧工作
（状态机推进、闲逛、提醒 tick、取帧、画气泡、尺寸同步、渲染），
两个平台层只负责**调度**——win32 用 `root.after`，macOS 用 `NSTimer`。
设置保存时如果 `scale` 变化需要重建 `AnimationManager`，`MeowWindow` 会同步
重建 `AnimationLoop`，让尺寸缓存与新动画对齐。

## 持久化

- `ConfigManager._save` / `FileDatabase.save` 走 `meowdesk.utils.io.atomic_write_json`：
  写入临时文件 → `os.fsync` → `os.replace`，避免半写文件。
- 加载时若 JSON 损坏，`load_json_with_backup` 会把损坏文件旋转为 `.bak`，
  然后尝试 `.bak` / `.bak.1` / `.bak.2` 的回退链，全部失败再返回 `None`。
- 所有 `print(...)` 都改走 `meowdesk.utils.logger.get_logger(__name__)`，错误
  信息不再混杂到 stdout。

## Agent 交互流程

```
用户双击宠物 / 触发对话
    ↓
ChatWindow 弹出
    ↓
用户输入消息或点击快捷命令
    ↓
AgentGateway.chat
    ↓
1) HTTP POST /v1/chat/completions
2) 失败时回退到 CLI（OpenClaw）
    ↓
返回结果并显示
```

## 配置文件

### `config.json`
```json
{
  "archive_dir": "D:\\meow-file",
  "temp_dir": "D:\\meow-temp",
  "window_opacity": 0.85,
  "auto_open_html": false,
  "screenshot_action": "recycle",
  "window_position": [1516, 430],
  "scale": 0.5,
  "categories": { ... },
  "agent": {
    "enabled": true,
    "agent_type": "openclaw",
    "endpoint": "http://localhost:8080",
    "api_key": "",
    "timeout": 30
  },
  "reminders": [],
  "period": {
    "enabled": false,
    "cycle_days": 28,
    "period_days": 5,
    "last_period_start": "",
    "records": []
  }
}
```

## 扩展点

1. **自定义分类器**：继承 `FileClassifier` 覆盖 `classify` / `_is_screenshot`
2. **自定义命令**：`@registry.register_command('name')` 注册
3. **新平台支持**：实现 `PlatformWindow` 接口
4. **Agent 适配器**：在 `AgentGateway` 增加协议分支

## 已知架构问题（待改进）

1. `ui/window.py` 内右键菜单/聊天气泡等仍有少量平台分支未抽出 —— 下一步可
   把 macOS 的 `show_context_menu` 移到一个独立的 menu helper。

## 已完成的 P1 改进

- ✅ `ui/window.py` 拆分（`WindowState` / `FileDropHandler` / `ReminderChecker`）
- ✅ 动画循环去重：`AnimationLoop` 抽出 win32/macOS 共享的单帧逻辑
- ✅ `meowdesk.utils` 包 + `logger.py` + `io.py`（原子写入 + 备份回退）
- ✅ 所有 `print(...)` 改走 `logging`（包括 `meowdesk_main.py`）
- ✅ `ConfigManager.set` 拒绝未知 key 并 warning；`get` 用哨兵区分"缺字段"与"显式 None"
- ✅ `FileHandler.archive_file` 失败时清理残留的空分类目录
- ✅ `AppConfig` 字段映射自动化：`from_dict` / `to_dict` 把"序列化"和"配置结构"放一处
- ✅ `_gen_html.py` 迁移为 `meowdesk/index_gen` 模块（正规 import，支持测试）

## 已完成的 P2 改进

- ✅ `ui/window.py` 右键菜单动作抽出为 `ui/menu_actions.py`（平台分支简化）
- ✅ 平台字体加载抽出为 `ui/bubble_font.py`
- ✅ `ensure_archive_dir_writable` 统一为模块函数
- ✅ 气泡绘制抽出为 `ui/bubble_renderer.py`
- ✅ macOS 动画定时器抽出为 `ui/macos_animation.py`（window.py 296 行，原始 513 行）

## 安全考虑

1. **路径验证**：未来需要防止路径遍历攻击
2. **文件大小限制**：避免处理超大文件
3. **权限检查**：确保有足够权限操作文件
4. **Agent 认证**：API Key 验证（已支持 `Authorization: Bearer` 头）
