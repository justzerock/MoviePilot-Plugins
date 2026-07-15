import base64
import colorsys
import html
import math
import mimetypes
from io import BytesIO
from pathlib import Path
import re
from urllib.parse import parse_qs, unquote, urlparse
from typing import Any, Dict, List, Optional, Tuple, Union

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from app.log import logger
from app.plugins.yahahacoverstudio.utils.color_helper import ColorHelper
from app.plugins.yahahacoverstudio.utils.image_manager import ResolutionConfig, managed_image


EDITOR_BASE_WIDTH = 1920.0
EDITOR_BASE_HEIGHT = 1080.0


def _num(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _image_to_data_uri(path: str) -> str:
    target = Path(path)
    if not target.is_file():
        return ""
    mime_type, _ = mimetypes.guess_type(str(target))
    suffix = target.suffix.lower()
    font_mime_types = {
        ".ttf": "font/ttf",
        ".ttc": "font/collection",
        ".otf": "font/otf",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
    }
    if suffix in font_mime_types:
        mime_type = font_mime_types[suffix]
    if not mime_type:
        mime_type = "image/jpeg"
    encoded = base64.b64encode(target.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def _image_to_file_href(path: str) -> str:
    target = Path(path)
    if not target.is_file():
        return ""
    try:
        return target.resolve().as_uri()
    except Exception:
        return _image_to_data_uri(path)


def _data_uri_to_image(data_uri: str) -> Optional[Image.Image]:
    if not data_uri or not str(data_uri).startswith("data:image/"):
        return None
    try:
        _, encoded = str(data_uri).split(",", 1)
        return Image.open(BytesIO(base64.b64decode(encoded))).convert("RGBA")
    except Exception as err:
        logger.warning("template svg: 贴图 data URI 解析失败: %s", err)
        return None


def _has_sticker_ref(layer: Dict[str, Any]) -> bool:
    return any(
        str(layer.get(key) or "").strip()
        for key in ("stickerDataUrl", "stickerPath", "stickerUrl")
    )


def _sticker_path_from_url(sticker_url: str) -> str:
    if not sticker_url:
        return ""
    try:
        parsed = urlparse(str(sticker_url))
        values = parse_qs(parsed.query).get("file") or []
        if not values:
            return ""
        candidate = unquote(str(values[0] or "")).strip()
        return candidate if candidate and Path(candidate).is_file() else ""
    except Exception:
        return ""


def _sticker_path_for_layer(layer: Dict[str, Any]) -> str:
    sticker_path = str(layer.get("stickerPath") or "").strip()
    if sticker_path and Path(sticker_path).is_file():
        return sticker_path
    return _sticker_path_from_url(str(layer.get("stickerUrl") or ""))


def _encode_pil_image_to_data_uri(image: Image.Image, image_format: str = "PNG", quality: int = 88) -> str:
    buffer = BytesIO()
    fmt = image_format.upper()
    if fmt in ("JPG", "JPEG"):
        image.convert("RGB").save(buffer, format="JPEG", quality=quality, optimize=True)
        mime_type = "image/jpeg"
    else:
        image.save(buffer, format="PNG", optimize=True)
        mime_type = "image/png"
    return f"data:{mime_type};base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"


def _cover_resize(image: Image.Image, size: Tuple[int, int]) -> Image.Image:
    target_width, target_height = size
    source_width, source_height = image.size
    if source_width <= 0 or source_height <= 0:
        return image.resize(size, Image.Resampling.LANCZOS)
    scale = max(target_width / source_width, target_height / source_height)
    resized_width = max(1, int(round(source_width * scale)))
    resized_height = max(1, int(round(source_height * scale)))
    resized = image.resize((resized_width, resized_height), Image.Resampling.LANCZOS)
    left = max(0, (resized_width - target_width) // 2)
    top = max(0, (resized_height - target_height) // 2)
    return resized.crop((left, top, left + target_width, top + target_height))


def _rgb_to_hex(color: Any, fallback: str = "#5f7185") -> str:
    if isinstance(color, (tuple, list)) and len(color) >= 3:
        try:
            r, g, b = (int(round(float(color[index]))) for index in range(3))
            return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"
        except (TypeError, ValueError):
            return fallback
    return _normalize_hex_color(color, fallback)


def _adjust_hex_color(hex_color: str, lightness_offset: float) -> str:
    normalized = _normalize_hex_color(hex_color, "#5f7185")
    r = int(normalized[1:3], 16) / 255.0
    g = int(normalized[3:5], 16) / 255.0
    b = int(normalized[5:7], 16) / 255.0
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    next_l = _clamp(l + lightness_offset, 0.18, 0.84)
    next_s = _clamp(s, 0.24, 0.72)
    nr, ng, nb = colorsys.hls_to_rgb(h, next_l, next_s)
    return f"#{int(round(nr * 255)):02x}{int(round(ng * 255)):02x}{int(round(nb * 255)):02x}"


def _extract_comfortable_color(image: Image.Image) -> str:
    sample = image.convert("RGBA").resize((48, 48), Image.Resampling.BILINEAR)
    total_r = total_g = total_b = total_weight = 0.0
    for r, g, b, alpha in sample.getdata():
        if alpha < 160:
            continue
        _, lightness, saturation = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        if lightness < 0.16 or lightness > 0.86:
            continue
        weight = 0.55 + min(0.45, saturation)
        total_r += r * weight
        total_g += g * weight
        total_b += b * weight
        total_weight += weight
    if not total_weight:
        return ""
    base = _rgb_to_hex((total_r / total_weight, total_g / total_weight, total_b / total_weight))
    return _adjust_hex_color(base, -0.06)


def _blurred_background_data_uri(path: str, canvas_width: int, canvas_height: int, blur_radius: float) -> str:
    if not path or not Path(path).is_file():
        return ""
    try:
        with managed_image(path, "RGB") as original:
            background = _cover_resize(original, (canvas_width, canvas_height))
            if blur_radius > 0:
                background = background.filter(ImageFilter.GaussianBlur(radius=max(1, float(blur_radius))))
            return _encode_pil_image_to_data_uri(background, "JPEG")
    except Exception as err:
        logger.warning("template svg: 预渲染模糊背景失败，回退原图 SVG filter: %s", err)
        return ""


FontPathInput = Optional[Union[Tuple[str, str, str], Dict[str, str]]]


def normalize_template(layout: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    source = dict(layout or {})
    document = source.get("canvas") if isinstance(source.get("canvas"), dict) else source.get("document")
    document = document if isinstance(document, dict) else {}
    width = int(_num(document.get("width"), EDITOR_BASE_WIDTH))
    height = int(_num(document.get("height"), EDITOR_BASE_HEIGHT))
    layers = source.get("layers") if isinstance(source.get("layers"), list) else []
    return {
        **source,
        "schema": "mcr-template/v1",
        "version": source.get("version", "1.0"),
        "canvas": {"width": width, "height": height, "unit": "px"},
        "document": {"width": width, "height": height, "unit": "px"},
        "background": source.get("background") if isinstance(source.get("background"), dict) else {
            "type": "blurred-image-color",
            "imageSource": {"kind": "slot", "slot": 1},
            "colorSource": "auto",
            "color": "#5f7185",
            "color2": "#0a1628",
            "colorRatio": 0.8,
            "opacity": 1,
            "blur": 50,
            "grain": 0.18,
        },
        "layers": [_normalize_layer(layer) for layer in layers if isinstance(layer, dict)],
    }


def _normalize_layer(layer: Dict[str, Any]) -> Dict[str, Any]:
    layer_type = str(layer.get("type") or "image")
    if layer_type in ("title_zh", "main_title"):
        layer_type = "main_title"
    elif layer_type in ("title_en", "subtitle"):
        layer_type = "subtitle"
    elif layer_type not in ("image", "text", "group"):
        layer_type = "image"

    transform = layer.get("transform") if isinstance(layer.get("transform"), dict) else {}
    effects = layer.get("effects") if isinstance(layer.get("effects"), dict) else {}
    shadow = effects.get("shadow") if isinstance(effects.get("shadow"), dict) else {}
    normalized = {
        **layer,
        "type": layer_type,
        "x": _num(layer.get("x"), 0),
        "y": _num(layer.get("y"), 0),
        "width": _num(layer.get("width"), 1),
        "height": _num(layer.get("height"), 1),
        "zIndex": int(_num(layer.get("zIndex"), 0)),
        "rotation": _num(layer.get("rotation", transform.get("rotation")), 0),
        "pivotX": _clamp(_num(layer.get("pivotX", transform.get("pivotX")), 0.5), 0, 1),
        "pivotY": _clamp(_num(layer.get("pivotY", transform.get("pivotY")), 0.5), 0, 1),
        "opacity": _clamp(_num(layer.get("opacity", transform.get("opacity")), 1), 0, 1),
        "blur": max(0, _num(layer.get("blur", effects.get("blur")), 0)),
        "shadowBlur": max(0, _num(layer.get("shadowBlur", shadow.get("blur")), 0)),
        "shadowOffsetX": _num(layer.get("shadowOffsetX", shadow.get("offsetX")), 0),
        "shadowOffsetY": _num(layer.get("shadowOffsetY", shadow.get("offsetY")), 0),
        "shadowOpacity": _clamp(_num(layer.get("shadowOpacity", shadow.get("opacity")), 0.28), 0, 1),
    }
    normalized["transform"] = {
        "rotation": normalized["rotation"],
        "pivotX": normalized["pivotX"],
        "pivotY": normalized["pivotY"],
        "opacity": normalized["opacity"],
    }
    normalized["effects"] = {
        "blur": normalized["blur"],
        "shadow": {
            "blur": normalized["shadowBlur"],
            "offsetX": normalized["shadowOffsetX"],
            "offsetY": normalized["shadowOffsetY"],
            "opacity": normalized["shadowOpacity"],
            "color": shadow.get("color", "#000000"),
        },
    }
    if layer_type == "image":
        source_index = int(_num(layer.get("sourceIndex"), _num((layer.get("source") or {}).get("slot") if isinstance(layer.get("source"), dict) else None, 1)))
        normalized["sourceIndex"] = source_index
        normalized["source"] = {"kind": "slot", "slot": source_index}
        normalized["assetKind"] = "sticker" if layer.get("assetKind") == "sticker" or _has_sticker_ref(layer) else "source"
        if normalized["assetKind"] == "sticker":
            normalized["stickerDataUrl"] = str(layer.get("stickerDataUrl") or "")
            normalized["stickerPath"] = str(layer.get("stickerPath") or "")
            normalized["stickerUrl"] = str(layer.get("stickerUrl") or "")
            normalized["stickerName"] = str(layer.get("stickerName") or "")
            normalized["stickerWidth"] = _num(layer.get("stickerWidth"), 0)
            normalized["stickerHeight"] = _num(layer.get("stickerHeight"), 0)
        normalized["fit"] = layer.get("fit") if layer.get("fit") in ("cover", "contain", "stretch") else "cover"
        normalized["cropFocusX"] = _clamp(_num(layer.get("cropFocusX"), 0.5), 0, 1)
        normalized["cropFocusY"] = _clamp(_num(layer.get("cropFocusY"), 0.5), 0, 1)
    elif layer_type == "group":
        normalized["children"] = [
            _normalize_layer(child)
            for child in (layer.get("children") or [])
            if isinstance(child, dict)
        ]
    else:
        text_style = layer.get("textStyle") if isinstance(layer.get("textStyle"), dict) else {}
        normalized["fontSize"] = _num(layer.get("fontSize"), 75 if layer_type == "subtitle" else 170)
        normalized["fontFamily"] = layer.get("fontFamily") or ("subtitle" if layer_type == "subtitle" else "custom_text" if layer_type == "text" else "main_title")
        normalized["textAlign"] = layer.get("textAlign") if layer.get("textAlign") in ("left", "center", "right") else "center"
        mask_mode = layer.get("maskMode", text_style.get("maskMode"))
        normalized["maskMode"] = mask_mode if mask_mode in ("knockout-text", "show-text") else "normal"
        if layer_type == "text":
            normalized["content"] = str(layer.get("content") or "")
    return normalized


def _layer_transform(layer: Dict[str, Any], scale_x: float, scale_y: float) -> str:
    rotation = _num(layer.get("rotation"), 0)
    if not rotation:
        return ""
    x = _num(layer.get("x"), 0) * scale_x
    y = _num(layer.get("y"), 0) * scale_y
    width = _num(layer.get("width"), 1) * scale_x
    height = _num(layer.get("height"), 1) * scale_y
    cx = x + width * _num(layer.get("pivotX"), 0.5)
    cy = y + height * _num(layer.get("pivotY"), 0.5)
    return f' transform="rotate({rotation} {cx} {cy})"'


def _filter_id(layer: Dict[str, Any]) -> str:
    # CairoSVG only supports a tiny SVG filter subset and does not support
    # feGaussianBlur. Backend blur/shadow effects are rendered by Pillow into
    # embedded PNG layers instead of relying on SVG filters.
    return ""


def _wrap_text(text: str, font_size: float, max_width: float) -> List[str]:
    lines: List[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if not current or len(candidate) * font_size * 0.56 <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines or [""]


def _measure_text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> float:
    try:
        return float(draw.textlength(text, font=font))
    except Exception:
        left, _, right, _ = draw.textbbox((0, 0), text, font=font)
        return float(right - left)


def _wrap_text_with_font(text: str, font: ImageFont.FreeTypeFont, max_width: float) -> List[str]:
    measure_canvas = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    draw = ImageDraw.Draw(measure_canvas)
    lines: List[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if not current or _measure_text_width(draw, candidate, font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines or [""]


def _text_value(layer: Dict[str, Any], title: Tuple[str, str]) -> str:
    layer_type = layer.get("type")
    if layer_type == "main_title":
        return title[0] if title else ""
    if layer_type == "subtitle":
        return title[1] if len(title) > 1 else ""
    return str(layer.get("content") or "")


def _font_family(layer: Dict[str, Any]) -> str:
    family = str(layer.get("fontFamily") or "").strip()
    if not family or family in ("main_title", "subtitle", "custom_text"):
        return "sans-serif"
    return _esc(family)


def _font_path_for_layer(layer: Dict[str, Any], font_paths: FontPathInput) -> str:
    if not font_paths:
        return ""
    family = str(layer.get("fontFamily") or "main_title")
    if isinstance(font_paths, dict):
        return str(
            font_paths.get(family)
            or font_paths.get("main_title" if family in ("", "main_title") else family)
            or font_paths.get("custom_text")
            or font_paths.get("subtitle")
            or font_paths.get("main_title")
            or ""
        )
    if family == "subtitle" and len(font_paths) > 1:
        return str(font_paths[1] or "")
    if family == "custom_text" and len(font_paths) > 2:
        return str(font_paths[2] or "")
    return str(font_paths[0] if len(font_paths) > 0 else "")


def _png_data_uri(image: Image.Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"


def _normalize_hex_color(value: Any, fallback: str = "#5f7185") -> str:
    raw = str(value or "").strip()
    if not raw:
        return fallback
    if not raw.startswith("#"):
        raw = f"#{raw}"
    if re.match(r"^#[0-9a-fA-F]{6}$", raw):
        return raw
    return fallback


def _hex_to_rgba(value: Any, opacity: float = 1, fallback: str = "#ffffff") -> Tuple[int, int, int, int]:
    normalized = _normalize_hex_color(value, fallback)
    return (
        int(normalized[1:3], 16),
        int(normalized[3:5], 16),
        int(normalized[5:7], 16),
        int(round(255 * _clamp(float(opacity), 0, 1))),
    )


def _resolve_template_color(
    color_source: Any,
    custom_color: Any,
    auto_color: str,
    config_color: str,
    fallback: str = "#ffffff",
) -> str:
    source = str(color_source or "custom")
    if source == "none":
        return ""
    if source == "custom":
        return _normalize_hex_color(custom_color, fallback)
    if source == "config":
        return _normalize_hex_color(config_color, fallback)
    return _normalize_hex_color(auto_color, fallback)


def _background_grain_defs() -> str:
    return (
        '<filter id="mcr-film-grain" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" seed="17" result="noise"/>'
        '<feColorMatrix in="noise" type="matrix" values="0.33 0.33 0.33 0 0 0.33 0.33 0.33 0 0 0.33 0.33 0.33 0 0 0 0 0 0.48 0" result="monoNoise"/>'
        '<feComponentTransfer in="monoNoise">'
        '<feFuncR type="linear" slope="1.8" intercept="-0.38"/>'
        '<feFuncG type="linear" slope="1.8" intercept="-0.38"/>'
        '<feFuncB type="linear" slope="1.8" intercept="-0.38"/>'
        '</feComponentTransfer>'
        '</filter>'
    )


def _render_grain_overlay(canvas_width: int, canvas_height: int, intensity: Any) -> str:
    opacity = _clamp(_num(intensity, 0), 0, 1)
    if opacity <= 0:
        return ""
    return (
        f'<rect x="0" y="0" width="{canvas_width}" height="{canvas_height}" fill="#808080" '
        f'filter="url(#mcr-film-grain)" opacity="{min(0.45, opacity * 0.72)}" style="mix-blend-mode:overlay"/>'
    )


def _render_background(
    template: Dict[str, Any],
    image_slots: Dict[int, str],
    auto_bg_color: str,
    config_bg_color: str,
    canvas_width: int,
    canvas_height: int,
    bg_blur: float,
    color_ratio: float,
) -> Tuple[str, str]:
    background_config = template.get("background") if isinstance(template.get("background"), dict) else {}
    bg_type = str(background_config.get("type") or "blurred-image-color")
    color_source = str(background_config.get("colorSource") or "auto")
    if color_source == "custom":
        base_color = _normalize_hex_color(background_config.get("color"), _rgb_to_hex(auto_bg_color))
    elif color_source == "config":
        base_color = _normalize_hex_color(config_bg_color, _rgb_to_hex(auto_bg_color))
    else:
        base_color = _rgb_to_hex(auto_bg_color, "#5f7185")
    second_color = _normalize_hex_color(background_config.get("color2"), "#0a1628")
    grain_overlay = _render_grain_overlay(canvas_width, canvas_height, background_config.get("grain", 0))
    background_opacity = _clamp(_num(background_config.get("opacity", background_config.get("colorOpacity")), 1), 0, 1)
    gradient_def = (
        f'<linearGradient id="mcr-bg-gradient" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="{_esc(base_color)}"/><stop offset="100%" stop-color="{_esc(second_color)}"/>'
        f'</linearGradient>'
    ) + _background_grain_defs()
    def wrap_background_layer(content: str) -> str:
        if not content or background_opacity <= 0:
            return ""
        if background_opacity >= 1:
            return content
        return f'<g opacity="{background_opacity}">{content}</g>'

    if bg_type == "transparent":
        return "", gradient_def
    if bg_type == "solid":
        return wrap_background_layer(f'<rect x="0" y="0" width="{canvas_width}" height="{canvas_height}" fill="{_esc(base_color)}"/>{grain_overlay}'), gradient_def
    if bg_type == "gradient":
        return wrap_background_layer(f'<rect x="0" y="0" width="{canvas_width}" height="{canvas_height}" fill="url(#mcr-bg-gradient)"/>{grain_overlay}'), gradient_def

    image_source = background_config.get("imageSource") if isinstance(background_config.get("imageSource"), dict) else {}
    bg_slot = int(_num(image_source.get("slot"), 1))
    bg_path = image_slots.get(bg_slot) or next((path for _, path in sorted(image_slots.items()) if path and Path(path).is_file()), "")
    bg_href = _blurred_background_data_uri(bg_path, canvas_width, canvas_height, bg_blur) if bg_path else ""
    if not bg_href and bg_path:
        bg_href = _image_to_data_uri(bg_path)
    overlay_opacity = _clamp(_num(background_config.get("colorRatio"), color_ratio), 0, 1)
    bg = f'<rect x="0" y="0" width="{canvas_width}" height="{canvas_height}" fill="{_esc(base_color)}"/>'
    if bg_href:
        bg += f'<image href="{_esc(bg_href)}" x="0" y="0" width="{canvas_width}" height="{canvas_height}" preserveAspectRatio="xMidYMid slice" opacity="0.72"/>'
    bg += f'<rect x="0" y="0" width="{canvas_width}" height="{canvas_height}" fill="{_esc(base_color)}" opacity="{overlay_opacity}"/>'
    bg += grain_overlay
    return wrap_background_layer(bg), gradient_def


def _render_image_layer(
    layer: Dict[str, Any],
    image_data: Dict[int, str],
    scale_x: float,
    scale_y: float,
    auto_bg_color: str,
    config_bg_color: str,
) -> str:
    slot = int(_num((layer.get("source") or {}).get("slot") if isinstance(layer.get("source"), dict) else layer.get("sourceIndex"), 1))
    if layer.get("assetKind") == "sticker":
        sticker_path = _sticker_path_for_layer(layer)
        href = _image_to_file_href(sticker_path) if sticker_path and Path(sticker_path).is_file() else str(layer.get("stickerDataUrl") or "")
    else:
        href = image_data.get(slot)
    if not href:
        return ""
    x = _num(layer.get("x"), 0) * scale_x
    y = _num(layer.get("y"), 0) * scale_y
    width = _num(layer.get("width"), 1) * scale_x
    height = _num(layer.get("height"), 1) * scale_y
    radius = max(0, _num(layer.get("radius"), 0) * min(scale_x, scale_y))
    fit = layer.get("fit") or "cover"
    aspect = "xMidYMid slice" if fit == "cover" else "xMidYMid meet" if fit == "contain" else "none"
    filter_id = _filter_id(layer)
    filter_attr = f' filter="url(#{filter_id})"' if filter_id else ""
    opacity = _clamp(_num(layer.get("opacity"), 1), 0, 1)
    blend_opacity = _clamp(_num(layer.get("colorRatio"), 0), 0, 1)
    blend_color = _resolve_template_color(
        layer.get("colorSource") or "none",
        layer.get("color"),
        auto_bg_color,
        config_bg_color,
        "#5f7185",
    )
    clip_id = f"clip-{_esc(layer.get('id'))}"
    clip = f'<clipPath id="{clip_id}" clipPathUnits="userSpaceOnUse"><rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" ry="{radius}"/></clipPath>' if radius else ""
    clip_attr = f' clip-path="url(#{clip_id})"' if radius else ""
    image_node = f'<image href="{_esc(href)}" x="{x}" y="{y}" width="{width}" height="{height}" preserveAspectRatio="{aspect}"{clip_attr}/>'
    blend_node = (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" ry="{radius}" fill="{_esc(blend_color)}" opacity="{blend_opacity}"{clip_attr}/>'
        if blend_color and blend_opacity > 0
        else ""
    )
    return f'<g{_layer_transform(layer, scale_x, scale_y)} opacity="{opacity}"{filter_attr}>{clip}{image_node}{blend_node}</g>'


def _polygon_points_for_layer(layer: Dict[str, Any], width: int, height: int) -> List[Tuple[float, float]]:
    polygon = layer.get("maskPolygon") if isinstance(layer.get("maskPolygon"), dict) else None
    if not polygon:
        return []
    points = polygon.get("points") if isinstance(polygon.get("points"), list) else []
    units = str(polygon.get("units") or "relative")
    normalized_points: List[Tuple[float, float]] = []
    for point in points:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            continue
        px = _num(point[0], 0)
        py = _num(point[1], 0)
        if units == "relative":
            normalized_points.append((px * width, py * height))
        else:
            normalized_points.append((px, py))
    return normalized_points if len(normalized_points) >= 3 else []


def _apply_layer_polygon_mask(image: Image.Image, layer: Dict[str, Any]) -> Image.Image:
    points = _polygon_points_for_layer(layer, image.width, image.height)
    if not points:
        return image
    polygon_mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(polygon_mask).polygon(points, fill=255)
    masked = image.copy()
    alpha = masked.getchannel("A")
    masked.putalpha(ImageChops.multiply(alpha, polygon_mask))
    return masked


def _fit_layer_image(source: Image.Image, width: int, height: int, fit: str, crop_focus_x: float = 0.5, crop_focus_y: float = 0.5) -> Image.Image:
    width = max(1, int(width))
    height = max(1, int(height))
    crop_focus_x = _clamp(_num(crop_focus_x, 0.5), 0, 1)
    crop_focus_y = _clamp(_num(crop_focus_y, 0.5), 0, 1)
    if fit == "stretch":
        return source.resize((width, height), Image.Resampling.LANCZOS)
    source_width, source_height = source.size
    if source_width <= 0 or source_height <= 0:
        return source.resize((width, height), Image.Resampling.LANCZOS)
    scale = max(width / source_width, height / source_height) if fit != "contain" else min(width / source_width, height / source_height)
    resized_width = max(1, int(round(source_width * scale)))
    resized_height = max(1, int(round(source_height * scale)))
    resized = source.resize((resized_width, resized_height), Image.Resampling.LANCZOS)
    layer_image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    left = int(round((width - resized_width) / 2))
    top = int(round((height - resized_height) / 2))
    if fit == "contain":
        layer_image.alpha_composite(resized.convert("RGBA"), (left, top))
        return layer_image
    crop_left = int(round(max(0, resized_width - width) * crop_focus_x))
    crop_top = int(round(max(0, resized_height - height) * crop_focus_y))
    return resized.crop((crop_left, crop_top, crop_left + width, crop_top + height)).convert("RGBA")


def _render_image_layer_as_image(
    layer: Dict[str, Any],
    image_slots: Dict[int, str],
    image_data: Dict[int, str],
    scale_x: float,
    scale_y: float,
    canvas_width: int,
    canvas_height: int,
    auto_bg_color: str,
    config_bg_color: str,
) -> str:
    slot = int(_num((layer.get("source") or {}).get("slot") if isinstance(layer.get("source"), dict) else layer.get("sourceIndex"), 1))
    is_sticker = layer.get("assetKind") == "sticker"
    source_path = _sticker_path_for_layer(layer) if is_sticker else image_slots.get(slot)
    sticker_image = (
        _data_uri_to_image(str(layer.get("stickerDataUrl") or ""))
        if is_sticker and not (source_path and Path(source_path).is_file())
        else None
    )
    shadow_blur = max(0, _num(layer.get("shadowBlur"), 0) * min(scale_x, scale_y))
    shadow_x = _num(layer.get("shadowOffsetX"), 0) * scale_x
    shadow_y = _num(layer.get("shadowOffsetY"), 0) * scale_y
    shadow_opacity = _clamp(_num(layer.get("shadowOpacity"), 0.28), 0, 1)
    layer_blur = max(0, _num(layer.get("blur"), 0) * min(scale_x, scale_y))
    rotation = _num(layer.get("rotation"), 0)
    fit = str(layer.get("fit") or "cover")
    crop_focus_x = _clamp(_num(layer.get("cropFocusX"), 0.5), 0, 1)
    crop_focus_y = _clamp(_num(layer.get("cropFocusY"), 0.5), 0, 1)
    blend_opacity = _clamp(_num(layer.get("colorRatio"), 0), 0, 1)
    blend_color = _resolve_template_color(
        layer.get("colorSource") or "none",
        layer.get("color"),
        auto_bg_color,
        config_bg_color,
        "#5f7185",
    )
    has_polygon_mask = bool(_polygon_points_for_layer(layer, 1, 1))
    has_custom_crop_focus = fit == "cover" and (abs(crop_focus_x - 0.5) > 0.001 or abs(crop_focus_y - 0.5) > 0.001)
    has_source_image = bool(sticker_image is not None or (source_path and Path(source_path).is_file()))
    should_rasterize = bool(has_source_image and (rotation or shadow_blur or shadow_x or shadow_y or layer_blur or has_custom_crop_focus or has_polygon_mask))
    if not should_rasterize:
        return _render_image_layer(layer, image_data, scale_x, scale_y, auto_bg_color, config_bg_color)

    try:
        x = _num(layer.get("x"), 0) * scale_x
        y = _num(layer.get("y"), 0) * scale_y
        width = max(1, int(round(_num(layer.get("width"), 1) * scale_x)))
        height = max(1, int(round(_num(layer.get("height"), 1) * scale_y)))
        radius = max(0, int(round(_num(layer.get("radius"), 0) * min(scale_x, scale_y))))
        if sticker_image is not None:
            fitted = _fit_layer_image(sticker_image, width, height, fit, crop_focus_x, crop_focus_y)
            sticker_image.close()
        else:
            with managed_image(str(source_path), "RGBA") as source:
                fitted = _fit_layer_image(source, width, height, fit, crop_focus_x, crop_focus_y)

        if radius:
            mask = Image.new("L", (width, height), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=255)
            fitted.putalpha(Image.composite(fitted.getchannel("A"), mask, mask))

        fitted = _apply_layer_polygon_mask(fitted, layer)
        shape_alpha = fitted.getchannel("A").copy()

        if layer_blur:
            fitted = fitted.filter(ImageFilter.GaussianBlur(radius=layer_blur))

        rotation_pad = int(math.ceil(math.hypot(width, height))) if rotation else 0
        shadow_pad = int(math.ceil(abs(shadow_x) + abs(shadow_y) + shadow_blur * 3))
        pad = max(0, rotation_pad, shadow_pad, 64 if (rotation or shadow_blur or shadow_x or shadow_y) else 0)
        work_width = canvas_width + pad * 2
        work_height = canvas_height + pad * 2
        paste_x = int(round(x + pad))
        paste_y = int(round(y + pad))
        element_canvas = Image.new("RGBA", (work_width, work_height), (0, 0, 0, 0))
        shadow_canvas = Image.new("RGBA", (work_width, work_height), (0, 0, 0, 0))
        if shadow_blur or shadow_x or shadow_y:
            shadow_shape = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            shadow_shape.putalpha(fitted.getchannel("A").point(lambda value: int(value * shadow_opacity)))
            shadow_canvas.alpha_composite(shadow_shape, (int(round(paste_x + shadow_x)), int(round(paste_y + shadow_y))))
            if shadow_blur:
                shadow_canvas = shadow_canvas.filter(ImageFilter.GaussianBlur(radius=max(1, shadow_blur)))

        element_canvas.alpha_composite(fitted, (paste_x, paste_y))
        if blend_color and blend_opacity > 0:
            blend_layer = Image.new("RGBA", (width, height), _hex_to_rgba(blend_color, blend_opacity, "#5f7185"))
            blend_layer.putalpha(shape_alpha.point(lambda value: int(value * blend_opacity)))
            if layer_blur:
                blend_layer = blend_layer.filter(ImageFilter.GaussianBlur(radius=layer_blur))
            element_canvas.alpha_composite(blend_layer, (paste_x, paste_y))
        combined = Image.alpha_composite(shadow_canvas, element_canvas)

        if rotation:
            pivot_x = _clamp(_num(layer.get("pivotX"), 0.5), 0, 1)
            pivot_y = _clamp(_num(layer.get("pivotY"), 0.5), 0, 1)
            center = (pad + x + width * pivot_x, pad + y + height * pivot_y)
            combined = combined.rotate(-rotation, resample=Image.BICUBIC, expand=False, center=center)

        opacity = _clamp(_num(layer.get("opacity"), 1), 0, 1)
        if opacity < 1:
            alpha = combined.getchannel("A")
            combined.putalpha(alpha.point(lambda value: int(value * opacity)))
        if pad:
            combined = combined.crop((pad, pad, pad + canvas_width, pad + canvas_height))
        return f'<image href="{_esc(_png_data_uri(combined))}" x="0" y="0" width="{canvas_width}" height="{canvas_height}" preserveAspectRatio="none"/>'
    except Exception as err:
        logger.warning("template svg: Pillow 图片阴影图层渲染失败，回退 SVG image: %s", err)
        return _render_image_layer(layer, image_data, scale_x, scale_y, auto_bg_color, config_bg_color)


def _render_text_layer(
    layer: Dict[str, Any],
    title: Tuple[str, str],
    scale_x: float,
    scale_y: float,
    auto_bg_color: str,
    config_bg_color: str,
) -> str:
    if layer.get("maskMode") in ("knockout-text", "show-text"):
        return ""
    text = _text_value(layer, title)
    if not text:
        return ""
    x = _num(layer.get("x"), 0) * scale_x
    y = _num(layer.get("y"), 0) * scale_y
    width = _num(layer.get("width"), 1) * scale_x
    height = _num(layer.get("height"), 1) * scale_y
    font_size = max(1, _num(layer.get("fontSize"), 60) * min(scale_x, scale_y))
    line_height = font_size * 1.1
    lines = _wrap_text(text, font_size, width)
    start_y = y + (height - line_height * len(lines)) / 2 + font_size
    text_align = layer.get("textAlign") if layer.get("textAlign") in ("left", "right") else "center"
    anchor_x = x if text_align == "left" else x + width if text_align == "right" else x + width / 2
    text_anchor = "start" if text_align == "left" else "end" if text_align == "right" else "middle"
    tspans = "".join(
        f'<tspan x="{anchor_x}" y="{start_y + index * line_height}">{_esc(line)}</tspan>'
        for index, line in enumerate(lines)
    )
    filter_id = _filter_id(layer)
    filter_attr = f' filter="url(#{filter_id})"' if filter_id else ""
    opacity = _clamp(_num(layer.get("opacity"), 1), 0, 1)
    text_color = _resolve_template_color(
        layer.get("colorSource") or "custom",
        layer.get("color") or "#ffffff",
        auto_bg_color,
        config_bg_color,
        "#ffffff",
    )
    return f'<g{_layer_transform(layer, scale_x, scale_y)} opacity="{opacity}"{filter_attr}><text font-family="{_font_family(layer)}" font-size="{font_size}" fill="{_esc(text_color)}" text-anchor="{text_anchor}">{tspans}</text></g>'


def _render_text_layer_as_image(
    layer: Dict[str, Any],
    title: Tuple[str, str],
    scale_x: float,
    scale_y: float,
    canvas_width: int,
    canvas_height: int,
    font_paths: FontPathInput,
    auto_bg_color: str,
    config_bg_color: str,
) -> str:
    if layer.get("maskMode") in ("knockout-text", "show-text"):
        return ""
    text = _text_value(layer, title)
    font_path = _font_path_for_layer(layer, font_paths)
    if not text or not font_path or not Path(font_path).is_file():
        return _render_text_layer(layer, title, scale_x, scale_y, auto_bg_color, config_bg_color)

    try:
        x = _num(layer.get("x"), 0) * scale_x
        y = _num(layer.get("y"), 0) * scale_y
        width = _num(layer.get("width"), 1) * scale_x
        height = _num(layer.get("height"), 1) * scale_y
        font_size = max(1, _num(layer.get("fontSize"), 60) * min(scale_x, scale_y))
        font = ImageFont.truetype(font_path, max(1, int(round(font_size))))
        lines = _wrap_text_with_font(text, font, max(1, width))
        line_height = font_size * 1.1
        total_height = line_height * len(lines)
        start_y = y + (height - total_height) / 2

        text_layer = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
        shadow_layer = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_layer)
        shadow_draw = ImageDraw.Draw(shadow_layer)
        shadow_blur = max(0, _num(layer.get("shadowBlur"), 0) * min(scale_x, scale_y))
        shadow_x = _num(layer.get("shadowOffsetX"), 0) * scale_x
        shadow_y = _num(layer.get("shadowOffsetY"), 0) * scale_y
        shadow_opacity = _clamp(_num(layer.get("shadowOpacity"), 0.28), 0, 1)
        text_color = _resolve_template_color(
            layer.get("colorSource") or "custom",
            layer.get("color") or "#ffffff",
            auto_bg_color,
            config_bg_color,
            "#ffffff",
        )
        text_fill = _hex_to_rgba(text_color, 1, "#ffffff")
        text_align = layer.get("textAlign") if layer.get("textAlign") in ("left", "right") else "center"

        for index, line in enumerate(lines):
            line_width = _measure_text_width(draw, line, font)
            line_x = x if text_align == "left" else x + width - line_width if text_align == "right" else x + (width - line_width) / 2
            line_y = start_y + index * line_height
            shadow_draw.text((line_x + shadow_x, line_y + shadow_y), line, font=font, fill=(0, 0, 0, int(255 * shadow_opacity)))
            draw.text((line_x, line_y), line, font=font, fill=text_fill)

        if shadow_blur:
            shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=max(1, shadow_blur)))
        blur = max(0, _num(layer.get("blur"), 0) * min(scale_x, scale_y))
        if blur:
            text_layer = text_layer.filter(ImageFilter.GaussianBlur(radius=blur))

        rotation = _num(layer.get("rotation"), 0)
        if rotation:
            pivot_x = _clamp(_num(layer.get("pivotX"), 0.5), 0, 1)
            pivot_y = _clamp(_num(layer.get("pivotY"), 0.5), 0, 1)
            center = (x + width * pivot_x, y + height * pivot_y)
            shadow_layer = shadow_layer.rotate(-rotation, resample=Image.BICUBIC, expand=False, center=center)
            text_layer = text_layer.rotate(-rotation, resample=Image.BICUBIC, expand=False, center=center)

        combined = Image.alpha_composite(shadow_layer, text_layer)
        opacity = _clamp(_num(layer.get("opacity"), 1), 0, 1)
        if opacity < 1:
            alpha = combined.getchannel("A")
            combined.putalpha(alpha.point(lambda value: int(value * opacity)))
        return f'<image href="{_esc(_png_data_uri(combined))}" x="0" y="0" width="{canvas_width}" height="{canvas_height}" preserveAspectRatio="none"/>'
    except Exception as err:
        logger.warning("template svg: Pillow 字体图层渲染失败，回退 SVG text: %s", err)
        return _render_text_layer(layer, title, scale_x, scale_y, auto_bg_color, config_bg_color)


def _render_layer(
    layer: Dict[str, Any],
    image_slots: Dict[int, str],
    image_data: Dict[int, str],
    title: Tuple[str, str],
    scale_x: float,
    scale_y: float,
    canvas_width: int,
    canvas_height: int,
    font_paths: FontPathInput,
    auto_bg_color: str,
    config_bg_color: str,
) -> str:
    layer_type = layer.get("type")
    if layer_type == "group":
        children = sorted(layer.get("children") or [], key=lambda item: int(item.get("zIndex", 0)))
        body = "".join(_render_layer(child, image_slots, image_data, title, scale_x, scale_y, canvas_width, canvas_height, font_paths, auto_bg_color, config_bg_color) for child in children)
        return f'<g{_layer_transform(layer, scale_x, scale_y)} opacity="{_clamp(_num(layer.get("opacity"), 1), 0, 1)}">{body}</g>'
    if layer_type == "image":
        return _render_image_layer_as_image(layer, image_slots, image_data, scale_x, scale_y, canvas_width, canvas_height, auto_bg_color, config_bg_color)
    return _render_text_layer_as_image(layer, title, scale_x, scale_y, canvas_width, canvas_height, font_paths, auto_bg_color, config_bg_color)


def render_template_svg(
    layout_config: Dict[str, Any],
    image_slots: Dict[int, str],
    title: Tuple[str, str],
    resolution_config: ResolutionConfig,
    blur_size: int,
    color_ratio: float,
    bg_color_config: Optional[Dict[str, Any]] = None,
    font_paths: FontPathInput = None,
) -> str:
    template = normalize_template(layout_config)
    canvas_width, canvas_height = resolution_config.size
    scale_x = canvas_width / EDITOR_BASE_WIDTH
    scale_y = canvas_height / EDITOR_BASE_HEIGHT
    scale = min(scale_x, scale_y)

    first_image_path = next((path for _, path in sorted(image_slots.items()) if path and Path(path).is_file()), "")
    image_data = {slot: _image_to_file_href(path) for slot, path in image_slots.items() if path}
    auto_bg_color = "#5f7185"
    if first_image_path:
        try:
            with managed_image(first_image_path, "RGB") as original_img:
                auto_bg_color = _extract_comfortable_color(original_img) or _rgb_to_hex(ColorHelper.get_background_color(original_img))
        except Exception as err:
            logger.warning("template svg: 获取背景色失败: %s", err)
    config_bg_color = str((bg_color_config or {}).get("config_color") or "")

    layers = sorted(template.get("layers") or [], key=lambda item: int(item.get("zIndex", 0)))
    bg_blur = max(0, int((template.get("background") or {}).get("blur", blur_size) or 0)) * scale
    bg, background_defs = _render_background(
        template=template,
        image_slots=image_slots,
        auto_bg_color=auto_bg_color,
        config_bg_color=config_bg_color,
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        bg_blur=bg_blur,
        color_ratio=_clamp(float(color_ratio or 0.8), 0, 1),
    )
    background_z_index = int(_num((template.get("background") or {}).get("zIndex"), 0))
    under_background_layers = [layer for layer in layers if int(layer.get("zIndex", 0)) < background_z_index]
    over_background_layers = [layer for layer in layers if int(layer.get("zIndex", 0)) >= background_z_index]
    under_body = "".join(
        _render_layer(layer, image_slots, image_data, title, scale_x, scale_y, canvas_width, canvas_height, font_paths, auto_bg_color, config_bg_color)
        for layer in under_background_layers
    )
    over_body = "".join(
        _render_layer(layer, image_slots, image_data, title, scale_x, scale_y, canvas_width, canvas_height, font_paths, auto_bg_color, config_bg_color)
        for layer in over_background_layers
    )
    text_mask_def = _render_text_alpha_mask_def(layers, title, canvas_width, canvas_height, scale_x, scale_y, font_paths)
    body = f"{under_body}{bg}{over_body}"
    masked_body = f'<g mask="url(#mcr-text-mask)">{body}</g>' if text_mask_def else body
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_width} {canvas_height}" '
        f'width="{canvas_width}" height="{canvas_height}" data-template-schema="mcr-template/v1">'
        f'<defs>{background_defs}{text_mask_def}</defs>{masked_body}</svg>'
    )


def _get_layer_source_image(layer: Dict[str, Any], image_slots: Dict[int, str]) -> Optional[Image.Image]:
    if layer.get("assetKind") == "sticker":
        sticker_path = _sticker_path_for_layer(layer)
        if sticker_path and Path(sticker_path).is_file():
            try:
                return Image.open(sticker_path).convert("RGBA")
            except Exception as err:
                logger.warning("template pillow: 读取贴图文件失败 %s: %s", sticker_path, err)
        return _data_uri_to_image(str(layer.get("stickerDataUrl") or ""))

    slot = int(_num((layer.get("source") or {}).get("slot") if isinstance(layer.get("source"), dict) else layer.get("sourceIndex"), 1))
    source_path = image_slots.get(slot)
    if not source_path or not Path(source_path).is_file():
        return None
    try:
        return Image.open(source_path).convert("RGBA")
    except Exception as err:
        logger.warning("template pillow: 读取图层图片失败 %s: %s", source_path, err)
        return None


def _make_linear_gradient(size: Tuple[int, int], color1: str, color2: str) -> Image.Image:
    width, height = size
    start = _hex_to_rgba(color1, 1, "#5f7185")
    end = _hex_to_rgba(color2, 1, "#0a1628")
    gradient = Image.new("RGBA", size, (0, 0, 0, 0))
    pixels = gradient.load()
    denom = max(1, width + height - 2)
    for y in range(height):
        for x in range(width):
            ratio = (x + y) / denom
            pixels[x, y] = tuple(
                int(round(start[index] * (1 - ratio) + end[index] * ratio))
                for index in range(4)
            )
    return gradient


def _render_background_image(
    template: Dict[str, Any],
    image_slots: Dict[int, str],
    auto_bg_color: str,
    config_bg_color: str,
    canvas_width: int,
    canvas_height: int,
    bg_blur: float,
    color_ratio: float,
) -> Image.Image:
    background_config = template.get("background") if isinstance(template.get("background"), dict) else {}
    bg_type = str(background_config.get("type") or "blurred-image-color")
    color_source = str(background_config.get("colorSource") or "auto")
    if color_source == "custom":
        base_color = _normalize_hex_color(background_config.get("color"), _rgb_to_hex(auto_bg_color))
    elif color_source == "config":
        base_color = _normalize_hex_color(config_bg_color, _rgb_to_hex(auto_bg_color))
    else:
        base_color = _rgb_to_hex(auto_bg_color, "#5f7185")
    opacity = _clamp(_num(background_config.get("opacity", background_config.get("colorOpacity")), 1), 0, 1)
    size = (canvas_width, canvas_height)

    if bg_type == "transparent" or opacity <= 0:
        return Image.new("RGBA", size, (0, 0, 0, 0))
    if bg_type == "solid":
        background = Image.new("RGBA", size, _hex_to_rgba(base_color, 1, "#5f7185"))
    elif bg_type == "gradient":
        background = _make_linear_gradient(size, base_color, _normalize_hex_color(background_config.get("color2"), "#0a1628"))
    else:
        image_source = background_config.get("imageSource") if isinstance(background_config.get("imageSource"), dict) else {}
        bg_slot = int(_num(image_source.get("slot"), 1))
        bg_path = image_slots.get(bg_slot) or next((path for _, path in sorted(image_slots.items()) if path and Path(path).is_file()), "")
        background = Image.new("RGBA", size, _hex_to_rgba(base_color, 1, "#5f7185"))
        if bg_path and Path(bg_path).is_file():
            try:
                with managed_image(bg_path, "RGB") as original:
                    image_background = _cover_resize(original, size).convert("RGBA")
                    if bg_blur > 0:
                        image_background = image_background.filter(ImageFilter.GaussianBlur(radius=max(1, bg_blur)))
                    background = Image.blend(image_background, background, _clamp(_num(background_config.get("colorRatio"), color_ratio), 0, 1))
            except Exception as err:
                logger.warning("template pillow: 背景图渲染失败: %s", err)

    if opacity < 1:
        alpha = background.getchannel("A")
        background.putalpha(alpha.point(lambda value: int(value * opacity)))
    return background


def _alpha_composite_clipped(base: Image.Image, overlay: Image.Image, dest: Tuple[int, int]) -> None:
    dest_x, dest_y = dest
    left = max(0, int(dest_x))
    top = max(0, int(dest_y))
    right = min(base.width, int(dest_x) + overlay.width)
    bottom = min(base.height, int(dest_y) + overlay.height)
    if right <= left or bottom <= top:
        return
    crop = overlay.crop((left - int(dest_x), top - int(dest_y), right - int(dest_x), bottom - int(dest_y)))
    base.alpha_composite(crop, (left, top))


def _paste_layer_canvas(base: Image.Image, layer_canvas: Image.Image, layer: Dict[str, Any], scale_x: float, scale_y: float) -> None:
    rotation = _num(layer.get("rotation"), 0)
    if rotation:
        x = _num(layer.get("x"), 0) * scale_x
        y = _num(layer.get("y"), 0) * scale_y
        width = _num(layer.get("width"), 1) * scale_x
        height = _num(layer.get("height"), 1) * scale_y
        pivot_x = _clamp(_num(layer.get("pivotX"), 0.5), 0, 1)
        pivot_y = _clamp(_num(layer.get("pivotY"), 0.5), 0, 1)
        pivot_abs = (x + width * pivot_x, y + height * pivot_y)
        bbox = layer_canvas.getbbox()
        if bbox:
            layer_crop = layer_canvas.crop(bbox)
            pivot_in_crop = (pivot_abs[0] - bbox[0], pivot_abs[1] - bbox[1])
            corners = (
                (0.0, 0.0),
                (float(layer_crop.width), 0.0),
                (0.0, float(layer_crop.height)),
                (float(layer_crop.width), float(layer_crop.height)),
            )
            pivot_radius = max(
                math.hypot(corner_x - pivot_in_crop[0], corner_y - pivot_in_crop[1])
                for corner_x, corner_y in corners
            )
            half_size = int(math.ceil(pivot_radius + 4))
            work_size = max(2, half_size * 2)
            center = work_size / 2
            work_canvas = Image.new("RGBA", (work_size, work_size), (0, 0, 0, 0))
            work_canvas.alpha_composite(
                layer_crop,
                (
                    int(round(center - pivot_in_crop[0])),
                    int(round(center - pivot_in_crop[1])),
                ),
            )
            layer_canvas = work_canvas.rotate(
                -rotation,
                resample=Image.BICUBIC,
                expand=False,
                center=(center, center),
            )
            paste_at = (
                int(round(pivot_abs[0] - center)),
                int(round(pivot_abs[1] - center)),
            )
        else:
            return
    else:
        paste_at = (0, 0)
    opacity = _clamp(_num(layer.get("opacity"), 1), 0, 1)
    if opacity < 1:
        alpha = layer_canvas.getchannel("A")
        layer_canvas.putalpha(alpha.point(lambda value: int(value * opacity)))
    _alpha_composite_clipped(base, layer_canvas, paste_at)


def _rotate_layer_image_around_pivot(
    layer_image: Image.Image,
    rotation: float,
    pivot_x: float,
    pivot_y: float,
) -> Tuple[Image.Image, Tuple[int, int]]:
    if not rotation:
        return layer_image, (0, 0)
    pivot_x = _clamp(float(pivot_x), 0, 1)
    pivot_y = _clamp(float(pivot_y), 0, 1)
    pivot_px = layer_image.width * pivot_x
    pivot_py = layer_image.height * pivot_y
    corners = (
        (0.0, 0.0),
        (float(layer_image.width), 0.0),
        (0.0, float(layer_image.height)),
        (float(layer_image.width), float(layer_image.height)),
    )
    pivot_radius = max(
        math.hypot(corner_x - pivot_px, corner_y - pivot_py)
        for corner_x, corner_y in corners
    )
    half_size = int(math.ceil(pivot_radius + 4))
    work_size = max(2, half_size * 2)
    center = work_size / 2
    work_canvas = Image.new("RGBA", (work_size, work_size), (0, 0, 0, 0))
    work_canvas.alpha_composite(
        layer_image,
        (
            int(round(center - pivot_px)),
            int(round(center - pivot_py)),
        ),
    )
    rotated = work_canvas.rotate(
        -rotation,
        resample=Image.BICUBIC,
        expand=False,
        center=(center, center),
    )
    return rotated, (int(round(pivot_px - center)), int(round(pivot_py - center)))


def _draw_template_image_layer(
    canvas: Image.Image,
    layer: Dict[str, Any],
    image_slots: Dict[int, str],
    scale_x: float,
    scale_y: float,
    auto_bg_color: str,
    config_bg_color: str,
) -> None:
    source = _get_layer_source_image(layer, image_slots)
    if source is None:
        return
    try:
        x = _num(layer.get("x"), 0) * scale_x
        y = _num(layer.get("y"), 0) * scale_y
        width = max(1, int(round(_num(layer.get("width"), 1) * scale_x)))
        height = max(1, int(round(_num(layer.get("height"), 1) * scale_y)))
        radius = max(0, int(round(_num(layer.get("radius"), 0) * min(scale_x, scale_y))))
        fitted = _fit_layer_image(
            source,
            width,
            height,
            str(layer.get("fit") or "cover"),
            _clamp(_num(layer.get("cropFocusX"), 0.5), 0, 1),
            _clamp(_num(layer.get("cropFocusY"), 0.5), 0, 1),
        )
        source.close()
        if radius:
            mask = Image.new("L", (width, height), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, width, height), radius=radius, fill=255)
            fitted.putalpha(ImageChops.multiply(fitted.getchannel("A"), mask))
        fitted = _apply_layer_polygon_mask(fitted, layer)
        shape_alpha = fitted.getchannel("A").copy()
        layer_blur = max(0, _num(layer.get("blur"), 0) * min(scale_x, scale_y))
        if layer_blur:
            fitted = fitted.filter(ImageFilter.GaussianBlur(radius=layer_blur))

        shadow_blur = max(0, _num(layer.get("shadowBlur"), 0) * min(scale_x, scale_y))
        shadow_x = _num(layer.get("shadowOffsetX"), 0) * scale_x
        shadow_y = _num(layer.get("shadowOffsetY"), 0) * scale_y
        shadow_opacity = _clamp(_num(layer.get("shadowOpacity"), 0.28), 0, 1)
        pad = int(math.ceil(max(abs(shadow_x), abs(shadow_y), shadow_blur * 3, 0) + 4))
        item_canvas = Image.new("RGBA", (width + pad * 2, height + pad * 2), (0, 0, 0, 0))
        if shadow_blur or shadow_x or shadow_y:
            shadow_shape = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            shadow_shape.putalpha(fitted.getchannel("A").point(lambda value: int(value * shadow_opacity)))
            _alpha_composite_clipped(
                item_canvas,
                shadow_shape,
                (
                    int(round(pad + shadow_x)),
                    int(round(pad + shadow_y)),
                ),
            )
            if shadow_blur:
                item_canvas = item_canvas.filter(ImageFilter.GaussianBlur(radius=max(1, shadow_blur)))
        item_canvas.alpha_composite(fitted, (pad, pad))

        blend_opacity = _clamp(_num(layer.get("colorRatio"), 0), 0, 1)
        blend_color = _resolve_template_color(layer.get("colorSource") or "none", layer.get("color"), auto_bg_color, config_bg_color, "#5f7185")
        if blend_color and blend_opacity > 0:
            blend_layer = Image.new("RGBA", (width, height), _hex_to_rgba(blend_color, blend_opacity, "#5f7185"))
            blend_layer.putalpha(shape_alpha.point(lambda value: int(value * blend_opacity)))
            item_canvas.alpha_composite(blend_layer, (pad, pad))

        rotation = _num(layer.get("rotation"), 0)
        if rotation:
            pivot_x = _clamp(_num(layer.get("pivotX"), 0.5), 0, 1)
            pivot_y = _clamp(_num(layer.get("pivotY"), 0.5), 0, 1)
            item_pivot_x = (pad + width * pivot_x) / item_canvas.width
            item_pivot_y = (pad + height * pivot_y) / item_canvas.height
            item_canvas, offset = _rotate_layer_image_around_pivot(item_canvas, rotation, item_pivot_x, item_pivot_y)
            paste = (
                int(round(x - pad + offset[0])),
                int(round(y - pad + offset[1])),
            )
        else:
            paste = (int(round(x - pad)), int(round(y - pad)))

        opacity = _clamp(_num(layer.get("opacity"), 1), 0, 1)
        if opacity < 1:
            alpha = item_canvas.getchannel("A")
            item_canvas.putalpha(alpha.point(lambda value: int(value * opacity)))
        _alpha_composite_clipped(canvas, item_canvas, paste)
    except Exception as err:
        logger.warning("template pillow: 图片图层渲染失败: %s", err)


def _draw_template_text_layer(
    canvas: Image.Image,
    layer: Dict[str, Any],
    title: Tuple[str, str],
    scale_x: float,
    scale_y: float,
    font_paths: FontPathInput,
    auto_bg_color: str,
    config_bg_color: str,
) -> None:
    text = _text_value(layer, title)
    if not text:
        return
    font_path = _font_path_for_layer(layer, font_paths)
    try:
        font_size = max(1, _num(layer.get("fontSize"), 60) * min(scale_x, scale_y))
        font = ImageFont.truetype(font_path, max(1, int(round(font_size)))) if font_path and Path(font_path).is_file() else ImageFont.load_default()
        x = _num(layer.get("x"), 0) * scale_x
        y = _num(layer.get("y"), 0) * scale_y
        width = _num(layer.get("width"), 1) * scale_x
        height = _num(layer.get("height"), 1) * scale_y
        lines = _wrap_text_with_font(text, font, max(1, width))
        line_height = font_size * 1.1
        total_height = line_height * len(lines)
        start_y = y + (height - total_height) / 2
        align = layer.get("textAlign") if layer.get("textAlign") in ("left", "right") else "center"
        text_color = _resolve_template_color(layer.get("colorSource") or "custom", layer.get("color") or "#ffffff", auto_bg_color, config_bg_color, "#ffffff")
        text_fill = _hex_to_rgba(text_color, 1, "#ffffff")
        layer_canvas = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        shadow_canvas = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer_canvas)
        shadow_draw = ImageDraw.Draw(shadow_canvas)
        shadow_blur = max(0, _num(layer.get("shadowBlur"), 0) * min(scale_x, scale_y))
        shadow_x = _num(layer.get("shadowOffsetX"), 0) * scale_x
        shadow_y = _num(layer.get("shadowOffsetY"), 0) * scale_y
        shadow_opacity = _clamp(_num(layer.get("shadowOpacity"), 0.28), 0, 1)
        for index, line in enumerate(lines):
            line_width = _measure_text_width(draw, line, font)
            line_x = x if align == "left" else x + width - line_width if align == "right" else x + (width - line_width) / 2
            line_y = start_y + index * line_height
            shadow_draw.text((line_x + shadow_x, line_y + shadow_y), line, font=font, fill=(0, 0, 0, int(255 * shadow_opacity)))
            draw.text((line_x, line_y), line, font=font, fill=text_fill)
        if shadow_blur:
            shadow_canvas = shadow_canvas.filter(ImageFilter.GaussianBlur(radius=max(1, shadow_blur)))
        blur = max(0, _num(layer.get("blur"), 0) * min(scale_x, scale_y))
        if blur:
            layer_canvas = layer_canvas.filter(ImageFilter.GaussianBlur(radius=blur))
        combined = Image.alpha_composite(shadow_canvas, layer_canvas)
        _paste_layer_canvas(canvas, combined, layer, scale_x, scale_y)
    except Exception as err:
        logger.warning("template pillow: 文字图层渲染失败: %s", err)


def _has_text_mask_layer(layers: List[Dict[str, Any]], mode: Optional[str] = None) -> bool:
    for layer in layers:
        if layer.get("type") == "group":
            if _has_text_mask_layer(layer.get("children") or [], mode):
                return True
            continue
        if layer.get("type") not in ("main_title", "subtitle", "text"):
            continue
        mask_mode = layer.get("maskMode")
        if mode:
            if mask_mode == mode:
                return True
        elif mask_mode in ("knockout-text", "show-text"):
            return True
    return False


def _count_image_layers(layers: List[Dict[str, Any]]) -> int:
    total = 0
    for layer in layers:
        if layer.get("type") == "group":
            total += _count_image_layers(layer.get("children") or [])
        elif layer.get("type") == "image":
            total += 1
    return total


def _has_sticker_layer(layers: List[Dict[str, Any]]) -> bool:
    for layer in layers:
        if layer.get("type") == "group":
            if _has_sticker_layer(layer.get("children") or []):
                return True
            continue
        if layer.get("type") == "image" and (layer.get("assetKind") == "sticker" or _has_sticker_ref(layer)):
            return True
    return False


def _should_render_template_with_pillow_first(layout_config: Dict[str, Any]) -> Tuple[bool, str]:
    template = normalize_template(layout_config)
    layers = template.get("layers") or []
    if _has_text_mask_layer(layers):
        return True, "text-mask"
    if _has_sticker_layer(layers):
        return True, "sticker"
    image_count = _count_image_layers(layers)
    if image_count >= 4:
        return True, f"{image_count}-image-layers"
    return False, ""


def _draw_text_mask_shape(
    shape: Image.Image,
    layer: Dict[str, Any],
    title: Tuple[str, str],
    scale_x: float,
    scale_y: float,
    font_paths: FontPathInput,
) -> None:
    text = _text_value(layer, title)
    if not text:
        return
    try:
        font_path = _font_path_for_layer(layer, font_paths)
        font_size = max(1, _num(layer.get("fontSize"), 60) * min(scale_x, scale_y))
        font = ImageFont.truetype(font_path, max(1, int(round(font_size)))) if font_path and Path(font_path).is_file() else ImageFont.load_default()
        x = _num(layer.get("x"), 0) * scale_x
        y = _num(layer.get("y"), 0) * scale_y
        width = _num(layer.get("width"), 1) * scale_x
        height = _num(layer.get("height"), 1) * scale_y
        lines = _wrap_text_with_font(text, font, max(1, width))
        line_height = font_size * 1.1
        start_y = y + (height - line_height * len(lines)) / 2
        align = layer.get("textAlign") if layer.get("textAlign") in ("left", "right") else "center"
        layer_shape = Image.new("L", shape.size, 0)
        draw = ImageDraw.Draw(layer_shape)
        opacity = _clamp(_num(layer.get("opacity"), 1), 0, 1)
        fill = int(round(255 * opacity))
        for index, line in enumerate(lines):
            line_width = _measure_text_width(draw, line, font)
            line_x = x if align == "left" else x + width - line_width if align == "right" else x + (width - line_width) / 2
            line_y = start_y + index * line_height
            draw.text((line_x, line_y), line, font=font, fill=fill)
        blur = max(0, _num(layer.get("blur"), 0) * min(scale_x, scale_y))
        if blur:
            layer_shape = layer_shape.filter(ImageFilter.GaussianBlur(radius=max(1, blur)))
        rotation = _num(layer.get("rotation"), 0)
        if rotation:
            pivot_x = _clamp(_num(layer.get("pivotX"), 0.5), 0, 1)
            pivot_y = _clamp(_num(layer.get("pivotY"), 0.5), 0, 1)
            center = (x + width * pivot_x, y + height * pivot_y)
            layer_shape = layer_shape.rotate(-rotation, resample=Image.BICUBIC, expand=False, center=center)
        shape.paste(ImageChops.lighter(shape, layer_shape), (0, 0))
    except Exception as err:
        logger.warning("template pillow: 文字蒙版形状渲染失败: %s", err)


def _draw_text_mask_shapes(
    shape: Image.Image,
    layers: List[Dict[str, Any]],
    mode: str,
    title: Tuple[str, str],
    scale_x: float,
    scale_y: float,
    font_paths: FontPathInput,
) -> None:
    for layer in sorted(layers, key=lambda item: int(item.get("zIndex", 0))):
        if layer.get("type") == "group":
            group_shape = Image.new("L", shape.size, 0)
            _draw_text_mask_shapes(group_shape, layer.get("children") or [], mode, title, scale_x, scale_y, font_paths)
            opacity = _clamp(_num(layer.get("opacity"), 1), 0, 1)
            if opacity < 1:
                group_shape = group_shape.point(lambda value: int(value * opacity))
            rotation = _num(layer.get("rotation"), 0)
            if rotation:
                x = _num(layer.get("x"), 0) * scale_x
                y = _num(layer.get("y"), 0) * scale_y
                width = _num(layer.get("width"), 1) * scale_x
                height = _num(layer.get("height"), 1) * scale_y
                pivot_x = _clamp(_num(layer.get("pivotX"), 0.5), 0, 1)
                pivot_y = _clamp(_num(layer.get("pivotY"), 0.5), 0, 1)
                group_shape = group_shape.rotate(
                    -rotation,
                    resample=Image.BICUBIC,
                    expand=False,
                    center=(x + width * pivot_x, y + height * pivot_y),
                )
            shape.paste(ImageChops.lighter(shape, group_shape), (0, 0))
            continue
        if layer.get("type") in ("main_title", "subtitle", "text") and layer.get("maskMode") == mode:
            _draw_text_mask_shape(shape, layer, title, scale_x, scale_y, font_paths)


def _build_text_alpha_mask(
    layers: List[Dict[str, Any]],
    title: Tuple[str, str],
    canvas_width: int,
    canvas_height: int,
    scale_x: float,
    scale_y: float,
    font_paths: FontPathInput,
) -> Optional[Image.Image]:
    if not _has_text_mask_layer(layers):
        return None
    has_show_mode = _has_text_mask_layer(layers, "show-text")
    alpha_mask = Image.new("L", (canvas_width, canvas_height), 0 if has_show_mode else 255)
    show_shape = Image.new("L", alpha_mask.size, 0)
    _draw_text_mask_shapes(show_shape, layers, "show-text", title, scale_x, scale_y, font_paths)
    if show_shape.getbbox():
        alpha_mask.paste(255, (0, 0), show_shape)
    knockout_shape = Image.new("L", alpha_mask.size, 0)
    _draw_text_mask_shapes(knockout_shape, layers, "knockout-text", title, scale_x, scale_y, font_paths)
    if knockout_shape.getbbox():
        alpha_mask.paste(0, (0, 0), knockout_shape)
    return alpha_mask


def _render_text_alpha_mask_def(
    layers: List[Dict[str, Any]],
    title: Tuple[str, str],
    canvas_width: int,
    canvas_height: int,
    scale_x: float,
    scale_y: float,
    font_paths: FontPathInput,
) -> str:
    alpha_mask = _build_text_alpha_mask(layers, title, canvas_width, canvas_height, scale_x, scale_y, font_paths)
    if alpha_mask is None:
        return ""
    return (
        f'<mask id="mcr-text-mask" maskUnits="userSpaceOnUse" x="0" y="0" '
        f'width="{canvas_width}" height="{canvas_height}" mask-type="alpha">'
        f'<image href="{_esc(_png_data_uri(alpha_mask))}" x="0" y="0" width="{canvas_width}" height="{canvas_height}" preserveAspectRatio="none"/>'
        f'</mask>'
    )


def _draw_template_layer(
    canvas: Image.Image,
    layer: Dict[str, Any],
    image_slots: Dict[int, str],
    title: Tuple[str, str],
    scale_x: float,
    scale_y: float,
    font_paths: FontPathInput,
    auto_bg_color: str,
    config_bg_color: str,
) -> None:
    if layer.get("type") == "group":
        group_canvas = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        for child in sorted(layer.get("children") or [], key=lambda item: int(item.get("zIndex", 0))):
            _draw_template_layer(group_canvas, child, image_slots, title, scale_x, scale_y, font_paths, auto_bg_color, config_bg_color)
        _paste_layer_canvas(canvas, group_canvas, layer, scale_x, scale_y)
    elif layer.get("type") == "image":
        _draw_template_image_layer(canvas, layer, image_slots, scale_x, scale_y, auto_bg_color, config_bg_color)
    else:
        if layer.get("maskMode") in ("knockout-text", "show-text"):
            return
        _draw_template_text_layer(canvas, layer, title, scale_x, scale_y, font_paths, auto_bg_color, config_bg_color)


def render_template_to_image_bytes_pillow(
    layout_config: Dict[str, Any],
    image_slots: Dict[int, str],
    title: Tuple[str, str],
    resolution_config: ResolutionConfig,
    blur_size: int,
    color_ratio: float,
    bg_color_config: Optional[Dict[str, Any]] = None,
    font_paths: FontPathInput = None,
    output_format: str = "png",
) -> bytes:
    template = normalize_template(layout_config)
    canvas_width, canvas_height = resolution_config.size
    scale_x = canvas_width / EDITOR_BASE_WIDTH
    scale_y = canvas_height / EDITOR_BASE_HEIGHT
    scale = min(scale_x, scale_y)
    first_image_path = next((path for _, path in sorted(image_slots.items()) if path and Path(path).is_file()), "")
    auto_bg_color = "#5f7185"
    if first_image_path:
        try:
            with managed_image(first_image_path, "RGB") as original_img:
                auto_bg_color = _extract_comfortable_color(original_img) or _rgb_to_hex(ColorHelper.get_background_color(original_img))
        except Exception as err:
            logger.warning("template pillow: 获取背景色失败: %s", err)
    config_bg_color = str((bg_color_config or {}).get("config_color") or "")
    canvas = _render_background_image(
        template,
        image_slots,
        auto_bg_color,
        config_bg_color,
        canvas_width,
        canvas_height,
        max(0, int((template.get("background") or {}).get("blur", blur_size) or 0)) * scale,
        _clamp(float(color_ratio or 0.8), 0, 1),
    )
    layers = sorted(template.get("layers") or [], key=lambda item: int(item.get("zIndex", 0)))
    background = canvas.copy()
    canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
    background_z_index = int(_num((template.get("background") or {}).get("zIndex"), 0))
    for layer in [item for item in layers if int(item.get("zIndex", 0)) < background_z_index]:
        _draw_template_layer(canvas, layer, image_slots, title, scale_x, scale_y, font_paths, auto_bg_color, config_bg_color)
    canvas.alpha_composite(background)
    for layer in [item for item in layers if int(item.get("zIndex", 0)) >= background_z_index]:
        _draw_template_layer(canvas, layer, image_slots, title, scale_x, scale_y, font_paths, auto_bg_color, config_bg_color)

    text_alpha_mask = _build_text_alpha_mask(layers, title, canvas_width, canvas_height, scale_x, scale_y, font_paths)
    if text_alpha_mask is not None:
        canvas.putalpha(ImageChops.multiply(canvas.getchannel("A"), text_alpha_mask))

    buffer = BytesIO()
    fmt = (output_format or "png").lower()
    if fmt in ("jpg", "jpeg"):
        canvas.convert("RGB").save(buffer, format="JPEG", quality=90, optimize=True)
    else:
        canvas.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def svg_to_image_bytes(svg: str, output_format: str = "png") -> bytes:
    fmt = (output_format or "png").lower()
    try:
        import cairosvg  # type: ignore

        png_bytes = cairosvg.svg2png(bytestring=svg.encode("utf-8"), unsafe=True)
        if fmt in ("jpg", "jpeg"):
            with Image.open(BytesIO(png_bytes)) as image:
                out = BytesIO()
                image.convert("RGB").save(out, format="JPEG", quality=90, optimize=True)
                return out.getvalue()
        return png_bytes
    except Exception as err:
        raise RuntimeError(f"CairoSVG 转换失败: {err}") from err


def render_template_to_base64(
    layout_config: Dict[str, Any],
    image_slots: Dict[int, str],
    title: Tuple[str, str],
    resolution_config: ResolutionConfig,
    blur_size: int,
    color_ratio: float,
    bg_color_config: Optional[Dict[str, Any]] = None,
    font_paths: FontPathInput = None,
    output_format: str = "png",
) -> str:
    pillow_first, pillow_reason = _should_render_template_with_pillow_first(layout_config)
    if pillow_first:
        try:
            logger.info("模板渲染使用 Pillow 快速路径: %s", pillow_reason)
            image_bytes = render_template_to_image_bytes_pillow(
                layout_config=layout_config,
                image_slots=image_slots,
                title=title,
                resolution_config=resolution_config,
                blur_size=blur_size,
                color_ratio=color_ratio,
                bg_color_config=bg_color_config,
                font_paths=font_paths,
                output_format=output_format,
            )
            return base64.b64encode(image_bytes).decode("utf-8")
        except Exception as err:
            logger.warning("Pillow 快速路径渲染失败，回退 CairoSVG: %s", err)

    try:
        svg = render_template_svg(
            layout_config=layout_config,
            image_slots=image_slots,
            title=title,
            resolution_config=resolution_config,
            blur_size=blur_size,
            color_ratio=color_ratio,
            bg_color_config=bg_color_config,
            font_paths=font_paths,
        )
        image_bytes = svg_to_image_bytes(svg, output_format)
    except Exception as err:
        logger.warning("CairoSVG 模板渲染失败，回退 Pillow: %s", err)
        image_bytes = render_template_to_image_bytes_pillow(
            layout_config=layout_config,
            image_slots=image_slots,
            title=title,
            resolution_config=resolution_config,
            blur_size=blur_size,
            color_ratio=color_ratio,
            bg_color_config=bg_color_config,
            font_paths=font_paths,
            output_format=output_format,
        )
    return base64.b64encode(image_bytes).decode("utf-8")
