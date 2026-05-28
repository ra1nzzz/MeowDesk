# MeowDesk v2 重构计划（Rearchitecture Plan）

## 目标

将 MeowDesk 从：

- 单脚本桌面工具
- 强耦合 Windows Python 应用
- 难以维护的 MVP

升级为：

- 可长期维护的桌面平台
- AI Agent 友好的工程系统
- 插件化文件自动化引擎
- 可扩展的跨平台 Runtime

---

# 一、当前架构问题

## 1. 单脚本职责过重

当前问题：

- install.py 同时承担安装、状态、系统逻辑
- UI / 文件分类 / 系统调用耦合
- 缺少明确模块边界

导致：

- 功能扩展成本高
- AI Agent 难以安全修改
- bug 修复容易引发连锁问题

---

## 2. Windows 强耦合

当前存在：

- 注册表直接调用
- PowerShell 逻辑内嵌
- 硬编码路径
- Python 路径绑定

导致：

- 无法迁移到 Mac/Linux
- 环境兼容性差
- 打包与部署成本高

---

## 3. 缺少核心 Runtime 层

当前逻辑：

```text
拖拽文件 → if/else → 移动文件
```

问题：

- 无事件系统
- 无 Pipeline
- 无插件机制
- 无 Hook

后期 AI / OCR / embedding 很难接入。

---

# 二、v2 架构目标

## 总体结构

```text
MeowDesk/
│
├── core/
│   ├── classifier/
│   ├── rules/
│   ├── indexer/
│   ├── events/
│   └── models/
│
├── runtime/
│   ├── watcher/
│   ├── dispatcher/
│   ├── pipeline/
│   └── plugin_manager/
│
├── platform/
│   ├── windows/
│   └── mac/
│
├── ui/
│   ├── pet/
│   ├── animation/
│   └── tray/
│
├── plugins/
│   ├── screenshot_detector/
│   ├── ai_classifier/
│   ├── duplicate_cleaner/
│   └── ocr/
│
├── infra/
│   ├── fs/
│   ├── db/
│   ├── logger/
│   ├── config/
│   └── cache/
│
└── cli/
```

---

# 三、核心设计思想

## 1. 事件驱动（Event Driven）

从：

```text
函数直接调用
```

升级为：

```text
事件 → Pipeline → Plugin → Action
```

例如：

```text
FileDroppedEvent
  ↓
ClassifierPipeline
  ↓
ScreenshotPlugin
  ↓
ArchiveAction
```

优势：

- 易扩展
- 易调试
- 易测试
- AI 能更稳定参与开发

---

## 2. Plugin First

插件接口：

```python
class Plugin:
    def on_event(self, event):
        pass
```

所有高级功能：

- AI 分类
- OCR
- embedding
- 自动标签
- 云同步

全部插件化。

优势：

- 功能扩展成本降低
- 不破坏核心 Runtime
- 可形成插件生态

---

## 3. Runtime 与 UI 解耦

当前：

```text
桌宠 = 系统本体
```

升级后：

```text
UI 只是 Runtime 的展示层
```

Runtime 可独立运行：

- CLI
- 后台服务
- Tray App
- Headless 模式

都可共用同一核心。

---

# 四、阶段性重构计划

---

## Phase 1：基础解耦（1-2 天）

目标：

- 降低耦合
- 建立模块边界

工作内容：

- 拆分 install.py
- 引入 config 模块
- 引入 logger
- 提取 classifier
- 建立 core/infra 目录

预期收益：

- 代码可维护性提升
- 减少未来重构成本

ROI：高

---

## Phase 2：事件系统（3-5 天）

目标：

- 建立 Runtime Core

工作内容：

- EventBus
- Dispatcher
- Pipeline
- Watcher
- Action System

预期收益：

- 复杂度停止指数增长
- 支持未来 AI 功能接入

ROI：非常高

---

## Phase 3：插件系统（5-10 天）

目标：

- 平台化

工作内容：

- PluginManager
- 动态加载
- Hook System
- 插件生命周期

预期收益：

- 扩展能力大幅提升
- AI Agent 更易协作开发

ROI：极高

---

## Phase 4：AI 能力层（长期）

目标：

- 智能化

工作内容：

- embedding 分类
- OCR
- LLM rule engine
- 智能标签
- 重复文件检测

预期收益：

- 从工具升级为智能桌面系统

ROI：战略级

---

# 五、技术选型建议

## 推荐保留

- Python
- PyQt5 / PySide6
- Pillow
- send2trash

---

## 推荐新增

### 工程能力

- pydantic
- watchdog
- loguru
- pytest

### AI 能力

- sentence-transformers
- rapidocr
- faiss

---

# 六、工程规范建议

## 必须增加

### 1. 类型系统

建议：

- dataclass
- TypedDict
- Enum
- pydantic

---

### 2. 测试结构

```text
tests/
  unit/
  integration/
```

---

### 3. CI

建议：

- Ruff
- Black
- Pytest
- GitHub Actions

---

# 七、ROI 评估

## 当前状态

| 项目 | 状态 |
|------|------|
| 开发效率 | 中 |
| 维护成本 | 持续上升 |
| AI 可协作性 | 低 |
| 扩展能力 | 差 |

---

## 重构后

| 项目 | 变化 |
|------|------|
| 功能开发成本 | ↓ 60-80% |
| Bug 修复风险 | ↓ 50% |
| AI 接入成本 | ↓ 70% |
| 功能扩展能力 | 大幅提升 |
| 长期维护性 | 明显改善 |

---

# 八、最终目标

MeowDesk 不再只是：

```text
桌宠整理工具
```

而是：

```text
AI Native Desktop Automation Platform
```

即：

- 文件自动化 Runtime
- 桌面 AI Agent 平台
- 插件化桌面操作系统

这是 MeowDesk 长期价值真正所在。
