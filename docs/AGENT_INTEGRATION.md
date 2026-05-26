# AI Agent 集成指南

## 概述

MeowDesk 支持通过 Gateway 连接本地 AI Agent，实现智能对话和命令执行。

## 支持的 Agent

### 1. OpenClaw
- 开源本地 AI Agent
- 支持自然语言对话
- 可执行系统命令

### 2. Hermes
- 轻量级 AI 助手
- 专注于任务自动化
- 插件化架构

### 3. 自定义 Agent
- 实现标准 HTTP API 即可接入

## API 规范

### 健康检查
```http
GET /health
Response: 200 OK
```

### 对话接口
```http
POST /chat
Content-Type: application/json

{
  "message": "帮我清理磁盘",
  "context": {
    "user_id": "xxx",
    "session_id": "xxx"
  }
}

Response:
{
  "response": "好的，正在清理磁盘...",
  "actions": [
    {
      "type": "command",
      "command": "clean_disk",
      "params": {}
    }
  ]
}
```

### 命令执行
```http
POST /execute
Content-Type: application/json

{
  "command": "clean_disk",
  "params": {}
}

Response:
{
  "success": true,
  "result": {
    "cleaned_files": 123,
    "cleaned_size_mb": 456.78
  }
}
```

### 智能建议
```http
POST /suggestions
Content-Type: application/json

{
  "context": {
    "total_files": 1000,
    "categories": {...},
    "disk_usage": 0.85
  }
}

Response:
{
  "suggestions": [
    "磁盘使用率较高，建议清理临时文件",
    "本周已归档 50 个文件，继续保持"
  ]
}
```

## 配置示例

### config.json
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

## 内置命令

### 1. 磁盘清理
```python
command = "clean_disk"
params = {}
```

### 2. 日期查询
```python
command = "check_date"
params = {}
# 返回：今天日期、星期、距离周末天数等
```

### 3. 假期提醒
```python
command = "check_holidays"
params = {}
# 返回：即将到来的假期列表
```

### 4. 经期提醒
```python
command = "period_reminder"
params = {
    "last_date": "2026-05-01",
    "cycle_days": 28
}
# 返回：距离下次经期天数、状态等
```

### 5. 系统信息
```python
command = "system_info"
params = {}
# 返回：CPU、内存、磁盘使用情况
```

### 6. 打开应用
```python
command = "open_app"
params = {
    "app_name": "记事本"  # 支持：记事本、计算器、画图、资源管理器
}
```

## 使用示例

### Python 代码
```python
from meowdesk.agent import AgentGateway, CommandRegistry

# 初始化 Gateway
config = {
    'enabled': True,
    'agent_type': 'openclaw',
    'endpoint': 'http://localhost:8080',
    'timeout': 30
}
gateway = AgentGateway(config)

# 检查可用性
if gateway.is_available():
    # 对话
    response = gateway.chat("今天星期几？")
    print(response['response'])
    
    # 执行命令
    result = gateway.execute_command('check_date')
    print(result['result'])

# 使用内置命令
registry = CommandRegistry()
result = registry.execute('clean_disk')
print(f"清理了 {result['result']['cleaned_files']} 个文件")
```

## 自定义命令

```python
from meowdesk.agent import CommandRegistry

registry = CommandRegistry()

# 注册自定义命令
@registry.register_command('my_command')
def my_command(params):
    name = params.get('name', 'World')
    return {'message': f'Hello, {name}!'}

# 执行
result = registry.execute('my_command', {'name': 'MeowDesk'})
print(result['result']['message'])  # Hello, MeowDesk!
```

## UI 交互

### 双击宠物触发对话
```python
def on_double_click():
    # 显示对话框
    dialog = AgentDialog(gateway, registry)
    dialog.show()
```

### 快捷命令菜单
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
3. **超时设置**：设置合理的超时时间，避免长时间等待
4. **错误处理**：优雅处理 Agent 不可用的情况

## 故障排查

### Agent 连接失败
1. 检查 Agent 是否运行：`curl http://localhost:8080/health`
2. 检查端口是否正确
3. 检查防火墙设置

### 命令执行失败
1. 查看错误信息
2. 检查命令参数是否正确
3. 查看 Agent 日志

### 响应超时
1. 增加 timeout 配置
2. 检查 Agent 性能
3. 考虑异步执行
