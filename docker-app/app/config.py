from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import secrets
from typing import Any

import yaml


DATA_DIR = Path(os.environ.get("YAHAA_DATA_DIR", "/app/data"))
CONFIG_PATH = DATA_DIR / "config.yaml"


DEFAULT_CONFIG: dict[str, Any] = {
    "enabled": True,
    "auto_save_config": False,
    "transfer_monitor": False,
    "monitor_source": "webhook",
    "lock_latest_sort": False,
    "cron": "",
    "delay": 60,
    "emby_url": "",
    "emby_api_key": "",
    "jellyfin_url": "",
    "jellyfin_api_key": "",
    "media_servers": [],
    "mock_enabled": True,
    "upload_after_generate": True,
    "api_token": "",
    "selected_servers": [],
    "all_servers": [],
    "include_libraries": [],
    "all_libraries": [],
    "sort_by": "Random",
    "covers_input": "/app/data/input",
    "covers_output": "/app/data/output",
    "save_recent_covers": True,
    "covers_history_limit_per_library": 10,
    "covers_page_history_limit": 50,
    "title_config": {
        "示例媒体库": {
            "title": "示例媒体库",
            "subtitle": "Library",
            "texts": {},
        },
    },
    "title_config_strict": False,
    "main_title_font_preset": "chaohei",
    "subtitle_font_preset": "EmblemaOne",
    "custom_text_font_preset": "EmblemaOne",
    "main_title_font_custom": "",
    "subtitle_font_custom": "",
    "custom_text_font_custom": "",
    "animation_duration": 8,
    "animation_scroll": "alternate",
    "animation_fps": 24,
    "animation_format": "apng",
    "animation_resolution": "320x180",
    "animation_reduce_colors": "medium",
    "animated_2_image_count": 6,
    "animated_2_departure_type": "fly",
    "animated_settings": {},
    "clean_images": False,
    "clean_fonts": False,
    "backup_enabled": False,
    "backup_cron": "",
    "backup_path": "",
    "page_tab": "generate-tab",
    "style_naming_v2": True,
    "custom_static_layout": None,
    "custom_static_layouts": None,
    "custom_static_active_id": None,
    "style_config": {
        "style": "single_1",
        "resolution": "1080p",
        "image_source": "backdrop",
        "image_count_mode": "fixed",
        "image_limit": 9,
        "background_color": "#6f8090",
        "color_ratio": 0.78,
        "blur": 42,
        "font": "",
        "main_font_size": 170,
        "subtitle_font_size": 76,
        "title_scale": 1,
        "output_format": "jpg",
    },
}


def ensure_data_dirs() -> None:
    for path in (
        DATA_DIR,
        DATA_DIR / "fonts",
        DATA_DIR / "input",
        DATA_DIR / "output",
        DATA_DIR / "stickers",
        DATA_DIR / "backups",
        DATA_DIR / "tmp",
    ):
        path.mkdir(parents=True, exist_ok=True)


def deep_merge(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in (incoming or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config() -> dict[str, Any]:
    ensure_data_dirs()
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return load_config()
    try:
        raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        raw = {}
    config = normalize_config(deep_merge(DEFAULT_CONFIG, raw if isinstance(raw, dict) else {}))
    if not isinstance(raw, dict) or not str(raw.get("api_token") or "").strip() or raw.get("monitor_source") != config.get("monitor_source"):
        CONFIG_PATH.write_text(
            yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
    return config


def save_config(config: dict[str, Any]) -> dict[str, Any]:
    ensure_data_dirs()
    normalized = normalize_config(deep_merge(DEFAULT_CONFIG, config or {}))
    CONFIG_PATH.write_text(
        yaml.safe_dump(normalized, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return normalized


def normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    monitor_source = str(config.get("monitor_source") or "webhook").strip().lower()
    if monitor_source not in {"webhook", "emby", "jellyfin"}:
        monitor_source = "webhook"
    config["monitor_source"] = monitor_source
    if not str(config.get("api_token") or "").strip():
        config["api_token"] = secrets.token_urlsafe(24)
    return config


def resolve_data_path(value: str | None, fallback: str) -> Path:
    raw = value or fallback
    path = Path(raw)
    if not path.is_absolute():
        path = DATA_DIR / path
    path.mkdir(parents=True, exist_ok=True)
    return path
