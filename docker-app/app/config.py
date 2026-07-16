from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import secrets
import shutil
import tempfile
from typing import Any

import yaml


DATA_DIR = Path(os.environ.get("YAHAA_DATA_DIR", "/app/data"))
CONFIG_PATH = DATA_DIR / "config.yaml"


DEFAULT_CONFIG: dict[str, Any] = {
    "enabled": True,
    "timezone": "Asia/Shanghai",
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
    "local_mode": True,
    "mock_enabled": False,
    "upload_after_generate": True,
    "api_token": "",
    "selected_servers": [],
    "all_servers": [],
    "include_libraries": [],
    "all_libraries": [],
    "sort_by": "Random",
    # An empty value means that server mode uses media-server artwork directly.
    # Local and test modes still use /app/data/input as their implicit source.
    "covers_input": "",
    "covers_output": "/app/data/output",
    "save_recent_covers": True,
    "history_enabled": True,
    "history_retention_batches": 30,
    "covers_history_limit_per_library": 10,
    "covers_page_history_limit": 50,
    "title_config": {},
    "title_config_strict": False,
    "distinguish_same_name_libraries": False,
    "main_title_font_preset": "chaohei",
    "subtitle_font_preset": "EmblemaOne",
    "custom_text_font_preset": "EmblemaOne",
    "main_title_font_custom": "",
    "subtitle_font_custom": "",
    "custom_text_font_custom": "",
    "preview_font_enabled": True,
    "font_subset_enabled": True,
    "font_script_adaptation_enabled": True,
    "font_script_target": "auto",
    "font_traditional_variant": "standard",
    "library_scheme_rules": [],
    "default_scheme_id": "",
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
    "log_retention_days": 7,
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
        DATA_DIR / "fonts" / "originals",
        DATA_DIR / "fonts" / "subsets",
        DATA_DIR / "input",
        DATA_DIR / "output",
        DATA_DIR / "stickers",
        DATA_DIR / "backups",
        DATA_DIR / "tmp",
        DATA_DIR / "tmp" / "preview_cache",
        DATA_DIR / "logs",
        DATA_DIR / "history",
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


def has_media_server_config(config: dict[str, Any]) -> bool:
    if str(config.get("emby_url") or "").strip() or str(config.get("emby_api_key") or "").strip():
        return True
    if str(config.get("jellyfin_url") or "").strip() or str(config.get("jellyfin_api_key") or "").strip():
        return True
    servers = config.get("media_servers")
    return isinstance(servers, list) and any(
        isinstance(item, dict)
        and str(item.get("url") or "").strip()
        and str(item.get("api_key") or "").strip()
        for item in servers
    )


def infer_local_mode(raw: dict[str, Any]) -> dict[str, Any]:
    if "local_mode" not in raw and has_media_server_config(raw):
        raw = dict(raw)
        raw["local_mode"] = False
    return raw


def load_config() -> dict[str, Any]:
    ensure_data_dirs()
    if CONFIG_PATH.is_dir():
        backup_path = DATA_DIR / "config.yaml.invalid-dir"
        index = 1
        while backup_path.exists():
            backup_path = DATA_DIR / f"config.yaml.invalid-dir.{index}"
            index += 1
        try:
            if any(CONFIG_PATH.iterdir()):
                shutil.move(str(CONFIG_PATH), str(backup_path))
            else:
                CONFIG_PATH.rmdir()
        except Exception:
            raw = {}
            return normalize_config(deep_merge(DEFAULT_CONFIG, raw))
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return load_config()
    try:
        raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        raw = {}
    raw_config = infer_local_mode(raw) if isinstance(raw, dict) else {}
    config = normalize_config(deep_merge(DEFAULT_CONFIG, raw_config))
    if not isinstance(raw, dict) or not str(raw.get("api_token") or "").strip() or raw.get("monitor_source") != config.get("monitor_source"):
        CONFIG_PATH.write_text(
            yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
    return config


def save_config(config: dict[str, Any]) -> dict[str, Any]:
    ensure_data_dirs()
    incoming = infer_local_mode(config or {}) if isinstance(config, dict) else {}
    normalized = normalize_config(deep_merge(DEFAULT_CONFIG, incoming))
    payload = yaml.safe_dump(normalized, allow_unicode=True, sort_keys=False)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=DATA_DIR, delete=False) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            temp_path = Path(handle.name)
        temp_path.replace(CONFIG_PATH)
        # Read back once: a successful HTTP response now means the volume has
        # a valid, parseable configuration rather than merely an open handle.
        saved = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
        if not isinstance(saved, dict):
            raise ValueError("配置文件写入后无法解析")
    except Exception:
        try:
            if temp_path:
                temp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise
    return normalized


def normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    monitor_source = str(config.get("monitor_source") or "webhook").strip().lower()
    if monitor_source not in {"webhook", "emby", "jellyfin"}:
        monitor_source = "webhook"
    config["monitor_source"] = monitor_source
    if not str(config.get("api_token") or "").strip():
        config["api_token"] = secrets.token_urlsafe(24)
    try:
        config["log_retention_days"] = max(1, min(365, int(config.get("log_retention_days") or 7)))
    except (TypeError, ValueError):
        config["log_retention_days"] = 7
    config["history_enabled"] = bool(config.get("history_enabled", config.get("save_recent_covers", True)))
    config["preview_font_enabled"] = bool(config.get("preview_font_enabled", True))
    config["font_subset_enabled"] = bool(config.get("font_subset_enabled", True))
    config["font_script_adaptation_enabled"] = bool(config.get("font_script_adaptation_enabled", True))
    if str(config.get("font_script_target") or "auto") not in {"auto", "simplified", "traditional"}:
        config["font_script_target"] = "auto"
    if str(config.get("font_traditional_variant") or "standard") not in {"standard", "taiwan", "hongkong"}:
        config["font_traditional_variant"] = "standard"
    legacy_scheme = str((config.get("style_config") or {}).get("style") or "single_1")
    config["default_scheme_id"] = str(config.get("default_scheme_id") or legacy_scheme)
    rules: list[dict[str, Any]] = []
    seen_libraries: set[str] = set()
    for raw in config.get("library_scheme_rules") or []:
        if not isinstance(raw, dict):
            continue
        scheme_id = str(raw.get("scheme_id") or "").strip()
        keys = [str(item).strip() for item in (raw.get("library_keys") or []) if str(item).strip()]
        keys = [item for item in keys if item not in seen_libraries]
        if not scheme_id or not keys:
            continue
        seen_libraries.update(keys)
        rules.append({"id": str(raw.get("id") or secrets.token_hex(6)), "scheme_id": scheme_id, "library_keys": keys})
    config["library_scheme_rules"] = rules
    try:
        config["history_retention_batches"] = max(1, min(1000, int(config.get("history_retention_batches") or 30)))
    except (TypeError, ValueError):
        config["history_retention_batches"] = 30
    if config.get("local_mode") is True:
        config["mock_enabled"] = False
        config["upload_after_generate"] = False
    elif config.get("mock_enabled") is True:
        config["upload_after_generate"] = False
    else:
        config["upload_after_generate"] = True
    return config


def resolve_data_path(value: str | None, fallback: str) -> Path:
    raw = value or fallback
    path = Path(raw)
    if not path.is_absolute():
        path = DATA_DIR / path
    path.mkdir(parents=True, exist_ok=True)
    return path
