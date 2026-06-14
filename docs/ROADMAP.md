# MeowDesk 开发路线图

> 状态说明：
> - ✅ 已完成
> - 🚧 进行中 / 部分完成
> - ⏳ 计划中

## 阶段 0：基线修正（进行中）

- [x] 修正 `README.md` 启动入口
- [x] 同步 `docs/ARCHITECTURE.md` 与真实代码结构
- [x] 同步 `docs/ROADMAP.md` 与真实完成度
- [x] 同步 `docs/AGENT_INTEGRATION.md` 与真实接口
- [x] 引入 `pytest` 并为核心模块添加单元测试（37 个用例）
- [x] 添加 GitHub Actions 测试 CI（`ci.yml`）

---

## 阶段 1：模块化重构（已完成）

- [x] 创建 `meowdesk` 包结构
- [x] 核心模块拆分
  - [x] `core/config.py` - 配置管理
  - [x] `core/database.py` - 数据库
  - [x] `core/classifier.py` - 文件分类
  - [x] `core/file_handler.py` - 文件处理
- [x] Agent 集成框架
  - [x] `agent/gateway.py` - Agent 网关
  - [x] `agent/commands.py` - 内置命令
- [x] 平台抽象层
  - [x] `platform/base.py` - 基类
  - [x] `platform/windows.py` - Windows 实现
  - [x] `platform/macos.py` - macOS 实现
- [x] 文档编写
  - [x] 架构文档
  - [x] macOS 支持指南
  - [x] Agent 集成指南

---

## 阶段 2：质量与可维护性（进行中）

### 单元测试
- [x] `core/config.py` 单元测试
- [x] `core/database.py` 单元测试
- [x] `core/classifier.py` 单元测试
- [x] `core/file_handler.py` 单元测试
- [x] `agent/commands.py` 纯逻辑测试
- [x] `agent/gateway.py` mock 测试（`tests/test_gateway.py`，22 用例）
- [x] `platform/base.py` 抽象契约测试（`tests/test_platform_base.py`，25 用例）
- [ ] UI 组件行为测试

### 质量门禁
- [x] GitHub Actions：单元测试
- [x] GitHub Actions：lint（ruff，`select=[F]`，可增量启用 E/W/I/B/UP）
- [ ] GitHub Actions：mypy（先覆盖 `core/`）

### 已修复
- [x] `period_reminder` 中 `coming_soon` 与 `overdue` 分支顺序错误（已修：先判 `< 0` 再判 `<= 3`）
- [x] `FileHandler.archive_file` 失败时残留空目录（`_cleanup_empty_category_dir` 逐级清理空父目录）
- [x] `ConfigManager.set` 拒绝未声明字段时已输出 `_log.warning`
- [x] 配置 / 数据库原子写入（`utils/io.atomic_write_json`，tmp + `os.replace`）
- [x] 损坏 JSON 自动回退备份（`utils/io.load_json_with_backup`）
- [x] `platform/macos.py` 缺失 `subprocess` 导入（开启完全磁盘访问时崩溃）
- [x] `ui/chat.py` 异常回调 lambda 晚绑定 `NameError`
- [x] `ui/menu_actions.py` `action_open_chat` / `action_show_about` 重复定义
- [x] `ui/settings.py` 测试连接以 dict 构造 `AgentGateway` 的死代码
- [x] `agent/gateway.py` `get_suggestions` 不可达重复代码 / 裸 `except` / `execute_command` 非 dict 响应崩溃
- [x] `platform/base.py` `on_drag_enter/exit_callback` 未在 `__init__` 初始化

---

## 阶段 3：核心窗口拆分（P1）

- [ ] 拆分 `meowdesk/ui/window.py`（约 980 行）
  - [ ] `window_controller.py`：主流程编排
  - [ ] `window_state.py`：状态机与计时器
  - [ ] `window_drop.py`：拖拽与文件处理流程
  - [ ] `window_reminders.py`：提醒逻辑
- [ ] 平台层只保留视图能力
- [ ] MeowWindow 收敛为协调器（< 300 行）

---

## 阶段 4：日志与异常恢复（P1）

- [ ] 用 `logging` 替换主要 `print`
- [ ] 区分用户提示日志和开发日志
- [ ] 文件处理失败统一错误信息
- [ ] 配置文件原子写入（tmp + replace）
- [ ] 数据库原子写入
- [ ] 损坏 JSON 备份恢复
- [ ] 配置版本号与迁移入口

---

## 阶段 5：跨平台稳定性（P2）

- [ ] Windows 完整测试矩阵（Win10 / Win11）
- [ ] macOS 行为测试（已在 `test_macos.py` 中有 smoke，需迁到 pytest）
- [ ] Linux 文档与最小支持说明
- [ ] macOS 自动构建流水线（py2app / PyInstaller）

---

## 阶段 6：macOS 完整支持（P2）

- [ ] 完善 `MacOSWindow` 行为
- [ ] 系统托盘（NSStatusBar）
- [ ] 文件操作权限适配
- [ ] 打包 `.app` / DMG

---

## 阶段 7：AI Agent 集成（P2）

### 已完成
- [x] `AgentGateway` HTTP + CLI 双模式
- [x] 内置命令：`clean_disk` / `check_date` / `check_holidays` / `period_reminder` / `system_info` / `open_app`
- [x] `ChatWindow` UI

### 待完善
- [ ] 文档与代码中的接口路径一致
- [ ] OpenClaw / Hermes 适配器显式分支
- [ ] AI 端到端集成测试（mock 化）
- [ ] 错误恢复与离线降级

---

## 阶段 8：性能优化（P2）

- [ ] 异步文件操作（`threading` / `asyncio`）
- [ ] HTML 索引增量生成
- [ ] APNG 懒加载与帧缓存
- [ ] 数据库迁移到 SQLite（含数据迁移脚本）

---

## 阶段 9：高级功能（P3）

- [ ] 文件预览（缩略图 / 视频 / 文档）
- [ ] 高级搜索（时间范围 / 大小 / 标签）
- [ ] 统计分析（图表、报告导出）
- [ ] 自动化规则引擎

---

## 阶段 10：插件系统（P3，长期）

- [ ] 插件 API 设计
- [ ] 插件加载器与沙箱
- [ ] 云同步插件（OneDrive / 阿里云盘）
- [ ] 第三方集成（Notion / Obsidian）

---

## 优先级总结

### P0 — 必须完成
- 模块化重构 ✅
- 单元测试 + CI ✅
- 文档校正 ✅

### P1 — 重要功能
- 拆分 `ui/window.py`
- 日志与原子写入
- 错误恢复策略

### P2 — 增强功能
- macOS 完整支持
- 性能优化与 SQLite
- Agent 生态完善

### P3 — 长期规划
- 高级搜索 / 预览
- 插件系统
- 云同步
