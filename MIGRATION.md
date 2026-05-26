# 迁移说明

## 文件变更

### 新架构文件
- ✅ `meowdesk_main.py` - 新的主程序入口
- ✅ `meowdesk/` - 模块化包结构
  - `core/` - 核心功能
  - `agent/` - AI 集成
  - `platform/` - 跨平台
  - `ui/` - 用户界面

### 旧文件（保留作为参考）
- `lingxi_droplet.py` - 原始主程序（Windows 版本）
- `lingxi_droplet_tk.py` - Tkinter 版本
- `_gen_html.py` - HTML 生成脚本
- `_locate.py` - 文件定位脚本

## 如何运行

### 新版本（推荐）
```bash
python meowdesk_main.py
```

### 旧版本（兼容）
```bash
python lingxi_droplet.py
```

## 配置兼容性

新版本完全兼容旧版本的配置文件：
- `config.json` - 配置文件
- `filedb.json` 或 `.filedb.json` - 数据库文件

## 功能对比

| 功能 | 旧版本 | 新版本 |
|------|--------|--------|
| 文件归档 | ✅ | ✅ |
| 截图识别 | ✅ | ✅ |
| HTML 导航 | ✅ | ⏳ |
| Windows 支持 | ✅ | ✅ |
| macOS 支持 | ❌ | ✅ |
| AI Agent | ❌ | ✅ |
| 模块化 | ❌ | ✅ |

## 迁移步骤

1. **备份数据**
   ```bash
   # 备份配置和数据库
   copy config.json config.json.bak
   copy filedb.json filedb.json.bak
   ```

2. **测试新版本**
   ```bash
   python meowdesk_main.py
   ```

3. **验证功能**
   - 拖入文件测试归档
   - 检查数据库记录
   - 查看 HTML 导航页

4. **切换到新版本**
   - 如果一切正常，可以使用新版本
   - 旧文件保留作为参考

## 注意事项

- 新旧版本可以共存，使用相同的配置和数据库
- 建议先在测试环境验证新版本
- 如有问题，可以随时切回旧版本

## 开发状态

当前版本：v1.3.0（模块化重构）

进行中：
- ⏳ Windows 平台完善
- ⏳ macOS 平台实现
- ⏳ AI Agent 集成

计划中：
- 📅 v1.4.0 - macOS 支持
- 📅 v1.5.0 - AI Agent 集成
- 📅 v1.6.0 - 性能优化
