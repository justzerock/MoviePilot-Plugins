from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Tuple

from app.log import logger
from app.plugins.yahahacoverstudio.style.preset_templates import create_preset_layout
from app.plugins.yahahacoverstudio.style.style_static_custom import create_style_static_custom
from app.plugins.yahahacoverstudio.utils.image_manager import ResolutionConfig


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def _valid_layout(layout_config: Dict[str, Any] | None) -> bool:
    return isinstance(layout_config, dict) and isinstance(layout_config.get("layers"), list) and bool(layout_config.get("layers"))


def _runtime_scale(resolution_config: ResolutionConfig | None) -> float:
    if not resolution_config:
        return 1.0
    try:
        return max(0.01, float(resolution_config.height) / 1080.0)
    except Exception:
        return 1.0


def _layout_for(
    base_style: str,
    layout_config: Dict[str, Any] | None,
    blur_size: int,
    color_ratio: float,
    resolution_config: ResolutionConfig | None,
    font_size: Tuple[float, float],
) -> Dict[str, Any]:
    has_saved_layout = _valid_layout(layout_config)
    layout = deepcopy(layout_config) if has_saved_layout else create_preset_layout(base_style)
    background = layout.get("background") if isinstance(layout.get("background"), dict) else {}
    if not has_saved_layout:
        background = {
            **background,
            "type": background.get("type") or "blurred-image-color",
            "imageSource": background.get("imageSource") or {"kind": "slot", "slot": 1},
            "colorSource": background.get("colorSource") or "auto",
            "color": background.get("color") or "#5f7185",
            "color2": background.get("color2") or "#0a1628",
            "blur": int(blur_size) if blur_size is not None else 50,
            "colorRatio": float(color_ratio) if color_ratio is not None else 0.8,
            "grain": background.get("grain", 0.18),
        }
        layout["background"] = background
        scale = _runtime_scale(resolution_config)
        main_size, subtitle_size = font_size
        for layer in layout.get("layers") or []:
            layer_type = str(layer.get("type") or "")
            if layer_type == "main_title":
                layer["fontSize"] = float(main_size) / scale
            elif layer_type == "subtitle":
                layer["fontSize"] = float(subtitle_size) / scale
            if layer_type in ("main_title", "subtitle"):
                layer["textStyle"] = {
                    **(layer.get("textStyle") if isinstance(layer.get("textStyle"), dict) else {}),
                    "fontFamily": layer.get("fontFamily") or ("subtitle" if layer_type == "subtitle" else "main_title"),
                    "fontSize": layer.get("fontSize"),
                }
    return layout


def _ensure_resolution(resolution_config: ResolutionConfig | None) -> ResolutionConfig:
    return resolution_config if resolution_config else ResolutionConfig("1080p")


def _layout_required_slots(layout_config: Dict[str, Any] | None, default: int = 1) -> int:
    if not _valid_layout(layout_config):
        return default
    indexes = []

    def visit(layers):
        for layer in layers or []:
            if not isinstance(layer, dict):
                continue
            if layer.get("type") == "group":
                visit(layer.get("children") or [])
                continue
            if layer.get("type") != "image":
                continue
            try:
                indexes.append(max(1, int(layer.get("sourceIndex", 1) or 1)))
            except (TypeError, ValueError):
                indexes.append(1)

    visit(layout_config.get("layers") or [])
    return max(indexes) if indexes else default


def _image_slots_from_input(image_input: Any, limit: int = 1) -> Dict[int, str]:
    if isinstance(image_input, (list, tuple)):
        paths = [str(path) for path in image_input if path and Path(str(path)).is_file()]
        if not paths:
            return {}
        return {index: paths[(index - 1) % len(paths)] for index in range(1, max(1, limit) + 1)}
    path = str(image_input or "")
    return {1: path} if path and Path(path).is_file() else {}


def _library_image_slots(library_dir: str | Path | None, limit: int = 9) -> Dict[int, str]:
    if not library_dir:
        return {}
    root = Path(library_dir)
    if not root.is_dir():
        return {}
    paths = [
        path
        for path in sorted(root.iterdir(), key=lambda item: item.name)
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
    if not paths:
        return {}
    return {index: str(paths[(index - 1) % len(paths)]) for index in range(1, limit + 1)}


def _render_preset(
    base_style: str,
    image_slots: Dict[int, str],
    title,
    font_path,
    font_size=(170, 75),
    blur_size=50,
    color_ratio=0.8,
    resolution_config=None,
    bg_color_config=None,
    layout_config=None,
    output_format="jpeg",
) -> str:
    if not image_slots:
        logger.error("%s: no source image available", base_style)
        return ""
    resolution = _ensure_resolution(resolution_config)
    layout = _layout_for(base_style, layout_config, blur_size, color_ratio, resolution, font_size)
    return create_style_static_custom(
        image_slots=image_slots,
        title=title,
        font_path=font_path,
        layout_config=layout,
        blur_size=blur_size,
        color_ratio=color_ratio,
        resolution_config=resolution,
        bg_color_config=bg_color_config,
        output_format=output_format,
    )


def create_style_static_1(
    image_path,
    title,
    font_path,
    font_size=(170, 75),
    font_offset=(0, 40, 40),
    blur_size=50,
    color_ratio=0.8,
    resolution_config=None,
    bg_color_config=None,
    layout_config=None,
):
    return _render_preset(
        "static_1",
        _image_slots_from_input(image_path, _layout_required_slots(layout_config, 1)),
        title,
        font_path,
        font_size=font_size,
        blur_size=blur_size,
        color_ratio=color_ratio,
        resolution_config=resolution_config,
        bg_color_config=bg_color_config,
        layout_config=layout_config,
    )


def create_style_static_2(
    image_path,
    title,
    font_path,
    font_size=(170, 75),
    font_offset=(0, 40, 40),
    blur_size=50,
    color_ratio=0.8,
    resolution_config=None,
    bg_color_config=None,
    layout_config=None,
):
    return _render_preset(
        "static_2",
        _image_slots_from_input(image_path, _layout_required_slots(layout_config, 1)),
        title,
        font_path,
        font_size=font_size,
        blur_size=blur_size,
        color_ratio=color_ratio,
        resolution_config=resolution_config,
        bg_color_config=bg_color_config,
        layout_config=layout_config,
    )


def create_style_static_3(
    library_dir,
    title,
    font_path,
    font_size=(170, 75),
    font_offset=(0, 40, 40),
    is_blur=False,
    blur_size=50,
    color_ratio=0.8,
    resolution_config=None,
    bg_color_config=None,
    layout_config=None,
):
    limit = _layout_required_slots(layout_config, 9)
    if isinstance(library_dir, (list, tuple)):
        image_slots = _image_slots_from_input(library_dir, limit)
    else:
        image_slots = _library_image_slots(library_dir, limit)
    return _render_preset(
        "static_3",
        image_slots,
        title,
        font_path,
        font_size=font_size,
        blur_size=blur_size,
        color_ratio=color_ratio,
        resolution_config=resolution_config,
        bg_color_config=bg_color_config,
        layout_config=layout_config,
    )


def create_style_static_4(
    image_path,
    title,
    font_path,
    font_size=(170, 75),
    font_offset=(0, 40, 40),
    blur_size=50,
    color_ratio=0.8,
    resolution_config=None,
    bg_color_config=None,
    layout_config=None,
):
    return _render_preset(
        "static_4",
        _image_slots_from_input(image_path, _layout_required_slots(layout_config, 1)),
        title,
        font_path,
        font_size=font_size,
        blur_size=blur_size,
        color_ratio=color_ratio,
        resolution_config=resolution_config,
        bg_color_config=bg_color_config,
        layout_config=layout_config,
    )


def create_style_single_1(*args, **kwargs):
    return create_style_static_1(*args, **kwargs)


def create_style_single_2(*args, **kwargs):
    return create_style_static_2(*args, **kwargs)


def create_style_multi_1(*args, **kwargs):
    return create_style_static_3(*args, **kwargs)
