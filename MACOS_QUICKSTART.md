# macOS 快速开始指南

## 🚀 5 分钟快速测试

### 1. 克隆代码（如果还没有）

```bash
git clone https://github.com/yourusername/desktopet.git
cd desktopet
```

### 2. 安装依赖

```bash
pip3 install Pillow send2trash pyobjc-framework-Cocoa
```

### 3. 运行测试

```bash
python3 test_macos.py
```

**预期输出**：
```
🍎 MeowDesk macOS 平台测试
✅ macOS 平台模块导入成功
✅ 窗口创建成功
✅ 动画渲染成功
✅ 拖放功能启用成功
✅ 所有测试通过！
```

### 4. 运行主程序

```bash
python3 meowdesk_main.py
```

### 5. 测试功能

1. **看到猫猫了吗？** ✅
2. **动画在播放吗？** ✅
3. **拖入一个文件试试** ✅
4. **点击猫猫 3 次** ✅（应该变害羞）
5. **等待 60 秒** ✅（应该睡觉）

---

## 🔧 如果遇到问题

### 问题 1：PyObjC 导入失败

```bash
pip3 uninstall pyobjc-framework-Cocoa
pip3 install pyobjc-framework-Cocoa
```

### 问题 2：窗口不显示

```bash
# 删除配置文件重置位置
rm config.json
python3 meowdesk_main.py
```

### 问题 3：拖放不工作

1. 系统偏好设置 → 安全性与隐私
2. 隐私 → 文件和文件夹
3. 允许 Python/终端访问

---

## 📦 打包测试

### 快速打包（PyInstaller）

```bash
pip3 install pyinstaller
pyinstaller meowdesk.spec
./dist/MeowDesk/MeowDesk
```

### 自动化打包

```bash
chmod +x build_macos.sh
./build_macos.sh
```

---

## 📚 详细文档

- **开发进度**: `MACOS_DEVELOPMENT.md`
- **完整测试**: `docs/MACOS_TESTING.md`
- **打包部署**: `docs/MACOS_DEPLOYMENT.md`
- **完成报告**: `MACOS_READY.md`

---

## ✅ 测试清单

- [ ] 测试脚本通过
- [ ] 主程序可以运行
- [ ] 窗口正常显示
- [ ] 动画正常播放
- [ ] 拖放功能正常
- [ ] 文件处理正常
- [ ] 打包成功

---

**需要帮助？** 查看 `docs/MACOS_TESTING.md` 的常见问题部分

**Made with ❤️ by ra1nzzz**
