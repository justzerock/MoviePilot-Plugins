from __future__ import annotations

from typing import Any


def _layer(layer_type: str, x: float, y: float, width: float, height: float, z: int, **extra: Any) -> dict[str, Any]:
    layer = {
        "id": f"preset_{layer_type}_{z}_{extra.get('sourceIndex', '')}", "type": layer_type,
        "x": x, "y": y, "width": width, "height": height, "zIndex": z,
        "rotation": 0, "pivotX": 0.5, "pivotY": 0.5, "opacity": 1,
        "blur": 0, "shadowBlur": 0, "shadowOffsetX": 0, "shadowOffsetY": 0,
        "shadowOpacity": 0.28, "radius": 0,
    }
    layer.update(extra)
    layer["frame"] = {key: layer[key] for key in ("x", "y", "width", "height")}
    layer["transform"] = {key: layer[key] for key in ("rotation", "pivotX", "pivotY", "opacity")}
    layer["effects"] = {"blur": layer["blur"], "shadow": {"blur": layer["shadowBlur"], "offsetX": layer["shadowOffsetX"], "offsetY": layer["shadowOffsetY"], "opacity": layer["shadowOpacity"], "color": "#000000"}}
    if layer_type == "image":
        slot = int(layer.get("sourceIndex") or 1)
        layer.update({"source": {"kind": "slot", "slot": slot}, "fit": "cover", "cropFocusX": 0.5, "cropFocusY": 0.5})
    else:
        layer["fontFamily"] = "subtitle" if layer_type == "subtitle" else "main_title"
        layer.setdefault("textAlign", "center")
        layer["textStyle"] = {"fontFamily": layer["fontFamily"], "fontSize": layer["fontSize"], "textAlign": layer["textAlign"]}
    return layer


def _layout(layers: list[dict[str, Any]]) -> dict[str, Any]:
    canvas = {"width": 1920, "height": 1080, "unit": "px"}
    return {
        "schema": "mcr-template/v1", "version": "1.0", "canvas": canvas, "document": dict(canvas),
        "background": {"type": "blurred-image-color", "imageSource": {"kind": "slot", "slot": 1}, "colorSource": "auto", "color": "#5f7185", "color2": "#0a1628", "colorRatio": 0.8, "blur": 50, "grain": 0.18},
        "assets": {}, "layers": layers,
    }


def create_preset_layout(style: str) -> dict[str, Any]:
    style = {"single_1": "static_1", "single_2": "static_2", "multi_1": "static_3"}.get(str(style), str(style))
    if style == "static_2":
        return _layout([
            _layer("image", 0, 0, 1920, 1080, 1, sourceIndex=1, shadowBlur=28, shadowOffsetX=-20, shadowOpacity=0.2, maskPolygon={"units": "relative", "points": [[0.55, 0], [1, 0], [1, 1], [0.4, 1]]}),
            _layer("main_title", 80, 340, 800, 180, 2, fontSize=187, shadowBlur=12, shadowOffsetX=12, shadowOffsetY=12, shadowOpacity=0.24),
            _layer("subtitle", 100, 545, 760, 140, 2, fontSize=82, shadowBlur=10, shadowOffsetX=8, shadowOffsetY=8, shadowOpacity=0.22),
        ])
    if style == "static_3":
        order = [3, 1, 5, 4, 2, 6, 9, 8, 7]
        row = [(0, 0), (-174, 618), (-349, 1241)]
        col = [(0, 0), (466, -7), (968, -112)]
        layers = []
        for index, slot in enumerate(order):
            cx, cy = col[index // 3]
            rx, ry = row[index % 3]
            layers.append(_layer("image", 977 + cx + rx, -334 + cy + ry, 410, 610, index + 1, sourceIndex=slot, rotation=15.8, radius=46, shadowBlur=18, shadowOffsetX=10, shadowOffsetY=14, shadowOpacity=0.2))
        layers.extend([
            _layer("main_title", -18, 383, 902, 124, 20, fontSize=170, shadowBlur=10, shadowOffsetX=8, shadowOffsetY=8, shadowOpacity=0.24),
            _layer("subtitle", 124, 625, 620, 150, 20, fontSize=75, shadowBlur=8, shadowOffsetX=6, shadowOffsetY=6, shadowOpacity=0.2),
        ])
        return _layout(layers)
    if style == "static_4":
        return _layout([
            _layer("main_title", 260, 360, 1400, 180, 2, fontSize=190, shadowBlur=18, shadowOffsetY=12, shadowOpacity=0.24),
            _layer("subtitle", 320, 560, 1280, 150, 2, fontSize=80, shadowBlur=14, shadowOffsetY=8, shadowOpacity=0.2),
        ])
    return _layout([
        _layer("image", 1002, 162, 756, 756, 1, sourceIndex=1, rotation=36, radius=94, opacity=0.56, blur=8, shadowBlur=12, shadowOffsetX=10, shadowOffsetY=16, shadowOpacity=0.4),
        _layer("image", 1002, 162, 756, 756, 2, sourceIndex=1, rotation=18, radius=94, opacity=0.74, blur=4, shadowBlur=15, shadowOffsetX=15, shadowOffsetY=22, shadowOpacity=0.5),
        _layer("image", 1002, 162, 756, 756, 3, sourceIndex=1, radius=94, shadowBlur=18, shadowOffsetX=20, shadowOffsetY=26, shadowOpacity=0.6),
        _layer("main_title", 80, 340, 800, 180, 4, fontSize=170, shadowBlur=12, shadowOffsetX=12, shadowOffsetY=12, shadowOpacity=0.3),
        _layer("subtitle", 100, 540, 760, 140, 4, fontSize=75, shadowBlur=10, shadowOffsetX=8, shadowOffsetY=8, shadowOpacity=0.26),
    ])
