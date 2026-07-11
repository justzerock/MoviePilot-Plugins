from __future__ import annotations

import base64
import json
import mimetypes
import re
from datetime import datetime, timezone
from .time_utils import app_zone
from pathlib import Path
from typing import Any

import yaml
from PIL import Image, ImageFont

from .config import DATA_DIR


FONT_EXTENSIONS = {".ttf", ".ttc", ".otf", ".woff", ".woff2"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
BACKUP_EXTENSIONS = {".json", ".yaml", ".yml"}


def safe_filename(name: str, fallback: str) -> str:
    raw = Path(str(name or fallback)).name
    raw = re.sub(r"[\\/:*?\"<>|]+", "_", raw).strip()
    return raw or fallback


def unique_path(directory: Path, filename: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    stem = Path(filename).stem or "file"
    suffix = Path(filename).suffix
    candidate = directory / f"{stem}{suffix}"
    index = 2
    while candidate.exists():
        candidate = directory / f"{stem}_{index}{suffix}"
        index += 1
    return candidate


def decode_data_url(data_url: str) -> tuple[str, bytes]:
    raw = str(data_url or "")
    if "," not in raw:
        return "application/octet-stream", base64.b64decode(raw)
    header, payload = raw.split(",", 1)
    mime = "application/octet-stream"
    if header.startswith("data:"):
        mime = header[5:].split(";")[0] or mime
    return mime, base64.b64decode(payload)


def encode_file_payload(path: Path, mime: str | None = None) -> dict[str, str]:
    guessed = mime or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return {
        "name": path.name,
        "mime": guessed,
        "b64": base64.b64encode(path.read_bytes()).decode("ascii"),
    }


def data_url_for_file(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def is_within_data_dir(path: Path) -> bool:
    try:
        path.resolve().relative_to(DATA_DIR.resolve())
        return True
    except Exception:
        return False


def font_item(path: Path, title: str | None = None) -> dict[str, Any]:
    stat = path.stat()
    return {
        "title": title or path.stem,
        "name": title or path.name,
        "value": path.name,
        "path": str(path),
        "url": data_file_url(path),
        "size": stat.st_size,
        "mtime": stat.st_mtime,
        "renderable": is_font_renderable(path),
    }


def sticker_item(path: Path) -> dict[str, Any]:
    width = 1
    height = 1
    try:
        with Image.open(path) as image:
            width, height = image.size
    except Exception:
        pass
    stat = path.stat()
    return {
        "name": path.name,
        "path": str(path),
        "url": data_file_url(path),
        "width": width,
        "height": height,
        "size": stat.st_size,
        "mtime": stat.st_mtime,
    }


def backup_item(path: Path) -> dict[str, Any]:
    stat = path.stat()
    exported_at = ""
    version = ""
    schema = ""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if isinstance(raw, dict):
            exported_at = str(raw.get("exported_at") or "")
            version = str(raw.get("version") or "")
            schema = str(raw.get("schema") or "")
    except Exception:
        pass
    return {
        "title": path.name,
        "name": path.name,
        "path": str(path),
        "size": stat.st_size,
        "mtime": stat.st_mtime,
        "mtime_label": datetime.fromtimestamp(stat.st_mtime, tz=app_zone()).strftime("%Y-%m-%d %H:%M:%S"),
        "exported_at": exported_at,
        "version": version,
        "schema": schema,
    }


def write_backup(path: Path, config: dict[str, Any], version: str = "docker") -> Path:
    payload = {
        "schema": "yahaha-cover-studio/docker-backup/v1",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "version": version,
        "config": config,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def read_backup_config(path: Path) -> dict[str, Any]:
    raw_text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        raw = json.loads(raw_text)
    else:
        raw = yaml.safe_load(raw_text)
    if isinstance(raw, dict) and isinstance(raw.get("config"), dict):
        return raw["config"]
    if isinstance(raw, dict):
        return raw
    raise ValueError("备份文件格式不正确")


def is_font_renderable(path: Path) -> bool:
    if path.suffix.lower() not in FONT_EXTENSIONS:
        return False
    try:
        ImageFont.truetype(str(path), 24)
        return True
    except Exception:
        return path.suffix.lower() in {".woff", ".woff2"}


def data_file_url(path: Path) -> str:
    try:
        rel = path.resolve().relative_to(DATA_DIR.resolve())
    except Exception:
        rel = Path(path.name)
    from urllib.parse import quote

    return "/data/" + "/".join(quote(part) for part in rel.parts)
