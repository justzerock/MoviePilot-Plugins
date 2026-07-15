"""Non-blocking, content-addressed preview font subsets.

Original font files remain owned by the normal renderer.  Browser previews get
an optional WOFF2 cache and fall back to the original file while it is built.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable

BASE_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz，。！？：；、（）【】《》\"'“”‘’-_+&·/ \n"


def collect_characters(config: dict[str, Any]) -> str:
    values = [BASE_CHARS]
    def visit(value: Any) -> None:
        if isinstance(value, str): values.append(value)
        elif isinstance(value, dict):
            for key, item in value.items(): values.append(str(key)); visit(item)
        elif isinstance(value, list):
            for item in value: visit(item)
    for key in ("title_config", "all_libraries", "custom_static_layout", "custom_static_layouts", "animated_settings"):
        visit(config.get(key))
    raw = unicodedata.normalize("NFC", "".join(values))
    return "".join(sorted({char for char in raw if not unicodedata.category(char).startswith("C") or char == "\n"}))


class PreviewFontService:
    def __init__(self, data_dir: Path, logger: Any = None):
        self.root = data_dir / "fonts"
        self.subsets = self.root / "subsets"
        self.originals = self.root / "originals"
        self.logger = logger
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="yahaha-font-subset")
        self.locks: dict[tuple[str, str], threading.Lock] = {}
        self.guard = threading.Lock()
        self.scheduled: dict[tuple[str, str], float] = {}

    def assets(self, paths: list[Path]) -> dict[str, dict[str, Any]]:
        result = {}
        for path in paths:
            try:
                path = path.resolve()
                if not path.is_file(): continue
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                font_id = f"font_{digest[:12]}"
                item = {"font_id": font_id, "path": path, "sha": digest, "format": path.suffix.lower().lstrip(".") or "ttf"}
                result[font_id] = item
                meta = self.originals / font_id / "metadata.json"
                original_copy = self.originals / font_id / f"original{path.suffix.lower()}"
                original_copy.parent.mkdir(parents=True, exist_ok=True)
                if not original_copy.exists() or original_copy.stat().st_size != path.stat().st_size:
                    shutil.copy2(path, original_copy)
                if not meta.exists():
                    meta.parent.mkdir(parents=True, exist_ok=True)
                    meta.write_text(json.dumps({"font_id": font_id, "display_name": path.stem, "source_filename": path.name, "source_sha256": digest, "source_format": item["format"], "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, ensure_ascii=False), encoding="utf-8")
            except Exception as error: self._log("warning", "读取预览字体失败: %s", error)
        return result

    def info(self, font_id: str, assets: dict[str, dict[str, Any]], config: dict[str, Any], url_for: Callable[[str, str, str], str]) -> dict[str, Any] | None:
        item = assets.get(font_id)
        if not item: return None
        chars = collect_characters(config)
        charset_hash = hashlib.sha256(chars.encode()).hexdigest()[:16]
        original_family = f"YahahaPreview_{font_id}_{item['sha']}"
        if not config.get("preview_font_enabled", True): return {"font_id": font_id, "font_family": original_family, "source_type": "disabled", "url": "", "format": "", "subset_status": "disabled", "charset_hash": charset_hash, "version": item["sha"]}
        if config.get("font_subset_enabled", True):
            manifest = self._manifest(item, charset_hash)
            subset = self._subset(item, charset_hash)
            if manifest.get("status") == "ready" and subset.is_file():
                return {"font_id": font_id, "font_family": f"YahahaPreview_{font_id}_{charset_hash}", "source_type": "subset", "url": url_for(font_id, "subset", charset_hash), "format": "woff2", "subset_status": "ready", "charset_hash": charset_hash, "version": charset_hash}
            self.schedule(item, chars, charset_hash)
            state = str(manifest.get("status") or "pending")
        else: state = "disabled"
        return {"font_id": font_id, "font_family": original_family, "source_type": "original", "url": url_for(font_id, "original", item["sha"]), "format": item["format"], "subset_status": state, "charset_hash": charset_hash, "version": item["sha"]}

    def file_for(self, font_id: str, variant: str, version: str, assets: dict[str, dict[str, Any]]):
        item = assets.get(font_id)
        if not item: return None
        path = self._subset(item, version) if variant == "subset" and len(version) >= 12 else item["path"]
        if not path.is_file(): path = item["path"]
        mime = "font/woff2" if path.suffix.lower() == ".woff2" else "font/otf" if path.suffix.lower() == ".otf" else "font/ttf"
        return path, mime, version

    def status(self, font_id: str, assets: dict[str, dict[str, Any]], config: dict[str, Any]):
        item = assets.get(font_id)
        if not item: return None
        charset_hash = hashlib.sha256(collect_characters(config).encode()).hexdigest()[:16]
        payload = self._manifest(item, charset_hash)
        return {"font_id": font_id, "charset_hash": charset_hash, "status": payload.get("status", "pending"), "size_bytes": payload.get("size_bytes", 0), "error": payload.get("error")}

    def schedule(self, item, chars, charset_hash, force=False):
        key = item["font_id"], charset_hash
        if not force and time.monotonic() - self.scheduled.get(key, 0) < 1.5: return
        self.scheduled[key] = time.monotonic()
        with self.guard: lock = self.locks.setdefault(key, threading.Lock())
        if not lock.locked(): self.executor.submit(self._build, item, chars, charset_hash, lock)

    def _build(self, item, chars, charset_hash, lock):
        with lock:
            self._write(item, charset_hash, {"status": "building", "character_count": len(chars), "error": None})
            try:
                from fontTools import subset
                from fontTools.ttLib import TTFont
                target = self._subset(item, charset_hash); target.parent.mkdir(parents=True, exist_ok=True)
                temp = target.with_suffix(".tmp")
                source_path = Path(item["path"])
                font_kwargs = {"fontNumber": 0} if source_path.suffix.lower() == ".ttc" else {}
                font = TTFont(str(source_path), recalcBBoxes=False, recalcTimestamp=False, **font_kwargs)
                opts = subset.Options(); opts.flavor = "woff2"; opts.recalc_timestamp = False
                worker = subset.Subsetter(options=opts); worker.populate(text=chars); worker.subset(font); font.flavor = "woff2"; font.save(str(temp)); os.replace(temp, target)
                self._write(item, charset_hash, {"status": "ready", "character_count": len(chars), "characters": chars, "woff2_file": target.name, "size_bytes": target.stat().st_size, "error": None})
            except Exception as error:
                self._write(item, charset_hash, {"status": "failed", "character_count": len(chars), "error": str(error)[:500]}); self._log("warning", "预览字体精简失败: %s", error)

    def _subset(self, item, charset_hash): return self.subsets / item["font_id"] / f"{charset_hash}.woff2"
    def _manifest_path(self, item, charset_hash): return self.subsets / item["font_id"] / f"{charset_hash}.manifest.json"
    def _manifest(self, item, charset_hash):
        try: return json.loads(self._manifest_path(item, charset_hash).read_text(encoding="utf-8"))
        except Exception: return {}
    def _write(self, item, charset_hash, data):
        path = self._manifest_path(item, charset_hash); path.parent.mkdir(parents=True, exist_ok=True); tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"schema_version": 1, "font_id": item["font_id"], "source_sha256": item["sha"], "charset_hash": charset_hash, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **data}, ensure_ascii=False), encoding="utf-8"); os.replace(tmp, path)
    def _log(self, level, message, *args):
        if self.logger and hasattr(self.logger, level): getattr(self.logger, level)(message, *args)
