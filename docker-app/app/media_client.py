from __future__ import annotations

from dataclasses import dataclass
import base64
import mimetypes
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlencode

import httpx


ServerKind = Literal["emby", "jellyfin"]


@dataclass
class MediaLibrary:
    id: str
    name: str
    collection_type: str = ""
    server: str = ""
    locations: list[str] | None = None


class MediaServerClient:
    def __init__(self, base_url: str, api_key: str, kind: ServerKind = "emby", timeout: float = 30, name: str = ""):
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key or ""
        self.kind = kind
        self.timeout = timeout
        self.name = (name or kind).strip() or kind
        if not self.base_url or not self.api_key:
            raise ValueError(f"{kind} url/api_key is not configured")

    @property
    def server_name(self) -> str:
        return self.name

    def _url(self, path: str, params: dict[str, Any] | None = None) -> str:
        query = {"api_key": self.api_key}
        if params:
            query.update({k: v for k, v in params.items() if v is not None and v != ""})
        return f"{self.base_url}/{path.lstrip('/')}?{urlencode(query, doseq=True)}"

    async def _get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self._url(path, params))
            response.raise_for_status()
            return response.json()

    async def get_libraries(self) -> list[MediaLibrary]:
        candidates = [
            ("Library/VirtualFolders/Query", {}),
            ("Library/VirtualFolders", {}),
            ("Library/MediaFolders", {}),
            ("Items", {
                "IncludeItemTypes": "CollectionFolder",
                "Recursive": "false",
                "Fields": "Path,CollectionType,Locations",
            }),
        ]
        last_error: Exception | None = None
        for path, params in candidates:
            try:
                data = await self._get_json(path, params)
                items = data.get("Items", data) if isinstance(data, dict) else data
                libraries: list[MediaLibrary] = []
                seen: set[tuple[str, str]] = set()
                for item in items or []:
                    library_id = str(item.get("ItemId") or item.get("Id") or item.get("Guid") or "")
                    name = str(
                        item.get("Name")
                        or item.get("LibraryOptions", {}).get("PathInfos", [{}])[0].get("Path")
                        or ""
                    )
                    locations = item.get("Locations") or [
                        path_info.get("Path")
                        for path_info in item.get("LibraryOptions", {}).get("PathInfos", [])
                        if isinstance(path_info, dict) and path_info.get("Path")
                    ]
                    if not locations and item.get("Path"):
                        locations = [item.get("Path")]
                    dedupe_key = (library_id, name)
                    if library_id and name and dedupe_key not in seen:
                        seen.add(dedupe_key)
                        libraries.append(
                            MediaLibrary(
                                id=library_id,
                                name=name,
                                collection_type=str(
                                    item.get("CollectionType")
                                    or item.get("LibraryOptions", {}).get("ContentType")
                                    or item.get("Type")
                                    or ""
                                ),
                                server=self.server_name,
                                locations=[str(location) for location in locations or []],
                            )
                        )
                if libraries:
                    return libraries
            except Exception as err:
                last_error = err
        if last_error:
            raise last_error
        return []

    async def get_items(self, library_id: str, limit: int = 12, sort_by: str = "DateCreated") -> list[dict[str, Any]]:
        params = {
            "ParentId": library_id,
            "Recursive": "true",
            "Limit": max(1, int(limit or 12)),
            "SortBy": sort_by or "DateCreated",
            "SortOrder": "Descending",
            "Fields": ",".join([
                "DateCreated",
                "PremiereDate",
                "PrimaryImageAspectRatio",
                "PrimaryImageItemId",
                "ImageTags",
                "BackdropImageTags",
                "ParentBackdropImageTags",
                "ParentBackdropItemId",
                "SeriesPrimaryImageTag",
                "AlbumPrimaryImageTag",
            ]),
        }
        data = await self._get_json("Items", params)
        return list(data.get("Items", [])) if isinstance(data, dict) else []

    async def get_item(self, item_id: str) -> dict[str, Any]:
        data = await self._get_json(f"Items/{item_id}", {
            "Fields": ",".join([
                "Path",
                "ParentId",
                "TopParentId",
                "AlbumId",
                "SeriesId",
                "SeasonId",
                "PresentationUniqueKey",
                "MediaSources",
            ]),
        })
        return dict(data) if isinstance(data, dict) else {}

    def item_image_url(self, item: dict[str, Any], image_source: str = "backdrop") -> str:
        item_id = str(item.get("Id") or "")
        if image_source == "poster":
            tag = item.get("PrimaryImageTag") or (item.get("ImageTags") or {}).get("Primary")
            image_id = item.get("PrimaryImageItemId") or item_id
            if tag and image_id:
                return self._url(f"Items/{image_id}/Images/Primary", {"tag": tag})

        backdrop_tags = item.get("BackdropImageTags") or []
        if backdrop_tags and item_id:
            return self._url(f"Items/{item_id}/Images/Backdrop/0", {"tag": backdrop_tags[0]})

        parent_tags = item.get("ParentBackdropImageTags") or []
        parent_id = item.get("ParentBackdropItemId")
        if parent_tags and parent_id:
            return self._url(f"Items/{parent_id}/Images/Backdrop/0", {"tag": parent_tags[0]})

        tag = item.get("PrimaryImageTag") or (item.get("ImageTags") or {}).get("Primary")
        image_id = item.get("PrimaryImageItemId") or item_id
        if tag and image_id:
            return self._url(f"Items/{image_id}/Images/Primary", {"tag": tag})
        return ""

    async def download_image(self, image_url: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
            suffix = {
                "image/jpeg": ".jpg",
                "image/jpg": ".jpg",
                "image/png": ".png",
                "image/webp": ".webp",
                "image/gif": ".gif",
            }.get(content_type)
            if suffix and output_path.suffix.lower() != suffix:
                output_path = output_path.with_suffix(suffix)
            output_path.write_bytes(response.content)
        return output_path

    async def upload_library_cover(self, library_id: str, image_path: Path) -> dict[str, Any]:
        content_type = media_image_mime_type(image_path)
        image_base64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self._url(f"Items/{library_id}/Images/Primary"),
                content=image_base64,
                headers={"Content-Type": content_type},
            )
            response.raise_for_status()
            return {"ok": True, "status_code": response.status_code}


def configured_clients(config: dict[str, Any]) -> list[MediaServerClient]:
    clients: list[MediaServerClient] = []
    seen: set[str] = set()
    for raw in config.get("media_servers") or []:
        if not isinstance(raw, dict) or raw.get("enabled") is False:
            continue
        kind = str(raw.get("type") or raw.get("kind") or "emby").lower()
        if kind not in {"emby", "jellyfin"}:
            continue
        url = str(raw.get("url") or raw.get("base_url") or "").strip()
        api_key = str(raw.get("api_key") or raw.get("apikey") or "").strip()
        name = str(raw.get("name") or kind).strip() or kind
        if not url or not api_key:
            continue
        key = f"{kind}:{name}:{url}"
        if key in seen:
            continue
        seen.add(key)
        clients.append(MediaServerClient(url, api_key, kind, name=name))
    if not clients and config.get("emby_url") and config.get("emby_api_key"):
        clients.append(MediaServerClient(config["emby_url"], config["emby_api_key"], "emby", name="emby"))
    if not config.get("media_servers") and config.get("jellyfin_url") and config.get("jellyfin_api_key"):
        clients.append(MediaServerClient(config["jellyfin_url"], config["jellyfin_api_key"], "jellyfin", name="jellyfin"))
    return clients


def media_image_mime_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".gif":
        return "image/gif"
    if suffix == ".webp":
        return "image/webp"
    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"
