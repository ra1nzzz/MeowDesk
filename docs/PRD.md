# 妙喵桌宠 MeowDesk — 产品需求文档（PRD）

> 版本：1.0 ｜ 状态：基线补全 ｜ 关联文档：`ARCHITECTURE.md`、`ROADMAP.md`、`AGENT_INTEGRATION.md`

---

## 1. 产品概述

### 1.1 一句话定位

桌面拖拽文件自动分类归档工具 —— 拖进去，它搞定。

### 1.2 背景与问题

桌面和下载目录长期堆积截图、文档、安装包等杂乱文件，手动整理成本高、容易拖延。
MeowDesk 以一只悬浮在桌面右上角的猫猫为交互入口，将"整理文件"压缩为一次拖拽动作：

- 截图 → 自动移入回收站（按文件名规则识别）
- 其它文件 → 按类型 + 年月归档到 `归档根目录/类型/YYYY-MM/`
- 全部归档记录写入文件数据库，并生成可搜索的 HTML 导航页

### 1.3 目标用户

| 画像 | 核心诉求 |
|------|----------|
| 文件杂乱的普通办公用户 | 零学习成本、一拖即归档、能找回文件 |
| 截图重度用户（客服 / 测试 / 学生） | 截图自动回收，不污染归档 |
| 开发者 / 极客 | 可配置分类规则、可接入本地 AI Agent、可二次开发 |

### 1.4 平台范围

| 平台 | 级别 | 说明 |
|------|------|------|
| Windows 10/11 | P0 正式支持 | 完整功能（托盘、拖放、开机自启） |
| macOS | P2 实验支持 | 透明窗口 / 拖放 / 托盘可用，打包与权限适配进行中 |
| Linux | P3 社区维护 | 仅保证核心逻辑可运行 |

---

## 2. 功能需求

### 2.1 已交付功能（现状）

| 编号 | 功能 | 模块 | 状态 |
|------|------|------|------|
| F-01 | 悬浮拖拽窗口（置顶、可拖动、动画状态机） | `ui/window.py` 及拆分模块 | ✅ |
| F-02 | 文件分类（截图识别 + 扩展名映射 + 自定义分类） | `core/classifier.py` | ✅ |
| F-03 | 归档落盘（类型/年月目录、重名加序号、失败清理空目录） | `core/file_handler.py` | ✅ |
| F-04 | 文件数据库（JSON、搜索/统计/最近记录） | `core/database.py` | ✅ |
| F-05 | HTML 导航页生成（暗色主题、搜索、分类筛选） | `index_gen.py` | ✅ |
| F-06 | 配置管理（类型化 AppConfig、原子写入、损坏备份恢复） | `core/config.py` + `utils/io.py` | ✅ |
| F-07 | 系统托盘 / 开机自启 / 一键安装 | `install.py`、platform 层 | ✅ Windows |
| F-08 | AI 助手（HTTP + OpenClaw CLI 双通道、内置命令、聊天窗口） | `agent/` + `ui/chat.py` | 🚧 实验 |
| F-09 | 提醒系统（节日 / 周期提醒 / 气泡） | `window_reminders.py` | ✅ |

### 2.2 本次迭代补全的需求（缺口分析）

审计代码与 ROADMAP 后确认的缺口，按严重度排列：

#### A. 缺陷修复（P0 — 影响可用性）

| 编号 | 缺陷 | 影响 | 验收标准 |
|------|------|------|----------|
| BUG-01 | `platform/macos.py` 使用 `subprocess` 但未导入 | macOS 引导用户开启"完全磁盘访问"时直接 NameError 崩溃 | 调用 `_open_full_disk_access_settings` 不抛 NameError |
| BUG-02 | `ui/chat.py` 异常回调 `lambda: ...str(e)` 晚绑定 | 聊天请求一旦出错，错误处理本身再抛 NameError，用户看不到任何提示 | 异常路径正确弹出错误消息 |
| BUG-03 | `ui/settings.py` "测试连接"以 dict 构造 `AgentGateway`（期望 `AgentConfig`） | 点击按钮即 AttributeError | 移除无用构造，连通性测试仅走 requests |
| BUG-04 | `agent/gateway.py::get_suggestions` 末尾存在 `return` 后的重复不可达代码块 | 死代码、误导维护者 | 函数只有一份逻辑 |
| BUG-05 | `agent/gateway.py::is_available` 使用裸 `except:` | 吞掉 `KeyboardInterrupt`/`SystemExit` | 仅捕获预期异常 |
| BUG-06 | `agent/gateway.py::execute_command` 对非 dict 的 `data` 直接 `**` 展开 | Agent 返回 list/null 时 TypeError | 非 dict 响应安全降级为错误返回 |
| BUG-07 | `ui/menu_actions.py` 中 `action_open_chat`、`action_show_about` 重复定义 2–3 次 | 行为由"最后定义"隐式决定，易引发回归 | 每个 action 仅一份定义，保留现行为 |

#### B. 测试补全（P1 — ROADMAP 阶段 2 未勾选项）

| 编号 | 需求 | 验收标准 |
|------|------|----------|
| TEST-01 | `agent/gateway.py` mock 单元测试 | 覆盖：禁用态、HTTP 成功（OpenAI 格式 / 简单格式）、HTTP 失败、超时、CLI 降级、`execute_command` 异常响应、`get_suggestions` |
| TEST-02 | `platform/base.py` 抽象契约测试 | 覆盖：抽象方法不可实例化、回调注册器、`set_size` 等具体方法默认行为 |

#### C. 质量门禁（P1 — ROADMAP 阶段 2 未勾选项）

| 编号 | 需求 | 验收标准 |
|------|------|----------|
| CI-01 | 引入 ruff 配置（`pyproject.toml`），清理现存 F 级问题（未使用导入/变量、重复定义、未定义名称） | `ruff check` 通过 |
| CI-02 | GitHub Actions 增加 lint job | push / PR 自动执行 `ruff check` |

#### D. 文档同步（P2）

| 编号 | 需求 | 验收标准 |
|------|------|----------|
| DOC-01 | 新增本 PRD | 产品定位、功能矩阵、缺口与验收标准单一可信来源 |
| DOC-02 | ROADMAP 与代码现状同步 | "待修"中已实现项（归档失败清理空目录、`ConfigManager.set` 日志、原子写入、备份恢复）勾选；阶段 2 新完成项更新 |

### 2.3 明确不做（本次迭代范围外）

- `ui/window.py` 进一步拆分（阶段 3，已在历史提交中大幅推进）
- SQLite 迁移、异步文件操作、HTML 增量生成（阶段 8）
- macOS 打包流水线 / DMG（阶段 5–6）
- 插件系统与云同步（阶段 10）

---

## 3. 非功能需求

| 类别 | 要求 |
|------|------|
| 可靠性 | 配置与数据库写入必须原子化（已实现 tmp + `os.replace`）；损坏 JSON 自动回退备份 |
| 可测试性 | 核心与 agent 逻辑不依赖 GUI；测试可在无显示环境（CI）运行，Tk 相关用例自动 skip |
| 兼容性 | Python 3.11+；`requests` 缺失时降级 urllib；Windows-only 依赖（windnd）可选 |
| 安全 | 不裸捕获 BaseException；Agent API key 仅存本地配置 |
| 工程质量 | 提交原子化；CI 必须含 pytest（3 平台 × 2 Python 版本）+ ruff lint |

---

## 4. 实施计划（PLAN）

按依赖排序的原子提交序列，每一步独立可回滚、测试保持绿色：

1. **docs(prd)** — 新增本 PRD（DOC-01）
2. **fix(platform)** — macos.py 补 `subprocess` 导入（BUG-01）
3. **fix(ui)** — chat.py lambda 晚绑定修复（BUG-02）
4. **fix(ui)** — menu_actions 去重 + settings 死构造移除（BUG-03、BUG-07）
5. **fix(agent)** — gateway 死代码 / 裸 except / execute_command 加固（BUG-04~06）
6. **test(agent)** — gateway mock 测试（TEST-01）
7. **test(platform)** — base 契约测试（TEST-02）
8. **chore(lint)** — ruff 配置 + 清理 F 级存量问题（CI-01）
9. **ci** — lint job 接入 GitHub Actions（CI-02）
10. **docs(roadmap)** — 同步路线图（DOC-02）

### 验收口径

- `python -m pytest -q` 全绿（用例数 ≥ 基线 117）
- `ruff check meowdesk/ tests/` 0 错误
- ROADMAP 阶段 2 的"质量门禁 / 单元测试"小节与实际一致
