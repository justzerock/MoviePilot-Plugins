from __future__ import annotations

"""Safe, non-blocking browser font delivery for preview surfaces.

The renderer always keeps using its original font files.  This module only
creates cacheable WOFF2 subsets for browser previews and deliberately falls
back to the original font whenever a subset is unavailable.
"""

import hashlib
import json
import os
import re
import shutil
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable


FONT_SUFFIXES = {".ttf", ".ttc", ".otf", ".woff", ".woff2"}
SCHEMA_VERSION = 2
BASE_CHARACTERS = (
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    "，。！？：；、（）【】《》\"'“”‘’-_+&·/ \\n"
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _clean_characters(value: Any) -> str:
    raw = unicodedata.normalize("NFC", str(value or ""))
    return "".join(char for char in raw if not unicodedata.category(char).startswith("C") or char in "\n\t")


def collect_preview_characters(config: dict[str, Any]) -> str:
    """Collect stable text from configuration without exposing user paths."""
    parts: list[str] = [BASE_CHARACTERS]

    def visit(value: Any) -> None:
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, dict):
            for key, item in value.items():
                parts.append(str(key))
                visit(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                visit(item)

    for key in ("title_config", "custom_static_layout", "custom_static_layouts", "animated_settings", "all_libraries", "media_servers", "preview_rendered_characters"):
        visit(config.get(key))
    chars = "".join(_clean_characters(part) for part in parts)
    return "".join(sorted(set(chars)))


class PreviewFontService:
    def __init__(self, data_dir: Path, logger: Any | None = None) -> None:
        self.data_dir = data_dir
        self.root = data_dir / "fonts"
        self.subsets_root = self.root / "subsets"
        self.originals_root = self.root / "originals"
        self.logger = logger
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="yahaha-font-subset")
        self._locks: dict[tuple[str, str], threading.Lock] = {}
        self._locks_guard = threading.Lock()
        self._last_schedule: dict[tuple[str, str], float] = {}

    def assets(self, paths: list[Path]) -> dict[str, dict[str, Any]]:
        assets: dict[str, dict[str, Any]] = {}
        for path in paths:
            try:
                resolved = path.resolve()
                if not resolved.is_file() or resolved.suffix.lower() not in FONT_SUFFIXES:
                    continue
                source_sha = _sha256_file(resolved)
                font_id = f"font_{source_sha[:12]}"
                assets[font_id] = {
                    "font_id": font_id,
                    "path": resolved,
                    "source_sha256": source_sha,
                    "source_filename": resolved.name,
                    "source_format": resolved.suffix.lower().lstrip(".") or "ttf",
                }
                original_copy = self.originals_root / font_id / f"original{resolved.suffix.lower()}"
                original_copy.parent.mkdir(parents=True, exist_ok=True)
                if not original_copy.exists() or original_copy.stat().st_size != resolved.stat().st_size:
                    shutil.copy2(resolved, original_copy)
                self._write_metadata(assets[font_id])
            except Exception as error:
                self._log("warning", "读取预览字体失败 %s: %s", path, error)
        return assets

    def info(self, font_id: str, assets: dict[str, dict[str, Any]], config: dict[str, Any], url_for: Callable[[str, str, str], str]) -> dict[str, Any] | None:
        asset = assets.get(str(font_id or ""))
        if not asset:
            return None
        source_sha = str(asset["source_sha256"])
        family = f"YahahaPreview_{font_id}_{source_sha}"
        enabled = bool(config.get("preview_font_enabled", True))
        characters = collect_preview_characters(config)
        cache_seed = "|".join((source_sha, str(config.get("font_script_adaptation_enabled", True)), str(config.get("font_script_target") or "auto"), str(config.get("font_traditional_variant") or "standard"), characters, str(SCHEMA_VERSION)))
        charset_hash = hashlib.sha256(cache_seed.encode("utf-8")).hexdigest()[:16]
        if not enabled:
            return {"font_id": font_id, "font_family": family, "source_type": "disabled", "url": "", "format": "", "subset_status": "disabled", "charset_hash": charset_hash, "version": source_sha}
        if not bool(config.get("font_subset_enabled", True)):
            return self._original_info(asset, family, charset_hash, url_for, "disabled")
        manifest = self._manifest(asset, charset_hash)
        subset_file = self._subset_path(asset, charset_hash)
        if manifest.get("status") == "ready" and subset_file.is_file():
            subset_family = f"YahahaPreview_{font_id}_{charset_hash}"
            return {"font_id": font_id, "font_family": subset_family, "source_type": "subset", "url": url_for(font_id, "subset", charset_hash), "format": "woff2", "subset_status": "ready", "charset_hash": charset_hash, "version": charset_hash}
        self.schedule(asset, characters, charset_hash)
        status = str(manifest.get("status") or "pending")
        return self._original_info(asset, family, charset_hash, url_for, status)

    def file_for(self, font_id: str, variant: str, charset_hash: str, assets: dict[str, dict[str, Any]]) -> tuple[Path, str, str] | None:
        asset = assets.get(str(font_id or ""))
        if not asset:
            return None
        if variant == "subset" and re.fullmatch(r"[a-f0-9]{12,16}", str(charset_hash or "")):
            subset = self._subset_path(asset, charset_hash)
            if subset.is_file():
                return subset, "font/woff2", charset_hash
        source = Path(asset["path"])
        mime = {".otf": "font/otf", ".woff2": "font/woff2", ".woff": "font/woff"}.get(source.suffix.lower(), "font/ttf")
        return source, mime, str(asset["source_sha256"])

    def status(self, font_id: str, assets: dict[str, dict[str, Any]], config: dict[str, Any]) -> dict[str, Any] | None:
        asset = assets.get(str(font_id or ""))
        if not asset:
            return None
        characters = collect_preview_characters(config)
        cache_seed = "|".join((str(asset["source_sha256"]), str(config.get("font_script_adaptation_enabled", True)), str(config.get("font_script_target") or "auto"), str(config.get("font_traditional_variant") or "standard"), characters, str(SCHEMA_VERSION)))
        charset_hash = hashlib.sha256(cache_seed.encode("utf-8")).hexdigest()[:16]
        manifest = self._manifest(asset, charset_hash)
        return {"font_id": font_id, "charset_hash": charset_hash, "status": manifest.get("status", "pending"), "size_bytes": manifest.get("size_bytes", 0), "error": manifest.get("error")}

    def schedule(self, asset: dict[str, Any], characters: str, charset_hash: str, force: bool = False) -> None:
        key = (str(asset["font_id"]), charset_hash)
        now = time.monotonic()
        if not force and now - self._last_schedule.get(key, 0) < 1.5:
            return
        self._last_schedule[key] = now
        with self._locks_guard:
            lock = self._locks.setdefault(key, threading.Lock())
        if lock.locked():
            return
        self._write_manifest(asset, charset_hash, {"status": "pending", "character_count": len(characters), "error": None})
        self._executor.submit(self._build, asset, characters, charset_hash, lock)

    def _build(self, asset: dict[str, Any], characters: str, charset_hash: str, lock: threading.Lock) -> None:
        with lock:
            self._write_manifest(asset, charset_hash, {"status": "building", "character_count": len(characters), "error": None})
            try:
                from fontTools import subset  # type: ignore
                from fontTools.ttLib import TTFont  # type: ignore

                source = Path(asset["path"])
                target = self._subset_path(asset, charset_hash)
                target.parent.mkdir(parents=True, exist_ok=True)
                temp = target.with_suffix(".woff2.tmp")
                font_kwargs = {"fontNumber": 0} if source.suffix.lower() == ".ttc" else {}
                font = TTFont(str(source), recalcBBoxes=False, recalcTimestamp=False, **font_kwargs)
                options = subset.Options()
                options.flavor = "woff2"
                options.desubroutinize = True
                options.recalc_timestamp = False
                subsetter = subset.Subsetter(options=options)
                subsetter.populate(text=characters)
                subsetter.subset(font)
                font.flavor = "woff2"
                font.save(str(temp))
                os.replace(temp, target)
                self._write_manifest(asset, charset_hash, {"status": "ready", "character_count": len(characters), "characters": characters, "woff2_file": target.name, "size_bytes": target.stat().st_size, "error": None})
            except Exception as error:
                self._write_manifest(asset, charset_hash, {"status": "failed", "character_count": len(characters), "error": str(error)[:500]})
                self._log("warning", "预览字体精简失败 font=%s: %s", asset.get("source_filename"), error)

    def _original_info(self, asset: dict[str, Any], family: str, charset_hash: str, url_for: Callable[[str, str, str], str], status: str) -> dict[str, Any]:
        return {"font_id": asset["font_id"], "font_family": family, "source_type": "original", "url": url_for(str(asset["font_id"]), "original", str(asset["source_sha256"])), "format": str(asset["source_format"]), "subset_status": status, "charset_hash": charset_hash, "version": str(asset["source_sha256"])}

    def _subset_path(self, asset: dict[str, Any], charset_hash: str) -> Path:
        return self.subsets_root / str(asset["font_id"]) / f"{charset_hash}.woff2"

    def _manifest_path(self, asset: dict[str, Any], charset_hash: str) -> Path:
        return self.subsets_root / str(asset["font_id"]) / f"{charset_hash}.manifest.json"

    def _manifest(self, asset: dict[str, Any], charset_hash: str) -> dict[str, Any]:
        try:
            value = json.loads(self._manifest_path(asset, charset_hash).read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except Exception:
            return {}

    def _write_manifest(self, asset: dict[str, Any], charset_hash: str, values: dict[str, Any]) -> None:
        payload = {"schema_version": SCHEMA_VERSION, "font_id": asset["font_id"], "source_sha256": asset["source_sha256"], "charset_hash": charset_hash, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **values}
        path = self._manifest_path(asset, charset_hash)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        os.replace(temp, path)

    def _write_metadata(self, asset: dict[str, Any]) -> None:
        path = self.originals_root / str(asset["font_id"]) / "metadata.json"
        if path.exists():
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"font_id": asset["font_id"], "display_name": Path(asset["source_filename"]).stem, "source_filename": asset["source_filename"], "source_sha256": asset["source_sha256"], "source_format": asset["source_format"], "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, ensure_ascii=False, indent=2), encoding="utf-8")

    def _log(self, level: str, message: str, *args: Any) -> None:
        if self.logger and hasattr(self.logger, level):
            getattr(self.logger, level)(message, *args)
