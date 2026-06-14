"""Platform window factory.

Creates the appropriate platform-specific window implementation
based on the current operating system.
"""

import sys

from ..platform.base import PlatformWindow


def create_platform_window(width: int, height: int) -> PlatformWindow:
    """Create a platform-specific window.

    Args:
        width: Window width in pixels.
        height: Window height in pixels.

    Returns:
        A PlatformWindow instance for the current platform.

    Raises:
        NotImplementedError: If the current platform is not supported.
    """

    if sys.platform == "win32":
        from ..platform.windows import WindowsWindow
        return WindowsWindow(width, height)
    elif sys.platform == "darwin":
        from ..platform.macos import MacOSWindow
        return MacOSWindow(width, height)
    else:
        raise NotImplementedError(f"不支持的平台：{sys.platform}")
