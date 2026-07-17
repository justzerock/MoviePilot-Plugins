import base64
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, List, Tuple, Union

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
from app.plugins.yahahacoverstudio.template_renderer import render_template_to_base64


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


def _float_value(value: Any, fallback: float) -> float:
    if value is None:
        return fallback
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _apply_film_grain(image: Image.Image, intensity: Any) -> Image.Image:
    amount = max(0.0, min(1.0, _float_value(intensity, 0)))
    if amount <= 0:
        return image
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    noise = Image.effect_noise(rgba.size, max(2, amount * 42)).convert("RGB")
    grained = Image.blend(rgba.convert("RGB"), noise, min(0.24, amount * 0.22)).convert("RGBA")
    grained.putalpha(alpha)
    return grained


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
        grain = (bg_color_config or {}).get("grain", 0)
        return _apply_film_grain(blend.convert("RGBA"), grain)


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
    opacity = max(0.0, min(1.0, _float_value(layer.get("opacity"), 1)))
    blur = max(0.0, _float_value(layer.get("blur"), 0) * min(scale_x, scale_y))
    grain = max(0.0, min(1.0, _float_value(layer.get("grain", (layer.get("effects") or {}).get("grain")), 0)))
    shadow_blur = max(0.0, _float_value(layer.get("shadowBlur"), 0) * min(scale_x, scale_y))
    shadow_offset_x = _float_value(layer.get("shadowOffsetX"), 0) * scale_x
    shadow_offset_y = _float_value(layer.get("shadowOffsetY"), 0) * scale_y
    shadow_opacity = max(0.0, min(1.0, _float_value(layer.get("shadowOpacity"), 0.28)))

    pivot_x = float(layer.get("pivotX", 0.5))
    pivot_y = float(layer.get("pivotY", 0.5))
    pivot_x = 0.0 if pivot_x < 0.0 else 1.0 if pivot_x > 1.0 else pivot_x
    pivot_y = 0.0 if pivot_y < 0.0 else 1.0 if pivot_y > 1.0 else pivot_y
    crop_focus_x = _float_value(layer.get("cropFocusX"), 0.5)
    crop_focus_y = _float_value(layer.get("cropFocusY"), 0.5)
    crop_focus_x = 0.0 if crop_focus_x < 0.0 else 1.0 if crop_focus_x > 1.0 else crop_focus_x
    crop_focus_y = 0.0 if crop_focus_y < 0.0 else 1.0 if crop_focus_y > 1.0 else crop_focus_y

    if width <= 0 or height <= 0:
        return

    fit = str(layer.get("fit") or "cover")

    with managed_image(path, "RGB") as img:
        img = img.copy()
        img_ratio = img.width / img.height if img.height > 0 else 1
        target_ratio = width / height if height > 0 else 1

        if fit == "stretch":
            pass
        elif fit == "contain":
            if img_ratio > target_ratio:
                contain_width = img.width
                contain_height = int(round(contain_width / target_ratio))
                padded = Image.new("RGB", (contain_width, contain_height), (0, 0, 0))
                top = max(0, (contain_height - img.height) // 2)
                padded.paste(img, (0, top))
                img = padded
            else:
                contain_height = img.height
                contain_width = int(round(contain_height * target_ratio))
                padded = Image.new("RGB", (contain_width, contain_height), (0, 0, 0))
                left = max(0, (contain_width - img.width) // 2)
                padded.paste(img, (left, 0))
                img = padded
        elif img_ratio > target_ratio:
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

        shape_alpha = img.getchannel("A").copy()
        if blur > 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=blur))
            img.putalpha(shape_alpha)
        img = _apply_film_grain(img, grain)

        if opacity < 1:
            alpha = img.getchannel("A")
            alpha = alpha.point(lambda value: int(value * opacity))
            img.putalpha(alpha)

        if rotation:
            pivot_px = target_size[0] * pivot_x
            pivot_py = target_size[1] * pivot_y
            shadow_pad = max(
                0.0,
                abs(shadow_offset_x),
                abs(shadow_offset_y),
                shadow_blur * 3.0,
            )
            pivot_radius = max(
                (pivot_px ** 2 + pivot_py ** 2) ** 0.5,
                ((target_size[0] - pivot_px) ** 2 + pivot_py ** 2) ** 0.5,
                (pivot_px ** 2 + (target_size[1] - pivot_py) ** 2) ** 0.5,
                ((target_size[0] - pivot_px) ** 2 + (target_size[1] - pivot_py) ** 2) ** 0.5,
            )
            half_size = int(round(pivot_radius + shadow_pad + 4))
            layer_size = max(2, half_size * 2)
            layer_canvas = Image.new("RGBA", (layer_size, layer_size), (0, 0, 0, 0))
            layer_center = layer_size / 2
            image_origin = (
                int(round(layer_center - pivot_px)),
                int(round(layer_center - pivot_py)),
            )

            if shadow_blur > 0 or shadow_offset_x != 0 or shadow_offset_y != 0:
                shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
                alpha_mask = img.getchannel("A")
                shadow_alpha = alpha_mask.point(lambda value: int(value * shadow_opacity))
                shadow.paste((0, 0, 0, 255), (0, 0), shadow_alpha)
                shadow = shadow.filter(ImageFilter.GaussianBlur(radius=max(1, shadow_blur)))
                layer_canvas.alpha_composite(
                    shadow,
                    (
                        int(round(image_origin[0] + shadow_offset_x)),
                        int(round(image_origin[1] + shadow_offset_y)),
                    ),
                )

            layer_canvas.alpha_composite(img, image_origin)
            layer_canvas = layer_canvas.rotate(
                -rotation,
                resample=Image.BICUBIC,
                expand=False,
                center=(layer_center, layer_center),
            )
            canvas.alpha_composite(
                layer_canvas,
                (
                    int(round(x + pivot_px - layer_center)),
                    int(round(y + pivot_py - layer_center)),
                ),
            )
            return

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

        canvas.alpha_composite(img, (int(round(x)), int(round(y))))


def _draw_group_layer(
    canvas: Image.Image,
    layer: Dict[str, Any],
    image_slots: Dict[int, str],
    title: Tuple[str, str],
    font_path: Tuple[str, str, str],
    scale_x: float,
    scale_y: float,
) -> None:
    children = sorted(layer.get("children") or [], key=lambda item: int(item.get("zIndex", 0)))
    if not children:
        return

    group_canvas = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    for child in children:
        _draw_layer(group_canvas, child, image_slots, title, font_path, scale_x, scale_y)

    opacity = max(0.0, min(1.0, _float_value(layer.get("opacity"), 1)))
    if opacity < 1:
        alpha = group_canvas.getchannel("A")
        alpha = alpha.point(lambda value: int(value * opacity))
        group_canvas.putalpha(alpha)

    rotation = float(layer.get("rotation", 0) or 0)
    if rotation:
        x = float(layer.get("x", 0) or 0) * scale_x
        y = float(layer.get("y", 0) or 0) * scale_y
        width = float(layer.get("width", 0) or 0) * scale_x
        height = float(layer.get("height", 0) or 0) * scale_y
        pivot_x = max(0.0, min(1.0, float(layer.get("pivotX", 0.5) or 0.5)))
        pivot_y = max(0.0, min(1.0, float(layer.get("pivotY", 0.5) or 0.5)))
        group_canvas = group_canvas.rotate(
            -rotation,
            resample=Image.BICUBIC,
            expand=False,
            center=(x + width * pivot_x, y + height * pivot_y),
        )

    canvas.alpha_composite(group_canvas)


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
    grain = max(0.0, min(1.0, _float_value(layer.get("grain", (layer.get("effects") or {}).get("grain")), 0)))
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
        text_alpha = text_layer.getchannel("A").copy()
        text_layer = text_layer.filter(ImageFilter.GaussianBlur(radius=blur))
        text_layer.putalpha(text_alpha)
    text_layer = _apply_film_grain(text_layer, grain)

    if opacity < 1:
        alpha = text_layer.getchannel("A")
        alpha = alpha.point(lambda value: int(value * opacity))
        text_layer.putalpha(alpha)

    if rotation:
        center_x = x + width * pivot_x
        center_y = y + height * pivot_y
        shadow_layer = shadow_layer.rotate(
            -rotation,
            resample=Image.BICUBIC,
            expand=False,
            center=(center_x, center_y),
        )
        text_layer = text_layer.rotate(
            -rotation,
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
    opacity = max(0.0, min(1.0, _float_value(layer.get("opacity"), 1)))
    blur = max(0.0, _float_value(layer.get("blur"), 0) * min(scale_x, scale_y))
    shadow_blur = max(0.0, _float_value(layer.get("shadowBlur"), 12) * min(scale_x, scale_y))
    shadow_offset_x = _float_value(layer.get("shadowOffsetX"), 0) * scale_x
    shadow_offset_y = _float_value(layer.get("shadowOffsetY"), 8) * scale_y
    shadow_opacity = max(0.0, min(1.0, _float_value(layer.get("shadowOpacity"), 0.24)))
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
    text_align = str(layer.get("textAlign") or "center")
    if text_align not in ("left", "center", "right"):
        text_align = "center"
    measured_lines: List[Dict[str, Any]] = []
    for index, line in enumerate(lines):
        line_width, line_box_height = _measure_text(draw, line, font)
        if text_align == "left":
            line_x = x
        elif text_align == "right":
            line_x = x + width - line_width
        else:
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


def _draw_layer(
    canvas: Image.Image,
    layer: Dict[str, Any],
    image_slots: Dict[int, str],
    title: Tuple[str, str],
    font_path: Tuple[str, str, str],
    scale_x: float,
    scale_y: float,
) -> None:
    layer_type = str(layer.get("type") or "image")
    if layer_type == "group":
        _draw_group_layer(canvas, layer, image_slots, title, font_path, scale_x, scale_y)
        return
    if layer_type == "image":
        _draw_image_layer(canvas, layer, image_slots, scale_x, scale_y)
        return

    main_title, subtitle = title
    main_font, subtitle_font, custom_font = font_path
    if layer_type in ("main_title", "title_zh"):
        text = main_title
        target_font = main_font
    elif layer_type in ("subtitle", "title_en"):
        text = subtitle
        target_font = subtitle_font
    else:
        text = str(layer.get("content") or "")
        font_family = str(layer.get("fontFamily") or "custom_text")
        if font_family == "main_title":
            target_font = main_font
        elif font_family == "subtitle":
            target_font = subtitle_font
        else:
            target_font = custom_font or subtitle_font or main_font

    if not text or not target_font:
        return
    _draw_title_layer(canvas, layer, text, target_font, scale_x, scale_y)


@memory_efficient_operation
def create_style_static_custom(
    image_slots: Dict[int, str],
    title: Tuple[str, str],
    font_path: Union[Tuple[str, str, str], Dict[str, str]],
    layout_config: Dict[str, Any] | None,
    blur_size: int,
    color_ratio: float,
    resolution_config: ResolutionConfig,
    bg_color_config: Dict[str, Any] | None,
    output_format: str = "png",
) -> str:
    if not layout_config or not isinstance(layout_config, dict):
        logger.error("custom_static: 布局配置无效，使用默认配置失败")
        return ""

    layers = layout_config.get("layers") or []
    if not layers:
        logger.error("custom_static: 布局中没有任何图层")
        return ""

    zh_title, en_title = title

    first_image_path = None
    for slot_index in sorted(image_slots.keys()):
        path = image_slots.get(slot_index)
        if path and Path(path).is_file():
            first_image_path = path
            break
    if not first_image_path:
        logger.info("custom_static: 未找到源图片，将按布局背景与非素材图层生成")

    blur_val = int(blur_size) if blur_size is not None else 50
    color_ratio_val = float(color_ratio) if color_ratio is not None else 0.8
    return render_template_to_base64(
        layout_config=layout_config,
        image_slots=image_slots,
        title=(zh_title, en_title),
        resolution_config=resolution_config,
        blur_size=blur_val,
        color_ratio=color_ratio_val,
        bg_color_config=bg_color_config,
        font_paths=font_path,
        output_format=output_format,
    )
