"""OTA 自动更新模块 — 检测 GitHub Release、下载、应用、回滚。

工作流程:
1. 启动时后台线程调用 ``check_for_update()`` 查询 GitHub API
2. 发现新版本后弹出对话框,用户确认后下载(支持镜像加速)
3. 下载完成后生成 ``.updater.bat`` 脚本,脚本负责:
   a. 等待当前进程退出
   b. 备份当前 EXE/目录 → .bak
   c. 替换为新版本
   d. 启动新版本并等待验证(20 秒超时)
   e. 新版本启动后 5 秒内创建验证标记 → 成功,清理备份
   f. 超时未验证 → 自动回滚到 .bak
"""

import json
import os
import subprocess
import sys
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from . import __version__
from .utils import get_logger

_log = get_logger(__name__)

# ---------------------------------------------------------------------------
# 仓库信息
# ---------------------------------------------------------------------------
REPO_OWNER = "ra1nzzz"
REPO_NAME = "MeowDesk"
API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
RELEASE_PAGE = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/latest"

# GitHub 下载加速镜像(国内)— 拼接在 github.com URL 前面
DOWNLOAD_MIRRORS = [
    "",                             # 直连优先(网络好时最快)
    "https://mirror.ghproxy.com/",  # ghproxy 镜像
    "https://gh-proxy.com/",        # gh-proxy 镜像
    "https://ghps.cc/",             # ghps 镜像
]

# ---------------------------------------------------------------------------
# 更新状态文件(放在 app_dir 即 EXE 同级目录)
# ---------------------------------------------------------------------------
UPDATE_PENDING_FLAG = ".update_pending"    # updater.bat 创建,表示新版本已启动待验证
UPDATE_VERIFIED_FLAG = ".update_verified"  # 新版本启动成功后创建,通知 updater.bat 验证通过

# 新版本启动后多少秒创建验证标记(太短可能误判,太长用户体验差)
VERIFY_DELAY_SECONDS = 5
# updater.bat 等待验证标记的超时秒数
VERIFY_TIMEOUT_SECONDS = 30


# ---------------------------------------------------------------------------
# 版本比较
# ---------------------------------------------------------------------------

def parse_version(v: str) -> tuple:
    """解析版本号字符串为可比较的元组。

    >>> parse_version("1.5.1")
    (1, 5, 1)
    >>> parse_version("v1.6.0")
    (1, 6, 0)
    """
    v = v.strip().lstrip("vV")
    main = v.split("-")[0].split("+")[0]
    parts = []
    for p in main.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def is_newer(remote: str, local: str) -> bool:
    """判断 ``remote`` 版本是否比 ``local`` 新。"""
    return parse_version(remote) > parse_version(local)


# ---------------------------------------------------------------------------
# HTTP 工具(复用 gateway.py 的 requests/urllib 降级模式)
# ---------------------------------------------------------------------------

def _http_get_json(url: str, timeout: int = 10) -> Optional[dict]:
    """GET 请求返回 JSON,自动选择 requests/urllib。"""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "MeowDesk-Updater",
    }
    try:
        import requests
        resp = requests.get(url, timeout=timeout, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        _log.warning("GitHub API returned %d", resp.status_code)
        return None
    except ImportError:
        pass

    import urllib.request
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        _log.warning("HTTP request failed: %s", e)
    return None


def _http_download(url: str, dest: str, timeout: int = 120,
                   progress_cb: Optional[Callable[[int, int], None]] = None) -> bool:
    """下载文件到 *dest*,支持进度回调。成功返回 True。"""
    headers = {"User-Agent": "MeowDesk-Updater"}

    try:
        import requests
        with requests.get(url, stream=True, timeout=timeout, headers=headers) as resp:
            if resp.status_code != 200:
                _log.warning("download %s returned %d", url[:60], resp.status_code)
                return False
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_cb:
                            progress_cb(downloaded, total)
        return True
    except ImportError:
        pass

    import urllib.request
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            with open(dest, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_cb:
                        progress_cb(downloaded, total)
        return True
    except Exception as e:
        _log.warning("download failed from %s: %s", url[:60], e)
        return False


# ---------------------------------------------------------------------------
# UpdateInfo
# ---------------------------------------------------------------------------

@dataclass
class UpdateInfo:
    """新版本信息。"""
    version: str           # "1.6.0"(不含 v 前缀)
    tag_name: str          # "v1.6.0"
    release_notes: str     # Release body
    download_url: str      # GitHub 直链
    asset_name: str        # "MeowDesk-standalone.exe" 或 "MeowDesk.zip"
    asset_size: int        # 字节数
    html_url: str          # Release 页面 URL


# ---------------------------------------------------------------------------
# UpdateManager
# ---------------------------------------------------------------------------

class UpdateManager:
    """OTA 更新管理器。

    负责检查更新、下载、应用(替换 EXE/目录)以及更新后验证。
    自动回滚机制: updater.bat 在替换后启动新版本,等待验证标记;
    超时未验证则自动恢复备份。
    """

    def __init__(self, config, app_dir: str):
        self.config = config
        self.app_dir = app_dir

    # ---- 运行环境判断 ----

    @property
    def is_frozen(self) -> bool:
        return getattr(sys, "frozen", False)

    @property
    def is_onefile(self) -> bool:
        """是否为 onefile 打包模式(单 EXE,无 _internal 目录)。"""
        if not self.is_frozen:
            return False
        meipass = getattr(sys, "_MEIPASS", "")
        if not meipass:
            return True
        exe_dir = os.path.dirname(sys.executable)
        internal = os.path.join(exe_dir, "_internal")
        return os.path.normpath(meipass) != os.path.normpath(internal)

    # ---- 检查更新 ----

    def check_for_update(self) -> Optional[UpdateInfo]:
        """查询 GitHub 最新 release,返回 ``UpdateInfo`` 或 ``None``。"""
        data = _http_get_json(API_URL, timeout=10)
        if not data:
            return None

        tag = data.get("tag_name", "")
        version = tag.lstrip("vV")
        if not version or not is_newer(version, __version__):
            return None

        asset = self._select_asset(data.get("assets", []))
        if not asset:
            _log.warning("no suitable asset found in release %s", tag)
            return None

        return UpdateInfo(
            version=version,
            tag_name=tag,
            release_notes=data.get("body", "") or "",
            download_url=asset["browser_download_url"],
            asset_name=asset["name"],
            asset_size=asset.get("size", 0),
            html_url=data.get("html_url", RELEASE_PAGE),
        )

    def _select_asset(self, assets: list) -> Optional[dict]:
        """根据当前运行模式(onefile/onedir)选择下载资产。"""
        if not assets:
            return None
        if self.is_onefile:
            for a in assets:
                if "standalone" in a.get("name", "").lower():
                    return a
        else:
            for a in assets:
                if a.get("name", "").lower().endswith(".zip"):
                    return a
        return assets[0]

    # ---- 下载 ----

    def download_update(self, info: UpdateInfo,
                        progress_cb: Optional[Callable[[int, int], None]] = None) -> Optional[str]:
        """下载更新包,返回本地临时文件路径或 ``None``。

        依次尝试直连和各镜像,直到成功。下载后校验文件大小。
        """
        tmp_path = os.path.join(self.app_dir, ".update_download.tmp")
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

        # 构建候选 URL 列表(直连 + 镜像)
        urls = [info.download_url]
        for mirror in DOWNLOAD_MIRRORS:
            if mirror:
                urls.append(mirror + info.download_url)

        for url in urls:
            _log.info("trying download: %s", url[:80])
            if _http_download(url, tmp_path, timeout=180, progress_cb=progress_cb):
                if info.asset_size > 0:
                    actual = os.path.getsize(tmp_path)
                    if actual != info.asset_size:
                        _log.warning("size mismatch: expected %d, got %d", info.asset_size, actual)
                        try:
                            os.remove(tmp_path)
                        except OSError:
                            pass
                        continue
                return tmp_path

        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return None

    # ---- 应用更新 ----

    def apply_update(self, local_path: str) -> bool:
        """应用更新:生成 updater 脚本,启动后通知主程序退出。

        返回 True 表示更新脚本已成功启动(主程序应随即退出)。
        """
        if not self.is_frozen:
            _log.warning("cannot apply update in dev mode")
            return False
        if sys.platform == "win32":
            return self._apply_windows(local_path)
        _log.info("auto-update not supported on platform: %s", sys.platform)
        return False

    def _apply_windows(self, local_path: str) -> bool:
        """Windows 平台:生成 .updater.bat 并以分离进程启动。"""
        exe_path = sys.executable
        exe_dir = os.path.dirname(exe_path)
        flag_pending = os.path.join(self.app_dir, UPDATE_PENDING_FLAG)
        flag_verified = os.path.join(self.app_dir, UPDATE_VERIFIED_FLAG)

        # 清理残留标记
        for f in (flag_pending, flag_verified):
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass

        if self.is_onefile:
            bat = self._build_onefile_bat(local_path, exe_path, flag_pending, flag_verified)
        else:
            bat = self._build_onedir_bat(local_path, exe_dir, flag_pending, flag_verified)

        bat_path = os.path.join(self.app_dir, ".updater.bat")
        try:
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(bat)
        except OSError as e:
            _log.error("failed to write updater bat: %s", e)
            return False

        try:
            subprocess.Popen(
                ["cmd", "/c", bat_path],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
                close_fds=True,
            )
        except Exception as e:
            _log.error("failed to launch updater: %s", e)
            return False
        return True

    def _build_onefile_bat(self, new_exe: str, exe_path: str,
                           flag_pending: str, flag_verified: str) -> str:
        """onefile 模式:替换单个 EXE 文件。"""
        cur_pid = os.getpid()
        bak_path = exe_path + ".bak"
        exe_name = os.path.basename(exe_path)
        bat_self = os.path.join(self.app_dir, ".updater.bat")
        T = VERIFY_TIMEOUT_SECONDS

        return f"""@echo off
chcp 65001 >nul 2>&1
setlocal

set "CUR_PID={cur_pid}"
set "NEW_EXE={new_exe}"
set "EXE_PATH={exe_path}"
set "EXE_NAME={exe_name}"
set "BAK_PATH={bak_path}"
set "FLAG_PENDING={flag_pending}"
set "FLAG_VERIFIED={flag_verified}"
set "BAT_SELF={bat_self}"

:: 等待当前进程退出
:wait_exit
tasklist /fi "pid eq %CUR_PID%" 2>nul | find "%CUR_PID%" >nul
if not errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait_exit
)

:: 删除旧备份
if exist "%BAK_PATH%" del /f /q "%BAK_PATH%"

:: 备份当前 EXE
move /y "%EXE_PATH%" "%BAK_PATH%" >nul 2>&1
if errorlevel 1 (
    if exist "%NEW_EXE%" del /f /q "%NEW_EXE%"
    start "" "%EXE_PATH%"
    exit /b 1
)

:: 应用新版本
move /y "%NEW_EXE%" "%EXE_PATH%" >nul 2>&1
if errorlevel 1 (
    move /y "%BAK_PATH%" "%EXE_PATH%" >nul 2>&1
    if exist "%NEW_EXE%" del /f /q "%NEW_EXE%"
    start "" "%EXE_PATH%"
    exit /b 1
)

:: 创建待验证标记
echo pending > "%FLAG_PENDING%"

:: 启动新版本
start "" "%EXE_PATH%"

:: 等待验证标记(最多 {T} 秒)
set /a count=0
:wait_verify
timeout /t 1 /nobreak >nul
set /a count+=1
if exist "%FLAG_VERIFIED%" (
    del /f /q "%FLAG_PENDING%" 2>nul
    del /f /q "%FLAG_VERIFIED%" 2>nul
    del /f /q "%BAK_PATH%" 2>nul
    del /f /q "%BAT_SELF%" 2>nul
    exit /b 0
)
if %count% lss {T} goto wait_verify

:: 超时未验证 → 回滚
taskkill /f /im "%EXE_NAME%" >nul 2>&1
timeout /t 2 /nobreak >nul
move /y "%EXE_PATH%" "%EXE_PATH%.failed" >nul 2>&1
move /y "%BAK_PATH%" "%EXE_PATH%" >nul 2>&1
del /f /q "%FLAG_PENDING%" 2>nul
del /f /q "%FLAG_VERIFIED%" 2>nul
start "" "%EXE_PATH%"
exit /b 1
"""

    def _build_onedir_bat(self, zip_path: str, exe_dir: str,
                          flag_pending: str, flag_verified: str) -> str:
        """onedir 模式:解压 ZIP 替换整个目录。"""
        cur_pid = os.getpid()
        parent_dir = os.path.dirname(exe_dir)
        dir_name = os.path.basename(exe_dir)
        bak_dir = os.path.join(parent_dir, dir_name + ".bak")
        exe_name = os.path.basename(sys.executable)
        bat_self = os.path.join(self.app_dir, ".updater.bat")
        T = VERIFY_TIMEOUT_SECONDS

        return f"""@echo off
chcp 65001 >nul 2>&1
setlocal

set "CUR_PID={cur_pid}"
set "ZIP_PATH={zip_path}"
set "APP_DIR={exe_dir}"
set "APP_PARENT={parent_dir}"
set "APP_NAME={dir_name}"
set "BAK_DIR={bak_dir}"
set "EXE_NAME={exe_name}"
set "FLAG_PENDING={flag_pending}"
set "FLAG_VERIFIED={flag_verified}"
set "BAT_SELF={bat_self}"

:wait_exit
tasklist /fi "pid eq %CUR_PID%" 2>nul | find "%CUR_PID%" >nul
if not errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait_exit
)

if exist "%BAK_DIR%" rmdir /s /q "%BAK_DIR%"

move "%APP_DIR%" "%BAK_DIR%" >nul 2>&1
if errorlevel 1 (
    if exist "%ZIP_PATH%" del /f /q "%ZIP_PATH%"
    start "" "%BAK_DIR%\\%EXE_NAME%"
    exit /b 1
)

powershell -NoProfile -Command "Expand-Archive -Path '%ZIP_PATH%' -DestinationPath '%APP_PARENT%' -Force" >nul 2>&1
if errorlevel 1 (
    move "%BAK_DIR%" "%APP_DIR%" >nul 2>&1
    if exist "%ZIP_PATH%" del /f /q "%ZIP_PATH%"
    start "" "%APP_DIR%\\%EXE_NAME%"
    exit /b 1
)

echo pending > "%FLAG_PENDING%"
start "" "%APP_DIR%\\%EXE_NAME%"

set /a count=0
:wait_verify
timeout /t 1 /nobreak >nul
set /a count+=1
if exist "%FLAG_VERIFIED%" (
    del /f /q "%FLAG_PENDING%" 2>nul
    del /f /q "%FLAG_VERIFIED%" 2>nul
    rmdir /s /q "%BAK_DIR%" 2>nul
    del /f /q "%ZIP_PATH%" 2>nul
    del /f /q "%BAT_SELF%" 2>nul
    exit /b 0
)
if %count% lss {T} goto wait_verify

taskkill /f /im "%EXE_NAME%" >nul 2>&1
timeout /t 2 /nobreak >nul
rmdir /s /q "%APP_DIR%" 2>nul
move "%BAK_DIR%" "%APP_DIR%" >nul 2>&1
del /f /q "%FLAG_PENDING%" 2>nul
del /f /q "%FLAG_VERIFIED%" 2>nul
start "" "%APP_DIR%\\%EXE_NAME%"
exit /b 1
"""

    # ---- 更新后验证 ----

    def is_post_update(self) -> bool:
        """检测是否由 updater.bat 启动(存在待验证标记)。"""
        return os.path.exists(os.path.join(self.app_dir, UPDATE_PENDING_FLAG))

    def mark_verified(self) -> None:
        """创建验证标记,通知 updater.bat 更新成功。"""
        path = os.path.join(self.app_dir, UPDATE_VERIFIED_FLAG)
        try:
            with open(path, "w") as f:
                f.write("verified")
            _log.info("update verified flag created")
        except OSError as e:
            _log.error("failed to write verified flag: %s", e)

    def schedule_verification(self, tk_root) -> None:
        """在 Tk 主循环上调度延迟验证(5 秒后标记成功)。

        如果 5 秒内应用崩溃,标记不会创建,updater.bat 将自动回滚。
        """
        tk_root.after(VERIFY_DELAY_SECONDS * 1000, self.mark_verified)

    # ---- 配置辅助 ----

    def should_auto_check(self) -> bool:
        """是否应该自动检查(考虑配置 + 24 小时冷却)。"""
        if not self.is_frozen:
            return False
        if not self.config.get("auto_check_update", True):
            return False
        last = self.config.get("last_update_check", "")
        if last:
            try:
                last_dt = datetime.fromisoformat(last)
                if (datetime.now() - last_dt).total_seconds() < 86400:
                    return False
            except (ValueError, TypeError):
                pass
        return True

    def should_skip_version(self, version: str) -> bool:
        return self.config.get("skip_update_version", "") == version

    def record_check(self) -> None:
        self.config.set("last_update_check", datetime.now().isoformat())

    def skip_version(self, version: str) -> None:
        self.config.set("skip_update_version", version)


# ---------------------------------------------------------------------------
# 后台检查(供 meowdesk_main.py 调用)
# ---------------------------------------------------------------------------

def start_background_check(window, config, app_dir: str) -> None:
    """启动后台线程检查更新,发现新版本后回调主线程显示对话框。

    线程为 daemon,不阻止进程退出。
    """
    mgr = UpdateManager(config, app_dir)

    if not mgr.should_auto_check():
        return

    def _worker():
        try:
            info = mgr.check_for_update()
            mgr.record_check()
            if not info:
                return
            if mgr.should_skip_version(info.version):
                return
            # 回到主线程显示对话框
            parent = getattr(window, "parent", None)
            if parent is None:
                return
            parent.after(0, lambda: _show_update_dialog(parent, mgr, info))
        except Exception:
            _log.exception("background update check failed")

    t = threading.Thread(target=_worker, daemon=True, name="ota-check")
    t.start()


def _show_update_dialog(parent, mgr: UpdateManager, info: UpdateInfo) -> None:
    """显示更新对话框(延迟导入避免循环依赖)。"""
    from .ui.update_dialog import show_update_dialog
    show_update_dialog(parent, mgr, info)
