"""Platform-specific font loading for bubble rendering.

Provides a single function to load an appropriate font for
Chinese/English text rendering on Windows and macOS.
"""

import sys
from typing import Optional

from PIL import ImageFont


def load_bubble_font(size: int = 14) -> Optional[ImageFont.FreeTypeFont]:
    """Load a font suitable for bubble text.

    Tries platform-specific fonts first (PingFang on macOS,
    Microsoft YaHei on Windows), then falls back to common
    fonts, and finally to the default built-in font.

    Args:
        size: Font size in points. Default is 14.

    Returns:
        A PIL ImageFont, or None if no font could be loaded
        (in which case callers should use load_default()).
    """

    font: Optional[ImageFont.FreeTypeFont] = None

    if sys.platform == "darwin":
        for fp in (
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ):
            try:
                font = ImageFont.truetype(fp, size)
                return font
            except OSError:
                continue
    else:
        for fp in ("msyh.ttc", "arial.ttf"):
            try:
                font = ImageFont.truetype(fp, size)
                return font
            except OSError:
                continue

    return None
