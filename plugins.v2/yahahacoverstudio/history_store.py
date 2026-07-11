"""Schema v1 history batches shared with the Yahaha Docker application."""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _safe(value: Any, fallback: str) -> str:
    raw = str(value or fallback)
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", raw).strip("._") or fallback
    return f"{name[:72]}_{hashlib.sha256(raw.encode()).hexdigest()[:10]}"


def _write(path: Path, value: dict[str, Any]) -> None:
    temp = path.with_name(f".{path.name}.{secrets.token_hex(3)}.tmp")
    with temp.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)


class HistoryStore:
    def __init__(self, data_dir: Path, version: str = "2.0.0"):
        self.root = data_dir / "history"
        self.tmp = self.root / ".tmp"
        self.batches = self.root / "batches"
        self.index = self.root / "index.json"
        self.version = version
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.batches.mkdir(parents=True, exist_ok=True)

    def create(self, trigger: str, mode: str) -> dict[str, Any]:
        stamp = datetime.now(timezone.utc)
        batch_id = f"{stamp.strftime('%Y%m%dT%H%M%S')}.{stamp.microsecond // 1000:03d}Z_{secrets.token_hex(3)}"
        directory = self.tmp / batch_id
        directory.mkdir()
        batch = {"schema_version": 1, "batch_id": batch_id, "created_at": _now(), "trigger": trigger if trigger in {"manual", "schedule", "monitor", "api"} else "api", "mode": mode, "app_version": self.version, "status": "running", "summary": {"total": 0, "success": 0, "failed": 0, "uploaded": 0}, "items": [], "_directory": directory}
        self._save(batch)
        return batch

    def add_bytes(self, batch: dict[str, Any], content: bytes, server_id: str, server_name: str, library_id: str, library_name: str, template_id: str, extension: str, uploaded: bool) -> None:
        server_key, library_key = _safe(server_id, "local"), _safe(library_id, "library")
        directory = batch["_directory"] / "servers" / server_key / "libraries" / library_key
        directory.mkdir(parents=True, exist_ok=True)
        ext = re.sub(r"[^a-z0-9]", "", extension.lower()) or "jpg"
        file = directory / f"cover.{ext}"
        file.write_bytes(content)
        digest = hashlib.sha256(content).hexdigest()
        item = {"server_id": server_key, "server_name": server_name, "server_type": "media_server", "library_id": library_key, "library_name": library_name, "library_key": f"{server_key}:{library_key}", "template_id": template_id, "status": "success", "upload_status": "success" if uploaded else "failed", "file": str(file.relative_to(batch["_directory"])), "thumbnail": None, "mime_type": f"image/{'jpeg' if ext == 'jpg' else ext}", "width": None, "height": None, "size": len(content), "sha256": digest, "generated_at": _now(), "error": None}
        batch["items"].append(item)
        self._save(batch)

    def finalize(self, batch: dict[str, Any], status: str = "success") -> None:
        batch["status"] = status
        self._save(batch)
        final = self.batches / batch["batch_id"]
        Path(batch["_directory"]).replace(final)
        self.rebuild_index()

    def _save(self, batch: dict[str, Any]) -> None:
        items = batch["items"]
        batch["summary"] = {"total": len(items), "success": sum(item["status"] == "success" for item in items), "failed": sum(item["status"] == "failed" for item in items), "uploaded": sum(item["upload_status"] == "success" for item in items)}
        payload = {key: value for key, value in batch.items() if key != "_directory"}
        _write(Path(batch["_directory"]) / "manifest.json", payload)

    def rebuild_index(self) -> None:
        records = []
        for directory in self.batches.iterdir():
            try:
                manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
                records.append({"batch_id": manifest["batch_id"], "created_at": manifest["created_at"], "trigger": manifest["trigger"], "status": manifest["status"], "item_count": manifest["summary"]["total"], "success_count": manifest["summary"]["success"], "failed_count": manifest["summary"]["failed"]})
            except Exception:
                continue
        _write(self.index, {"schema_version": 1, "batches": sorted(records, key=lambda item: item["created_at"], reverse=True)})
