# 下一步行动清单

## 🎯 立即可做（无需 macOS 设备）

### 1. 代码审查 ✅
- [x] 检查代码规范
- [x] 检查类型注解
- [x] 检查错误处理
- [x] 检查文档注释

### 2. 文档完善 ✅
- [x] 更新 README
- [x] 编写发布说明
- [x] 创建测试指南
- [x] 创建部署指南

### 3. 准备发布材料 ⏳
- [ ] 更新版本号
- [ ] 准备 CHANGELOG
- [ ] 准备发布说明
- [ ] 准备宣传材料

---

## 🍎 需要 macOS 设备

### 阶段 1：基础测试（1-2 小时）

```bash
# 1. 克隆代码
git clone https://github.com/yourusername/desktopet.git
cd desktopet

# 2. 安装依赖
pip3 install Pillow send2trash pyobjc-framework-Cocoa

# 3. 运行测试
python3 test_macos.py

# 4. 运行主程序
python3 meowdesk_main.py
```

**检查清单**：
- [ ] 测试脚本全部通过
- [ ] 窗口正常显示
- [ ] 动画正常播放
- [ ] 可以拖动窗口
- [ ] 可以点击交互

### 阶段 2：功能测试（2-3 小时）

**拖放测试**：
- [ ] 拖入单个文件
- [ ] 拖入多个文件
- [ ] 拖入文件夹
- [ ] 拖入截图文件

**动画测试**：
- [ ] 闲置状态（IDLE）
- [ ] 惊讶状态（SURPRISED）
- [ ] 开心状态（HAPPY）
- [ ] 害羞状态（SHY）
- [ ] 睡眠状态（SLEEPING）
- [ ] 闲逛行为

**文件处理测试**：
- [ ] 文件正确分类
- [ ] 截图正确回收
- [ ] MD5 去重工作
- [ ] 数据库正确记录
- [ ] HTML 索引生成

### 阶段 3：性能测试（1 小时）

```bash
# 监控 CPU 和内存
top -pid $(pgrep -f meowdesk_main)

# 测试启动时间
time python3 meowdesk_main.py
```

**检查清单**：
- [ ] CPU 使用率 < 5%
- [ ] 内存占用 < 100 MB
- [ ] 启动时间 < 2 秒
- [ ] 动画流畅（12+ FPS）

### 阶段 4：打包测试（1-2 小时）

```bash
# 方式一：PyInstaller
pip3 install pyinstaller
pyinstaller meowdesk.spec
./dist/MeowDesk/MeowDesk

# 方式二：自动化脚本
chmod +x build_macos.sh
./build_macos.sh
```

**检查清单**：
- [ ] PyInstaller 打包成功
- [ ] .app 可以运行
- [ ] 所有功能正常
- [ ] DMG 创建成功

### 阶段 5：长时间测试（24 小时）

```bash
# 后台运行
nohup python3 meowdesk_main.py &

# 24 小时后检查
ps aux | grep meowdesk
```

**检查清单**：
- [ ] 程序稳定运行
- [ ] 无内存泄漏
- [ ] 无崩溃
- [ ] 性能稳定

---

## 📝 测试报告模板

完成测试后，请填写以下报告：

```markdown
# MeowDesk macOS 测试报告

**测试日期**: 2024-XX-XX
**测试人员**: XXX
**系统版本**: macOS XX.X
**处理器**: Apple M1/M2/Intel
**Python 版本**: 3.X.X

## 测试结果

### 基础功能
- [ ] 测试脚本通过
- [ ] 窗口显示正常
- [ ] 动画播放正常
- [ ] 拖动功能正常

### 拖放功能
- [ ] 单个文件
- [ ] 多个文件
- [ ] 文件夹
- [ ] 截图回收

### 动画状态
- [ ] 所有状态正常

### 性能
- CPU: X%
- 内存: X MB
- 启动时间: X 秒

### 打包
- [ ] PyInstaller 成功
- [ ] .app 运行正常
- [ ] DMG 创建成功

## 问题列表

1. **问题描述**: XXX
   - 严重程度: 高/中/低
   - 复现步骤: XXX

## 总体评价

- 功能完整性: X%
- 稳定性: 优秀/良好/一般/差
- 性能: 优秀/良好/一般/差
- 用户体验: 优秀/良好/一般/差

## 建议

1. XXX
2. XXX
```

---

## 🐛 如果发现问题

### 报告 Bug

1. 在 GitHub 创建 Issue
2. 使用模板填写信息
3. 附加截图和日志
4. 标记优先级

### 修复流程

1. 开发者修复代码
2. 推送到 GitHub
3. 测试者验证修复
4. 关闭 Issue

---

## 🚀 发布流程

### 1. 准备发布（1 天）

- [ ] 所有测试通过
- [ ] 更新版本号
- [ ] 更新 CHANGELOG
- [ ] 准备发布说明
- [ ] 打包所有平台

### 2. 创建 Release（1 小时）

```bash
# 1. 创建 tag
git tag -a v1.4.0 -m "Release v1.4.0"
git push origin v1.4.0

# 2. 在 GitHub 创建 Release
# 3. 上传文件
#    - Windows: MeowDesk-1.4.0-win64.exe
#    - macOS: MeowDesk-1.4.0.dmg
#    - Source: 自动生成

# 4. 发布
```

### 3. 宣传推广（持续）

- [ ] 更新项目主页
- [ ] 发布社交媒体
- [ ] 通知用户
- [ ] 收集反馈

---

## 📅 时间表

### Week 1（当前）
- ✅ 完成 macOS 开发
- ✅ 完成文档编写
- ⏳ 准备发布材料

### Week 2
- 🎯 macOS 实际测试
- 🎯 Bug 修复
- 🎯 发布 v1.4.0

### Week 3-4
- 🎯 收集用户反馈
- 🎯 Bug 修复
- 🎯 发布 v1.4.1

### Month 2
- 🎯 开始 v1.5.0 开发
- 🎯 AI Agent 集成
- 🎯 功能增强

---

## 🎯 优先级

### P0 - 必须完成
- macOS 实际测试
- 关键 Bug 修复
- 发布 v1.4.0

### P1 - 重要
- 性能优化
- 系统托盘完善
- 右键菜单优化

### P2 - 可选
- AI Agent 对话界面
- TODO 管理
- 旅行规划

### P3 - 未来
- 插件系统
- 云同步
- 多套主题

---

## 📞 需要帮助？

### 文档
- [快速开始](MACOS_QUICKSTART.md)
- [测试指南](docs/MACOS_TESTING.md)
- [部署指南](docs/MACOS_DEPLOYMENT.md)

### 联系方式
- GitHub Issues
- Discussions
- Email: support@meowdesk.com

---

**更新日期**: 2026-05-26  
**状态**: 等待 macOS 实际测试

**Made with ❤️ by ra1nzzz**
