from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image

from .time_utils import now_local

HISTORY_SCHEMA_VERSION = 1
HISTORY_ROOT_NAME = "history"
VALID_TRIGGERS = {"manual", "schedule", "monitor", "api"}
VALID_BATCH_STATUS = {"running", "success", "partial_success", "failed", "cancelled"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_time(value: datetime | None = None) -> str:
    return (value or utc_now()).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def batch_id() -> str:
    now = utc_now()
    return f"{now.strftime('%Y%m%dT%H%M%S')}.{now.microsecond // 1000:03d}Z_{secrets.token_hex(3)}"


def safe_id(value: Any, fallback: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        raw = fallback
    encoded = re.sub(r"[^A-Za-z0-9._-]+", "_", raw).strip("._") or fallback
    return encoded[:72] + "_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{secrets.token_hex(4)}.tmp")
    try:
        with temp.open("w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


@dataclass
class HistoryBatch:
    store: "HistoryStore"
    batch_id: str
    trigger: str
    mode: str
    directory: Path
    created_at: str = field(default_factory=iso_time)
    items: list[dict[str, Any]] = field(default_factory=list)

    @property
    def manifest_path(self) -> Path:
        return self.directory / "manifest.json"

    def write(self, status: str = "running") -> None:
        total = len(self.items)
        success = sum(1 for item in self.items if item.get("status") == "success")
        failed = sum(1 for item in self.items if item.get("status") == "failed")
        uploaded = sum(1 for item in self.items if item.get("upload_status") == "success")
        atomic_json(self.manifest_path, {
            "schema_version": HISTORY_SCHEMA_VERSION,
            "batch_id": self.batch_id,
            "created_at": self.created_at,
            "created_at_local": now_local().isoformat(timespec="seconds"),
            "trigger": self.trigger,
            "mode": self.mode,
            "app_version": self.store.app_version,
            "status": status,
            "summary": {"total": total, "success": success, "failed": failed, "uploaded": uploaded},
            "items": self.items,
        })

    def add_result(self, result: dict[str, Any], *, server_id: str, server_name: str, server_type: str, library_id: str, library_name: str) -> dict[str, Any]:
        source = Path(str(result.get("output") or ""))
        item: dict[str, Any] = {
            "server_id": safe_id(server_id, "local"),
            "server_name": server_name,
            "server_type": server_type,
            "library_id": safe_id(library_id, "library"),
            "library_name": library_name,
            "library_key": f"{safe_id(server_id, 'local')}:{safe_id(library_id, 'library')}",
            "template_id": str(result.get("style") or ""),
            "status": "failed",
            "upload_status": "success" if result.get("uploaded") else ("failed" if result.get("upload_error") else "skipped"),
            "file": None,
            "thumbnail": None,
            "mime_type": None,
            "width": None,
            "height": None,
            "size": 0,
            "sha256": None,
            "generated_at": iso_time(),
            "error": str(result.get("upload_error") or "") or None,
            "original_filename": source.name,
            "source_item_id": str(result.get("source_item_id") or "") or None,
        }
        if source.is_file():
            suffix = source.suffix.lower() if source.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"} else ".jpg"
            target_dir = self.directory / "servers" / item["server_id"] / "libraries" / item["library_id"]
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / f"cover{suffix}"
            shutil.copy2(source, target)
            item["file"] = str(target.relative_to(self.directory)).replace("\\", "/")
            item["size"] = target.stat().st_size
            item["sha256"] = sha256(target)
            item["mime_type"] = {".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}.get(suffix, "image/jpeg")
            try:
                with Image.open(target) as image:
                    item["width"], item["height"] = image.size
                    thumb = image.convert("RGB")
                    thumb.thumbnail((480, 270))
                    thumb_path = target_dir / "thumbnail.webp"
                    thumb.save(thumb_path, "WEBP", quality=82, method=4)
                    item["thumbnail"] = str(thumb_path.relative_to(self.directory)).replace("\\", "/")
            except Exception:
                pass
            item["status"] = "success"
        self.items.append(item)
        self.write()
        return item


class HistoryStore:
    def __init__(self, data_dir: Path, app_version: str = "2.2.9") -> None:
        self.root = data_dir / HISTORY_ROOT_NAME
        self.batches = self.root / "batches"
        self.tmp = self.root / ".tmp"
        self.index_path = self.root / "index.json"
        self.app_version = app_version
        self.batches.mkdir(parents=True, exist_ok=True)
        self.tmp.mkdir(parents=True, exist_ok=True)

    def create_history_batch(self, trigger: str, mode: str) -> HistoryBatch:
        value = batch_id()
        batch = HistoryBatch(self, value, trigger if trigger in VALID_TRIGGERS else "api", mode, self.tmp / value)
        batch.directory.mkdir(parents=True, exist_ok=False)
        batch.write("running")
        return batch

    def finalize_history_batch(self, batch: HistoryBatch, status: str = "success") -> dict[str, Any]:
        if status not in VALID_BATCH_STATUS:
            status = "failed"
        if status == "success" and any(item.get("status") == "failed" for item in batch.items):
            status = "partial_success" if any(item.get("status") == "success" for item in batch.items) else "failed"
        batch.write(status)
        final = self.batches / batch.batch_id
        if final.exists():
            raise FileExistsError(batch.batch_id)
        batch.directory.replace(final)
        self.rebuild_history_index()
        return self.get_history_batch(batch.batch_id) or {}

    def list_history_batches(self, page: int = 1, page_size: int = 50, **filters: str) -> dict[str, Any]:
        index = self._read_index().get("batches", [])
        values = [item for item in index if all(not filters.get(key) or str(item.get(key)) == str(filters[key]) for key in ("trigger", "status"))]
        start = max(0, (max(1, page) - 1) * max(1, min(page_size, 100)))
        return {"total": len(values), "items": values[start:start + max(1, min(page_size, 100))]}

    def stats(self) -> dict[str, int]:
        batches = self._read_index().get("batches", [])
        if not isinstance(batches, list):
            batches = []
        return {
            "history_cover_count": sum(max(0, int(item.get("item_count") or 0)) for item in batches if isinstance(item, dict)),
            "execution_count": len(batches),
        }

    def get_history_batch(self, value: str) -> dict[str, Any] | None:
        if not re.fullmatch(r"[A-Za-z0-9._-]+", str(value or "")):
            return None
        path = self.batches / value / "manifest.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except Exception:
            return None

    def safe_file(self, batch_id_value: str, relative: str) -> Path | None:
        manifest = self.get_history_batch(batch_id_value)
        if not manifest or relative not in {item.get("file") for item in manifest.get("items", [])} | {item.get("thumbnail") for item in manifest.get("items", [])}:
            return None
        path = (self.batches / batch_id_value / relative).resolve()
        try:
            path.relative_to((self.batches / batch_id_value).resolve())
        except ValueError:
            return None
        return path if path.is_file() else None

    def rebuild_history_index(self) -> dict[str, Any]:
        batches: list[dict[str, Any]] = []
        for directory in self.batches.iterdir():
            manifest = self.get_history_batch(directory.name) if directory.is_dir() else None
            if not manifest:
                continue
            summary = manifest.get("summary") or {}
            batches.append({"batch_id": manifest.get("batch_id"), "created_at": manifest.get("created_at"), "trigger": manifest.get("trigger"), "status": manifest.get("status"), "item_count": summary.get("total", 0), "success_count": summary.get("success", 0), "failed_count": summary.get("failed", 0)})
        batches.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        index = {"schema_version": HISTORY_SCHEMA_VERSION, "batches": batches}
        atomic_json(self.index_path, index)
        return index

    def cleanup_history(self, retention: int) -> int:
        retention = max(1, min(1000, int(retention or 30)))
        batches = [(directory, self.get_history_batch(directory.name)) for directory in self.batches.iterdir() if directory.is_dir()]
        batches = [row for row in batches if row[1]]
        batches.sort(key=lambda row: str(row[1].get("created_at") or ""), reverse=True)
        removed = 0
        for directory, _manifest in batches[retention:]:
            shutil.rmtree(directory, ignore_errors=True)
            removed += 1
        self.rebuild_history_index()
        return removed

    def latest_source_item_id(self, server_id: str, library_id: str) -> str:
        """Return the latest successfully rendered source media ID for a library."""
        expected_server = safe_id(server_id, "local")
        expected_library = safe_id(library_id, "library")
        manifests: list[dict[str, Any]] = []
        for directory in self.batches.iterdir():
            if directory.is_dir():
                manifest = self.get_history_batch(directory.name)
                if manifest:
                    manifests.append(manifest)
        manifests.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        for manifest in manifests:
            for item in manifest.get("items") or []:
                if (
                    str(item.get("server_id") or "") == expected_server
                    and str(item.get("library_id") or "") == expected_library
                    and item.get("status") == "success"
                    and str(item.get("upload_status") or "") in {"success", "skipped"}
                    and str(item.get("source_item_id") or "").strip()
                ):
                    return str(item["source_item_id"])
        return ""

    def migrate_legacy(self, legacy_output: Path) -> int:
        """Import the old flat output folder once without altering its files."""
        marker = self.root / ".migration_v1_complete"
        if marker.exists() or not legacy_output.exists():
            return 0
        imported = 0
        for source in sorted(legacy_output.glob("*.*"), key=lambda path: path.stat().st_mtime):
            if source.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                continue
            stem = source.stem.rsplit("_", 1)[0] or source.stem
            batch = self.create_history_batch("api", "legacy")
            result = {"output": str(source), "style": "legacy", "uploaded": False}
            batch.add_result(result, server_id="legacy", server_name="Legacy", server_type="legacy", library_id=stem, library_name=stem)
            self.finalize_history_batch(batch, "success")
            imported += 1
        marker.write_text(iso_time(), encoding="utf-8")
        return imported

    def _read_index(self) -> dict[str, Any]:
        try:
            value = json.loads(self.index_path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) and isinstance(value.get("batches"), list) else self.rebuild_history_index()
        except Exception:
            return self.rebuild_history_index()
