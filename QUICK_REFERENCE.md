# MeowDesk 快速参考

## 🚀 快速开始

### 安装依赖
```bash
# Windows
pip install Pillow send2trash windnd

# macOS
pip install Pillow send2trash pyobjc-framework-Cocoa
```

### 运行程序
```bash
# 旧版本（单文件）
python lingxi_droplet.py

# 新版本（模块化）
python meowdesk_demo.py
```

---

## 📦 核心模块

### ConfigManager - 配置管理
```python
from meowdesk.core import ConfigManager

config = ConfigManager("config.json")
archive_dir = config.get('archive_dir')
config.set('window_opacity', 0.9)
```

### FileDatabase - 文件数据库
```python
from meowdesk.core import FileDatabase

db = FileDatabase("filedb.json")
db.add_record({...})
results = db.search(keyword='测试')
stats = db.get_stats()
```

### FileClassifier - 文件分类
```python
from meowdesk.core import FileClassifier

classifier = FileClassifier(config)
category, action = classifier.classify(filepath)
```

### FileHandler - 文件处理
```python
from meowdesk.core import FileHandler

handler = FileHandler(archive_dir, temp_dir)
success, dest, error = handler.archive_file(filepath, category)
success, error = handler.recycle_file(filepath)
```

---

## 🤖 AI Agent

### AgentGateway - Agent 网关
```python
from meowdesk.agent import AgentGateway

config = {
    'enabled': True,
    'agent_type': 'openclaw',
    'endpoint': 'http://localhost:8080'
}
gateway = AgentGateway(config)

# 对话
response = gateway.chat("今天星期几？")

# 执行命令
result = gateway.execute_command('check_date')
```

### CommandRegistry - 命令系统
```python
from meowdesk.agent import CommandRegistry

registry = CommandRegistry()

# 执行内置命令
result = registry.execute('check_date')
result = registry.execute('clean_disk')
result = registry.execute('check_holidays')

# 注册自定义命令
@registry.register_command('my_cmd')
def my_cmd(params):
    return {'message': 'Hello!'}
```

---

## 🎨 内置命令

| 命令 | 说明 | 参数 |
|------|------|------|
| `clean_disk` | 清理磁盘临时文件 | 无 |
| `check_date` | 查询日期信息 | 无 |
| `check_holidays` | 查询假期 | 无 |
| `period_reminder` | 经期提醒 | `last_date`, `cycle_days` |
| `system_info` | 系统信息 | 无 |
| `open_app` | 打开应用 | `app_name` |

---

## 🖥️ 跨平台

### 获取平台窗口
```python
from meowdesk.platform import get_platform_window

WindowClass = get_platform_window()
window = WindowClass(width=128, height=128)

window.create()
window.set_position(100, 100)
window.show()

# 设置回调
window.on_drop(lambda files: print(files))
window.on_click(lambda: print("clicked"))

window.run()
```

---

## ⚙️ 配置文件

### config.json
```json
{
  "archive_dir": "D:\\meow-file",
  "temp_dir": "D:\\meow-temp",
  "window_opacity": 0.85,
  "auto_open_html": false,
  "screenshot_action": "recycle",
  "window_position": [1516, 430],
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

---

## 📁 目录结构

```
meowdesk/
├── core/              # 核心功能
│   ├── config.py
│   ├── database.py
│   ├── classifier.py
│   └── file_handler.py
├── agent/             # AI 集成
│   ├── gateway.py
│   └── commands.py
└── platform/          # 跨平台
    ├── base.py
    ├── windows.py
    └── macos.py
```

---

## 🔧 常用操作

### 添加自定义分类
编辑 `config.json`:
```json
{
  "categories": {
    "我的分类": {
      "exts": [".custom"],
      "action": "archive"
    }
  }
}
```

### 添加自定义命令
```python
from meowdesk.agent import CommandRegistry

registry = CommandRegistry()

@registry.register_command('my_command')
def my_command(params):
    # 你的逻辑
    return {'result': 'success'}
```

### 连接自定义 Agent
```python
config = {
    'enabled': True,
    'agent_type': 'custom',
    'endpoint': 'http://your-agent:port',
    'api_key': 'your_key'
}
```

---

## 🐛 调试

### 查看日志
```bash
# Windows
type logs\meow_desk.log

# macOS/Linux
cat logs/meow_desk.log
```

### 测试模块
```python
# 测试分类器
python -c "from meowdesk.core import FileClassifier; ..."

# 测试命令
python -c "from meowdesk.agent import CommandRegistry; ..."
```

---

## 📚 文档链接

- [架构设计](docs/ARCHITECTURE.md)
- [macOS 支持](docs/MACOS_SUPPORT.md)
- [Agent 集成](docs/AGENT_INTEGRATION.md)
- [开发路线图](docs/ROADMAP.md)
- [项目总结](PROJECT_SUMMARY.md)

---

## 🆘 常见问题

### Q: 如何更改归档目录？
A: 编辑 `config.json` 中的 `archive_dir`

### Q: 如何禁用截图自动回收？
A: 设置 `screenshot_action` 为 `archive`

### Q: Agent 连接失败？
A: 检查 Agent 是否运行，端口是否正确

### Q: macOS 拖放不工作？
A: 检查文件访问权限，首次使用需授权

---

**快速参考 v1.3.0**
