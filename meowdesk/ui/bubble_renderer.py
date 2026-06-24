"""Bubble rendering for MeowDesk.

Draws a polished speech bubble with rounded corners, soft shadow,
and a downward arrow pointer above the cat image.
Supports multi-line text (lines separated by ``\\n``).
"""

from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .bubble_font import load_bubble_font

# ── Styling constants ──────────────────────────────────────────────
_FONT_SIZE = 13
_PADDING_X = 14
_PADDING_Y = 10
_LINE_SPACING = 4          # extra pixels between lines
_RADIUS = 12               # bubble corner radius
_ARROW_W = 14              # arrow base width
_ARROW_H = 8               # arrow height
_GAP = 6                   # gap between bubble bottom and cat top
_SHADOW_BLUR = 6           # shadow blur radius
_SHADOW_OFFSET = 2         # shadow y-offset
_MAX_WIDTH = 260           # max bubble width before wrapping

_FILL = (38, 34, 48, 230)          # dark semi-transparent fill
_OUTLINE = (244, 132, 95, 160)     # coral border
_TEXT_COLOR = (245, 240, 235, 255) # warm white
_SHADOW_COLOR = (0, 0, 0, 60)     # subtle shadow


def _wrap_lines(
    lines: List[str],
    font: ImageFont.FreeTypeFont,
    draw: ImageDraw.ImageDraw,
    max_width: int,
) -> List[str]:
    """Wrap lines so each fits within *max_width* pixels.

    Uses greedy character-by-character measurement for accurate
    CJK / mixed-width support.
    """
    wrapped: List[str] = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            wrapped.append(line)
            continue
        # Greedy wrap: accumulate chars until next char would overflow
        current = ""
        for ch in line:
            test = current + ch
            tw = draw.textbbox((0, 0), test, font=font)[2]
            if tw > max_width and current:
                wrapped.append(current)
                current = ch
            else:
                current = test
        if current:
            wrapped.append(current)
    return wrapped


def _measure_lines(
    lines: List[str],
    font: ImageFont.FreeTypeFont,
    draw: ImageDraw.ImageDraw,
) -> Tuple[List[Tuple[int, int]], int, int]:
    """Return per-line (width, height) and the total text block size."""
    sizes = []
    max_w = 0
    total_h = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        sizes.append((w, h))
        if w > max_w:
            max_w = w
        total_h += h
    total_h += _LINE_SPACING * max(0, len(lines) - 1)
    return sizes, max_w, total_h


def draw_bubble(
    frame: Image.Image,
    text: str,
    font_size: int = _FONT_SIZE,
    bubble_fill: Tuple[int, int, int, int] = _FILL,
    bubble_outline: Tuple[int, int, int, int] = _OUTLINE,
    text_color: Tuple[int, int, int, int] = _TEXT_COLOR,
) -> Image.Image:
    """Draw a speech bubble above the cat frame.

    Args:
        frame: The cat image (RGBA).
        text: Text to display (may contain ``\\n`` for multi-line).
        font_size: Font size in points.
        bubble_fill: Bubble background (RGBA).
        bubble_outline: Bubble border (RGBA).
        text_color: Text colour (RGBA).

    Returns:
        A new RGBA image with the bubble composited above the cat.
    """

    # ── Font ────────────────────────────────────────────────────────
    font = load_bubble_font(font_size)
    if font is None:
        font = ImageFont.load_default()

    # ── Split into lines, wrap long lines, and measure ─────────────
    raw_lines = text.split("\n") if "\n" in text else [text]
    dummy_draw = ImageDraw.Draw(frame)
    text_area_w = _MAX_WIDTH - _PADDING_X * 2
    lines = _wrap_lines(raw_lines, font, dummy_draw, text_area_w)
    line_sizes, text_max_w, text_total_h = _measure_lines(
        lines, font, dummy_draw
    )

    bubble_w = text_max_w + _PADDING_X * 2
    bubble_h = text_total_h + _PADDING_Y * 2

    # Ensure bubble doesn't exceed max width (wrapping should prevent this)
    if bubble_w > _MAX_WIDTH:
        bubble_w = _MAX_WIDTH

    # ── Canvas sizing ───────────────────────────────────────────────
    canvas_w = max(frame.width, bubble_w + _ARROW_W)
    canvas_h = frame.height + bubble_h + _ARROW_H + _GAP + _SHADOW_BLUR
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    # ── Paste cat at the bottom ─────────────────────────────────────
    cat_y = bubble_h + _ARROW_H + _GAP + _SHADOW_BLUR
    cat_x = (canvas_w - frame.width) // 2
    canvas.paste(frame, (cat_x, cat_y), frame)

    # ── Bubble position ─────────────────────────────────────────────
    bx = (canvas_w - bubble_w) // 2
    by = _SHADOW_BLUR  # leave room for shadow above
    bx2 = bx + bubble_w
    by2 = by + bubble_h

    draw = ImageDraw.Draw(canvas)

    # ── Shadow ──────────────────────────────────────────────────────
    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow_layer)
    sd.rounded_rectangle(
        [bx + _SHADOW_OFFSET, by + _SHADOW_OFFSET,
         bx2 + _SHADOW_OFFSET, by2 + _SHADOW_OFFSET],
        radius=_RADIUS,
        fill=_SHADOW_COLOR,
    )
    # Also shadow the arrow
    arrow_cx = canvas_w // 2
    sd.polygon(
        [
            (arrow_cx - _ARROW_W // 2 + _SHADOW_OFFSET,
             by2 + _SHADOW_OFFSET),
            (arrow_cx + _ARROW_W // 2 + _SHADOW_OFFSET,
             by2 + _SHADOW_OFFSET),
            (arrow_cx + _SHADOW_OFFSET,
             by2 + _ARROW_H + _SHADOW_OFFSET),
        ],
        fill=_SHADOW_COLOR,
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(_SHADOW_BLUR))
    canvas = Image.alpha_composite(canvas, shadow_layer)

    # Re-create draw on the composited canvas
    draw = ImageDraw.Draw(canvas)

    # ── Bubble body ─────────────────────────────────────────────────
    draw.rounded_rectangle(
        [bx, by, bx2, by2],
        radius=_RADIUS,
        fill=bubble_fill,
        outline=bubble_outline,
        width=1,
    )

    # ── Arrow (smoothed triangle) ───────────────────────────────────
    # Three-point triangle pointing down from bubble centre
    arrow_pts = [
        (arrow_cx - _ARROW_W // 2, by2 - 1),   # overlap 1px to hide seam
        (arrow_cx + _ARROW_W // 2, by2 - 1),
        (arrow_cx, by2 + _ARROW_H),
    ]
    draw.polygon(arrow_pts, fill=bubble_fill)
    # Draw outline on the two slanted sides only (skip the top edge)
    draw.line(
        [arrow_pts[0], arrow_pts[2], arrow_pts[1]],
        fill=bubble_outline, width=1,
    )

    # ── Text (multi-line) ───────────────────────────────────────────
    ty = by + _PADDING_Y
    for idx, line in enumerate(lines):
        lw, lh = line_sizes[idx]
        # Centre each line horizontally within the bubble
        tx = bx + (bubble_w - lw) // 2
        draw.text((tx, ty), line, fill=text_color, font=font)
        ty += lh + _LINE_SPACING

    return canvas
