# 旧文件说明

这些文件是原始的单文件实现，保留作为参考和兼容性。

## 主程序文件

### lingxi_droplet.py
- **用途**: 原始 Windows 主程序（Win32 API + ULW）
- **状态**: 保留，可继续使用
- **特点**: 
  - 完整的 Windows 实现
  - UpdateLayeredWindow 透明窗口
  - windnd 拖放支持
  - 1000+ 行单文件

### lingxi_droplet_tk.py
- **用途**: Tkinter 版本（跨平台尝试）
- **状态**: 保留作为参考
- **特点**:
  - 基于 Tkinter
  - 相对简化的实现
  - 800+ 行

## 辅助脚本

### _gen_html.py
- **用途**: 生成 HTML 导航页面
- **状态**: 保留，新版本会调用
- **功能**:
  - 读取 filedb.json
  - 生成暗色主题 HTML
  - 支持搜索和筛选

### _locate.py
- **用途**: 文件定位脚本（从 HTML 打开资源管理器）
- **状态**: 保留，HTML 页面需要
- **功能**:
  - 解析 meow-locate:// 协议
  - 在资源管理器中定位文件

### locate.bat
- **用途**: Windows 批处理，调用 _locate.py
- **状态**: 保留，注册表协议需要
- **功能**:
  - 注册 meow-locate:// 协议
  - 调用 Python 脚本

## Spec 文件

### 妙喵桌宠.spec
- **用途**: PyInstaller 打包配置（文件夹版）
- **状态**: 保留，用于打包旧版本
- **输出**: dist/妙喵桌宠/

### 妙喵桌宠-onefile.spec
- **用途**: PyInstaller 打包配置（单文件版）
- **状态**: 保留，用于打包旧版本
- **输出**: dist/妙喵桌宠.exe

### meowdesk.spec
- **用途**: 新版本打包配置（文件夹版）
- **状态**: 使用中
- **输出**: dist/MeowDesk/

### meowdesk-onefile.spec
- **用途**: 新版本打包配置（单文件版）
- **状态**: 使用中
- **输出**: dist/MeowDesk.exe

## 其他文件

### install.py
- **用途**: 安装脚本（快捷方式 + 开机自启）
- **状态**: 保留，新旧版本通用
- **功能**:
  - 创建桌面快捷方式
  - 添加到开机自启动
  - 复制文件到安装目录

### launch_with_log.py
- **用途**: 带日志的启动脚本
- **状态**: 保留，调试用
- **功能**:
  - 捕获输出到日志文件
  - 错误处理

### test_ulw.py
- **用途**: UpdateLayeredWindow 测试
- **状态**: 保留，开发参考
- **功能**:
  - 测试透明窗口
  - Win32 API 调试

## 批处理文件

### run.bat
- **用途**: 快速启动脚本
- **状态**: 保留
- **内容**: `python lingxi_droplet.py`

### 启动妙喵桌宠.bat
- **用途**: 中文名启动脚本
- **状态**: 保留
- **内容**: `python lingxi_droplet.py`

## 迁移建议

### 立即迁移
- ✅ 使用 `meowdesk_main.py` 作为新的主程序
- ✅ 使用 `meowdesk.spec` 打包新版本

### 保留使用
- 📦 `_gen_html.py` - HTML 生成（新版本会调用）
- 📦 `_locate.py` - 文件定位（HTML 需要）
- 📦 `install.py` - 安装脚本（通用）

### 可以删除（如果不需要旧版本）
- 🗑️ `lingxi_droplet.py` - 被 `meowdesk_main.py` 替代
- 🗑️ `lingxi_droplet_tk.py` - 实验性版本
- 🗑️ `妙喵桌宠.spec` - 被 `meowdesk.spec` 替代
- 🗑️ `妙喵桌宠-onefile.spec` - 被 `meowdesk-onefile.spec` 替代

## 兼容性

新旧版本可以共存：
- 使用相同的 `config.json`
- 使用相同的 `filedb.json`
- 使用相同的归档目录

建议：
1. 先测试新版本
2. 确认功能正常后再删除旧文件
3. 保留旧文件至少一个版本周期
