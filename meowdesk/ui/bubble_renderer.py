"""Bubble rendering for MeowDesk.

Draws a rounded speech bubble with an arrow pointer above
the cat image. Handles sizing, positioning, and styling.
"""

from typing import Tuple

from PIL import Image, ImageDraw, ImageFont

from .bubble_font import load_bubble_font


def draw_bubble(
    frame: Image.Image,
    text: str,
    font_size: int = 14,
    bubble_fill: Tuple[int, int, int, int] = (40, 35, 50, 220),
    bubble_outline: Tuple[int, int, int, int] = (244, 132, 95, 180),
    text_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
) -> Image.Image:
    """Draw a speech bubble above the cat frame.

    Args:
        frame: The cat image (RGBA).
        text: Text to display in the bubble.
        font_size: Font size in points.
        bubble_fill: Bubble background color (RGBA).
        bubble_outline: Bubble border color (RGBA).
        text_color: Text color (RGBA).

    Returns:
        A new RGBA image with the bubble composited above the cat.
    """

    font = load_bubble_font(font_size)
    if font is None:
        font = ImageFont.load_default()

    dummy_draw = ImageDraw.Draw(frame)
    bbox = dummy_draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    padding = 8
    bubble_height = text_height + padding * 2
    bubble_width = text_width + padding * 2 + 20

    new_width = max(frame.width, bubble_width)
    new_height = frame.height + bubble_height + 8
    new_frame = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))
    cat_x = (new_width - frame.width) // 2
    new_frame.paste(frame, (cat_x, bubble_height + 8))

    draw = ImageDraw.Draw(new_frame)
    bubble_x = (new_width - bubble_width) // 2
    bubble_y = 0
    draw.rounded_rectangle(
        [bubble_x, bubble_y, bubble_x + bubble_width, bubble_y + bubble_height],
        radius=8,
        fill=bubble_fill,
        outline=bubble_outline,
        width=1,
    )
    text_x = bubble_x + padding + 10
    text_y = bubble_y + padding
    draw.text((text_x, text_y), text, fill=text_color, font=font)

    arrow_cx = new_width // 2
    arrow_top = bubble_y + bubble_height
    draw.polygon(
        [(arrow_cx - 6, arrow_top), (arrow_cx + 6, arrow_top), (arrow_cx, arrow_top + 8)],
        fill=bubble_fill,
    )
    return new_frame
