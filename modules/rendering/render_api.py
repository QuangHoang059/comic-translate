from ast import Tuple
import os
from typing import List
from PIL import Image, ImageFont, ImageDraw
import numpy as np
from modules.utils.textblock import TextBlock
from .hyphen_textwrap import wrap as hyphen_wrap
import cv2

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


class TextRenderer:
    """Class để render text lên image"""

    def initialize(self, config: dict = {}):
        pass

    def __init__(self, config: dict):
        self.config = config
        self.font_size = config.get("font_size", 12)
        self.font_color = config.get("font_color", "#000000")
        self.background_color = config.get("background_color", "#FFFFFF")
        self.line_spacing = config.get("line_spacing", 1.2)
        self.font_path = "../../fonts/simfang.ttf"

    def render_text(self, image, text_blocks):
        """Render text lên image"""
        # Implementation sẽ được thêm sau
        return self.draw_text(
            image,
            text_blocks,
            self.font_path,
            self.font_size,
            self.font_color,
            self.background_color,
            self.line_spacing,
        )

    def draw_text(
        self,
        image: np.ndarray,
        blk_list: List[TextBlock],
        font_pth: str,
        colour: str = "#000",
        init_font_size: int = 40,
        min_font_size=10,
        outline: bool = True,
    ):
        image = cv2_to_pil(image)
        draw = ImageDraw.Draw(image)

        font = ImageFont.truetype(font_pth, size=init_font_size)

        for blk in blk_list:
            x1, y1, width, height = blk.xywh
            tbbox_top_left = (x1, y1)

            translation = blk.translation
            if not translation or len(translation) == 1:
                continue

            if blk.min_font_size > 0:
                min_font_size = blk.min_font_size
            if blk.max_font_size > 0:
                init_font_size = blk.max_font_size
            if blk.font_color:
                colour = blk.font_color

            translation, font_size = pil_word_wrap(
                image,
                tbbox_top_left,
                font_pth,
                translation,
                width,
                height,
                align=blk.alignment,
                spacing=blk.line_spacing,
                init_font_size=init_font_size,
                min_font_size=min_font_size,
            )
            font = font.font_variant(size=font_size)

            # Font Detection Workaround. Draws white color offset around text
            if outline:
                offsets = [
                    (dx, dy)
                    for dx in (-2, -1, 0, 1, 2)
                    for dy in (-2, -1, 0, 1, 2)
                    if dx != 0 or dy != 0
                ]
                for dx, dy in offsets:
                    draw.multiline_text(
                        (tbbox_top_left[0] + dx, tbbox_top_left[1] + dy),
                        translation,
                        font=font,
                        fill="#FFF",
                        align=blk.alignment,
                        spacing=1,
                    )
            draw.multiline_text(
                tbbox_top_left,
                translation,
                colour,
                font,
                align=blk.alignment,
                spacing=1,
            )

        image = pil_to_cv2(image)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image


def cv2_to_pil(cv2_image: np.ndarray):
    # Convert color channels from BGR to RGB
    rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    # Convert the NumPy array to a PIL Image
    pil_image = Image.fromarray(rgb_image)
    return pil_image


def pil_to_cv2(pil_image: Image):
    # Convert the PIL image to a numpy array
    numpy_image = np.array(pil_image)

    # PIL images are in RGB by default, OpenCV uses BGR, so convert the color space
    cv2_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)

    return cv2_image


def pil_word_wrap(
    image: Image,
    tbbox_top_left: Tuple,
    font_pth: str,
    text: str,
    roi_width,
    roi_height,
    align: str,
    spacing,
    init_font_size: int,
    min_font_size: int = 10,
):
    """Break long text to multiple lines, and reduce point size
    until all text fits within a bounding box."""
    mutable_message = text
    font_size = init_font_size
    font = ImageFont.truetype(font_pth, font_size)

    def eval_metrics(txt, font):
        """Quick helper function to calculate width/height of text."""
        (left, top, right, bottom) = ImageDraw.Draw(image).multiline_textbbox(
            xy=tbbox_top_left, text=txt, font=font, align=align, spacing=spacing
        )
        return (right - left, bottom - top)

    while font_size > min_font_size:
        font = font.font_variant(size=font_size)
        width, height = eval_metrics(mutable_message, font)
        if height > roi_height:
            font_size -= 0.75  # Reduce pointsize
            mutable_message = text  # Restore original text
        elif width > roi_width:
            columns = len(mutable_message)
            while columns > 0:
                columns -= 1
                if columns == 0:
                    break
                mutable_message = "\n".join(
                    hyphen_wrap(
                        text,
                        columns,
                        break_on_hyphens=False,
                        break_long_words=False,
                        hyphenate_broken_words=True,
                    )
                )
                wrapped_width, _ = eval_metrics(mutable_message, font)
                if wrapped_width <= roi_width:
                    break
            if columns < 1:
                font_size -= 0.75  # Reduce pointsize
                mutable_message = text  # Restore original text
        else:
            break

    if font_size <= min_font_size:
        font_size = min_font_size
        mutable_message = text
        font = font.font_variant(size=font_size)

        # Wrap text to fit within as much as possible
        # Minimize cost function: (width - roi_width)^2 + (height - roi_height)^2
        # This is a brute force approach, but it works well enough
        min_cost = 1e9
        min_text = text
        for columns in range(1, len(text)):
            wrapped_text = "\n".join(
                hyphen_wrap(
                    text,
                    columns,
                    break_on_hyphens=False,
                    break_long_words=False,
                    hyphenate_broken_words=True,
                )
            )
            wrapped_width, wrapped_height = eval_metrics(wrapped_text, font)
            cost = (wrapped_width - roi_width) ** 2 + (wrapped_height - roi_height) ** 2
            if cost < min_cost:
                min_cost = cost
                min_text = wrapped_text

        mutable_message = min_text

    return mutable_message, font_size
