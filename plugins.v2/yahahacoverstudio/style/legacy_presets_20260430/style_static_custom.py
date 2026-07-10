import base64
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, List, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.log import logger
from app.plugins.yahahacoverstudio.utils.image_manager import (
    ResolutionConfig,
    managed_image,
)
from app.plugins.yahahacoverstudio.utils.performance_helper import (
    memory_efficient_operation,
)
from app.plugins.yahahacoverstudio.utils.color_helper import ColorHelper


def _compat_textsize(self, text: str, font=None, *args, **kwargs):
    try:
        left, top, right, bottom = self.textbbox((0, 0), text, font=font, *args, **kwargs)
        return right - left, bottom - top
    except Exception:
        try:
            width = self.textlength(text, font=font, *args, **kwargs)
            return width, float(getattr(font, "size", 0) or 0)
        except Exception:
            if font is not None and hasattr(font, "getbbox"):
                bbox = font.getbbox(text)
                return bbox[2] - bbox[0], bbox[3] - bbox[1]
            return 0.0, 0.0


if not hasattr(ImageDraw.ImageDraw, "textsize"):
    ImageDraw.ImageDraw.textsize = _compat_textsize


ALPHA_MODES = {"RGBA", "LA", "PA"}
EDITOR_BASE_WIDTH = 1920.0
EDITOR_BASE_HEIGHT = 1080.0


def _load_font(font_path: str, size: float) -> ImageFont.FreeTypeFont:
    size_int = max(1, int(round(float(size))))
    return ImageFont.truetype(font_path, size_int)


def _measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> Tuple[float, float]:
    try:
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        return right - left, bottom - top
    except Exception:
        try:
            return draw.textlength(text, font=font), float(getattr(font, "size", 0) or 0)
        except Exception:
            bbox = font.getbbox(text)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _encode_image_to_base64(image: Image.Image, format: str = "auto", quality: int = 85) -> str:
    buffer = BytesIO()
    save_format = (format or "auto").lower()
    has_alpha = image.mode in ALPHA_MODES or "A" in image.getbands() or image.info.get("transparency") is not None

    if save_format == "auto":
        if has_alpha:
            save_format = "png"
        else:
            try:
                image.save(buffer, format="WEBP", quality=quality, optimize=True)
                return base64.b64encode(buffer.getvalue()).decode("utf-8")
            except Exception:
                save_format = "jpeg"

    if save_format == "png":
        image.save(buffer, format="PNG", optimize=True)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    if save_format == "jpeg":
        rgb_image = image.convert("RGB") if image.mode != "RGB" else image
        rgb_image.save(buffer, format="JPEG", quality=quality, optimize=True, progressive=True)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    raise ValueError(f"Unsupported format: {save_format}")


def _create_background(
    source_image_path: str,
    resolution_config: ResolutionConfig,
    blur_size: int,
    color_ratio: float,
    bg_color_config: Dict[str, Any] | None,
) -> Image.Image:
    """根据静态样式 1 的逻辑，生成模糊 + 颜色混合背景。"""
    canvas_size = resolution_config.size

    with managed_image(source_image_path, "RGB") as original_img:
        if bg_color_config:
            bg_color = ColorHelper.get_background_color(
                original_img,
                color_mode=bg_color_config.get("mode", "auto"),
                custom_color=bg_color_config.get("custom_color"),
                config_color=bg_color_config.get("config_color"),
            )
            logger.info(
                "custom_static: 使用背景颜色 %s (mode=%s)",
                bg_color,
                bg_color_config.get("mode", "auto"),
            )
        else:
            bg_color = ColorHelper.get_background_color(original_img)

        bg = original_img.resize(canvas_size, Image.Resampling.LANCZOS)
        if blur_size and blur_size > 0:
            bg = bg.filter(ImageFilter.GaussianBlur(radius=int(blur_size)))

        color_layer = Image.new("RGB", canvas_size, bg_color)
        ratio = float(color_ratio) if 0 <= float(color_ratio) <= 1 else 0.8
        blend = Image.blend(bg, color_layer, ratio)
        return blend.convert("RGBA")


def _draw_image_layer(
    canvas: Image.Image,
    layer: Dict[str, Any],
    image_slots: Dict[int, str],
    scale_x: float,
    scale_y: float,
) -> None:
    source_index = int(layer.get("sourceIndex", 1))
    path = image_slots.get(source_index)
    if not path:
        logger.warning("custom_static: 找不到 sourceIndex=%s 对应的图片", source_index)
        return

    x = float(layer.get("x", 0)) * scale_x
    y = float(layer.get("y", 0)) * scale_y
    width = float(layer.get("width", 0)) * scale_x
    height = float(layer.get("height", 0)) * scale_y
    rotation = float(layer.get("rotation", 0))
    radius = float(layer.get("radius", 0)) * min(scale_x, scale_y)
    opacity = max(0.0, min(1.0, float(layer.get("opacity", 1) or 1)))
    blur = max(0.0, float(layer.get("blur", 0) or 0) * min(scale_x, scale_y))
    shadow_blur = max(0.0, float(layer.get("shadowBlur", 0) or 0) * min(scale_x, scale_y))
    shadow_offset_x = float(layer.get("shadowOffsetX", 0) or 0) * scale_x
    shadow_offset_y = float(layer.get("shadowOffsetY", 0) or 0) * scale_y
    shadow_opacity = max(0.0, min(1.0, float(layer.get("shadowOpacity", 0.28) or 0.28)))

    pivot_x = float(layer.get("pivotX", 0.5))
    pivot_y = float(layer.get("pivotY", 0.5))
    pivot_x = 0.0 if pivot_x < 0.0 else 1.0 if pivot_x > 1.0 else pivot_x
    pivot_y = 0.0 if pivot_y < 0.0 else 1.0 if pivot_y > 1.0 else pivot_y
    crop_focus_x = float(layer.get("cropFocusX", 0.5) or 0.5)
    crop_focus_y = float(layer.get("cropFocusY", 0.5) or 0.5)
    crop_focus_x = 0.0 if crop_focus_x < 0.0 else 1.0 if crop_focus_x > 1.0 else crop_focus_x
    crop_focus_y = 0.0 if crop_focus_y < 0.0 else 1.0 if crop_focus_y > 1.0 else crop_focus_y

    if width <= 0 or height <= 0:
        return

    with managed_image(path, "RGB") as img:
        img = img.copy()
        img_ratio = img.width / img.height if img.height > 0 else 1
        target_ratio = width / height if height > 0 else 1

        if img_ratio > target_ratio:
            new_height = img.height
            new_width = int(new_height * target_ratio)
            available = max(0, img.width - new_width)
            left = int(round(available * crop_focus_x))
            img = img.crop((left, 0, left + new_width, new_height))
        else:
            new_width = img.width
            new_height = int(new_width / target_ratio)
            available = max(0, img.height - new_height)
            top = int(round(available * crop_focus_y))
            img = img.crop((0, top, new_width, top + new_height))

        target_size = (max(1, int(round(width))), max(1, int(round(height))))
        img = img.resize(target_size, Image.Resampling.LANCZOS).convert("RGBA")

        if radius and radius > 0:
            mask = Image.new("L", img.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle(
                [(0, 0), (img.size[0], img.size[1])],
                radius=int(round(radius)),
                fill=255,
            )
            rounded = Image.new("RGBA", img.size)
            rounded.paste(img, (0, 0), mask)
            img = rounded

        if blur > 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=blur))

        if opacity < 1:
            alpha = img.getchannel("A")
            alpha = alpha.point(lambda value: int(value * opacity))
            img.putalpha(alpha)

        if shadow_blur > 0 or shadow_offset_x != 0 or shadow_offset_y != 0:
            shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
            alpha_mask = img.getchannel("A")
            shadow_alpha = alpha_mask.point(lambda value: int(value * shadow_opacity))
            shadow.paste((0, 0, 0, 255), (0, 0), shadow_alpha)
            shadow = shadow.filter(ImageFilter.GaussianBlur(radius=max(1, shadow_blur)))
            canvas.alpha_composite(
                shadow,
                (
                    int(round(x + shadow_offset_x)),
                    int(round(y + shadow_offset_y)),
                ),
            )

        if rotation:
            pivot_px = target_size[0] * pivot_x
            pivot_py = target_size[1] * pivot_y
            img = img.rotate(
                rotation,
                resample=Image.BICUBIC,
                expand=False,
                center=(pivot_px, pivot_py),
            )

        paste_x = int(round(x))
        paste_y = int(round(y))
        canvas.alpha_composite(img, (paste_x, paste_y))


def _draw_title_layer(
    canvas: Image.Image,
    layer: Dict[str, Any],
    text: str,
    font_path: str,
    scale_x: float,
    scale_y: float,
) -> None:
    layout = measure_text_layer(
        layer=layer,
        text=text,
        font_path=font_path,
        scale_x=scale_x,
        scale_y=scale_y,
    )
    if not layout:
        return

    x = float(layout["frame"]["x"])
    y = float(layout["frame"]["y"])
    width = float(layout["frame"]["width"])
    height = float(layout["frame"]["height"])
    rotation = float(layout["rotation"])
    opacity = float(layout["opacity"])
    blur = float(layout["blur"])
    shadow_blur = float(layout["shadow"]["blur"])
    shadow_offset_x = float(layout["shadow"]["offset_x"])
    shadow_offset_y = float(layout["shadow"]["offset_y"])
    shadow_opacity = float(layout["shadow"]["opacity"])
    pivot_x = float(layout["pivot"]["x"])
    pivot_y = float(layout["pivot"]["y"])
    font = _load_font(font_path, float(layout["font_size"]))

    text_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    shadow_draw = ImageDraw.Draw(shadow_layer)
    for line_info in layout["lines"]:
        line = str(line_info["text"])
        line_x = float(line_info["x"])
        line_y = float(line_info["y"])
        shadow_draw.text(
            (line_x + shadow_offset_x, line_y + shadow_offset_y),
            line,
            font=font,
            fill=(0, 0, 0, int(255 * shadow_opacity)),
        )
        draw.text((line_x, line_y), line, font=font, fill=(255, 255, 255, 255))

    if shadow_blur > 0:
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=max(1, shadow_blur)))

    if blur > 0:
        text_layer = text_layer.filter(ImageFilter.GaussianBlur(radius=blur))

    if opacity < 1:
        alpha = text_layer.getchannel("A")
        alpha = alpha.point(lambda value: int(value * opacity))
        text_layer.putalpha(alpha)

    if rotation:
        center_x = x + width * pivot_x
        center_y = y + height * pivot_y
        shadow_layer = shadow_layer.rotate(
            rotation,
            resample=Image.BICUBIC,
            expand=False,
            center=(center_x, center_y),
        )
        text_layer = text_layer.rotate(
            rotation,
            resample=Image.BICUBIC,
            expand=False,
            center=(center_x, center_y),
        )

    canvas.alpha_composite(shadow_layer)
    canvas.alpha_composite(text_layer)


def measure_text_layer(
    layer: Dict[str, Any],
    text: str,
    font_path: str,
    scale_x: float,
    scale_y: float,
) -> Dict[str, Any] | None:
    if not text:
        return None

    x = float(layer.get("x", 0)) * scale_x
    y = float(layer.get("y", 0)) * scale_y
    width = float(layer.get("width", 0)) * scale_x
    height = float(layer.get("height", 0)) * scale_y
    rotation = float(layer.get("rotation", 0))
    font_size = float(layer.get("fontSize", 0)) * min(scale_x, scale_y)
    opacity = max(0.0, min(1.0, float(layer.get("opacity", 1) or 1)))
    blur = max(0.0, float(layer.get("blur", 0) or 0) * min(scale_x, scale_y))
    shadow_blur = max(0.0, float(layer.get("shadowBlur", 12) or 12) * min(scale_x, scale_y))
    shadow_offset_x = float(layer.get("shadowOffsetX", 0) or 0) * scale_x
    shadow_offset_y = float(layer.get("shadowOffsetY", 8) or 8) * scale_y
    shadow_opacity = max(0.0, min(1.0, float(layer.get("shadowOpacity", 0.24) or 0.24)))
    pivot_x = float(layer.get("pivotX", 0.5))
    pivot_y = float(layer.get("pivotY", 0.5))
    pivot_x = 0.0 if pivot_x < 0.0 else 1.0 if pivot_x > 1.0 else pivot_x
    pivot_y = 0.0 if pivot_y < 0.0 else 1.0 if pivot_y > 1.0 else pivot_y

    if width <= 0 or height <= 0 or font_size <= 0:
        return None

    font = _load_font(font_path, font_size)
    measure_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    draw = ImageDraw.Draw(measure_img)

    max_width = width
    lines: List[str] = []
    current = ""
    for ch in text:
        candidate = current + ch
        measured_width, _ = _measure_text(draw, candidate, font)
        if measured_width <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = ch
    if current:
        lines.append(current)

    line_height = font_size * 1.1
    total_height = line_height * len(lines)
    start_y = y + (height - total_height) / 2
    measured_lines: List[Dict[str, Any]] = []
    for index, line in enumerate(lines):
        line_width, line_box_height = _measure_text(draw, line, font)
        line_x = x + (width - line_width) / 2
        line_y = start_y + index * line_height
        measured_lines.append({
            "text": line,
            "x": float(line_x),
            "y": float(line_y),
            "width": float(line_width),
            "height": float(line_box_height),
        })

    return {
        "text": text,
        "font_size": float(font_size),
        "line_height": float(line_height),
        "frame": {
            "x": float(x),
            "y": float(y),
            "width": float(width),
            "height": float(height),
        },
        "rotation": float(rotation),
        "opacity": float(opacity),
        "blur": float(blur),
        "pivot": {"x": float(pivot_x), "y": float(pivot_y)},
        "shadow": {
            "blur": float(shadow_blur),
            "offset_x": float(shadow_offset_x),
            "offset_y": float(shadow_offset_y),
            "opacity": float(shadow_opacity),
        },
        "lines": measured_lines,
    }


@memory_efficient_operation
def create_style_static_custom(
    image_slots: Dict[int, str],
    title: Tuple[str, str],
    font_path: Tuple[str, str, str],
    layout_config: Dict[str, Any] | None,
    blur_size: int,
    color_ratio: float,
    resolution_config: ResolutionConfig,
    bg_color_config: Dict[str, Any] | None,
) -> str:
    if not layout_config or not isinstance(layout_config, dict):
        logger.error("custom_static: 布局配置无效，使用默认配置失败")
        return ""

    layers = layout_config.get("layers") or []
    if not layers:
        logger.error("custom_static: 布局中没有任何图层")
        return ""

    zh_title, en_title = title
    main_title_font_path, subtitle_font_path, custom_text_font_path = font_path

    first_image_path = None
    for slot_index in sorted(image_slots.keys()):
        path = image_slots.get(slot_index)
        if path and Path(path).is_file():
            first_image_path = path
            break
    if not first_image_path:
        logger.error("custom_static: 未找到任何可用的源图片")
        return ""

    blur_val = int(blur_size) if blur_size is not None else 50
    color_ratio_val = float(color_ratio) if color_ratio is not None else 0.8

    canvas = _create_background(
        first_image_path,
        resolution_config,
        blur_val,
        color_ratio_val,
        bg_color_config,
    )

    canvas_width, canvas_height = resolution_config.size
    scale_x = canvas_width / EDITOR_BASE_WIDTH if EDITOR_BASE_WIDTH > 0 else 1.0
    scale_y = canvas_height / EDITOR_BASE_HEIGHT if EDITOR_BASE_HEIGHT > 0 else 1.0

    sorted_layers = sorted(layers, key=lambda l: int(l.get("zIndex", 0)))
    for layer in sorted_layers:
        l_type = layer.get("type")
        if l_type == "image":
            _draw_image_layer(canvas, layer, image_slots, scale_x, scale_y)
        elif l_type in ("main_title", "title_zh"):
            _draw_title_layer(canvas, layer, zh_title, main_title_font_path, scale_x, scale_y)
        elif l_type in ("subtitle", "title_en"):
            _draw_title_layer(canvas, layer, en_title, subtitle_font_path, scale_x, scale_y)
        elif l_type == "text":
            custom_text = str(layer.get("content") or "").strip()
            if not custom_text:
                continue
            font_family = str(layer.get("fontFamily") or "main_title")
            if font_family == "subtitle":
                text_font_path = subtitle_font_path
            elif font_family == "custom_text":
                text_font_path = custom_text_font_path
            else:
                text_font_path = main_title_font_path
            _draw_title_layer(canvas, layer, custom_text, text_font_path, scale_x, scale_y)

    return _encode_image_to_base64(canvas)
