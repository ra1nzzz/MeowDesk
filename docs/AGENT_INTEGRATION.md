# AI Agent 集成指南

## 概述

MeowDesk 通过 `AgentGateway` 统一连接本地 AI Agent。HTTP 是首选协议，OpenClaw CLI 作为回退方案。本文档描述的是**当前实现**的接口与行为，对应 `meowdesk/agent/gateway.py` 与 `meowdesk/agent/commands.py`。

## 支持的 Agent

| 类型 | 配置值 | 连接方式 | 备注 |
|------|--------|---------|------|
| OpenClaw | `openclaw` | HTTP + CLI 回退 | 同时尝试 `/v1/chat/completions` 与 `openclaw` 命令行 |
| Hermes | `hermes` | HTTP | 仅 HTTP 协议 |
| 自定义 | `custom` | HTTP | 实现相同协议即可接入 |

## 实际 HTTP 协议

> 旧版文档描述的 `POST /chat`、`POST /execute`、`POST /suggestions` 路径与当前实现不一致。下表为真实请求。

### 1. 健康检查

`AgentGateway.is_available()` 会依次尝试以下路径，直到任一返回 200：

```
GET /health
GET /api/health
GET /v1/health
GET /status
GET /
```

如果配置了 `agent_type == openclaw`，以上都失败时再尝试 `openclaw agents list`，输出中包含 `main` 即视为可用。

### 2. 对话

```http
POST {endpoint}/v1/chat/completions
Content-Type: application/json
Authorization: Bearer {api_key}   # 仅在 api_key 非空时

{
  "message": "帮我清理磁盘",
  "messages": [
    { "role": "user", "content": "帮我清理磁盘" }
  ],
  "context": {
    "session_id": "...",
    "history": [...]
  }
}
```

返回结构支持两种：

- OpenAI 兼容：`{"choices": [{"message": {"content": "..."}}]}` — 取 `choices[0].message.content`
- 简单结构：`{"response": "..."}` — 直接取 `response`

HTTP 失败或返回无数据时，OpenClaw 会回退到 CLI：

```bash
openclaw agent --agent main --message "..."
```

### 3. 命令执行

```http
POST {endpoint}/execute
Content-Type: application/json
Authorization: Bearer {api_key}   # 可选

{
  "command": "check_date",
  "params": {}
}
```

### 4. 智能建议

```http
POST {endpoint}/suggestions
Content-Type: application/json
Authorization: Bearer {api_key}   # 可选

{
  "context": {
    "total_files": 1000,
    "categories": {...},
    "disk_usage": 0.85
  }
}
```

期望返回：

```json
{
  "suggestions": ["建议 1", "建议 2"]
}
```

## 配置示例

### `config.json`

```json
{
  "agent": {
    "enabled": true,
    "agent_type": "openclaw",
    "endpoint": "http://localhost:8080",
    "api_key": "your_api_key_here",
    "timeout": 30
  }
}
```

字段说明：

| 字段 | 类型 | 说明 |
|------|------|------|
| `enabled` | bool | 是否启用 AI 助手 |
| `agent_type` | string | `openclaw` / `hermes` / `custom` |
| `endpoint` | string | HTTP 端点（自动去除尾部 `/`） |
| `api_key` | string | 可选；非空时发送 `Authorization: Bearer ...` |
| `timeout` | int | HTTP 请求超时（秒） |

## 内置命令

内置命令由 `meowdesk/agent/commands.py` 的 `CommandRegistry` 注册。下列是**当前实现**真实存在的命令。

### 1. 磁盘清理
```python
command = "clean_disk"
params = {}
# 清理超过 7 天的临时文件（按平台选目录）
# 返回：cleaned_files / cleaned_size / cleaned_size_mb
```

### 2. 日期查询
```python
command = "check_date"
params = {}
# 返回：today / weekday / days_to_weekend / days_to_month_end / week_of_year
```

### 3. 假期提醒
```python
command = "check_holidays"
params = {}
# 返回：upcoming_holidays（最多 3 条）
# 内置 2026 年中国大陆法定节假日硬编码
```

### 4. 经期提醒
```python
command = "period_reminder"
params = {
    "last_date": "2026-05-01",   # 必填
    "cycle_days": 28
}
# 返回：last_date / days_since / days_until_next / next_date / status
# status 取值：
#   days_until_next < 0   -> 'overdue'
#   0 <= days_until_next <= 3 -> 'coming_soon'
#   其它 -> 'normal'
```

### 5. 系统信息
```python
command = "system_info"
params = {}
# 返回：os / os_version / cpu_count / cpu_percent / memory_* / disk_*
# 可选依赖 psutil 提供更详细信息
```

### 6. 打开应用
```python
command = "open_app"
params = {
    "app_name": "记事本"   # Windows: 记事本/计算器/画图/资源管理器
                          # macOS:   记事本/计算器/终端/Finder
}
# 未知 app_name 时返回 {'error': '未知应用: ...'}
```

## 代码使用

### Python

```python
from meowdesk.agent import AgentGateway, CommandRegistry

# 1) 构造 gateway（构造时不发起请求）
gateway = AgentGateway(config.agent_config)

# 2) 健康检查
if gateway.is_available():
    response = gateway.chat("今天星期几？")
    print(response.get("response"))

# 3) 调用内置命令
registry = CommandRegistry()
result = registry.execute("clean_disk")
print(result["result"]["cleaned_size_mb"])
```

### 自定义命令

```python
from meowdesk.agent import CommandRegistry

registry = CommandRegistry()

@registry.register_command("my_command")
def my_command(params):
    name = params.get("name", "World")
    return {"message": f"Hello, {name}!"}

result = registry.execute("my_command", {"name": "MeowDesk"})
# {"success": True, "result": {"message": "Hello, MeowDesk!"}}
```

## UI 集成

`meowdesk/ui/chat.py` 提供了 `ChatWindow`，负责：

- 消息输入与显示
- 快捷命令按钮（清理磁盘 / 系统信息 / 日期查询）
- 异步调用 `AgentGateway.chat`（不阻塞 UI）
- 历史会话（最多 100 条消息）

主窗口（`meowdesk/ui/window.py`）通过 `ContextMenu` 把"AI 助手"子菜单暴露给右键：

```
右键菜单：
├── 打开导航页
├── 打开归档目录
├── 设置
├── AI 助手 ▶
│   ├── 清理磁盘
│   ├── 查看日期
│   ├── 假期提醒
│   ├── 经期提醒
│   └── 自由对话...
└── 退出
```

## 安全建议

1. **本地运行**：Agent 应在本地运行，避免数据泄露
2. **API Key**：使用 API Key 认证，防止未授权访问
3. **超时设置**：默认 30 秒；按需调整
4. **错误处理**：`is_available()` 失败时所有调用立即返回错误，UI 显示降级提示
5. **高风险命令**：`clean_disk` 与 `open_app` 会真实操作文件系统，调用方需做权限判断

## 故障排查

### Agent 连接失败
1. 确认 Agent 正在运行：`curl http://localhost:8080/health`
2. 确认 `config.json` 中 `endpoint` 端口正确
3. 检查防火墙

### 命令执行失败
1. 查看 `result["error"]` 内容
2. 确认参数 schema（见上文各命令说明）
3. 启用 `logging` 后查看 `meowdesk.agent` 命名空间下的日志

### 响应超时
1. 调大 `agent.timeout`
2. 检查 Agent 性能
3. 后续将改为异步执行以不阻塞 UI
