from copy import deepcopy
from typing import Any, Dict, List


EDITOR_BASE_WIDTH = 1920
EDITOR_BASE_HEIGHT = 1080


def _background() -> Dict[str, Any]:
    return {
        "type": "blurred-image-color",
        "imageSource": {"kind": "slot", "slot": 1},
        "colorSource": "auto",
        "color": "#5f7185",
        "color2": "#0a1628",
        "colorRatio": 0.8,
        "blur": 50,
        "grain": 0.18,
    }


def _image_layer(
    slot: int,
    x: float,
    y: float,
    width: float,
    height: float,
    z: int,
    **kwargs: Any,
) -> Dict[str, Any]:
    layer = {
        "id": f"preset_img_{slot}_{z}",
        "type": "image",
        "sourceIndex": slot,
        "source": {"kind": "slot", "slot": slot},
        "fit": "cover",
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "zIndex": z,
        "rotation": 0,
        "radius": 0,
        "pivotX": 0.5,
        "pivotY": 0.5,
        "opacity": 1,
        "blur": 0,
        "shadowBlur": 0,
        "shadowOffsetX": 0,
        "shadowOffsetY": 0,
        "shadowOpacity": 0.28,
        "cropFocusX": 0.5,
        "cropFocusY": 0.5,
    }
    layer.update(kwargs)
    return _with_legacy_fields(layer)


def _title_layer(
    layer_type: str,
    x: float,
    y: float,
    width: float,
    height: float,
    z: int,
    font_size: float,
    **kwargs: Any,
) -> Dict[str, Any]:
    layer = {
        "id": f"preset_{layer_type}_{z}",
        "type": layer_type,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "zIndex": z,
        "fontSize": font_size,
        "fontFamily": "subtitle" if layer_type == "subtitle" else "main_title",
        "textAlign": "center",
        "rotation": 0,
        "radius": 0,
        "pivotX": 0.5,
        "pivotY": 0.5,
        "opacity": 1,
        "blur": 0,
        "shadowBlur": 0,
        "shadowOffsetX": 0,
        "shadowOffsetY": 0,
        "shadowOpacity": 0.28,
    }
    layer.update(kwargs)
    return _with_legacy_fields(layer)


def _with_legacy_fields(layer: Dict[str, Any]) -> Dict[str, Any]:
    layer["frame"] = {
        "x": layer.get("x", 0),
        "y": layer.get("y", 0),
        "width": layer.get("width", 0),
        "height": layer.get("height", 0),
    }
    layer["transform"] = {
        "rotation": layer.get("rotation", 0),
        "pivotX": layer.get("pivotX", 0.5),
        "pivotY": layer.get("pivotY", 0.5),
        "opacity": layer.get("opacity", 1),
    }
    layer["effects"] = {
        "blur": layer.get("blur", 0),
        "shadow": {
            "blur": layer.get("shadowBlur", 0),
            "offsetX": layer.get("shadowOffsetX", 0),
            "offsetY": layer.get("shadowOffsetY", 0),
            "opacity": layer.get("shadowOpacity", 0.28),
            "color": "#000000",
        },
    }
    if layer.get("type") in ("main_title", "subtitle", "text"):
        layer["textStyle"] = {
            "fontFamily": layer.get("fontFamily"),
            "fontSize": layer.get("fontSize", 0),
            "textAlign": layer.get("textAlign", "center"),
        }
    return layer


def _template(layers: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "schema": "mcr-template/v1",
        "version": "1.0",
        "canvas": {"width": EDITOR_BASE_WIDTH, "height": EDITOR_BASE_HEIGHT, "unit": "px"},
        "document": {"width": EDITOR_BASE_WIDTH, "height": EDITOR_BASE_HEIGHT, "unit": "px"},
        "background": _background(),
        "assets": {},
        "layers": layers,
    }


def create_preset_layout(base_style: str) -> Dict[str, Any]:
    style = str(base_style or "static_1")
    if style == "static_1":
        return _template([
            _image_layer(1, 1002, 162, 756, 756, 1, rotation=36, radius=94, opacity=0.56, blur=8, shadowBlur=12, shadowOffsetX=10, shadowOffsetY=16, shadowOpacity=0.4),
            _image_layer(1, 1002, 162, 756, 756, 2, rotation=18, radius=94, opacity=0.74, blur=4, shadowBlur=15, shadowOffsetX=15, shadowOffsetY=22, shadowOpacity=0.5),
            _image_layer(1, 1002, 162, 756, 756, 3, radius=94, shadowBlur=18, shadowOffsetX=20, shadowOffsetY=26, shadowOpacity=0.6),
            _title_layer("main_title", 80, 340, 800, 180, 4, 170, shadowBlur=12, shadowOffsetX=12, shadowOffsetY=12, shadowOpacity=0.3),
            _title_layer("subtitle", 100, 540, 760, 140, 4, 75, shadowBlur=10, shadowOffsetX=8, shadowOffsetY=8, shadowOpacity=0.26),
        ])

    if style == "static_2":
        return _template([
            _image_layer(
                1,
                0,
                0,
                1920,
                1080,
                1,
                shadowBlur=28,
                shadowOffsetX=-20,
                shadowOffsetY=0,
                shadowOpacity=0.2,
                maskPolygon={
                    "units": "relative",
                    "points": [[0.55, 0], [1, 0], [1, 1], [0.4, 1]],
                },
            ),
            _title_layer("main_title", 80, 340, 800, 180, 2, 187, shadowBlur=12, shadowOffsetX=12, shadowOffsetY=12, shadowOpacity=0.24),
            _title_layer("subtitle", 100, 545, 760, 140, 2, 82, shadowBlur=10, shadowOffsetX=8, shadowOffsetY=8, shadowOpacity=0.22),
        ])

    if style == "static_3":
        order = [3, 1, 5, 4, 2, 6, 9, 8, 7]
        row_offsets = [
            {"x": 0, "y": 0},
            {"x": -174, "y": 618},
            {"x": -349, "y": 1241},
        ]
        column_offsets = [
            {"x": 0, "y": 0},
            {"x": 466, "y": -7},
            {"x": 968, "y": -112},
        ]
        positions = []
        for index, _ in enumerate(order):
            column = index // 3
            row = index % 3
            positions.append({
                "x": 977 + column_offsets[column]["x"] + row_offsets[row]["x"],
                "y": -334 + column_offsets[column]["y"] + row_offsets[row]["y"],
            })
        layers = [
            _image_layer(
                slot,
                positions[index]["x"],
                positions[index]["y"],
                410,
                610,
                index + 1,
                rotation=15.8,
                radius=46,
                shadowBlur=18,
                shadowOffsetX=10,
                shadowOffsetY=14,
                shadowOpacity=0.2,
            )
            for index, slot in enumerate(order)
        ]
        layers.append(_title_layer("main_title", -18, 383, 902, 124, 20, 170, shadowBlur=10, shadowOffsetX=8, shadowOffsetY=8, shadowOpacity=0.24))
        layers.append(_title_layer("subtitle", 124, 625, 620, 150, 20, 75, shadowBlur=8, shadowOffsetX=6, shadowOffsetY=6, shadowOpacity=0.2))
        return _template(layers)

    if style == "static_4":
        return _template([
            _title_layer("main_title", 260, 360, 1400, 180, 2, 190, shadowBlur=18, shadowOffsetY=12, shadowOpacity=0.24),
            _title_layer("subtitle", 320, 560, 1280, 150, 2, 80, shadowBlur=14, shadowOffsetY=8, shadowOpacity=0.2),
        ])

    return create_preset_layout("static_1")


def clone_preset_layout(base_style: str) -> Dict[str, Any]:
    return deepcopy(create_preset_layout(base_style))
