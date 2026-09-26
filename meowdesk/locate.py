"""Reveal an archived file in the system file manager.

The navigation page is a static ``file://`` document, so the browser cannot
start Explorer itself.  "定位" uses the ``meow-locate:`` URL protocol.

The payload is a URL-safe token in the path (``meow-locate://locate/<token>``),
not the host.  Chromium lowercases custom-protocol hosts, which corrupts a
case-sensitive token, and standard base64 ``/`` ``+`` ``=`` breaks the URL.
"""

from __future__ import annotations

import base64
import logging
import os
import subprocess
import sys
from typing import Optional, Sequence, Tuple
from urllib.parse import unquote

from .utils import get_logger

_log = get_logger(__name__)

LOCATE_SCHEME = "meow-locate"
_LOCATE_HOST = "locate"
RevealTarget = Tuple[str, str]


def encode_locate_token(path: str) -> str:
    """Encode an absolute path as a URL-safe token without padding."""

    absolute = os.path.abspath(path)
    token = base64.urlsafe_b64encode(absolute.encode("utf-8")).decode("ascii")
    return token.rstrip("=")


def locate_protocol_url(path: str) -> str:
    """Build a ``meow-locate:`` URL that survives browser canonicalization."""

    return f"{LOCATE_SCHEME}://{_LOCATE_HOST}/{encode_locate_token(path)}"


def decode_locate_token(token: str) -> Optional[str]:
    """Decode a locate token. Returns None unless it is an absolute path."""

    token = unquote(token or "").strip().strip("/")
    if not token or token.lower() == _LOCATE_HOST:
        return None
    token = token.split("?", 1)[0].split("#", 1)[0].strip()
    if not token:
        return None
    padded = token + ("=" * (-len(token) % 4))
    for decoder in (base64.urlsafe_b64decode, base64.b64decode):
        try:
            path = decoder(padded).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            continue
        path = path.strip().strip("\x00")
        if path and _is_absolute_path(path) and "\n" not in path and "\r" not in path:
            return os.path.normpath(path)
    return None


def decode_locate_url(raw: str) -> Optional[str]:
    """Parse a protocol URL, a bare token, or a quoted/slash-suffixed variant."""

    if not raw:
        return None
    text = unquote(str(raw).strip().strip('"').strip("'")).strip().strip('"')
    lowered = text.lower()
    for prefix in (
        f"{LOCATE_SCHEME}://",
        "lingxi-locate://",
        f"{LOCATE_SCHEME}:",
        "lingxi-locate:",
    ):
        if lowered.startswith(prefix):
            text = text[len(prefix):]
            break
    parts = [part for part in text.strip().strip("/").split("/") if part]
    if not parts:
        return None
    if parts[0].lower() == _LOCATE_HOST and len(parts) >= 2:
        token = parts[1]
    else:
        token = parts[0]
    return decode_locate_token(token)


def resolve_reveal_target(path: str) -> Optional[RevealTarget]:
    """Choose select-file or open-parent. None if nothing on disk can be shown."""

    if not path:
        return None
    normalized = os.path.normpath(os.path.abspath(path))
    if os.path.exists(normalized):
        return ("select", normalized)
    parent = os.path.dirname(normalized)
    if parent and os.path.isdir(parent):
        return ("open", parent)
    return None


def reveal_in_file_manager(path: str) -> bool:
    """Open the file manager with ``path`` selected, or its parent if missing."""

    resolved = resolve_reveal_target(path)
    if resolved is None:
        _log.warning("locate target not found: %s", path)
        return False
    action, target = resolved
    try:
        if sys.platform == "win32":
            return _reveal_windows(target, action)
        if sys.platform == "darwin":
            return _reveal_darwin(target, action)
        return _reveal_xdg(target, action)
    except OSError:
        _log.exception("failed to reveal %s", target)
        return False


def extract_locate_argument(argv: Sequence[str]) -> Optional[str]:
    """Return the raw URL when this process was started as the protocol handler."""

    if not argv:
        return None
    if argv[0] == "--locate":
        return argv[1] if len(argv) > 1 else ""
    blob = " ".join(argv)
    lowered = blob.lower()
    if f"{LOCATE_SCHEME}://" in lowered or "lingxi-locate://" in lowered:
        return blob
    return None


def handle_locate_invocation(argv: Sequence[str]) -> bool:
    """Handle ``--locate`` and return True if the GUI must not start."""

    raw = extract_locate_argument(argv)
    if raw is None:
        return False
    _configure_locate_log()
    try:
        path = decode_locate_url(raw)
        if not path:
            _log.warning("could not decode locate url: %s", raw)
            return True
        if not reveal_in_file_manager(path):
            _log.warning("could not reveal locate target: %s", path)
            _notify_failure(f"找不到文件，无法在资源管理器中定位：\n{path}")
    except Exception:
        _log.exception("locate handler failed")
    return True


def build_locate_command() -> str:
    """Command line stored in the protocol handler registry value."""

    exe = _handler_executable()
    if getattr(sys, "frozen", False):
        return f'"{exe}" --locate "%1"'
    script = _main_script()
    return f'"{exe}" "{script}" --locate "%1"'


def register_locate_protocol() -> bool:
    """Register ``meow-locate:`` for the current user. No-op off Windows."""

    if sys.platform != "win32":
        return False
    import winreg

    command = build_locate_command()
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\meow-locate") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "URL:MeowDesk Locate Protocol")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
            with winreg.CreateKey(key, r"shell\open\command") as shell:
                winreg.SetValueEx(shell, "", 0, winreg.REG_SZ, command)
            with winreg.CreateKey(key, "Application") as app:
                winreg.SetValueEx(app, "ApplicationName", 0, winreg.REG_SZ, "妙喵桌宠")
        _log.info("registered meow-locate protocol: %s", command)
        return True
    except OSError:
        _log.exception("failed to register meow-locate protocol")
        return False


def _is_absolute_path(path: str) -> bool:
    if os.path.isabs(path):
        return True
    return len(path) >= 3 and path[1] == ":" and path[2] in "\\/"


def _handler_executable() -> str:
    exe = sys.executable
    if getattr(sys, "frozen", False):
        return exe
    if exe.lower().endswith("python.exe"):
        pythonw = exe[: -len("python.exe")] + "pythonw.exe"
        if os.path.isfile(pythonw):
            return pythonw
    return exe


def _main_script() -> str:
    package_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(package_dir), "meowdesk_main.py")


def _explorer_exe() -> str:
    root = os.environ.get("SystemRoot", r"C:\Windows")
    return os.path.join(root, "explorer.exe")


def _reveal_windows(path: str, action: str) -> bool:
    if action == "select":
        try:
            if _shell_select(path):
                return True
        except (OSError, AttributeError, ValueError):
            _log.exception("SHOpenFolderAndSelectItems failed for %s", path)
        if '"' in path:
            return False
        # The comma must stay attached. A separate "/select," argument makes
        # Explorer open the default folder and look like nothing happened.
        subprocess.Popen([_explorer_exe(), f"/select,{path}"])
        return True
    os.startfile(path)
    return True


def _shell_select(path: str) -> bool:
    """Select ``path`` via the shell API. A file PIDL with cidl=0 is the supported form."""

    import ctypes
    from ctypes import wintypes

    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    ole32 = ctypes.WinDLL("ole32", use_last_error=True)

    ole32.CoInitialize.argtypes = [ctypes.c_void_p]
    ole32.CoInitialize.restype = ctypes.c_long
    ole32.CoUninitialize.argtypes = []
    ole32.CoUninitialize.restype = None

    shell32.ILCreateFromPathW.argtypes = [wintypes.LPCWSTR]
    shell32.ILCreateFromPathW.restype = ctypes.c_void_p
    shell32.ILFree.argtypes = [ctypes.c_void_p]
    shell32.ILFree.restype = None
    shell32.SHOpenFolderAndSelectItems.argtypes = [
        ctypes.c_void_p,
        wintypes.UINT,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    shell32.SHOpenFolderAndSelectItems.restype = ctypes.c_long

    hr_init = ole32.CoInitialize(None)
    owns_com = hr_init == 0
    pidl = None
    try:
        pidl = shell32.ILCreateFromPathW(path)
        if not pidl:
            return False
        hr = shell32.SHOpenFolderAndSelectItems(pidl, 0, None, 0)
        return hr == 0
    finally:
        if pidl:
            shell32.ILFree(pidl)
        if owns_com:
            ole32.CoUninitialize()


def _reveal_darwin(path: str, action: str) -> bool:
    if action == "select":
        subprocess.Popen(["open", "-R", path])
    else:
        subprocess.Popen(["open", path])
    return True


def _reveal_xdg(path: str, action: str) -> bool:
    folder = os.path.dirname(path) if action == "select" else path
    subprocess.Popen(["xdg-open", folder or path])
    return True


def _notify_failure(message: str) -> None:
    _log.warning(message)
    if sys.platform != "win32" or os.environ.get("PYTEST_CURRENT_TEST"):
        return
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.MessageBoxW.argtypes = [
        wintypes.HWND,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.UINT,
    ]
    user32.MessageBoxW.restype = ctypes.c_int
    # MB_OK | MB_ICONWARNING | MB_SETFOREGROUND | MB_TOPMOST
    user32.MessageBoxW(None, message, "妙喵桌宠", 0x00050030)


def _configure_locate_log() -> None:
    if os.environ.get("PYTEST_CURRENT_TEST") or sys.platform != "win32":
        return
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        return
    path = os.path.join(base, "MeowDesk", "locate.log")
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        handler = logging.FileHandler(path, encoding="utf-8")
    except OSError:
        return
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger = logging.getLogger("meowdesk.locate")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
