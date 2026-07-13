from __future__ import annotations

import asyncio
import base64
from email import policy
from email.parser import BytesParser
import io
import json
import mimetypes
import os
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any
from datetime import datetime, timezone
from urllib.parse import parse_qs, quote

import httpx
import yaml
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import DATA_DIR, ensure_data_dirs, load_config, resolve_data_path, save_config
from .mock import MOCK_LIBRARIES, ensure_mock_images, mock_library_by_name
from .media_client import configured_clients
from .services import library_title_payload, remove_history_item, slugify, title_for_library
from .time_utils import localize, now_local
from .services import CoverService
from .history_store import HistoryStore, sha256
from . import storage
from .run_logs import APP_LOGGER, RunLog, clean_expired_logs, iter_logs, safe_log_path


class GenerateRequest(BaseModel):
    library_name: str | None = None
    style: str | None = None


STYLE_TO_PLUGIN = {
    "single_1": ("static_1", "static"),
    "single_2": ("static_2", "static"),
    "multi_1": ("static_3", "static"),
    "static_1": ("static_1", "static"),
    "static_2": ("static_2", "static"),
    "static_3": ("static_3", "static"),
    "static_4": ("static_4", "static"),
    "custom_static": ("custom_static", "static"),
    "animated_1": ("static_1", "animated"),
    "animated_2": ("static_2", "animated"),
    "animated_3": ("static_3", "animated"),
    "animated_4": ("static_4", "animated"),
}

PLUGIN_TO_STYLE = {
    "static_1": "single_1",
    "static_2": "single_2",
    "static_3": "multi_1",
    "static_4": "static_4",
    "animated_1": "animated_1",
    "animated_2": "animated_2",
    "animated_3": "animated_3",
    "animated_4": "animated_4",
    "custom_static": "custom_static",
}

ANIMATED_SETTING_KEYS = (
    "animation_duration",
    "animation_fps",
    "animation_format",
    "animation_scroll",
    "animation_reduce_colors",
    "animated_2_image_count",
    "animated_2_departure_type",
    "main_title_font_preset",
    "subtitle_font_preset",
    "custom_text_font_preset",
    "main_title_font_size",
    "subtitle_font_size",
    "blur_size",
    "color_ratio",
    "title_scale",
)


def normalize_media_servers(config: dict[str, Any]) -> list[dict[str, Any]]:
    raw_servers = config.get("media_servers")
    servers: list[dict[str, Any]] = []
    if isinstance(raw_servers, list):
        for index, raw in enumerate(raw_servers):
            if not isinstance(raw, dict):
                continue
            kind = str(raw.get("type") or raw.get("kind") or "emby").lower()
            if kind not in {"emby", "jellyfin"}:
                kind = "emby"
            name = str(raw.get("name") or kind).strip() or kind
            url = str(raw.get("url") or raw.get("base_url") or "").strip()
            api_key = str(raw.get("api_key") or raw.get("apikey") or "").strip()
            servers.append({
                "id": str(raw.get("id") or f"{kind}-{index + 1}"),
                "name": name,
                "type": kind,
                "url": url,
                "api_key": api_key,
                "enabled": raw.get("enabled") is not False,
            })
    if not servers:
        if config.get("emby_url") or config.get("emby_api_key"):
            servers.append({
                "id": "emby",
                "name": "emby",
                "type": "emby",
                "url": str(config.get("emby_url") or ""),
                "api_key": str(config.get("emby_api_key") or ""),
                "enabled": True,
            })
        if (config.get("jellyfin_url") or config.get("jellyfin_api_key")) and not any(item.get("type") == "jellyfin" for item in servers):
            servers.append({
                "id": "jellyfin",
                "name": "jellyfin",
                "type": "jellyfin",
                "url": str(config.get("jellyfin_url") or ""),
                "api_key": str(config.get("jellyfin_api_key") or ""),
                "enabled": True,
            })
    return servers


app = FastAPI(title="Yahaha Cover Studio", version="2.0.5")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

service = CoverService()


class GenerationManager:
    def __init__(self, cover_service: CoverService) -> None:
        self.service = cover_service
        self.task: asyncio.Task | None = None
        self.is_generating = False
        self.stop_requested = False
        self.current = 0
        self.total = 0
        self.label = ""
        self.items: list[dict[str, Any]] = []
        self.error = ""
        self.run_log: RunLog | None = None

    def snapshot(self) -> dict[str, Any]:
        return {
            "is_generating": self.is_generating,
            "generation_current": self.current,
            "generation_total": self.total,
            "generation_label": self.label,
            "generation_error": self.error,
            "generation_items": self.items,
        }

    async def start(self, style: str = "", library_name: str | None = None, trigger: str = "manual") -> dict[str, Any]:
        if self.task and not self.task.done():
            return self.snapshot()
        self.is_generating = True
        self.stop_requested = False
        self.current = 0
        self.total = 0
        self.label = "准备生成"
        self.items = []
        self.error = ""
        self.run_log = RunLog(trigger)
        self.service.reload()
        batch = self.service.begin_history_batch(trigger)
        if batch:
            self.run_log.info("历史批次开始 batch_id=%s", batch.batch_id)
        self.run_log.info("任务开始 trigger=%s style=%s library=%s mode=%s", trigger, style or "default", library_name or "all", "local" if self.service.local_mode() else "server")
        self.task = asyncio.create_task(self._run(style, library_name))
        await asyncio.sleep(0)
        return self.snapshot()

    async def stop(self) -> dict[str, Any]:
        if self.task and not self.task.done():
            self.stop_requested = True
            self.label = "停止中"
            return self.snapshot()
        self.is_generating = False
        self.label = "已停止"
        return self.snapshot()

    async def _run(self, style: str = "", library_name: str | None = None) -> None:
        try:
            style_name = normalize_style(style)
            if library_name:
                self.total = 1
                self.label = f"正在生成 {library_name}"
                self.items.extend(await self.service.generate(library_name, style_name))
                self.run_log and self.run_log.info("媒体库完成 library=%s result=%s", library_name, self.items[-1] if self.items else {})
                self.current = 1
                self.label = "生成完成"
                return
            libraries = self.service.selected_generation_libraries(await self.service.libraries())
            if not libraries:
                self.total = 1
                self.label = "正在生成本地封面"
                self.items.extend(await self.service.generate(None, style_name))
                self.current = 1
                self.label = "生成完成"
                return
            self.total = len(libraries)
            for library in libraries:
                if self.stop_requested:
                    self.label = "已停止"
                    break
                library_name = str(library.get("name") or library.get("id") or "").strip()
                if not library_name:
                    self.current += 1
                    continue
                self.label = f"正在生成 {library_name}"
                self.items.extend(await self.service.generate(str(library.get("value") or library_name), style_name))
                self.run_log and self.run_log.info("媒体库完成 library=%s", library_name)
                self.current += 1
                await asyncio.sleep(0)
            if not self.stop_requested:
                self.label = "生成完成"
        except Exception as err:
            self.error = str(err)
            self.label = "生成失败"
            if self.run_log:
                self.run_log.exception("任务失败: %s", err)
        finally:
            try:
                manifest = self.service.finalize_history_batch("cancelled" if self.stop_requested else ("failed" if self.error else "success"))
                if manifest and self.run_log:
                    self.run_log.info("历史批次完成 batch_id=%s status=%s", manifest.get("batch_id"), manifest.get("status"))
            except Exception as history_error:
                APP_LOGGER.exception("历史批次归档失败: %s", history_error)
            if self.run_log:
                succeeded = sum(1 for item in self.items if not item.get("upload_error"))
                failed = sum(1 for item in self.items if item.get("upload_error"))
                self.run_log.info("任务结束 status=%s success=%s failed=%s skipped=%s", self.label, succeeded, failed, max(0, self.total - self.current))
                self.run_log.close()
                self.run_log = None
            try:
                clean_expired_logs(int(self.service.config.get("log_retention_days") or 7))
            except Exception as cleanup_error:
                APP_LOGGER.warning("任务后清理日志失败: %s", cleanup_error)
            self.is_generating = False
            self.stop_requested = False


generation_manager = GenerationManager(service)


class ScheduleManager:
    def __init__(self) -> None:
        self.task: asyncio.Task | None = None
        self.stop_event = asyncio.Event()
        self.last_generation_key = ""
        self.last_backup_key = ""
        self.last_error = ""
        self.last_backup = ""

    def start(self) -> None:
        if self.task and not self.task.done():
            return
        self.stop_event = asyncio.Event()
        self.task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self.stop_event.set()
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

    async def _loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                await self.tick()
            except Exception as err:
                self.last_error = str(err)
            try:
                await asyncio.wait_for(self.stop_event.wait(), timeout=20)
            except asyncio.TimeoutError:
                pass

    async def tick(self, now: datetime | None = None) -> dict[str, Any]:
        now = now or now_local(str(load_config().get("timezone") or "Asia/Shanghai"))
        key = now.strftime("%Y%m%d%H%M")
        config = load_config()
        actions: list[str] = []

        cron_expr = str(config.get("cron") or "").strip()
        if bool(config.get("enabled", True)) and cron_expr and cron_matches(cron_expr, now) and self.last_generation_key != key:
            self.last_generation_key = key
            style = str(config.get("style_config", {}).get("style") or "")
            await generation_manager.start(style, trigger="schedule")
            actions.append("generation")

        backup_expr = str(config.get("backup_cron") or "").strip()
        if backup_expr and cron_matches(backup_expr, now) and self.last_backup_key != key:
            self.last_backup_key = key
            path = create_config_backup(config, str(config.get("backup_path") or ""))
            self.last_backup = str(path)
            actions.append("backup")

        return {"actions": actions, "last_backup": self.last_backup, "last_error": self.last_error}

    def snapshot(self) -> dict[str, Any]:
        return {
            "scheduler_last_error": self.last_error,
            "scheduler_last_backup": self.last_backup,
        }


scheduler = ScheduleManager()


@app.on_event("startup")
async def startup_scheduler():
    try:
        clean_expired_logs(int(load_config().get("log_retention_days") or 7))
    except Exception as error:
        APP_LOGGER.warning("启动时清理日志失败: %s", error)
    scheduler.start()


@app.on_event("shutdown")
async def shutdown_scheduler():
    await scheduler.stop()

static_dir = Path(__file__).parent / "static"
ensure_data_dirs()
app.mount("/static", StaticFiles(directory=static_dir), name="static")
assets_dir = static_dir / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
icons_dir = static_dir / "icons"
if icons_dir.exists():
    app.mount("/icons", StaticFiles(directory=icons_dir), name="icons")
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")


@app.get("/")
async def index():
    return FileResponse(static_dir / "index.html")


@app.get("/favicon.ico")
async def favicon():
    icon = icons_dir / "favicon-32.png"
    if icon.exists():
        return FileResponse(icon, media_type="image/png")
    return Response(status_code=204)


@app.get("/manifest.webmanifest")
async def manifest():
    return FileResponse(static_dir / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/api/health")
async def health():
    config = load_config()
    clients = configured_clients(config)
    kinds = {client.kind for client in clients}
    return {
        "ok": True,
        "app": "Yahaha Cover Studio",
        "data_dir": str(DATA_DIR),
        "mock_enabled": bool(config.get("mock_enabled", True)),
        "has_emby": "emby" in kinds,
        "has_jellyfin": "jellyfin" in kinds,
        "media_servers": [client.server_name for client in clients],
        "local_mode": bool(config.get("local_mode", False)),
    }


@app.get("/api/config")
async def get_config():
    return service.reload()


@app.post("/api/config")
async def post_config(config: dict[str, Any]):
    try:
        return service.save(config)
    except Exception as error:
        APP_LOGGER.exception("配置保存失败: %s", error)
        raise HTTPException(status_code=500, detail=f"配置保存失败: {error}") from error


@app.get("/api/logs")
async def list_logs():
    items = []
    for path in iter_logs():
        stat = path.stat()
        items.append({"name": str(path.relative_to(DATA_DIR / "logs")), "size": stat.st_size, "modified": stat.st_mtime})
    return {"items": items}


@app.get("/api/logs/content/{name:path}")
async def read_log(name: str):
    path = safe_log_path(name)
    if not path:
        raise HTTPException(status_code=404, detail="日志不存在")
    return {"name": name, "content": path.read_text(encoding="utf-8", errors="replace")[-200_000:]}


@app.get("/api/logs/download/{name:path}")
async def download_log(name: str):
    path = safe_log_path(name)
    if not path:
        raise HTTPException(status_code=404, detail="日志不存在")
    return FileResponse(path, media_type="text/plain; charset=utf-8", filename=path.name)


@app.delete("/api/logs/{name:path}")
async def delete_log(name: str):
    path = safe_log_path(name)
    if not path:
        raise HTTPException(status_code=404, detail="日志不存在")
    path.unlink()
    return {"ok": True}


@app.post("/api/logs/cleanup")
async def cleanup_logs():
    return {"removed": clean_expired_logs(int(load_config().get("log_retention_days") or 7))}


@app.get("/api/libraries")
async def libraries():
    try:
        items = await service.libraries()
        remember_libraries(load_config(), items)
        return {"items": items}
    except Exception as err:
        APP_LOGGER.exception("读取媒体库失败: %s", err)
        raise HTTPException(status_code=500, detail=str(err)) from err


@app.get("/api/history/batches")
async def history_batches(page: int = 1, page_size: int = 50, trigger: str = "", status: str = ""):
    return HistoryStore(DATA_DIR).list_history_batches(page=page, page_size=page_size, trigger=trigger, status=status)


@app.get("/api/history/batches/{batch_id}")
async def history_batch(batch_id: str):
    manifest = HistoryStore(DATA_DIR).get_history_batch(batch_id)
    if not manifest:
        raise HTTPException(status_code=404, detail="历史批次不存在")
    return manifest


@app.post("/api/history/rebuild-index")
async def rebuild_history_index():
    return HistoryStore(DATA_DIR).rebuild_history_index()


@app.delete("/api/history/batches/{batch_id}")
async def delete_history_batch(batch_id: str):
    store = HistoryStore(DATA_DIR)
    manifest = store.get_history_batch(batch_id)
    if not manifest:
        raise HTTPException(status_code=404, detail="历史批次不存在")
    shutil.rmtree(store.batches / batch_id)
    store.rebuild_history_index()
    return {"ok": True}


@app.post("/api/generate")
async def generate(payload: GenerateRequest | None = None):
    payload = payload or GenerateRequest()
    try:
        service.reload()
        service.begin_history_batch("api")
        try:
            items = await service.generate(payload.library_name, payload.style)
            manifest = service.finalize_history_batch("success")
        except Exception:
            service.finalize_history_batch("failed")
            raise
        return {"items": items, "batch_id": (manifest or {}).get("batch_id")}
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err)) from err


@app.post("/api/generate/{library_name}")
async def generate_library(library_name: str, payload: GenerateRequest | None = None):
    try:
        return await generate(GenerateRequest(library_name=library_name, style=payload.style if payload else None))
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err)) from err


@app.post("/api/upload/{library_name}")
async def upload_library(library_name: str):
    try:
        return await service.upload(library_name)
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err)) from err


@app.post("/api/v1/webhook")
@app.post("/api/v1/webhook/")
@app.post("/api/webhook")
@app.post("/api/webhook/")
async def media_server_webhook(request: Request, token: str = Query(""), source: str = Query("")):
    config = load_config()
    expected_token = str(
        config.get("api_token")
        or os.environ.get("YAHAAHA_WEBHOOK_TOKEN")
        or os.environ.get("YAHAHA_WEBHOOK_TOKEN")
        or os.environ.get("API_TOKEN")
        or ""
    ).strip()
    if not token or token != expected_token:
        raise HTTPException(status_code=403, detail="invalid webhook token")
    source = str(source or "").strip()
    if not source:
        raise HTTPException(status_code=400, detail="source is required")
    if not webhook_source_known(config, source):
        return ok({
            "accepted": False,
            "reason": "unknown_source",
            "source": source,
            "allowed_sources": webhook_allowed_sources(config),
        })
    payload = await parse_webhook_request(request)
    if not isinstance(payload, dict):
        payload = {"payload": payload}

    event_name = webhook_first(payload, "Event", "event", "NotificationType")
    if event_name and not webhook_is_item_added_event(event_name):
        return ok({
            "accepted": False,
            "reason": "ignored_event",
            "event": event_name,
            "summary": webhook_summary(payload, source),
        })

    if not bool(config.get("enabled", True)):
        return ok({"accepted": False, "reason": "disabled"})
    if not bool(config.get("transfer_monitor", False)):
        return ok({"accepted": False, "reason": "monitor_disabled"})
    if str(config.get("monitor_source") or "webhook") not in {"webhook", "emby", "jellyfin"}:
        return ok({"accepted": False, "reason": "monitor_source_not_webhook"})

    library_name = await resolve_webhook_library_name(config, payload, source)
    if not library_name:
        return ok({
            "accepted": False,
            "reason": "library_not_found",
            "event": event_name,
            "summary": webhook_summary(payload, source),
        })

    delay_seconds = max(0, int(config.get("delay") or 0))
    style = str(config.get("style_config", {}).get("style") or "")
    if config.get("lock_latest_sort"):
        config["sort_by"] = "DateCreated"
        config.setdefault("style_config", {})["image_count_mode"] = "auto"
        save_config(config)
        service.reload()

    asyncio.create_task(delayed_generation_start(delay_seconds, style, library_name))
    return ok({
        "accepted": True,
        "library": library_name,
        "delay": delay_seconds,
        "event": event_name or "",
        "summary": webhook_summary(payload, source),
    })


@app.get("/api/webhook/example")
async def webhook_example():
    config = load_config()
    token = str(config.get("api_token") or "API_TOKEN")
    return {
        "endpoint": f"/api/webhook/?token={token}&source=媒体服务器名",
        "emby": {
            "event": "媒体库 -> 新媒体已添加",
            "url": f"http://你的Docker宿主机:8899/api/webhook/?token={token}&source=emby",
            "payload": {
                "Event": "library.new",
                "ServerName": "{{ServerName}}",
                "Item": {
                    "Id": "{{ItemId}}",
                    "Name": "{{Name}}",
                    "LibraryId": "{{LibraryId}}",
                    "LibraryName": "{{LibraryName}}",
                    "Path": "{{Path}}",
                },
            },
        },
        "jellyfin": {
            "event": "Item Added / Item Created",
            "url": f"http://你的Docker宿主机:8899/api/webhook/?token={token}&source=jellyfin",
            "payload": {
                "NotificationType": "ItemAdded",
                "ServerName": "{{ServerName}}",
                "ItemId": "{{ItemId}}",
                "ItemName": "{{Name}}",
                "LibraryId": "{{LibraryId}}",
                "LibraryName": "{{LibraryName}}",
                "Path": "{{Path}}",
            },
        },
    }


@app.get("/api/plugin/MediaCoverGenerator/config")
async def plugin_config():
    return ok({"config": to_plugin_config(load_config())})


@app.get("/api/plugin/MediaCoverGenerator/status")
async def plugin_status():
    payload = to_status_payload(load_config())
    payload.update(generation_manager.snapshot())
    payload.update(scheduler.snapshot())
    return ok(payload)


@app.get("/api/plugin/MediaCoverGenerator/libraries")
async def plugin_libraries(servers: str = ""):
    previous = service.config.get("selected_servers")
    if servers.strip():
        service.config["selected_servers"] = [item for item in servers.split(",") if item.strip()]
    try:
        return ok(await service.libraries())
    finally:
        service.config["selected_servers"] = previous


@app.get("/api/plugin/MediaCoverGenerator/history")
async def plugin_history():
    store = HistoryStore(DATA_DIR)
    items = []
    for summary in store.list_history_batches(page_size=1000).get("items", []):
        manifest = store.get_history_batch(str(summary.get("batch_id") or "")) or {}
        for item in manifest.get("items") or []:
            relative = str(item.get("file") or "")
            path = store.safe_file(str(manifest.get("batch_id") or ""), relative)
            if not path:
                continue
            created_dt = localize(str(manifest.get("created_at") or ""), str(load_config().get("timezone") or "Asia/Shanghai"))
            url = f"/data/history/batches/{manifest['batch_id']}/{relative}"
            thumbnail = str(item.get("thumbnail") or "")
            thumbnail_path = store.safe_file(str(manifest.get("batch_id") or ""), thumbnail) if thumbnail else None
            thumbnail_url = f"/data/history/batches/{manifest['batch_id']}/{thumbnail}" if thumbnail_path else url
            items.append({"path": str(path), "name": path.name, "library": item.get("library_name"), "server": item.get("server_name"), "style": item.get("template_id"), "created_at": created_dt.timestamp(), "created_label": created_dt.strftime("%Y-%m-%d %H:%M"), "date": created_dt.strftime("%Y-%m-%d"), "date_label": created_dt.strftime("%m-%d %H:%M"), "size": item.get("size", 0), "uploaded": item.get("upload_status") == "success", "upload_error": item.get("error") or "", "url": url, "src": thumbnail_url, "thumbnail": thumbnail_url, "batch_id": manifest.get("batch_id")})
    return ok(items)


@app.post("/api/plugin/MediaCoverGenerator/restore_history_batch")
async def plugin_restore_history_batch(payload: dict[str, Any] | None = None):
    batch_id = str((payload or {}).get("batch_id") or "").strip()
    store = HistoryStore(DATA_DIR, app_version=app.version)
    manifest = store.get_history_batch(batch_id)
    if not manifest:
        return {"code": 1, "msg": "历史批次不存在"}
    restored = skipped = failed = 0
    clients = service.clients()
    library_cache: dict[str, list[Any]] = {}
    for item in manifest.get("items") or []:
        server_name = str(item.get("server_name") or "")
        library_name = str(item.get("library_name") or "")
        path = store.safe_file(batch_id, str(item.get("file") or ""))
        client = next((value for value in clients if value.server_name == server_name), None)
        expected_hash = str(item.get("sha256") or "")
        if not client or not path:
            skipped += 1
            continue
        if expected_hash and sha256(path) != expected_hash:
            APP_LOGGER.warning("跳过校验失败的历史封面 server=%s library=%s", server_name, library_name)
            skipped += 1
            continue
        try:
            if client.server_id not in library_cache:
                library_cache[client.server_id] = await client.get_libraries()
            library = next((value for value in library_cache[client.server_id] if value.name == library_name), None)
            if not library:
                skipped += 1
                continue
            await client.upload_library_cover(library.id, path)
            restored += 1
        except Exception as error:
            APP_LOGGER.warning("恢复历史封面失败 server=%s library=%s: %s", server_name, library_name, error)
            failed += 1
    return ok({"batch_id": batch_id, "restored": restored, "skipped": skipped, "failed": failed})


@app.get("/api/plugin/MediaCoverGenerator/preview_sources")
async def plugin_preview_sources(required_items: int = Query(9), force_refresh: bool = Query(False)):
    config = load_config()
    library = await first_library_name(config)
    source = await ensure_preview_images(config, library, required_items, force_refresh=force_refresh)
    return ok(source)


@app.post("/api/plugin/MediaCoverGenerator/preview")
async def plugin_preview(payload: dict[str, Any] | None = None):
    payload = payload or {}
    config = load_config()
    style = normalize_style(payload.get("style") or config.get("style_config", {}).get("style"))
    library_name = str(payload.get("library") or "") or await first_library_name(config)
    cached = cached_preview_payload(config, library_name, style)
    if cached:
        return ok(cached)
    generated = await service.generate(library_name, style)
    item = generated[0] if generated else {}
    return ok({
        "src": item.get("url", ""),
        "server": item.get("server", "docker"),
        "library": item.get("library", ""),
        "style": style,
    })


@app.post("/api/plugin/MediaCoverGenerator/start_generation")
async def plugin_start_generation(style: str = Query("")):
    return ok(await generation_manager.start(style))


@app.post("/api/plugin/MediaCoverGenerator/generate_now")
async def plugin_generate_now(style: str = Query("")):
    return ok(await generation_manager.start(style))


@app.post("/api/plugin/MediaCoverGenerator/stop_generation")
async def plugin_stop_generation():
    return ok(await generation_manager.stop())


@app.post("/api/plugin/MediaCoverGenerator/set_cover_style")
async def plugin_set_cover_style(style: str = Query("")):
    config = load_config()
    config.setdefault("style_config", {})["style"] = normalize_style(style)
    save_config(config)
    service.reload()
    return ok({"style": style})


@app.post("/api/plugin/MediaCoverGenerator/select_style_1")
async def plugin_select_style_1():
    return set_style_by_index(1)


@app.post("/api/plugin/MediaCoverGenerator/select_style_2")
async def plugin_select_style_2():
    return set_style_by_index(2)


@app.post("/api/plugin/MediaCoverGenerator/select_style_3")
async def plugin_select_style_3():
    return set_style_by_index(3)


@app.post("/api/plugin/MediaCoverGenerator/select_style_4")
async def plugin_select_style_4():
    return set_style_by_index(4)


@app.post("/api/plugin/MediaCoverGenerator/set_page_tab_generate")
async def plugin_set_page_tab_generate():
    return set_page_tab("generate-tab")


@app.post("/api/plugin/MediaCoverGenerator/set_page_tab_custom")
async def plugin_set_page_tab_custom():
    return set_page_tab("custom-tab")


@app.post("/api/plugin/MediaCoverGenerator/set_page_tab_history")
async def plugin_set_page_tab_history():
    return set_page_tab("history-tab")


@app.post("/api/plugin/MediaCoverGenerator/set_page_tab_clean")
async def plugin_set_page_tab_clean():
    return set_page_tab("clean-tab")


@app.post("/api/plugin/MediaCoverGenerator/toggle_style_variant")
async def plugin_toggle_style_variant():
    return ok({"variant": "static"})


@app.post("/api/plugin/MediaCoverGenerator/set_render_options")
async def plugin_set_render_options(payload: dict[str, Any] | None = None):
    config = load_config()
    payload = payload or {}
    style_config = config.setdefault("style_config", {})
    if "sort_by" in payload and payload["sort_by"] not in (None, ""):
        config["sort_by"] = payload["sort_by"]
    if "lock_latest_sort" in payload:
        config["lock_latest_sort"] = bool(payload["lock_latest_sort"])
    for source_key, target_key in {
        "poster_source": "image_source",
        "resolution": "resolution",
        "image_count_mode": "image_count_mode",
        "image_count": "image_limit",
        "blur_size": "blur",
        "color_ratio": "color_ratio",
        "output_format": "output_format",
    }.items():
        if source_key in payload and payload[source_key] not in (None, ""):
            style_config[target_key] = payload[source_key]
    if payload.get("use_primary") is True:
        style_config["image_source"] = "poster"
    save_config(config)
    service.reload()
    return ok(to_status_payload(config))


@app.post("/api/plugin/MediaCoverGenerator/set_animated_settings")
async def plugin_set_animated_settings(payload: dict[str, Any] | None = None):
    config = load_config()
    payload = payload or {}
    style_key = str(payload.get("style") or "animated_1")
    if style_key not in {"animated_1", "animated_2", "animated_3", "animated_4"}:
        style_key = "animated_1"
    animated_settings = dict(config.get("animated_settings") or {})
    current = dict(animated_settings.get(style_key) or {})
    for key in ANIMATED_SETTING_KEYS:
        if key in payload and payload[key] not in (None, ""):
            current[key] = normalize_animated_setting_value(key, payload[key])
    animated_settings[style_key] = current
    config["animated_settings"] = animated_settings
    save_config(config)
    service.reload()
    return ok({**to_status_payload(config), **current, "style": style_key})


@app.post("/api/plugin/MediaCoverGenerator/set_custom_static_layout")
async def plugin_set_custom_static_layout(payload: dict[str, Any] | None = None):
    config = load_config()
    payload = payload or {}
    if "layout" in payload:
        config["custom_static_layout"] = payload["layout"]
    if "templates" in payload:
        config["custom_static_layouts"] = payload["templates"]
    if "active_id" in payload:
        config["custom_static_active_id"] = payload["active_id"]
    save_config(config)
    service.reload()
    plugin_config = to_plugin_config(config)
    return ok({
        "config": plugin_config,
        "custom_static_layout": plugin_config.get("custom_static_layout"),
        "custom_static_layouts": plugin_config.get("custom_static_layouts"),
        "custom_static_active_id": plugin_config.get("custom_static_active_id"),
    })


@app.post("/api/plugin/MediaCoverGenerator/measure_custom_static_layout")
async def plugin_measure_custom_static_layout(payload: dict[str, Any] | None = None):
    layout = (payload or {}).get("layout") or {}
    return ok(layout)


@app.get("/api/v1/user/current")
@app.get("/api/v1/user/info")
@app.get("/api/v1/user")
@app.get("/api/v1/auth/user")
@app.get("/api/v1/users/current")
async def docker_current_user():
    return {
        "code": 0,
        "data": {
            "name": "Yahaha Cover Studio",
            "nickname": "Yahaha Cover Studio",
            "avatar": default_avatar_data_url(),
            "avatarUrl": default_avatar_data_url(),
        },
    }


@app.get("/api/plugin/MediaCoverGenerator/fonts")
async def plugin_fonts():
    fonts_dir = DATA_DIR / "fonts"
    items = [
        storage.font_item(path)
        for path in sorted(fonts_dir.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True)
        if path.is_file() and path.suffix.lower() in storage.FONT_EXTENSIONS
    ]
    return ok({"custom": items})


@app.get("/api/plugin/MediaCoverGenerator/stickers")
async def plugin_stickers():
    stickers_dir = DATA_DIR / "stickers"
    items = [
        storage.sticker_item(path)
        for path in sorted(stickers_dir.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True)
        if path.is_file() and path.suffix.lower() in storage.IMAGE_EXTENSIONS
    ]
    return ok(items)


@app.get("/api/plugin/MediaCoverGenerator/backups")
async def plugin_backups():
    backups_dir = DATA_DIR / "backups"
    items = [
        storage.backup_item(path)
        for path in sorted(backups_dir.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True)
        if path.is_file() and path.suffix.lower() in storage.BACKUP_EXTENSIONS
    ]
    return ok(items)


@app.post("/api/plugin/MediaCoverGenerator/save_config")
async def plugin_save_config(payload: dict[str, Any]):
    incoming = dict(payload.get("config") or payload or {})
    config = from_plugin_config(incoming, load_config())
    save_config(config)
    service.reload()
    return ok({"config": to_plugin_config(config)})


@app.post("/api/plugin/MediaCoverGenerator/validate_title_config")
async def plugin_validate_title_config(payload: dict[str, Any] | None = None):
    payload = payload or {}
    raw = str(payload.get("title_config") or payload.get("yaml") or payload.get("content") or "")
    strict = parse_bool(payload.get("strict", payload.get("title_config_strict", False)))
    parsed, errors, processed_yaml = parse_title_config(raw, strict=strict)
    return {
        "code": 0 if not errors else 1,
        "msg": "标题配置有效" if not errors else errors[0],
        "data": {
            "valid": not errors,
            "errors": errors,
            "parsed": parsed,
            "processed_yaml": processed_yaml,
            "strict": strict,
        },
    }


@app.post("/api/plugin/MediaCoverGenerator/title_config_template")
async def plugin_title_config_template(payload: dict[str, Any] | None = None):
    payload = payload or {}
    raw = str(payload.get("title_config") or payload.get("yaml") or payload.get("content") or "")
    strict = parse_bool(payload.get("strict", payload.get("title_config_strict", False)))
    distinguish_same_name = parse_bool(payload.get("distinguish_same_name_libraries", False))
    current, errors, processed_yaml = parse_title_config(raw, strict=strict)
    if errors:
        return {
            "code": 1,
            "msg": errors[0],
            "data": {"valid": False, "errors": errors, "processed_yaml": processed_yaml},
        }
    existing_keys = {normalize_template_key(key) for key in current.keys() if normalize_template_key(key)}
    existing_keys.update(collect_raw_top_level_keys(raw))
    generated_keys: set[str] = set()
    missing = []
    blocks = []
    libraries = await service.libraries()
    if not libraries:
        libraries = list(load_config().get("all_libraries") or [])
    for item in libraries:
        name = item.get("name") or ""
        server_name = str(item.get("server_name") or item.get("server") or "").strip()
        template_name = f"{server_name}_{name}" if distinguish_same_name and server_name else name
        normalized_template_name = normalize_template_key(template_name)
        if template_name and normalized_template_name not in existing_keys and normalized_template_name not in generated_keys:
            generated_keys.add(normalized_template_name)
            missing.append(template_name)
            blocks.append("\n".join([
                f"{template_name}:",
                f"  title: {quote_yaml_value(name)}",
                "  subtitle: \"副标题\"",
                "  background: \"#5f7185\"",
                "  texts:",
                "    slogan: \"自定义文本\"",
                "    note: \"备注文本\"",
                "    any_key: \"任意自定义文本\"",
            ]))
    reference = "\n".join([
        "媒体库名称:",
        "  title: \"主标题\"",
        "  subtitle: \"副标题\"",
        "  background: \"#5f7185\"",
        "  texts:",
        "    slogan: \"自定义文本\"",
        "    note: \"备注文本\"",
        "    any_key: \"任意自定义文本\"",
        "",
        "# texts 下的 slogan / note / any_key 都不是固定变量名，可以随意命名。",
        "# 在画布编辑的文字图层中选择「按媒体库配置」，并在「配置文本键」填写同名键即可。",
    ])
    return ok({
        "valid": True,
        "libraries": [str(item.get("name") or "") for item in libraries],
        "existing": sorted(existing_keys),
        "missing": missing,
        "yaml": "\n\n".join(blocks),
        "reference": reference,
        "processed_yaml": processed_yaml,
    })


@app.post("/api/plugin/MediaCoverGenerator/clean_images")
async def plugin_clean_images():
    config = load_config()
    removed = 0
    skipped: list[str] = []
    output_dir = resolve_cleanable_data_dir(config.get("covers_output") or "/app/data/output")
    if output_dir:
        removed += clean_directory_contents(output_dir)
    else:
        skipped.append("covers_output")
    input_dir = resolve_cleanable_data_dir(config.get("covers_input") or "/app/data/input")
    if input_dir and input_dir.resolve() == (DATA_DIR / "input").resolve():
        removed += clean_directory_contents(input_dir)
    elif input_dir:
        skipped.append("covers_input_custom")
    return ok({"cleaned": True, "removed": removed, "skipped": skipped})


@app.post("/api/plugin/MediaCoverGenerator/clean_fonts")
async def plugin_clean_fonts():
    fonts_dir = resolve_cleanable_data_dir(DATA_DIR / "fonts")
    removed = clean_directory_contents(fonts_dir) if fonts_dir else 0
    config = load_config()
    for key in ("main_title_font_custom", "subtitle_font_custom", "custom_text_font_custom"):
        config[key] = ""
    save_config(config)
    service.reload()
    return ok({"cleaned": True, "removed": removed})


@app.post("/api/plugin/MediaCoverGenerator/backup_config")
async def plugin_backup_config(payload: dict[str, Any] | None = None):
    payload = payload or {}
    config = load_config()
    path = create_config_backup(config, str(payload.get("backup_path") or config.get("backup_path") or ""))
    return ok(storage.backup_item(path))


@app.post("/api/plugin/MediaCoverGenerator/upload_backup")
async def plugin_upload_backup(payload: dict[str, Any] | None = None):
    payload = payload or {}
    name = storage.safe_filename(str(payload.get("name") or "backup.json"), "backup.json")
    if Path(name).suffix.lower() not in storage.BACKUP_EXTENSIONS:
        name = f"{Path(name).stem}.json"
    try:
        _, bytes_data = storage.decode_data_url(str(payload.get("data_url") or ""))
    except Exception as err:
        return {"code": 1, "msg": f"备份数据无效: {err}", "data": None}
    path = storage.unique_path(DATA_DIR / "backups", name)
    path.write_bytes(bytes_data)
    try:
        storage.read_backup_config(path)
    except Exception as err:
        path.unlink(missing_ok=True)
        return {"code": 1, "msg": f"备份文件格式不正确: {err}", "data": None}
    return ok(storage.backup_item(path))


@app.post("/api/plugin/MediaCoverGenerator/restore_backup")
async def plugin_restore_backup(file: str = Query("")):
    path = asset_path(DATA_DIR / "backups", file)
    if not path or not path.exists():
        return {"code": 1, "msg": "备份文件不存在", "data": None}
    try:
        saved = save_config(storage.read_backup_config(path))
        service.reload()
        return ok({"file": str(path), "config": to_plugin_config(saved)})
    except Exception as err:
        return {"code": 1, "msg": f"恢复备份失败: {err}", "data": None}


@app.post("/api/plugin/MediaCoverGenerator/delete_backup")
@app.get("/api/plugin/MediaCoverGenerator/delete_backup")
@app.delete("/api/plugin/MediaCoverGenerator/delete_backup")
async def plugin_delete_backup(file: str = Query("")):
    path = asset_path(DATA_DIR / "backups", file)
    if path and path.exists() and path.is_file():
        path.unlink()
        return ok({"file": file, "deleted": True})
    return ok({"file": file, "deleted": False})


@app.post("/api/plugin/MediaCoverGenerator/download_backup")
async def plugin_download_backup(file: str = Query("")):
    path = asset_path(DATA_DIR / "backups", file) or (DATA_DIR / "config.yaml")
    if not path.exists():
        return {"code": 1, "msg": "备份文件不存在", "data": None}
    return ok(storage.encode_file_payload(path))


@app.post("/api/plugin/MediaCoverGenerator/upload_font")
async def plugin_upload_font(payload: dict[str, Any] | None = None):
    payload = payload or {}
    try:
        if payload.get("chunk_data"):
            item = save_chunked_upload(payload, DATA_DIR / "fonts", storage.FONT_EXTENSIONS, "font")
            return ok(item if item else {"done": False})
        if payload.get("url"):
            filename = storage.safe_filename(str(payload.get("name") or str(payload["url"]).split("/")[-1] or "font.ttf"), "font.ttf")
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                response = await client.get(str(payload["url"]))
                response.raise_for_status()
                bytes_data = response.content
        elif payload.get("data_url"):
            filename = storage.safe_filename(str(payload.get("name") or "font.ttf"), "font.ttf")
            _, bytes_data = storage.decode_data_url(str(payload["data_url"]))
        else:
            return {"code": 1, "msg": "字体数据为空", "data": None}
        return ok(save_binary_asset(DATA_DIR / "fonts", filename, bytes_data, storage.FONT_EXTENSIONS, "font"))
    except Exception as err:
        return {"code": 1, "msg": f"字体上传失败: {err}", "data": None}


@app.post("/api/plugin/MediaCoverGenerator/rename_font")
async def plugin_rename_font(payload: dict[str, Any] | None = None):
    payload = payload or {}
    path = asset_path(DATA_DIR / "fonts", str(payload.get("value") or payload.get("path") or payload.get("name") or ""))
    next_name = storage.safe_filename(str(payload.get("new_name") or ""), "")
    if not path or not path.exists():
        return {"code": 1, "msg": "字体文件不存在", "data": None}
    if not next_name:
        return {"code": 1, "msg": "新字体名称不能为空", "data": None}
    target = storage.unique_path(DATA_DIR / "fonts", f"{Path(next_name).stem}{path.suffix}")
    path.rename(target)
    return ok(storage.font_item(target, title=Path(next_name).stem))


@app.post("/api/plugin/MediaCoverGenerator/delete_font")
@app.get("/api/plugin/MediaCoverGenerator/delete_font")
@app.delete("/api/plugin/MediaCoverGenerator/delete_font")
async def plugin_delete_font(file: str = Query("")):
    path = asset_path(DATA_DIR / "fonts", file)
    if path and path.exists() and path.is_file():
        path.unlink()
        return ok({"file": file, "deleted": True})
    return ok({"file": file, "deleted": False})


@app.post("/api/plugin/MediaCoverGenerator/upload_sticker")
async def plugin_upload_sticker(payload: dict[str, Any] | None = None):
    payload = payload or {}
    try:
        filename = storage.safe_filename(str(payload.get("name") or "sticker.png"), "sticker.png")
        _, bytes_data = storage.decode_data_url(str(payload.get("data_url") or ""))
        item = save_binary_asset(DATA_DIR / "stickers", filename, bytes_data, storage.IMAGE_EXTENSIONS, "sticker")
        sticker = storage.sticker_item(Path(item["path"]))
        return ok({
            "stickerDataUrl": "",
            "stickerPath": sticker["path"],
            "stickerUrl": sticker["url"],
            "stickerName": sticker["name"],
            "stickerWidth": sticker["width"],
            "stickerHeight": sticker["height"],
        })
    except Exception as err:
        return {"code": 1, "msg": f"贴图上传失败: {err}", "data": None}


@app.post("/api/plugin/MediaCoverGenerator/delete_sticker")
@app.get("/api/plugin/MediaCoverGenerator/delete_sticker")
@app.delete("/api/plugin/MediaCoverGenerator/delete_sticker")
async def plugin_delete_sticker(file: str = Query("")):
    path = asset_path(DATA_DIR / "stickers", file)
    if path and path.exists() and path.is_file():
        path.unlink()
        return ok({"file": file, "deleted": True})
    return ok({"file": file, "deleted": False})


@app.post("/api/plugin/MediaCoverGenerator/delete_custom_static_template")
@app.get("/api/plugin/MediaCoverGenerator/delete_custom_static_template")
@app.delete("/api/plugin/MediaCoverGenerator/delete_custom_static_template")
async def plugin_delete_custom_static_template(request: Request, id: str = Query("")):
    if not id and request.method.upper() == "POST":
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        if isinstance(payload, dict):
            id = str(payload.get("id") or "").strip()
    id = str(id or "").strip()
    if not id:
        return {"code": 1, "msg": "方案 ID 不能为空", "data": None}
    config = load_config()
    existing_templates = [item for item in (config.get("custom_static_layouts") or []) if isinstance(item, dict)]
    templates = [item for item in existing_templates if str(item.get("id") or "") != id]
    if len(templates) == len(existing_templates):
        return {"code": 1, "msg": "方案不存在或已删除", "data": None}
    config["custom_static_layouts"] = templates
    if config.get("custom_static_active_id") == id:
        config["custom_static_active_id"] = str(templates[0].get("id") or "") if templates else None
        config["custom_static_layout"] = templates[0].get("layout") if templates else None
    save_config(config)
    service.reload()
    plugin_config = to_plugin_config(config)
    return ok({
        "id": id,
        "custom_static_layout": plugin_config.get("custom_static_layout"),
        "custom_static_layouts": plugin_config.get("custom_static_layouts"),
        "custom_static_active_id": plugin_config.get("custom_static_active_id"),
    })


@app.post("/api/plugin/MediaCoverGenerator/delete_saved_cover")
@app.get("/api/plugin/MediaCoverGenerator/delete_saved_cover")
@app.delete("/api/plugin/MediaCoverGenerator/delete_saved_cover")
async def plugin_delete_saved_cover(file: str = Query("")):
    path = safe_data_path(file)
    if path and path.exists() and path.is_file():
        path.unlink()
        remove_history_item(path)
        return ok({"deleted": True})
    return ok({"deleted": False})


@app.post("/api/plugin/MediaCoverGenerator/delete_saved_covers")
async def plugin_delete_saved_covers(payload: dict[str, Any] | None = None):
    deleted = 0
    for file in (payload or {}).get("files") or []:
        path = safe_data_path(str(file))
        if path and path.exists() and path.is_file():
            path.unlink()
            remove_history_item(path)
            deleted += 1
    return ok({"deleted": deleted})


@app.get("/api/plugin/MediaCoverGenerator/download_saved_cover")
async def plugin_download_saved_cover(file: str = Query("")):
    path = safe_data_path(file)
    if not path or not path.exists():
        return {"code": 1, "msg": "文件不存在", "data": None}
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return ok({"name": path.name, "mime": mime, "b64": base64.b64encode(path.read_bytes()).decode("ascii")})


@app.post("/api/plugin/MediaCoverGenerator/download_saved_covers")
async def plugin_download_saved_covers(payload: dict[str, Any] | None = None):
    files = []
    for raw in (payload or {}).get("files") or []:
        path = safe_data_path(str(raw))
        if path and path.exists() and path.is_file():
            files.append(path)
    if not files:
        return {"code": 1, "msg": "没有可下载的封面", "data": None}
    buffer = io.BytesIO()
    used_names: set[str] = set()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive_name = path.name
            if archive_name in used_names:
                archive_name = f"{path.stem}_{len(used_names) + 1}{path.suffix}"
            used_names.add(archive_name)
            archive.write(path, archive_name)
    return ok({
        "name": f"yahaha_covers_{timestamp_label()}.zip",
        "mime": "application/zip",
        "b64": base64.b64encode(buffer.getvalue()).decode("ascii"),
    })


@app.get("/api/v1/plugin/MediaCoverGenerator/saved_cover_image")
@app.get("/api/plugin/MediaCoverGenerator/saved_cover_image")
async def plugin_saved_cover_image(file: str = Query("")):
    path = safe_data_path(file)
    if not path or not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    stat = path.stat()
    return FileResponse(path, headers={"Cache-Control": "private, max-age=86400", "ETag": f'\"{stat.st_mtime_ns}-{stat.st_size}\"'})


def ok(data: Any = None, msg: str = "ok"):
    return {"code": 0, "msg": msg, "data": data}


def set_style_by_index(index: int):
    config = load_config()
    style = {
        1: "single_1",
        2: "single_2",
        3: "multi_1",
        4: "static_4",
    }.get(index, "single_1")
    config.setdefault("style_config", {})["style"] = style
    save_config(config)
    service.reload()
    return ok({"style": style, **to_status_payload(config)})


def set_page_tab(tab: str):
    valid_tabs = {"generate-tab", "custom-tab", "history-tab", "clean-tab"}
    next_tab = tab if tab in valid_tabs else "generate-tab"
    config = load_config()
    config["page_tab"] = next_tab
    save_config(config)
    service.reload()
    return ok({"page_tab": next_tab, **to_status_payload(config)})


def create_config_backup(config: dict[str, Any], target: str = "") -> Path:
    raw = str(target or "").strip()
    if not raw:
        return storage.write_backup(
            storage.unique_path(DATA_DIR / "backups", f"yahaha_cover_studio_{timestamp_label()}.json"),
            config,
            version=app.version,
        )
    path = Path(raw)
    if not path.is_absolute():
        path = DATA_DIR / raw
    if path.suffix.lower() in storage.BACKUP_EXTENSIONS:
        target_path = storage.unique_path(path.parent, path.name)
    else:
        target_path = storage.unique_path(path, f"yahaha_cover_studio_{timestamp_label()}.json")
    return storage.write_backup(target_path, config, version=app.version)


def cron_matches(expr: str, now: datetime) -> bool:
    parts = str(expr or "").strip().split()
    if len(parts) != 5:
        return False
    minute, hour, day, month, weekday = parts
    cron_weekday = (now.weekday() + 1) % 7
    return (
        cron_field_matches(minute, now.minute, 0, 59)
        and cron_field_matches(hour, now.hour, 0, 23)
        and cron_field_matches(day, now.day, 1, 31)
        and cron_field_matches(month, now.month, 1, 12)
        and cron_field_matches(weekday, cron_weekday, 0, 6, sunday_alias=True)
    )


def cron_field_matches(field: str, value: int, minimum: int, maximum: int, sunday_alias: bool = False) -> bool:
    field = str(field or "").strip()
    if not field:
        return False
    for token in field.split(","):
        token = token.strip()
        if not token:
            continue
        if cron_token_matches(token, value, minimum, maximum, sunday_alias):
            return True
    return False


def cron_token_matches(token: str, value: int, minimum: int, maximum: int, sunday_alias: bool = False) -> bool:
    step = 1
    if "/" in token:
        token, raw_step = token.split("/", 1)
        try:
            step = max(1, int(raw_step))
        except Exception:
            return False
    is_wildcard = token in {"*", "?"}
    is_range = "-" in token
    if is_wildcard:
        start, end = minimum, maximum
    elif is_range:
        raw_start, raw_end = token.split("-", 1)
        try:
            start, end = int(raw_start), int(raw_end)
        except Exception:
            return False
    else:
        try:
            start = end = int(token)
        except Exception:
            return False
    if sunday_alias:
        if not is_wildcard and not is_range and start == 7 and end == 7:
            return value == 0
        if value == 0 and (start == 7 or end == 7):
            return True
        if start == 7:
            start = 0
        if end == 7:
            end = maximum
    start = max(minimum, min(maximum, start))
    end = max(minimum, min(maximum, end))
    if start <= end:
        return value >= start and value <= end and ((value - start) % step == 0)
    return (value >= start or value <= end) and ((value - start) % step == 0)


async def delayed_generation_start(delay_seconds: int, style: str, library_name: str) -> None:
    if delay_seconds > 0:
        await asyncio.sleep(delay_seconds)
    await generation_manager.start(style, library_name, trigger="monitor")


async def parse_webhook_request(request: Request) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    body = await request.body()
    if not body:
        return {}
    if content_type == "application/json" or content_type.endswith("+json"):
        try:
            return normalize_webhook_payload(json.loads(body.decode("utf-8") or "{}"))
        except Exception:
            return {"payload": body.decode("utf-8", errors="replace")}
    if content_type == "application/x-www-form-urlencoded":
        return normalize_webhook_payload(flatten_form_values(parse_qs(body.decode("utf-8"), keep_blank_values=True)))
    if content_type == "multipart/form-data":
        return normalize_webhook_payload(parse_multipart_form(body, request.headers.get("content-type", "")))
    text = body.decode("utf-8", errors="replace").strip()
    if text:
        try:
            return normalize_webhook_payload(json.loads(text))
        except Exception:
            if "=" in text:
                return normalize_webhook_payload(flatten_form_values(parse_qs(text, keep_blank_values=True)))
            return {"payload": text}
    return {}


def flatten_form_values(values: dict[str, list[str]]) -> dict[str, Any]:
    return {
        str(key): value[0] if len(value) == 1 else value
        for key, value in values.items()
    }


def parse_multipart_form(body: bytes, content_type: str) -> dict[str, Any]:
    message = BytesParser(policy=policy.default).parsebytes(
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8") + body
    )
    result: dict[str, Any] = {}
    if not message.is_multipart():
        return result
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if not name:
            continue
        payload = part.get_payload(decode=True) or b""
        charset = part.get_content_charset() or "utf-8"
        value = payload.decode(charset, errors="replace")
        if name in result:
            current = result[name]
            if isinstance(current, list):
                current.append(value)
            else:
                result[name] = [current, value]
        else:
            result[name] = value
    return result


def normalize_webhook_payload(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"payload": value}
    normalized: dict[str, Any] = {}
    for key, raw in value.items():
        normalized[str(key)] = parse_embedded_json(raw)
    for key in ("payload", "data", "json", "body", "message"):
        embedded = normalized.get(key)
        if isinstance(embedded, dict):
            merged = dict(embedded)
            merged.update({k: v for k, v in normalized.items() if k != key})
            return merged
    return normalized


def parse_embedded_json(value: Any) -> Any:
    if isinstance(value, list):
        return [parse_embedded_json(item) for item in value]
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text or text[0] not in "{[":
        return value
    try:
        return json.loads(text)
    except Exception:
        return value


def webhook_is_item_added_event(value: Any) -> bool:
    raw = str(value or "").strip().lower().replace(" ", "")
    if not raw:
        return True
    return raw in {
        "library.new",
        "itemadded",
        "item.added",
        "itemcreated",
        "mediaitemadded",
        "newmediaadded",
        "newitem",
        "新媒体已添加",
    } or ("added" in raw and "item" in raw)


def webhook_allowed_sources(config: dict[str, Any]) -> list[str]:
    sources: set[str] = set()
    for client in configured_clients(config):
        sources.add(client.kind)
        sources.add(client.server_name)
    return sorted(item for item in sources if item)


def webhook_source_known(config: dict[str, Any], source: str) -> bool:
    if config.get("mock_enabled", True):
        return True
    allowed = {item.lower() for item in webhook_allowed_sources(config)}
    return not allowed or source.lower() in allowed


def webhook_walk(value: Any):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from webhook_walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from webhook_walk(item)


def webhook_first(payload: dict[str, Any], *keys: str) -> str:
    targets = {key.lower() for key in keys}
    for node in webhook_walk(payload):
        for key, value in node.items():
            if str(key).lower() in targets and value not in (None, ""):
                return str(value)
    return ""


def webhook_item_first(payload: dict[str, Any], *keys: str) -> str:
    targets = {key.lower() for key in keys}
    for node in webhook_walk(payload):
        item = None
        for key, value in node.items():
            if str(key).lower() == "item" and isinstance(value, dict):
                item = value
                break
        if not item:
            continue
        for key, value in item.items():
            if str(key).lower() in targets and value not in (None, ""):
                return str(value)
    return ""


def webhook_summary(payload: dict[str, Any], source: str = "") -> dict[str, str]:
    return {
        "source": source or webhook_first(payload, "ServerName", "server_name", "Server", "server"),
        "event": webhook_first(payload, "Event", "event", "NotificationType"),
        "item_id": webhook_item_first(payload, "Id", "ItemId") or webhook_first(payload, "ItemId", "item_id", "item_id_str"),
        "item_name": webhook_item_first(payload, "Name") or webhook_first(payload, "ItemName", "item_name", "Name"),
        "library_id": webhook_item_first(payload, "LibraryId", "TopParentId", "ParentId", "AlbumId") or webhook_first(payload, "LibraryId", "library_id", "TopParentId", "top_parent_id", "ParentId", "AlbumId"),
        "library_name": webhook_item_first(payload, "LibraryName", "CollectionName", "ParentName") or webhook_first(payload, "LibraryName", "library_name", "CollectionName", "ParentName", "SeriesName"),
        "path": webhook_item_first(payload, "Path") or webhook_first(payload, "Path", "path", "ItemPath"),
    }


def normalize_path_for_match(value: str) -> str:
    return str(value or "").replace("\\", "/").rstrip("/").lower()


async def resolve_webhook_library_name(config: dict[str, Any], payload: dict[str, Any], source: str = "") -> str:
    summary = webhook_summary(payload, source)
    library_id = summary.get("library_id", "").strip()
    library_name = summary.get("library_name", "").strip()
    item_path = summary.get("path", "").strip()
    item_id = summary.get("item_id", "").strip()
    source_name = str(source or "").strip().lower()

    libraries = await service.libraries()
    for library in libraries:
        if library_name and library_name in {str(library.get("name") or ""), str(library.get("title") or "")}:
            return str(library.get("name") or library_name)
        if library_id and library_id in {str(library.get("id") or ""), str(library.get("ItemId") or "")}:
            return str(library.get("name") or library_id)

    matched_by_path = match_library_by_path(libraries, item_path)
    if matched_by_path:
        return matched_by_path

    if item_id and not config.get("mock_enabled", True):
        for client in service.clients():
            if source_name and source_name not in {client.kind, client.server_name}:
                continue
            try:
                item = await client.get_item(item_id)
            except Exception:
                continue
            item_library_id = str(item.get("TopParentId") or item.get("ParentId") or item.get("AlbumId") or item.get("SeasonId") or item.get("SeriesId") or "")
            item_path = str(item.get("Path") or item_path or "")
            for library in await client.get_libraries():
                if item_library_id and item_library_id == str(library.id):
                    return library.name
                if item_path:
                    matched = match_library_by_path([library.__dict__], item_path)
                    if matched:
                        return matched

    return ""


def match_library_by_path(libraries: list[dict[str, Any]], item_path: str) -> str:
    normalized_item_path = normalize_path_for_match(item_path)
    if not normalized_item_path:
        return ""
    for library in libraries:
        for location in library.get("locations") or library.get("Locations") or []:
            normalized_location = normalize_path_for_match(str(location or ""))
            if normalized_location and normalized_item_path.startswith(normalized_location):
                return str(library.get("name") or library.get("Name") or "")
    return ""


def normalize_style(style: Any) -> str:
    raw = str(style or "").strip()
    return PLUGIN_TO_STYLE.get(
        raw,
        raw if raw in {"single_1", "single_2", "multi_1", "static_4", "custom_static", "animated_1", "animated_2", "animated_3", "animated_4"} else "single_1",
    )


def cached_preview_payload(config: dict[str, Any], library_name: str, style: str) -> dict[str, Any] | None:
    style_config = dict(config.get("style_config") or {})
    service.config = config
    render_config = service.render_config(style_config, library_name, style)
    output_dir = resolve_data_path(config.get("covers_output"), "/app/data/output")
    output_path = output_dir / f"{slugify(library_name)}_{style}{service.output_suffix(render_config, style)}"
    if output_path.exists() and output_path.is_file() and output_path.stat().st_size > 0:
        return {
            "src": data_file_url(output_path),
            "server": "cache",
            "library": library_name,
            "style": style,
        }
    return None


def remember_libraries(config: dict[str, Any], libraries: list[dict[str, Any]]) -> None:
    if not libraries or config.get("mock_enabled", True):
        return
    entries = [
        {
            "name": str(item.get("name") or item.get("id") or ""),
            "value": str(item.get("value") or f"{item.get('server_id') or item.get('server')}:{item.get('id') or item.get('name')}"),
            "server": str(item.get("server") or ""),
            "server_id": str(item.get("server_id") or item.get("server") or ""),
        }
        for item in libraries
        if str(item.get("name") or item.get("id") or "").strip()
    ]
    if not entries:
        return
    config["all_libraries"] = entries
    config["all_servers"] = sorted({
        str(item.get("server_id") or item.get("server") or "").strip()
        for item in libraries
        if str(item.get("server") or "").strip()
    })
    save_config(config)
    service.config = config


def first_cached_input_library(config: dict[str, Any]) -> str:
    input_dir = resolve_data_path(config.get("covers_input"), "/app/data/input")
    if not input_dir.exists():
        return ""
    for child in sorted(input_dir.iterdir(), key=lambda path: path.stat().st_mtime if path.exists() else 0, reverse=True):
        if not child.is_dir():
            continue
        try:
            if any(
                path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
                and not path.name.lower().startswith("mock_")
                for path in child.iterdir()
                if path.is_file()
            ):
                return child.name
        except Exception:
            continue
    return ""


def parse_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def clamp_number(value: Any, minimum: int, maximum: int, fallback: int) -> int:
    try:
        parsed = int(round(float(value)))
    except Exception:
        return fallback
    return max(minimum, min(maximum, parsed))


def clamp_float(value: Any, minimum: float, maximum: float, fallback: float) -> float:
    try:
        parsed = float(value)
    except Exception:
        return fallback
    return max(minimum, min(maximum, parsed))


def normalize_animated_setting_value(key: str, value: Any) -> Any:
    if key == "animation_duration":
        return clamp_number(value, 1, 60, 8)
    if key == "animation_fps":
        return clamp_number(value, 1, 60, 24)
    if key == "animated_2_image_count":
        return clamp_number(value, 1, 60, 6)
    if key == "main_title_font_size":
        return clamp_number(value, 24, 320, 170)
    if key == "subtitle_font_size":
        return clamp_number(value, 12, 220, 75)
    if key == "blur_size":
        return clamp_number(value, 0, 100, 50)
    if key == "color_ratio":
        return clamp_float(value, 0, 1, 0.8)
    if key == "title_scale":
        return clamp_float(value, 0.2, 3, 1)
    if key == "animation_format":
        return str(value).lower() if str(value).lower() in {"apng", "gif"} else "apng"
    if key == "animation_scroll":
        return str(value) if str(value) in {"down", "up", "alternate", "alternate_reverse"} else "alternate"
    if key == "animation_reduce_colors":
        return str(value) if str(value) in {"off", "medium", "strong"} else "medium"
    if key == "animated_2_departure_type":
        return str(value) if str(value) in {"fly", "fade", "crossfade"} else "fly"
    return str(value)


KNOWN_TITLE_ENTRY_KEYS = {
    "title",
    "main",
    "zh",
    "name",
    "subtitle",
    "sub",
    "en",
    "background",
    "bg",
    "color",
    "text",
    "custom_text",
    "content",
    "texts",
}


def parse_title_config(yaml_text: str, strict: bool = False) -> tuple[dict[str, Any], list[str], str]:
    errors: list[str] = []
    raw_yaml = str(yaml_text or "")
    if not raw_yaml.strip():
        return {}, [], ""
    try:
        if strict:
            processed_yaml = raw_yaml
            if "：" in raw_yaml:
                errors.append("严格模式不允许中文冒号，请使用英文冒号 ':'。")
            if "\t" in raw_yaml:
                errors.append("严格模式不允许制表符缩进，请使用空格。")
            if errors:
                return {}, errors, processed_yaml
        else:
            processed_yaml = preprocess_lenient_title_yaml(raw_yaml)
        title_config = yaml.safe_load(processed_yaml) or {}
        if title_config == {}:
            return {}, [], processed_yaml
        if not isinstance(title_config, dict):
            return {}, ["标题配置根节点必须是 YAML 对象。"], processed_yaml
        filtered: dict[str, Any] = {}

        def normalize_texts(raw_texts: Any) -> dict[str, str]:
            if not isinstance(raw_texts, dict):
                return {}
            return {
                str(text_key).strip(): str(text_val)
                for text_key, text_val in raw_texts.items()
                if str(text_key).strip() and text_val is not None
            }

        def collect_extra_texts(raw_map: dict[str, Any]) -> dict[str, str]:
            texts = normalize_texts(raw_map.get("texts"))
            for text_key, text_val in raw_map.items():
                normalized_text_key = str(text_key).strip()
                if normalized_text_key in KNOWN_TITLE_ENTRY_KEYS:
                    continue
                if normalized_text_key and isinstance(text_val, (str, int, float, bool)):
                    texts.setdefault(normalized_text_key, str(text_val))
            return texts

        for key, value in title_config.items():
            normalized_key = str(key).strip()
            if not normalized_key:
                errors.append(f"标题配置项键为空: {key} -> {value}")
                continue
            if isinstance(value, list) and len(value) >= 2 and isinstance(value[0], str) and isinstance(value[1], str):
                entry: list[Any] = [value[0], value[1]]
                bg_color = None
                texts: dict[str, str] = {}
                for item in value[2:]:
                    if isinstance(item, str) and not bg_color:
                        bg_color = item
                        continue
                    if isinstance(item, dict):
                        if "texts" in item:
                            texts.update(normalize_texts(item.get("texts")))
                        texts.update(collect_extra_texts(item))
                if isinstance(bg_color, str) and bg_color.strip():
                    entry.append(bg_color.strip())
                if texts:
                    entry.append({"texts": texts})
                filtered[normalized_key] = entry
                continue
            if isinstance(value, dict):
                zh_title = str(value.get("title") or value.get("main") or value.get("zh") or value.get("name") or normalized_key)
                en_title = str(value.get("subtitle") or value.get("sub") or value.get("en") or "")
                bg_color = value.get("background") or value.get("bg") or value.get("color")
                text_value = value.get("text") or value.get("custom_text") or value.get("content")
                texts = collect_extra_texts(value)
                if text_value is not None:
                    texts.setdefault("default", str(text_value))
                entry = [zh_title, en_title]
                if isinstance(bg_color, str) and bg_color.strip():
                    entry.append(bg_color.strip())
                if texts:
                    entry.append({"texts": texts})
                filtered[normalized_key] = entry
                continue
            errors.append(f"标题配置项格式不正确: {normalized_key}。请使用列表格式 [- 主标题, - 副标题] 或字典格式 title/subtitle。")
        if raw_yaml.strip() and not filtered:
            errors.append("没有解析到任何有效媒体库配置。")
        return filtered, errors, processed_yaml
    except Exception as err:
        return {}, [f"YAML 解析失败: {err}"], raw_yaml


def preprocess_lenient_title_yaml(raw_yaml: str) -> str:
    yaml_text = str(raw_yaml or "").replace("：", ":").replace("\t", "  ")
    processed_lines: list[str] = []
    current_library_open = False
    current_texts_open = False
    for line in yaml_text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            processed_lines.append(line)
            continue
        if ":" not in line:
            if current_library_open and not line[:1].isspace() and stripped.startswith("-"):
                processed_lines.append(f"  {line}")
            else:
                processed_lines.append(line)
            continue
        match = re.match(r"^(\s*)(-\s*)?([^:]+?):(.*)$", line)
        if not match:
            processed_lines.append(line)
            continue
        indent, list_marker, key_part, value_part = match.groups()
        key_part = key_part.strip()
        list_marker = list_marker or ""
        key_lookup = key_part.strip("\"'").strip()
        if not indent and current_library_open:
            if list_marker:
                indent = "  "
            elif key_lookup in KNOWN_TITLE_ENTRY_KEYS:
                indent = "  "
            elif current_texts_open and str(value_part or "").strip():
                indent = "    "
        elif current_library_open and current_texts_open and len(indent) < 4 and key_lookup not in KNOWN_TITLE_ENTRY_KEYS and str(value_part or "").strip():
            indent = "    "
        if key_part and not (key_part.startswith("\"") or key_part.startswith("'")):
            if key_part[0].isdigit() or any(char in key_part for char in [" ", ".", "(", ")", "[", "]"]):
                key_part = f'"{key_part}"'
        if value_part and not value_part.startswith((" ", "\t", "\n")):
            value_part = f" {value_part.lstrip()}"
        processed_lines.append(f"{indent}{list_marker}{key_part}:{value_part}")
        effective_indent_len = len(indent)
        if not list_marker and effective_indent_len == 0 and key_lookup not in KNOWN_TITLE_ENTRY_KEYS:
            current_library_open = True
            current_texts_open = False
        elif current_library_open:
            if key_lookup == "texts":
                current_texts_open = True
            elif effective_indent_len <= 2 and key_lookup in KNOWN_TITLE_ENTRY_KEYS:
                current_texts_open = False
    return "\n".join(processed_lines)


def normalize_template_key(value: Any) -> str:
    key = str(value or "").replace("：", ":").strip().strip("\"'")
    if ":" in key:
        key = key.split(":", 1)[-1].strip()
    return re.sub(r"\s+", "", key).lower()


def collect_raw_top_level_keys(text: str) -> set[str]:
    keys: set[str] = set()
    for raw_line in str(text or "").replace("：", ":").splitlines():
        if not raw_line or raw_line[:1].isspace():
            continue
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-") or ":" not in stripped:
            continue
        key = normalize_template_key(stripped.split(":", 1)[0])
        if key:
            keys.add(key)
    return keys


def quote_yaml_value(value: str) -> str:
    return json.dumps(str(value or ""), ensure_ascii=False)


def resolve_cleanable_data_dir(value: Any) -> Path | None:
    path = Path(str(value or ""))
    if not path.is_absolute():
        path = DATA_DIR / path
    try:
        resolved = path.resolve()
        resolved.relative_to(DATA_DIR.resolve())
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved
    except Exception:
        return None


def clean_directory_contents(directory: Path) -> int:
    removed = 0
    if not directory.exists() or not directory.is_dir():
        return removed
    for entry in directory.iterdir():
        if entry.name == ".gitkeep":
            continue
        try:
            if entry.is_dir():
                import shutil
                shutil.rmtree(entry)
                removed += 1
            elif entry.is_file():
                entry.unlink(missing_ok=True)
                removed += 1
        except Exception:
            continue
    gitkeep = directory / ".gitkeep"
    if not gitkeep.exists():
        try:
            gitkeep.touch()
        except Exception:
            pass
    return removed


def to_plugin_config(config: dict[str, Any]) -> dict[str, Any]:
    status = to_status_payload(config)
    title_config = config.get("title_config") or {}
    if isinstance(title_config, str):
        title_yaml = title_config
    else:
        title_yaml = yaml.safe_dump(title_config, allow_unicode=True, sort_keys=False)
    style_config = config.get("style_config") or {}
    return {
        **status,
        "enabled": bool(config.get("enabled", True)),
        "update_now": False,
        "auto_save_config": bool(config.get("auto_save_config", False)),
        "api_token": str(config.get("api_token") or ""),
        "cron": str(config.get("cron") or ""),
        "delay": int(config.get("delay") or 60),
        "emby_url": str(config.get("emby_url") or ""),
        "emby_api_key": str(config.get("emby_api_key") or ""),
        "jellyfin_url": str(config.get("jellyfin_url") or ""),
        "jellyfin_api_key": str(config.get("jellyfin_api_key") or ""),
        "media_servers": normalize_media_servers(config),
        "local_mode": bool(config.get("local_mode", False)),
        "mock_enabled": bool(config.get("mock_enabled", True)),
        "upload_after_generate": bool(config.get("upload_after_generate", True)),
        "selected_servers": config.get("selected_servers") or [],
        "include_libraries": config.get("include_libraries") or [],
        "sort_by": str(config.get("sort_by") or "Random"),
        "covers_input": str(config.get("covers_input") or "/app/data/input"),
        "covers_output": str(config.get("covers_output") or "/app/data/output"),
        "save_recent_covers": bool(config.get("save_recent_covers", True)),
        "history_enabled": bool(config.get("history_enabled", True)),
        "history_retention_batches": int(config.get("history_retention_batches") or 30),
        "covers_history_limit_per_library": int(config.get("covers_history_limit_per_library") or 10),
        "covers_page_history_limit": int(config.get("covers_page_history_limit") or 50),
        "title_config": title_yaml,
        "title_config_strict": bool(config.get("title_config_strict", False)),
        "distinguish_same_name_libraries": bool(config.get("distinguish_same_name_libraries", False)),
        "main_title_font_preset": str(config.get("main_title_font_preset") or style_config.get("font") or "chaohei"),
        "subtitle_font_preset": str(config.get("subtitle_font_preset") or "EmblemaOne"),
        "custom_text_font_preset": str(config.get("custom_text_font_preset") or "EmblemaOne"),
        "main_title_font_custom": str(config.get("main_title_font_custom") or ""),
        "subtitle_font_custom": str(config.get("subtitle_font_custom") or ""),
        "custom_text_font_custom": str(config.get("custom_text_font_custom") or ""),
        "main_title_font_size": style_config.get("main_font_size"),
        "subtitle_font_size": style_config.get("subtitle_font_size"),
        "blur_size": int(style_config.get("blur") or 42),
        "color_ratio": float(style_config.get("color_ratio") or 0.78),
        "title_scale": float(style_config.get("title_scale") or config.get("title_scale") or 1),
        "poster_source": style_config.get("image_source") or "backdrop",
        "use_primary": (style_config.get("image_source") == "poster"),
        "image_count_mode": style_config.get("image_count_mode") or config.get("image_count_mode") or "fixed",
        "image_count": int(style_config.get("image_limit") or 9),
        "resolution": str(style_config.get("resolution") or "1080p"),
        "custom_width": int(config.get("custom_width") or 1920),
        "custom_height": int(config.get("custom_height") or 1080),
        "bg_color_mode": str(config.get("bg_color_mode") or "auto"),
        "custom_bg_color": str(style_config.get("background_color") or ""),
        "animation_duration": int(config.get("animation_duration") or 8),
        "animation_scroll": str(config.get("animation_scroll") or "alternate"),
        "animation_fps": int(config.get("animation_fps") or 24),
        "animation_format": str(config.get("animation_format") or "apng"),
        "animation_resolution": str(config.get("animation_resolution") or "320x180"),
        "animation_reduce_colors": str(config.get("animation_reduce_colors") or "medium"),
        "animated_2_image_count": int(config.get("animated_2_image_count") or 6),
        "animated_2_departure_type": str(config.get("animated_2_departure_type") or "fly"),
        "animated_settings": config.get("animated_settings") or {},
        "clean_images": bool(config.get("clean_images", False)),
        "clean_fonts": bool(config.get("clean_fonts", False)),
        "backup_enabled": bool(config.get("backup_enabled", False)),
        "backup_cron": str(config.get("backup_cron") or ""),
        "backup_path": str(config.get("backup_path") or ""),
        "log_retention_days": int(config.get("log_retention_days") or 7),
        "page_tab": str(config.get("page_tab") or "generate-tab"),
        "style_naming_v2": bool(config.get("style_naming_v2", True)),
        "custom_static_layout": config.get("custom_static_layout"),
        "custom_static_layouts": config.get("custom_static_layouts"),
        "custom_static_active_id": config.get("custom_static_active_id"),
    }


def from_plugin_config(incoming: dict[str, Any], base: dict[str, Any]) -> dict[str, Any]:
    config = dict(base)
    style_config = dict(config.get("style_config") or {})
    passthrough_keys = (
        "enabled",
        "auto_save_config",
        "transfer_monitor",
        "monitor_source",
        "lock_latest_sort",
        "cron",
        "delay",
        "emby_url",
        "emby_api_key",
        "jellyfin_url",
        "jellyfin_api_key",
        "media_servers",
        "local_mode",
        "mock_enabled",
        "upload_after_generate",
        "api_token",
        "selected_servers",
        "all_servers",
        "include_libraries",
        "all_libraries",
        "sort_by",
        "covers_input",
        "covers_output",
        "save_recent_covers",
        "history_enabled",
        "history_retention_batches",
        "covers_history_limit_per_library",
        "covers_page_history_limit",
        "title_config_strict",
        "distinguish_same_name_libraries",
        "main_title_font_preset",
        "subtitle_font_preset",
        "custom_text_font_preset",
        "main_title_font_custom",
        "subtitle_font_custom",
        "custom_text_font_custom",
        "animation_duration",
        "animation_scroll",
        "animation_fps",
        "animation_format",
        "animation_resolution",
        "animation_reduce_colors",
        "animated_2_image_count",
        "animated_2_departure_type",
        "animated_settings",
        "clean_images",
        "clean_fonts",
        "backup_enabled",
        "backup_cron",
        "backup_path",
        "log_retention_days",
        "page_tab",
        "style_naming_v2",
        "custom_width",
        "custom_height",
        "bg_color_mode",
    )
    for key in passthrough_keys:
        if key in incoming:
            config[key] = incoming[key]
    if "media_servers" in incoming:
        servers = normalize_media_servers(config)
        config["media_servers"] = servers
        first_emby = next((item for item in servers if item.get("type") == "emby"), None)
        first_jellyfin = next((item for item in servers if item.get("type") == "jellyfin"), None)
        if first_emby:
            config["emby_url"] = first_emby.get("url") or ""
            config["emby_api_key"] = first_emby.get("api_key") or ""
        if first_jellyfin:
            config["jellyfin_url"] = first_jellyfin.get("url") or ""
            config["jellyfin_api_key"] = first_jellyfin.get("api_key") or ""
    if "title_config" in incoming:
        raw_title = incoming.get("title_config")
        if isinstance(raw_title, str):
            parsed, errors, _processed_yaml = parse_title_config(raw_title, strict=parse_bool(config.get("title_config_strict", False)))
            config["title_config"] = parsed if not errors else raw_title
        else:
            config["title_config"] = raw_title or {}
    if "cover_style_base" in incoming:
        variant = incoming.get("cover_style_variant") or "static"
        key = "custom_static" if incoming["cover_style_base"] == "custom_static" else f"{variant}_{str(incoming['cover_style_base']).split('_')[-1]}"
        style_config["style"] = normalize_style(key)
    for source_key, target_key in {
        "poster_source": "image_source",
        "resolution": "resolution",
        "image_count_mode": "image_count_mode",
        "image_count": "image_limit",
        "blur_size": "blur",
        "color_ratio": "color_ratio",
        "custom_bg_color": "background_color",
        "main_title_font_size": "main_font_size",
        "subtitle_font_size": "subtitle_font_size",
        "title_scale": "title_scale",
    }.items():
        if source_key in incoming and incoming[source_key] not in (None, ""):
            style_config[target_key] = incoming[source_key]
    if incoming.get("use_primary") is True:
        style_config["image_source"] = "poster"
    if incoming.get("use_primary") is False and "poster_source" not in incoming:
        style_config.setdefault("image_source", "backdrop")
    config["style_config"] = style_config
    for key in ("custom_static_layout", "custom_static_layouts", "custom_static_active_id"):
        if key in incoming:
            config[key] = incoming[key]
    return config


def to_status_payload(config: dict[str, Any]) -> dict[str, Any]:
    style_config = config.get("style_config") or {}
    base, variant = STYLE_TO_PLUGIN.get(str(style_config.get("style") or "single_1"), ("static_1", "static"))
    local_mode = bool(config.get("local_mode", False))
    mock = bool(config.get("mock_enabled", True)) and not local_mode
    local_libraries = service.local_libraries() if local_mode else []
    libraries = (
        [{"name": item["name"], "value": f"mock:{item.get('id') or item['name']}", "server": "mock", "server_id": "mock"} for item in MOCK_LIBRARIES]
        if mock
        else (local_libraries if local_mode else (config.get("all_libraries") or []))
    )
    all_servers = ["local"] if local_mode else (["mock"] if mock else [client.server_id for client in configured_clients(config)])
    allowed_servers = set(all_servers)
    selected_servers = [
        str(item)
        for item in (config.get("selected_servers") or [])
        if str(item) in allowed_servers
    ]
    return {
        "warnings": [],
        "enabled": bool(config.get("enabled", True)),
        "has_selected_servers": bool(selected_servers or all_servers),
        "servers_ready": True,
        "transfer_monitor": bool(config.get("transfer_monitor", False)),
        "lock_latest_sort": bool(config.get("lock_latest_sort", False)),
        "is_generating": False,
        "generation_current": 0,
        "generation_total": 0,
        "generation_label": "",
        "all_servers": all_servers,
        "selected_servers": selected_servers,
        "include_libraries": config.get("include_libraries") or [],
        "all_libraries": libraries,
        "monitor_source": str(config.get("monitor_source") or "webhook") if str(config.get("monitor_source") or "webhook") in {"webhook", "emby", "jellyfin"} else "webhook",
        "local_mode": local_mode,
        "cover_style_base": base,
        "cover_style_variant": variant,
        "poster_source": style_config.get("image_source") or "backdrop",
        "use_primary": (style_config.get("image_source") == "poster"),
        "sort_by": config.get("sort_by") or "Random",
        "image_count_mode": style_config.get("image_count_mode") or config.get("image_count_mode") or "fixed",
        "image_count": int(style_config.get("image_limit") or 9),
        "auto_image_count": int(style_config.get("image_limit") or 9),
        "resolution": style_config.get("resolution") or "1080p",
        "animation_resolution": config.get("animation_resolution") or "320x180",
        "custom_width": int(config.get("custom_width") or 1920),
        "custom_height": int(config.get("custom_height") or 1080),
        "animation_duration": int(config.get("animation_duration") or 8),
        "animation_fps": int(config.get("animation_fps") or 24),
        "animation_format": config.get("animation_format") or "apng",
        "animation_scroll": config.get("animation_scroll") or "alternate",
        "animation_reduce_colors": config.get("animation_reduce_colors") or "medium",
        "animated_2_image_count": int(config.get("animated_2_image_count") or 6),
        "animated_2_departure_type": config.get("animated_2_departure_type") or "fly",
        "animated_settings": config.get("animated_settings") or {},
        "main_title_font_preset": config.get("main_title_font_preset") or "chaohei",
        "subtitle_font_preset": config.get("subtitle_font_preset") or "EmblemaOne",
        "custom_text_font_preset": config.get("custom_text_font_preset") or "EmblemaOne",
        "main_title_font_size": style_config.get("main_font_size"),
        "subtitle_font_size": style_config.get("subtitle_font_size"),
        "blur_size": int(style_config.get("blur") or 42),
        "color_ratio": float(style_config.get("color_ratio") or 0.78),
        "title_scale": float(style_config.get("title_scale") or config.get("title_scale") or 1),
        "page_tab": str(config.get("page_tab") or "generate-tab"),
        "custom_static_layout": config.get("custom_static_layout"),
        "custom_static_layouts": config.get("custom_static_layouts"),
        "custom_static_active_id": config.get("custom_static_active_id"),
    }


async def first_library_name(config: dict[str, Any]) -> str:
    if config.get("local_mode", False):
        local_libraries = service.local_libraries()
        if local_libraries:
            return str(local_libraries[0].get("name") or "本地封面")
        return "本地封面"
    if config.get("mock_enabled", True):
        return MOCK_LIBRARIES[0]["name"]
    include_libraries = [str(item) for item in (config.get("include_libraries") or []) if str(item)]
    if include_libraries:
        return include_libraries[0]
    cached_input_library = first_cached_input_library(config)
    if cached_input_library:
        return cached_input_library
    cached_libraries = [
        str(item.get("name") or item.get("value") or "").strip()
        for item in (config.get("all_libraries") or [])
        if isinstance(item, dict) and str(item.get("name") or item.get("value") or "").strip()
    ]
    if cached_libraries:
        return cached_libraries[0]
    try:
        libraries = await service.libraries()
        if libraries:
            remember_libraries(config, libraries)
            return str(libraries[0].get("name") or libraries[0].get("id") or "")
    except Exception:
        pass
    title_config = config.get("title_config") or {}
    if isinstance(title_config, dict) and title_config:
        return next(iter(title_config.keys()))
    return "本地封面"


async def ensure_preview_images(config: dict[str, Any], library: str, required_items: int, force_refresh: bool = False) -> dict[str, Any]:
    style_config = config.get("style_config") or {}
    input_dir = Path(config.get("covers_input") or "/app/data/input")
    if not input_dir.is_absolute():
        input_dir = DATA_DIR / input_dir
    default_input_dir = (DATA_DIR / "input").resolve()
    try:
        input_is_default = input_dir.resolve() == default_input_dir
    except Exception:
        input_is_default = False
    limit = max(1, min(60, required_items or int(style_config.get("image_limit") or 9)))
    if config.get("local_mode", False):
        images = service.local_images(library, limit, include_mock=False)
        server = "local"
        source_mode = ("cache" if input_is_default else "custom") if images else "custom"
        if not images:
            images = service.local_images("", limit, include_mock=False)
    elif config.get("mock_enabled", True):
        images = ensure_mock_images(input_dir, slugify(library), title_for_library(config, library)[0], limit)
        server = "mock"
        source_mode = "custom"
    else:
        images = [] if force_refresh and input_is_default else service.local_images(library, limit, include_mock=False)
        server = "local"
        source_mode = ("cache" if input_is_default else "custom") if images else "media_server"
        if not images:
            try:
                client, media_library = await service.find_library(library)
                server = client.server_name
                library = media_library.name
                cache_dir = input_dir / slugify(media_library.name)
                cache_dir.mkdir(parents=True, exist_ok=True)
                items = await client.get_items(
                    media_library.id,
                    limit,
                    str(style_config.get("sort_by") or config.get("sort_by") or "DateCreated"),
                )
                image_source = str(style_config.get("image_source") or "backdrop")
                downloaded: list[Path] = []
                for index, item in enumerate(items):
                    image_url = client.item_image_url(item, image_source)
                    if not image_url:
                        continue
                    try:
                        downloaded.append(await client.download_image(image_url, cache_dir / f"{index + 1:02d}.jpg"))
                    except Exception:
                        continue
                    if len(downloaded) >= limit:
                        break
                images = downloaded
                source_mode = "media_server" if images else "cache"
            except Exception:
                images = []
        if not images:
            images = service.local_images("", limit, include_mock=False)
            server = "local"
            source_mode = ("cache" if input_is_default else "custom") if images else "media_server"
    if force_refresh and len(images) > 1:
        offset = int(datetime.now(timezone.utc).timestamp() * 1000) % len(images)
        images = images[offset:] + images[:offset]
    preview_version = str(int(datetime.now(timezone.utc).timestamp() * 1000)) if force_refresh else ""
    title, subtitle, custom_texts = library_title_payload(config, library)
    base, variant = STYLE_TO_PLUGIN.get(str(style_config.get("style") or "single_1"), ("static_1", "static"))
    return {
        "server": server,
        "library": library,
        "style": style_config.get("style") or "single_1",
        "cover_style_base": base,
        "cover_style_variant": variant,
        "source_mode": source_mode,
        "titles": {"zh": title, "en": subtitle or ("Local Library" if config.get("local_mode", False) else ("Mock Library" if config.get("mock_enabled", True) else ""))},
        "custom_texts": custom_texts,
        "images": [
            {
                "slot": index + 1,
                "src": data_file_url(path) + (f"?preview_version={preview_version}" if preview_version else ""),
                "kind": source_mode,
                "label": path.name,
            }
            for index, path in enumerate(images)
        ],
        "custom_static_layout": config.get("custom_static_layout"),
        "bg_color": style_config.get("background_color") or "#6f8090",
        "font_faces": {},
    }


def data_file_url(path: Path) -> str:
    try:
        rel = path.resolve().relative_to(DATA_DIR.resolve())
    except Exception:
        rel = Path("output") / path.name
    return "/data/" + "/".join(quote(part) for part in rel.parts)


def safe_data_path(value: str) -> Path | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw.startswith("/data/"):
        raw = raw[len("/data/") :]
    path = Path(raw)
    if not path.is_absolute():
        path = DATA_DIR / raw
    try:
        resolved = path.resolve()
        resolved.relative_to(DATA_DIR.resolve())
        return resolved
    except Exception:
        return None


def history_library_name(stem: str) -> str:
    for suffix in (
        "_custom_static",
        "_single_1",
        "_single_2",
        "_multi_1",
        "_static_1",
        "_static_2",
        "_static_3",
        "_static_4",
        "_animated_1",
        "_animated_2",
        "_animated_3",
        "_animated_4",
    ):
        if stem.endswith(suffix):
            return stem[: -len(suffix)]
    return stem.rsplit("_", 1)[0] if "_" in stem else stem


def history_style_name(stem: str) -> str:
    for suffix in (
        "custom_static",
        "single_1",
        "single_2",
        "multi_1",
        "static_1",
        "static_2",
        "static_3",
        "static_4",
        "animated_1",
        "animated_2",
        "animated_3",
        "animated_4",
    ):
        if stem.endswith(f"_{suffix}"):
            return suffix
    return "generated"


def timestamp_label() -> str:
    return now_local(str(load_config().get("timezone") or "Asia/Shanghai")).strftime("%Y%m%d_%H%M%S")


def default_avatar_data_url() -> str:
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
      <rect width="128" height="128" rx="34" fill="#eaf4ff"/>
      <circle cx="64" cy="58" r="32" fill="#ffe2b9"/>
      <path d="M28 58c5-27 24-42 50-34 18 6 28 21 24 42-12-16-24-22-38-20-14 2-25 7-36 12z" fill="#45a82f"/>
      <path d="M40 39c12-16 38-17 54-2-12-3-24-1-34 6-8 5-13 5-20-4z" fill="#ffd245"/>
      <circle cx="52" cy="64" r="5" fill="#102228"/>
      <circle cx="78" cy="64" r="5" fill="#102228"/>
      <path d="M52 82c8 8 18 8 26 0" fill="none" stroke="#102228" stroke-width="6" stroke-linecap="round"/>
      <path d="M36 94c16 13 41 15 59 1-8 16-50 17-59-1z" fill="#45a82f"/>
    </svg>
    """.strip()
    return "data:image/svg+xml," + quote(svg)


def asset_path(directory: Path, value: str) -> Path | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw.startswith("/data/"):
        raw = raw[len("/data/") :]
    path = Path(raw)
    if not path.is_absolute():
        if len(path.parts) > 1 and path.parts[0] in {"fonts", "stickers", "backups", "output", "input"}:
            path = DATA_DIR / path
        else:
            path = directory / path.name
    try:
        resolved = path.resolve()
        resolved.relative_to(directory.resolve())
        return resolved
    except Exception:
        return None


def save_binary_asset(directory: Path, filename: str, bytes_data: bytes, allowed_extensions: set[str], kind: str) -> dict[str, Any]:
    safe_name = storage.safe_filename(filename, f"{kind}.bin")
    suffix = Path(safe_name).suffix.lower()
    if suffix not in allowed_extensions:
        fallback_suffix = ".png" if kind == "sticker" else ".ttf"
        safe_name = f"{Path(safe_name).stem or kind}{fallback_suffix}"
    if not bytes_data:
        raise ValueError("文件数据为空")
    path = storage.unique_path(directory, safe_name)
    path.write_bytes(bytes_data)
    if kind == "sticker":
        return storage.sticker_item(path)
    if kind == "font":
        return storage.font_item(path)
    return {"name": path.name, "path": str(path), "url": data_file_url(path)}


def save_chunked_upload(payload: dict[str, Any], directory: Path, allowed_extensions: set[str], kind: str) -> dict[str, Any] | None:
    upload_id = storage.safe_filename(str(payload.get("upload_id") or "upload"), "upload")
    filename = storage.safe_filename(str(payload.get("name") or f"{kind}.bin"), f"{kind}.bin")
    chunk_index = int(payload.get("chunk_index") or 0)
    chunk_total = max(1, int(payload.get("chunk_total") or 1))
    chunk_mime, chunk_bytes = storage.decode_data_url(str(payload.get("chunk_data") or ""))
    del chunk_mime

    tmp_dir = DATA_DIR / "tmp" / upload_id
    tmp_dir.mkdir(parents=True, exist_ok=True)
    (tmp_dir / f"{chunk_index:06d}.part").write_bytes(chunk_bytes)

    if chunk_index < chunk_total - 1:
        return {"done": False, "received": chunk_index + 1, "total": chunk_total}

    combined = bytearray()
    for index in range(chunk_total):
        part = tmp_dir / f"{index:06d}.part"
        if not part.exists():
            raise ValueError(f"缺少上传分片 {index + 1}/{chunk_total}")
        combined.extend(part.read_bytes())
    for part in tmp_dir.glob("*.part"):
        part.unlink(missing_ok=True)
    tmp_dir.rmdir()
    item = save_binary_asset(directory, filename, bytes(combined), allowed_extensions, kind)
    item["done"] = True
    return item
