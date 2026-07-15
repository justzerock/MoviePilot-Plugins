from __future__ import annotations

# Keep this adapter dependency-free so it can run inside MoviePilot.
from typing import Any
import re

_HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_ALIASES = {"title", "main", "zh", "name", "subtitle", "sub", "en", "background", "bg", "color", "text", "custom_text", "content", "texts"}

def _text(value: Any, default: str, field: str, warnings: list[str]) -> str:
    if value is None: return default
    if isinstance(value, (str, int, float, bool)): return str(value)
    warnings.append(f"{field} 必须是文本，已使用默认值。")
    return default

def _background(value: Any, warnings: list[str]) -> str | None:
    if value in (None, ""): return None
    if isinstance(value, str) and _HEX_COLOR.fullmatch(value.strip()): return value.strip()
    warnings.append(f"background 不是有效的 #RGB 或 #RRGGBB 颜色: {value!r}，已忽略。")
    return None

def _texts(value: Any, warnings: list[str]) -> dict[str, str]:
    if value in (None, ""): return {}
    if not isinstance(value, dict):
        warnings.append("texts 必须是键值对象，已忽略。")
        return {}
    result: dict[str, str] = {}
    for raw_key, raw_value in value.items():
        key = str(raw_key or "").strip()
        if not key: continue
        if not isinstance(raw_value, (str, int, float, bool)) and raw_value is not None:
            warnings.append(f"texts.{key} 必须是简单文本，已忽略。")
            continue
        result[key] = "" if raw_value is None else str(raw_value)
    return result

def normalize_title_config_item(key: str, value: Any) -> tuple[dict[str, Any] | None, list[str]]:
    warnings: list[str] = []
    if isinstance(value, (str, int, float, bool)):
        return {"title": str(value), "subtitle": "", "background": None, "texts": {}}, warnings
    if isinstance(value, list):
        if not value: return None, ["旧列表至少需要一个标题值。"]
        title = _text(value[0] if value else key, key, "title", warnings)
        subtitle = _text(value[1] if len(value) > 1 else "", "", "subtitle", warnings)
        background = None
        texts: dict[str, str] = {}
        for item in value[2:]:
            if isinstance(item, str) and background is None: background = _background(item, warnings)
            elif isinstance(item, dict): texts.update(_texts(item.get("texts") if isinstance(item.get("texts"), dict) else item, warnings))
        return {"title": title, "subtitle": subtitle, "background": background, "texts": texts}, warnings
    if not isinstance(value, dict): return None, ["配置项必须是对象、旧列表或标题字符串。"]
    title = _text(value.get("title", value.get("main", value.get("zh", value.get("name", key)))), key, "title", warnings)
    subtitle = _text(value.get("subtitle", value.get("sub", value.get("en", ""))), "", "subtitle", warnings)
    background = _background(value.get("background", value.get("bg", value.get("color"))), warnings)
    texts = _texts(value.get("texts"), warnings)
    legacy = value.get("text", value.get("custom_text", value.get("content")))
    if legacy is not None: texts.setdefault("default", _text(legacy, "", "text", warnings))
    for extra_key, extra_value in value.items():
        name = str(extra_key).strip()
        if name and name not in _ALIASES and isinstance(extra_value, (str, int, float, bool)): texts.setdefault(name, str(extra_value))
    normalized: dict[str, Any] = {"title": title, "subtitle": subtitle, "background": background, "texts": texts}
    for extra_key, extra_value in value.items():
        if str(extra_key) not in _ALIASES: normalized.setdefault(str(extra_key), extra_value)
    return normalized, warnings

def normalize_title_config(value: Any) -> tuple[dict[str, dict[str, Any]], list[str]]:
    if value in (None, ""): return {}, []
    if not isinstance(value, dict): return {}, ["标题配置根节点必须是 YAML 对象。"]
    result: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []
    for raw_key, raw_value in value.items():
        key = str(raw_key or "").strip()
        if not key:
            warnings.append("标题配置中的空媒体库键已忽略。")
            continue
        item, item_warnings = normalize_title_config_item(key, raw_value)
        warnings.extend(f"{key}: {message}" for message in item_warnings)
        if item is not None: result[key] = item
    return result, warnings
