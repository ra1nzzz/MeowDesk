# 妙喵桌宠 MeowDesk 🐱

> 桌面拖拽文件自动分类归档工具 — 拖进去，它搞定。

把文件拖到桌面右上角的猫猫身上，自动分类归档到对应目录，截图自动回收。支持 HTML 导航页浏览归档文件。

![screenshot](assets/idle.apng)

---

## 功能

- **悬浮拖拽区** — 桌面右上角猫猫图标，拖入文件即自动整理
- **智能分类** — 截图自动移入回收站，其它文件按类型归档（文档 / 图片 / 视频 / 音频 / 代码 / 压缩包 / 设计稿 / 电子书等）
- **日期归档** — 按 `类型/年-月/` 目录结构存放
- **HTML 导航** — 自动生成暗色主题文件索引页面，支持搜索、分类筛选、定位文件
- **多种动画** — idle / happy / shy / surprised / sleeping 等状态动画
- **系统托盘** — 最小化到托盘，开机自启动（通过 install.py）

---

## 快速开始

### 方式一：直接运行（需 Python）

```bash
# 双击启动（推荐）
启动妙喵桌宠.bat

# 或命令行
python lingxi_droplet.py
```

### 方式二：一键安装

```bash
python install.py install    # 安装（快捷方式 + 开机自启 + 复制文件）
python install.py status     # 查看状态
python install.py uninstall  # 卸载
```

### 方式三：打包 EXE（无需 Python）

从 [Releases](https://github.com/ra1nzzz/MeowDesk/releases) 下载 `妙喵桌宠.exe`，双击即可运行。

---

## 目录结构

```
D:\meow-temp\           ← 拖入文件的临时暂存目录
D:\meow-file\           ← 归档根目录
  ├── index.html        ← HTML 导航页面
  ├── .filedb.json      ← 文件数据库（自动维护）
  ├── 截图\             ← 自动回收（移入回收站）
  ├── 文档\             ← 按月归档
  │   └── 2026-05\
  ├── 图片\
  ├── 视频\
  ├── 音频\
  ├── 代码\
  ├── 压缩包\
  ├── 设计稿\
  ├── 电子书\
  └── 其他\
```

## 截图识别规则

文件被判定为「临时截图」并自动移入回收站的条件（满足任一即可）：

1. 文件名包含关键词：`截图`、`截屏`、`Screenshot`、`Screen Shot`、`微信截图`、`QQ截图`、`Snipaste`、`Capture` 等
2. 文件位于临时目录（`Temp`、`AppData`、`Clipboard` 等）
3. 图片分辨率接近当前屏幕分辨率（宽 ≥ 屏幕 80% 且 高 ≥ 屏幕 50%）

## 自定义配置

编辑 `config.json`（首次运行后自动生成）：

```json
{
  "temp_dir": "D:\\meow-temp",
  "archive_dir": "D:\\meow-file",
  "window_opacity": 0.85,
  "auto_open_html": false,
  "categories": {
    "文档": { "exts": [".doc", ".docx", ".pdf", "..."], "action": "archive" },
    "截图": { "exts": [".png", ".jpg", "..."], "action": "recycle" }
  }
}
```

## 依赖

| 依赖 | 用途 | 安装 |
|------|------|------|
| **Python 3.12+** | 运行环境 | — |
| **Pillow** | 图像处理 / APNG 解析 | `pip install Pillow` |
| **send2trash** | 安全回收站 | `pip install send2trash` |
| **windnd** | 拖拽支持 | `pip install windnd` |

可选：

| 依赖 | 用途 | 安装 |
|------|------|------|
| **PyQt5** | Qt 图形界面版 | `pip install PyQt5` |
| **PyInstaller** | 打包 EXE | `pip install pyinstaller` |

## 使用技巧

- 猫猫可**拖动**到桌面任意位置，位置会自动记忆
- 拖入多文件时**批量处理**，处理过程有动画提示
- 按 `/` 键在 HTML 导航页面可快速聚焦搜索框
- 右键猫猫可打开导航页面、归档目录或退出
- 导航页点击「定位」按钮可直接在资源管理器中定位文件

## 构建 EXE

```bash
pip install pyinstaller
pyinstaller 妙喵桌宠.spec
```

输出在 `dist/妙喵桌宠/` 目录。

## 许可证

MIT
