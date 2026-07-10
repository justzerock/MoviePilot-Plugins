from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path
from typing import Any

from .config import DATA_DIR, load_config, resolve_data_path, save_config
from .cover import CoverRenderer
from .media_client import MediaLibrary, MediaServerClient, configured_clients
from .mock import MOCK_LIBRARIES, ensure_mock_images, mock_library_by_name


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
OUTPUT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
FONT_EXTENSIONS = {".ttf", ".ttc", ".otf", ".woff", ".woff2"}
HISTORY_INDEX_FILE = DATA_DIR / "output" / ".history.json"
LEGACY_HISTORY_INDEX_FILE = DATA_DIR / "history.json"
BUILTIN_FONT_URLS = {
    "emblemaone": {
        "filename": "EmblemaOne-Regular.ttf",
        "urls": [
            "https://raw.githubusercontent.com/google/fonts/main/ofl/emblemaone/EmblemaOne-Regular.ttf",
            "https://github.com/google/fonts/raw/main/ofl/emblemaone/EmblemaOne-Regular.ttf",
        ],
    },
    "josefinsans": {
        "filename": "JosefinSans[wght].ttf",
        "urls": [
            "https://raw.githubusercontent.com/google/fonts/main/ofl/josefinsans/JosefinSans%5Bwght%5D.ttf",
            "https://github.com/google/fonts/raw/main/ofl/josefinsans/JosefinSans%5Bwght%5D.ttf",
        ],
    },
    "lilitaone": {
        "filename": "LilitaOne-Regular.ttf",
        "urls": [
            "https://raw.githubusercontent.com/google/fonts/main/ofl/lilitaone/LilitaOne-Regular.ttf",
            "https://github.com/google/fonts/raw/main/ofl/lilitaone/LilitaOne-Regular.ttf",
        ],
    },
}
BUILTIN_FONT_FALLBACKS = {
    "chaohei": [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "yasong": [
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ],
    "emblemaone": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "melete": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    ],
    "phosphate": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
    ],
    "josefinsans": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
    "lilitaone": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
}


def slugify(value: str) -> str:
    safe = re.sub(r"[\\/:*?\"<>|]+", "_", str(value or "").strip())
    safe = re.sub(r"\s+", "_", safe)
    return safe or "library"


def library_title_payload(config: dict[str, Any], library_name: str) -> tuple[str, str, dict[str, str]]:
    title_config = config.get("title_config") or {}
    if isinstance(title_config, str):
        title_config = {}
    raw = title_config.get(library_name) or {}
    if isinstance(raw, list):
        texts = raw[2] if len(raw) > 2 and isinstance(raw[2], dict) else {}
        return str(raw[0] if raw else library_name), str(raw[1] if len(raw) > 1 else ""), {str(k): str(v) for k, v in texts.items()}
    if isinstance(raw, dict):
        texts = raw.get("texts") if isinstance(raw.get("texts"), dict) else {}
        return str(raw.get("title") or library_name), str(raw.get("subtitle") or ""), {str(k): str(v) for k, v in texts.items()}
    return library_name, "", {}


def title_for_library(config: dict[str, Any], library_name: str) -> tuple[str, str]:
    title, subtitle, _texts = library_title_payload(config, library_name)
    return title, subtitle


def normalize_font_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def first_existing_path(candidates: list[str]) -> str:
    for candidate in candidates:
        path = Path(candidate)
        if path.exists() and path.is_file():
            return str(path)
    return ""


def download_builtin_font(key: str) -> str:
    spec = BUILTIN_FONT_URLS.get(normalize_font_key(key))
    if not spec:
        return ""
    target_dir = DATA_DIR / "fonts" / "builtin"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / str(spec["filename"])
    if target.exists() and target.stat().st_size > 1024:
        return str(target.resolve())
    temp = target.with_suffix(target.suffix + ".tmp")
    for url in spec.get("urls", []):
        try:
            with urllib.request.urlopen(str(url), timeout=8) as response:
                data = response.read()
            if len(data) < 1024:
                continue
            temp.write_bytes(data)
            temp.replace(target)
            return str(target.resolve())
        except Exception:
            try:
                temp.unlink(missing_ok=True)
            except Exception:
                pass
            continue
    return ""


def read_history_index() -> dict[str, dict[str, Any]]:
    source = HISTORY_INDEX_FILE if HISTORY_INDEX_FILE.exists() else LEGACY_HISTORY_INDEX_FILE
    if not source.exists():
        return {}
    try:
        raw = json.loads(source.read_text(encoding="utf-8") or "{}")
    except Exception:
        return {}
    if isinstance(raw, list):
        return {
            str(item.get("path") or item.get("name") or index): item
            for index, item in enumerate(raw)
            if isinstance(item, dict)
        }
    return {str(key): value for key, value in raw.items() if isinstance(value, dict)} if isinstance(raw, dict) else {}


def write_history_index(items: dict[str, dict[str, Any]]) -> None:
    HISTORY_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_INDEX_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def record_history_item(item: dict[str, Any]) -> None:
    path = Path(str(item.get("path") or ""))
    if not path:
        return
    try:
        resolved = str(path.resolve())
    except Exception:
        resolved = str(path)
    items = read_history_index()
    current = dict(items.get(resolved) or items.get(path.name) or {})
    current.update(item)
    current["path"] = resolved
    current["name"] = path.name
    items[resolved] = current
    write_history_index(items)


def remove_history_item(path: Path) -> None:
    items = read_history_index()
    keys = {str(path), path.name}
    try:
        keys.add(str(path.resolve()))
    except Exception:
        pass
    changed = False
    for key in list(items.keys()):
        if key in keys or str(items[key].get("path") or "") in keys or str(items[key].get("name") or "") == path.name:
            items.pop(key, None)
            changed = True
    if changed:
        write_history_index(items)


class CoverService:
    def __init__(self) -> None:
        self.config = load_config()

    def reload(self) -> dict[str, Any]:
        self.config = load_config()
        return self.config

    def save(self, config: dict[str, Any]) -> dict[str, Any]:
        self.config = save_config(config)
        return self.config

    def clients(self) -> list[MediaServerClient]:
        return configured_clients(self.config)

    def mock_enabled(self) -> bool:
        return bool(self.config.get("mock_enabled", True)) and not bool(self.config.get("local_mode", False))

    def local_mode(self) -> bool:
        return bool(self.config.get("local_mode", False))

    def renderer(self) -> CoverRenderer:
        return CoverRenderer(DATA_DIR / "fonts")

    def font_library_index(self) -> dict[str, str]:
        fonts_dir = DATA_DIR / "fonts"
        index: dict[str, str] = {}
        if fonts_dir.exists():
            for path in fonts_dir.iterdir():
                if not path.is_file() or path.suffix.lower() not in FONT_EXTENSIONS:
                    continue
                resolved = str(path.resolve())
                keys = {
                    path.name,
                    path.stem,
                    normalize_font_key(path.name),
                    normalize_font_key(path.stem),
                }
                for key in keys:
                    if key:
                        index[str(key)] = resolved
        return index

    def resolve_font_reference(self, value: Any, font_index: dict[str, str]) -> str:
        raw = str(value or "").strip()
        if not raw:
            return ""
        if raw.startswith("/data/"):
            candidate = DATA_DIR / raw[len("/data/"):]
            if candidate.exists() and candidate.is_file():
                return str(candidate.resolve())
        candidate = Path(raw)
        if candidate.is_absolute() and candidate.exists() and candidate.is_file():
            return str(candidate.resolve())
        if not candidate.is_absolute():
            direct = DATA_DIR / "fonts" / raw
            if direct.exists() and direct.is_file():
                return str(direct.resolve())
        for key in (raw, normalize_font_key(raw), Path(raw).name, Path(raw).stem, normalize_font_key(Path(raw).stem)):
            resolved = font_index.get(str(key))
            if resolved:
                return resolved
        normalized = normalize_font_key(raw)
        return (
            download_builtin_font(normalized)
            or first_existing_path(BUILTIN_FONT_FALLBACKS.get(normalized, []))
        )

    def build_font_paths(self) -> dict[str, str]:
        font_index = self.font_library_index()
        main_title = (
            self.resolve_font_reference(self.config.get("main_title_font_custom"), font_index)
            or self.resolve_font_reference(self.config.get("main_title_font_path"), font_index)
            or self.resolve_font_reference(self.config.get("main_title_font_preset") or "chaohei", font_index)
            or first_existing_path(BUILTIN_FONT_FALLBACKS["chaohei"])
        )
        subtitle = (
            self.resolve_font_reference(self.config.get("subtitle_font_custom"), font_index)
            or self.resolve_font_reference(self.config.get("subtitle_font_path"), font_index)
            or self.resolve_font_reference(self.config.get("subtitle_font_preset") or "EmblemaOne", font_index)
            or main_title
        )
        custom_text = (
            self.resolve_font_reference(self.config.get("custom_text_font_custom"), font_index)
            or self.resolve_font_reference(self.config.get("custom_text_font_path"), font_index)
            or self.resolve_font_reference(self.config.get("custom_text_font_preset") or self.config.get("subtitle_font_preset") or "EmblemaOne", font_index)
            or subtitle
            or main_title
        )
        font_paths = {
            "main_title": main_title,
            "subtitle": subtitle,
            "custom_text": custom_text,
        }
        for key, value in font_index.items():
            font_paths[key] = value
        for key in BUILTIN_FONT_FALLBACKS:
            resolved = self.resolve_font_reference(key, font_index)
            if resolved:
                font_paths[key] = resolved
        return {key: value for key, value in font_paths.items() if value}

    def render_config(self, style_config: dict[str, Any], library_name: str, style_name: str) -> dict[str, Any]:
        config = dict(style_config)
        if style_name.startswith("animated_"):
            animated_settings = self.config.get("animated_settings") if isinstance(self.config.get("animated_settings"), dict) else {}
            specific_settings = animated_settings.get(style_name) if isinstance(animated_settings.get(style_name), dict) else {}
            for key in (
                "animation_duration",
                "animation_fps",
                "animation_format",
                "animation_scroll",
                "animation_resolution",
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
            ):
                if key in self.config and self.config[key] not in (None, ""):
                    config[key] = self.config[key]
                if key in specific_settings and specific_settings[key] not in (None, ""):
                    config[key] = specific_settings[key]
            if "blur_size" in config:
                config["blur"] = config["blur_size"]
            if "main_title_font_size" in config:
                config["main_font_size"] = config["main_title_font_size"]
        _title, _subtitle, custom_texts = library_title_payload(self.config, library_name)
        config["custom_texts"] = custom_texts
        config["font_paths"] = self.build_font_paths()
        config.setdefault("font", config["font_paths"].get("main_title", ""))
        if style_name == "custom_static":
            layout = self.config.get("custom_static_layout")
            if not isinstance(layout, dict):
                active_id = self.config.get("custom_static_active_id")
                for template in self.config.get("custom_static_layouts") or []:
                    if isinstance(template, dict) and str(template.get("id") or "") == str(active_id or "") and isinstance(template.get("layout"), dict):
                        layout = template.get("layout")
                        break
            if isinstance(layout, dict):
                config["custom_static_layout"] = layout
        return config

    def output_suffix(self, style_config: dict[str, Any], style_name: str = "") -> str:
        if str(style_name or "").startswith("animated_"):
            animation_format = str(style_config.get("animation_format") or self.config.get("animation_format") or "apng").lower()
            return ".gif" if animation_format == "gif" else ".png"
        output_format = str(style_config.get("output_format") or "").lower()
        return ".png" if output_format == "png" else ".jpg"

    def image_limit_for_style(self, style_config: dict[str, Any], style_name: str) -> int:
        if style_name.startswith("animated_"):
            animated_settings = self.config.get("animated_settings") if isinstance(self.config.get("animated_settings"), dict) else {}
            specific_settings = animated_settings.get(style_name) if isinstance(animated_settings.get(style_name), dict) else {}
            raw_limit = specific_settings.get("animated_2_image_count", self.config.get("animated_2_image_count", style_config.get("image_limit", 9)))
            return max(1, min(60, int(raw_limit or 9)))
        return max(1, min(60, int(style_config.get("image_limit") or 9)))

    async def libraries(self) -> list[dict[str, Any]]:
        if self.local_mode():
            return self.local_libraries()
        if self.mock_enabled():
            return [dict(item) for item in MOCK_LIBRARIES]
        result: list[dict[str, Any]] = []
        for client in self.clients():
            for library in await client.get_libraries():
                result.append(library.__dict__)
        return result

    async def find_library(self, library_name: str) -> tuple[MediaServerClient, MediaLibrary]:
        for client in self.clients():
            for library in await client.get_libraries():
                if library.name == library_name or library.id == library_name:
                    return client, library
        raise ValueError(f"Library not found: {library_name}")

    async def generate(self, library_name: str | None = None, style: str | None = None) -> list[dict[str, Any]]:
        if self.local_mode():
            if library_name:
                return [await self.generate_local_library(library_name, style)]
            libraries = self.local_libraries()
            if libraries:
                return [await self.generate_local_library(str(library["name"]), style) for library in libraries]
            return [await self.generate_from_local(style)]

        if self.mock_enabled():
            if library_name:
                library = mock_library_by_name(library_name)
                if not library:
                    raise ValueError(f"Mock library not found: {library_name}")
                return [await self.generate_mock_library(library, style)]
            return [await self.generate_mock_library(library, style) for library in MOCK_LIBRARIES]

        if library_name:
            client, library = await self.find_library(library_name)
            return [await self.generate_library(client, library, style)]

        libraries = await self.libraries()
        if libraries:
            output = []
            for library_info in libraries:
                client, library = await self.find_library(library_info["name"])
                output.append(await self.generate_library(client, library, style))
            return output

        return [await self.generate_from_local(style)]

    async def generate_library(self, client: MediaServerClient, library: MediaLibrary, style: str | None = None) -> dict[str, Any]:
        style_config = dict(self.config.get("style_config") or {})
        style_name = style or style_config.get("style") or "single_1"
        image_limit = self.image_limit_for_style(style_config, style_name)
        image_source = str(style_config.get("image_source") or "backdrop")

        output_dir = resolve_data_path(self.config.get("covers_output"), "/app/data/output")
        media_cache_dir = DATA_DIR / "tmp" / "media_cache" / slugify(library.name)
        media_cache_dir.mkdir(parents=True, exist_ok=True)

        image_paths: list[Path] = self.local_images(library.name, image_limit, include_mock=False)
        sort_by = str(style_config.get("sort_by") or self.config.get("sort_by") or "DateCreated")
        if len(image_paths) < image_limit:
            items = await client.get_items(library.id, image_limit, sort_by)
            used_paths = {path.resolve() for path in image_paths if path.exists()}
            start_index = len(image_paths)
            for index, item in enumerate(items, start=start_index + 1):
                if len(image_paths) >= image_limit:
                    break
                image_url = client.item_image_url(item, image_source)
                if not image_url:
                    continue
                path = media_cache_dir / f"{index:02d}.jpg"
                try:
                    downloaded = await client.download_image(image_url, path)
                except Exception:
                    continue
                resolved = downloaded.resolve()
                if resolved in used_paths:
                    continue
                used_paths.add(resolved)
                image_paths.append(downloaded)
        if not image_paths:
            raise ValueError(f"No image sources available for {library.name}")

        title, subtitle = title_for_library(self.config, library.name)
        render_config = self.render_config(style_config, library.name, style_name)
        output_path = output_dir / f"{slugify(library.name)}_{style_name}{self.output_suffix(render_config, style_name)}"
        self.renderer().render(image_paths, title, subtitle, style_name, render_config, output_path)
        uploaded = False
        upload_error = ""
        if bool(self.config.get("upload_after_generate", True)):
            try:
                result = await client.upload_library_cover(library.id, output_path)
                uploaded = bool(result.get("uploaded", True))
            except Exception as exc:
                upload_error = str(exc)
        record_history_item({
            "path": str(output_path),
            "library": library.name,
            "library_id": library.id,
            "server": client.server_name,
            "style": style_name,
            "uploaded": uploaded,
            "upload_error": upload_error,
            "source_count": len(image_paths),
            "created_at": output_path.stat().st_mtime,
            "size": output_path.stat().st_size,
        })
        return {
            "library": library.name,
            "library_id": library.id,
            "server": client.server_name,
            "style": style_name,
            "output": str(output_path),
            "url": f"/data/output/{output_path.name}",
            "source_count": len(image_paths),
            "uploaded": uploaded,
            "upload_error": upload_error,
        }

    async def generate_from_local(self, style: str | None = None) -> dict[str, Any]:
        style_config = dict(self.config.get("style_config") or {})
        style_name = style or style_config.get("style") or "single_1"
        output_dir = resolve_data_path(self.config.get("covers_output"), "/app/data/output")
        image_paths = self.local_images("", self.image_limit_for_style(style_config, style_name))
        if not image_paths:
            raise ValueError("本地图片模式未找到素材，请将图片放入 /app/data/input 或 /app/data/input/媒体库名")
        render_config = self.render_config(style_config, "本地封面", style_name)
        output_path = output_dir / f"local_{style_name}{self.output_suffix(render_config, style_name)}"
        self.renderer().render(image_paths, "本地封面", "Local Library", style_name, render_config, output_path)
        record_history_item({
            "path": str(output_path),
            "library": "本地封面",
            "library_id": "",
            "server": "local",
            "style": style_name,
            "uploaded": False,
            "source_count": len(image_paths),
            "created_at": output_path.stat().st_mtime,
            "size": output_path.stat().st_size,
        })
        return {
            "library": "local",
            "library_id": "",
            "server": "local",
            "style": style_name,
            "output": str(output_path),
            "url": f"/data/output/{output_path.name}",
            "source_count": len(image_paths),
            "uploaded": False,
        }

    async def generate_local_library(self, library_name: str, style: str | None = None) -> dict[str, Any]:
        style_config = dict(self.config.get("style_config") or {})
        style_name = style or style_config.get("style") or "single_1"
        output_dir = resolve_data_path(self.config.get("covers_output"), "/app/data/output")
        image_limit = self.image_limit_for_style(style_config, style_name)
        image_paths = self.local_images(library_name, image_limit, include_mock=False)
        if not image_paths:
            raise ValueError(f"本地媒体库没有可用图片: {library_name}")
        title, subtitle = title_for_library(self.config, library_name)
        render_config = self.render_config(style_config, library_name, style_name)
        output_path = output_dir / f"{slugify(library_name)}_{style_name}{self.output_suffix(render_config, style_name)}"
        self.renderer().render(image_paths, title, subtitle, style_name, render_config, output_path)
        record_history_item({
            "path": str(output_path),
            "library": library_name,
            "library_id": slugify(library_name),
            "server": "local",
            "style": style_name,
            "uploaded": False,
            "source_count": len(image_paths),
            "created_at": output_path.stat().st_mtime,
            "size": output_path.stat().st_size,
        })
        return {
            "library": library_name,
            "library_id": slugify(library_name),
            "server": "local",
            "style": style_name,
            "output": str(output_path),
            "url": f"/data/output/{output_path.name}",
            "source_count": len(image_paths),
            "uploaded": False,
        }

    def local_images(self, library_name: str = "", limit: int = 9, include_mock: bool = True) -> list[Path]:
        input_dir = resolve_data_path(self.config.get("covers_input"), "/app/data/input")
        roots: list[Path] = []
        if library_name:
            exact_root = input_dir / str(library_name)
            slug_root = input_dir / slugify(library_name)
            roots.extend([exact_root])
            if slug_root != exact_root:
                roots.append(slug_root)
        roots.append(input_dir)
        paths: list[Path] = []
        for root in roots:
            if not root.exists():
                continue
            for path in sorted(root.iterdir(), key=lambda item: item.name):
                if not include_mock and path.name.lower().startswith("mock_"):
                    continue
                if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS and path not in paths:
                    paths.append(path)
                if len(paths) >= limit:
                    return paths
        return paths

    def local_libraries(self) -> list[dict[str, Any]]:
        input_dir = resolve_data_path(self.config.get("covers_input"), "/app/data/input")
        libraries: list[dict[str, Any]] = []
        if not input_dir.exists():
            return libraries
        for child in sorted(input_dir.iterdir(), key=lambda item: item.name):
            if not child.is_dir():
                continue
            images = [
                path
                for path in child.iterdir()
                if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS and not path.name.lower().startswith("mock_")
            ]
            if images:
                libraries.append({
                    "id": slugify(child.name),
                    "name": child.name,
                    "server": "local",
                    "type": "local",
                    "image_count": len(images),
                })
        root_images = [
            path
            for path in input_dir.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS and not path.name.lower().startswith("mock_")
        ]
        if root_images:
            libraries.insert(0, {
                "id": "local",
                "name": "本地封面",
                "server": "local",
                "type": "local",
                "image_count": len(root_images),
            })
        return libraries

    async def upload(self, library_name: str) -> dict[str, Any]:
        if self.local_mode():
            output_dir = resolve_data_path(self.config.get("covers_output"), "/app/data/output")
            lookup_name = "本地封面" if library_name in {"local", "本地封面", ""} else library_name
            image_path = self.latest_output_for_library(output_dir, lookup_name)
            if image_path is None:
                generated = await self.generate(lookup_name if lookup_name != "本地封面" else None)
                image_path = Path(generated[0]["output"])
            return {
                "library": lookup_name,
                "local_mode": True,
                "uploaded": False,
                "image": str(image_path),
            }
        if self.mock_enabled():
            output_dir = resolve_data_path(self.config.get("covers_output"), "/app/data/output")
            image_path = self.latest_output_for_library(output_dir, library_name)
            if image_path is None:
                generated = await self.generate(library_name)
                image_path = Path(generated[0]["output"])
            return {"library": library_name, "mock": True, "uploaded": False, "image": str(image_path)}
        client, library = await self.find_library(library_name)
        output_dir = resolve_data_path(self.config.get("covers_output"), "/app/data/output")
        image_path = self.latest_output_for_library(output_dir, library.name)
        if image_path is None:
            generated = await self.generate_library(client, library)
            image_path = Path(generated["output"])
        result = await client.upload_library_cover(library.id, image_path)
        return {"library": library.name, "image": str(image_path), **result}

    def latest_output_for_library(self, output_dir: Path, library_name: str) -> Path | None:
        candidates = sorted(
            [
                path for path in output_dir.glob(f"{slugify(library_name)}_*.*")
                if path.suffix.lower() in OUTPUT_EXTENSIONS
            ],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return candidates[0] if candidates else None

    async def generate_mock_library(self, library: dict[str, Any], style: str | None = None) -> dict[str, Any]:
        style_config = dict(self.config.get("style_config") or {})
        style_name = style or style_config.get("style") or "single_1"
        image_limit = self.image_limit_for_style(style_config, style_name)
        input_dir = resolve_data_path(self.config.get("covers_input"), "/app/data/input")
        output_dir = resolve_data_path(self.config.get("covers_output"), "/app/data/output")
        title, subtitle = title_for_library(self.config, library["name"])
        image_paths = ensure_mock_images(input_dir, slugify(library["name"]), title, image_limit)
        render_config = self.render_config(style_config, library["name"], style_name)
        output_path = output_dir / f"{slugify(library['name'])}_{style_name}{self.output_suffix(render_config, style_name)}"
        self.renderer().render(image_paths, title, subtitle or "Mock Library", style_name, render_config, output_path)
        record_history_item({
            "path": str(output_path),
            "library": library["name"],
            "library_id": library["id"],
            "server": "mock",
            "style": style_name,
            "uploaded": False,
            "source_count": len(image_paths),
            "created_at": output_path.stat().st_mtime,
            "size": output_path.stat().st_size,
        })
        return {
            "library": library["name"],
            "library_id": library["id"],
            "server": "mock",
            "style": style_name,
            "output": str(output_path),
            "url": f"/data/output/{output_path.name}",
            "source_count": len(image_paths),
            "uploaded": False,
        }
