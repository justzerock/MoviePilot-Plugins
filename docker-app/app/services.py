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
from .run_logs import APP_LOGGER
from .history_store import HistoryBatch, HistoryStore
from .font_preview import PreviewFontService


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
OUTPUT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
FONT_EXTENSIONS = {".ttf", ".ttc", ".otf", ".woff", ".woff2"}
BUNDLED_FONTS_DIR = Path(__file__).parent / "bundled_fonts"
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


def library_title_payload(config: dict[str, Any], library_name: str, server_name: str = "") -> tuple[str, str, dict[str, str]]:
    title_config = config.get("title_config") or {}
    if isinstance(title_config, str):
        title_config = {}
    raw = title_config.get(library_name) or {}
    if bool(config.get("distinguish_same_name_libraries", False)) and server_name:
        normalized_server = re.sub(r"[^\w\u4e00-\u9fff]+", "", server_name, flags=re.UNICODE).casefold()
        normalized_library = re.sub(r"[^\w\u4e00-\u9fff]+", "", library_name, flags=re.UNICODE).casefold()
        for key, value in title_config.items():
            normalized_key = re.sub(r"[^\w\u4e00-\u9fff]+", "", str(key), flags=re.UNICODE).casefold()
            if normalized_server in normalized_key and normalized_library in normalized_key:
                raw = value
                break
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
        self.history_batch: HistoryBatch | None = None
        self.preview_fonts = PreviewFontService(DATA_DIR, APP_LOGGER)
        self._preview_font_paths: set[str] = set()

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

    def input_directory(self) -> Path | None:
        """Return an explicit local source directory, if this mode has one.

        Server mode intentionally has no implicit input directory. Previously the
        default /app/data/input also held downloaded preview cache files, so an
        empty custom-directory field silently became a local image source.
        """
        configured = str(self.config.get("covers_input") or "").strip()
        if configured:
            return resolve_data_path(configured, "/app/data/input")
        if self.local_mode() or self.mock_enabled():
            return resolve_data_path(None, "/app/data/input")
        return None

    def renderer(self) -> CoverRenderer:
        return CoverRenderer(DATA_DIR / "fonts")

    def begin_history_batch(self, trigger: str) -> HistoryBatch | None:
        if not bool(self.config.get("history_enabled", True)):
            return None
        store = HistoryStore(DATA_DIR)
        store.migrate_legacy(resolve_data_path(self.config.get("covers_output"), "/app/data/output"))
        self.history_batch = store.create_history_batch(trigger, "local" if self.local_mode() else ("mock" if self.mock_enabled() else "remote"))
        return self.history_batch

    def finalize_history_batch(self, status: str) -> dict[str, Any] | None:
        batch, self.history_batch = self.history_batch, None
        if not batch:
            return None
        store = HistoryStore(DATA_DIR)
        manifest = store.finalize_history_batch(batch, status)
        store.cleanup_history(int(self.config.get("history_retention_batches") or 30))
        return manifest

    def record_batch_result(self, result: dict[str, Any], server_id: str, server_name: str, server_type: str, library_id: str, library_name: str) -> None:
        if result.get("skipped"):
            return
        if self.history_batch:
            item = self.history_batch.add_result(result, server_id=server_id, server_name=server_name, server_type=server_type, library_id=library_id, library_name=library_name)
            result["history_batch_id"] = self.history_batch.batch_id
            result["history_file"] = item.get("file")

    def font_library_index(self) -> dict[str, str]:
        fonts_dir = DATA_DIR / "fonts"
        index: dict[str, str] = {}
        for source_dir in (BUNDLED_FONTS_DIR, fonts_dir):
            if not source_dir.exists():
                continue
            for path in source_dir.rglob("*"):
                if not path.is_file() or path.suffix.lower() not in FONT_EXTENSIONS:
                    continue
                if "subsets" in path.parts:
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
                if Path(resolved).suffix.lower() in {".woff", ".woff2"}:
                    converted = download_builtin_font(normalize_font_key(raw))
                    if converted:
                        return converted
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

    def preview_font_assets(self, paths: list[str] | None = None) -> dict[str, dict[str, Any]]:
        selected = paths or list(self._preview_font_paths)
        if not selected:
            semantic = self.build_font_paths()
            selected = [semantic.get(key, "") for key in ("main_title", "subtitle", "custom_text")]
        return self.preview_fonts.assets([Path(value) for value in set(selected) if value])

    def preview_font_info(self, font_id: str) -> dict[str, Any] | None:
        return self.preview_fonts.info(
            font_id,
            self.preview_font_assets(),
            self.config,
            lambda asset_id, variant, version: f"/api/fonts/{asset_id}/file?variant={variant}&v={version}",
        )

    def preview_font_file(self, font_id: str, variant: str, version: str) -> tuple[Path, str, str] | None:
        return self.preview_fonts.file_for(font_id, variant, version, self.preview_font_assets())

    def preview_font_status(self, font_id: str) -> dict[str, Any] | None:
        return self.preview_fonts.status(font_id, self.preview_font_assets(), self.config)

    def preview_font_faces(self, layout: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
        if not bool(self.config.get("preview_font_enabled", True)):
            return {}
        paths = self.build_font_paths()
        aliases = {"main_title", "subtitle", "custom_text"}

        def visit(layers: list[Any]) -> None:
            for layer in layers:
                if not isinstance(layer, dict):
                    continue
                if str(layer.get("type") or "") == "group":
                    visit(layer.get("children") or [])
                    continue
                if str(layer.get("type") or "") in {"main_title", "title_zh", "subtitle", "title_en", "text"}:
                    aliases.add(str(layer.get("fontFamily") or ("subtitle" if layer.get("type") in {"subtitle", "title_en"} else "custom_text" if layer.get("type") == "text" else "main_title")))

        if isinstance(layout, dict):
            visit(layout.get("layers") or [])
        selected_paths = [paths.get(alias) or self.resolve_font_reference(alias, self.font_library_index()) for alias in aliases]
        self._preview_font_paths.update(str(path) for path in selected_paths if path)
        assets = self.preview_font_assets(selected_paths)
        path_to_id = {str(item["path"]): asset_id for asset_id, item in assets.items()}
        faces: dict[str, dict[str, Any]] = {}
        # Preview surfaces only need the three semantic fonts.  Loading the
        # complete custom-font library here used to create many redundant
        # FontFace requests before a user even selected a text layer.
        for alias in aliases:
            path = paths.get(alias) or self.resolve_font_reference(alias, self.font_library_index())
            if not path:
                continue
            info = self.preview_font_info(path_to_id.get(str(Path(path).resolve()), ""))
            if info and info.get("url"):
                faces[alias] = info
        return faces

    def scheme_catalog(self) -> list[dict[str, str]]:
        entries = [
            {"id": "single_1", "name": "风格 1"},
            {"id": "single_2", "name": "风格 2"},
            {"id": "multi_1", "name": "风格 3"},
            {"id": "static_4", "name": "风格 4"},
            {"id": "animated_1", "name": "动态风格 1"},
            {"id": "animated_2", "name": "动态风格 2"},
            {"id": "animated_3", "name": "动态风格 3"},
            {"id": "animated_4", "name": "动态风格 4"},
        ]
        for template in self.config.get("custom_static_layouts") or []:
            if isinstance(template, dict) and str(template.get("id") or "").strip():
                entries.append({"id": str(template["id"]), "name": str(template.get("name") or "自定义方案")})
        return entries

    def resolve_scheme_for_library(self, library_key: str) -> str:
        for rule in self.config.get("library_scheme_rules") or []:
            if isinstance(rule, dict) and library_key in {str(value) for value in (rule.get("library_keys") or [])}:
                return str(rule.get("scheme_id") or "")
        return str(self.config.get("default_scheme_id") or (self.config.get("style_config") or {}).get("style") or "single_1")

    def scheme_style_and_layout(self, scheme_id: str) -> tuple[str, dict[str, Any] | None]:
        for template in self.config.get("custom_static_layouts") or []:
            if isinstance(template, dict) and str(template.get("id") or "") == scheme_id and isinstance(template.get("layout"), dict):
                return "custom_static", template["layout"]
        known = {item["id"] for item in self.scheme_catalog()}
        return (scheme_id if scheme_id in known else str((self.config.get("style_config") or {}).get("style") or "single_1")), None

    def render_config(self, style_config: dict[str, Any], library_name: str, style_name: str, server_name: str = "", custom_layout: dict[str, Any] | None = None) -> dict[str, Any]:
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
        _title, _subtitle, custom_texts = library_title_payload(self.config, library_name, server_name)
        config["custom_texts"] = custom_texts
        config["font_paths"] = self.build_font_paths()
        config.setdefault("font", config["font_paths"].get("main_title", ""))
        if style_name == "custom_static":
            layout = custom_layout or self.config.get("custom_static_layout")
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
        selected_servers = {
            str(value).strip()
            for value in (self.config.get("selected_servers") or [])
            if str(value).strip()
        }
        for client in self.clients():
            # Filter before making the network request. A configured but
            # unselected server must never be able to break this run.
            if selected_servers and client.server_id not in selected_servers:
                continue
            try:
                libraries = await client.get_libraries()
            except Exception as error:
                APP_LOGGER.warning(
                    "读取媒体库失败，已跳过服务器 server=%s server_id=%s: %s",
                    client.server_name,
                    client.server_id,
                    error,
                )
                continue
            for library in libraries:
                item = library.__dict__.copy()
                item["server_id"] = client.server_id
                item["server_name"] = client.server_name
                item["value"] = f"{client.server_id}:{library.id}"
                result.append(item)
        return result

    def selected_generation_libraries(self, libraries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        selected_servers = {str(item) for item in (self.config.get("selected_servers") or []) if str(item)}
        selected_libraries = {str(item) for item in (self.config.get("include_libraries") or []) if str(item)}
        available_values = {
            str(library.get("value") or f"{library.get('server_id') or library.get('server')}:{library.get('id')}")
            for library in libraries
        }
        missing = selected_libraries - available_values
        if missing:
            APP_LOGGER.warning("已忽略不存在的媒体库范围: %s", ", ".join(sorted(missing)))
        return [
            library for library in libraries
            if (not selected_servers or str(library.get("server_id") or library.get("server") or "") in selected_servers)
            and (not selected_libraries or str(library.get("value") or f"{library.get('server_id') or library.get('server')}:{library.get('id')}") in selected_libraries)
        ]

    async def find_library(self, library_name: str) -> tuple[MediaServerClient, MediaLibrary]:
        selected_servers = {
            str(value).strip()
            for value in (self.config.get("selected_servers") or [])
            if str(value).strip()
        }
        for client in self.clients():
            if selected_servers and client.server_id not in selected_servers:
                continue
            try:
                libraries = await client.get_libraries()
            except Exception as error:
                APP_LOGGER.warning(
                    "查找媒体库时跳过不可用服务器 server=%s server_id=%s: %s",
                    client.server_name,
                    client.server_id,
                    error,
                )
                continue
            for library in libraries:
                if library.name == library_name or library.id == library_name or f"{client.server_id}:{library.id}" == library_name:
                    return client, library
        raise ValueError(f"Library not found: {library_name}")

    async def generate(self, library_name: str | None = None, style: str | None = None, trigger: str = "manual") -> list[dict[str, Any]]:
        if self.local_mode():
            if library_name:
                local_libraries = self.local_libraries()
                selected = self.selected_generation_libraries(local_libraries)
                target = next(
                    (
                        library for library in local_libraries
                        if str(library.get("value")) == str(library_name)
                        or str(library.get("id")) == str(library_name)
                        or str(library.get("name")) == str(library_name)
                    ),
                    None,
                )
                if target is None:
                    raise ValueError(f"本地媒体库不存在: {library_name}")
                has_explicit_scope = bool(self.config.get("include_libraries"))
                if has_explicit_scope and str(target.get("value")) not in {str(item.get("value")) for item in selected}:
                    raise ValueError(f"本地媒体库不在当前生成范围内: {target.get('name')}")
                return [await self.generate_local_library(str(target["name"]), style)]
            libraries = self.selected_generation_libraries(self.local_libraries())
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
            return [await self.generate_library(client, library, style, trigger=trigger)]

        libraries = self.selected_generation_libraries(await self.libraries())
        if libraries:
            output = []
            for library_info in libraries:
                client, library = await self.find_library(str(library_info.get("value") or library_info["name"]))
                output.append(await self.generate_library(client, library, style, trigger=trigger))
            return output

        return [await self.generate_from_local(style)]

    async def generate_library(self, client: MediaServerClient, library: MediaLibrary, style: str | None = None, trigger: str = "manual") -> dict[str, Any]:
        style_config = dict(self.config.get("style_config") or {})
        library_key = f"{client.server_id}:{library.id}"
        scheme_id = self.resolve_scheme_for_library(library_key)
        style_name, scheme_layout = self.scheme_style_and_layout(scheme_id)
        image_limit = self.image_limit_for_style(style_config, style_name)
        image_source = str(style_config.get("image_source") or "backdrop")

        output_dir = resolve_data_path(self.config.get("covers_output"), "/app/data/output")
        media_cache_dir = DATA_DIR / "tmp" / "media_cache" / slugify(library.name)
        media_cache_dir.mkdir(parents=True, exist_ok=True)

        image_paths: list[Path] = self.local_images(library.name, image_limit, include_mock=False)
        # A monitor run always reflects the newest scanned item. Manual and
        # scheduled runs intentionally keep the user's configured sort order.
        sort_by = "DateCreated" if trigger == "monitor" else str(style_config.get("sort_by") or self.config.get("sort_by") or "DateCreated")
        source_item_id = ""
        if len(image_paths) < image_limit:
            items = await client.get_items(library.id, image_limit, sort_by)
            download_jobs: list[tuple[str, Path]] = []
            for index, item in enumerate(items, start=1):
                image_url = client.item_image_url(item, image_source)
                if not image_url:
                    continue
                if not source_item_id:
                    source_item_id = str(item.get("Id") or item.get("ItemId") or "").strip()
                download_jobs.append((image_url, media_cache_dir / f"{index:02d}.jpg"))
                if len(download_jobs) >= image_limit:
                    break
            if trigger == "monitor" and source_item_id:
                previous_item_id = HistoryStore(DATA_DIR).latest_source_item_id(client.server_id, library.id)
                if previous_item_id == source_item_id:
                    APP_LOGGER.info(
                        "监控跳过未变化媒体库 server=%s library=%s source_item_id=%s",
                        client.server_name,
                        library.name,
                        source_item_id,
                    )
                    return {
                        "library": library.name,
                        "library_id": library.id,
                        "server": client.server_name,
                        "style": style_name,
                        "skipped": True,
                        "skip_reason": "latest_item_unchanged",
                        "source_item_id": source_item_id,
                    }
            used_paths = {path.resolve() for path in image_paths if path.exists()}
            start_index = len(image_paths)
            for index, (image_url, downloaded_path) in enumerate(download_jobs, start=start_index + 1):
                if len(image_paths) >= image_limit:
                    break
                path = media_cache_dir / f"{index:02d}.jpg"
                try:
                    downloaded = await client.download_image(image_url, path)
                except Exception as error:
                    APP_LOGGER.warning("图片下载失败 library=%s index=%s: %s", library.name, index, error)
                    continue
                resolved = downloaded.resolve()
                if resolved in used_paths:
                    continue
                used_paths.add(resolved)
                image_paths.append(downloaded)
        if not image_paths:
            raise ValueError(f"No image sources available for {library.name}")

        title, subtitle, _texts = library_title_payload(self.config, library.name, client.server_name)
        render_config = self.render_config(style_config, library.name, style_name, client.server_name, scheme_layout)
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
                APP_LOGGER.warning("媒体库封面更新失败 server=%s library=%s: %s", client.server_name, library.name, exc)
        result = {
            "library": library.name,
            "library_id": library.id,
            "server": client.server_name,
            "style": style_name,
            "scheme_id": scheme_id,
            "output": str(output_path),
            "url": f"/data/output/{output_path.name}",
            "source_count": len(image_paths),
            "source_item_id": source_item_id,
            "uploaded": uploaded,
            "upload_error": upload_error,
        }
        self.record_batch_result(result, client.server_id, client.server_name, client.kind, library.id, library.name)
        return result

    async def generate_from_local(self, style: str | None = None) -> dict[str, Any]:
        style_config = dict(self.config.get("style_config") or {})
        scheme_id = self.resolve_scheme_for_library("local:local")
        style_name, scheme_layout = self.scheme_style_and_layout(scheme_id)
        output_dir = resolve_data_path(self.config.get("covers_output"), "/app/data/output")
        image_paths = self.local_images("", self.image_limit_for_style(style_config, style_name))
        if not image_paths:
            raise ValueError("本地图片模式未找到素材，请将图片放入 /app/data/input 或 /app/data/input/媒体库名")
        render_config = self.render_config(style_config, "本地封面", style_name, custom_layout=scheme_layout)
        output_path = output_dir / f"local_{style_name}{self.output_suffix(render_config, style_name)}"
        self.renderer().render(image_paths, "本地封面", "Local Library", style_name, render_config, output_path)
        result = {
            "library": "local",
            "library_id": "",
            "server": "local",
            "style": style_name,
            "scheme_id": scheme_id,
            "output": str(output_path),
            "url": f"/data/output/{output_path.name}",
            "source_count": len(image_paths),
            "uploaded": False,
        }
        self.record_batch_result(result, "local", "本地", "local", "local", "本地封面")
        return result

    async def generate_local_library(self, library_name: str, style: str | None = None) -> dict[str, Any]:
        style_config = dict(self.config.get("style_config") or {})
        scheme_id = self.resolve_scheme_for_library(f"local:{slugify(library_name)}")
        style_name, scheme_layout = self.scheme_style_and_layout(scheme_id)
        output_dir = resolve_data_path(self.config.get("covers_output"), "/app/data/output")
        image_limit = self.image_limit_for_style(style_config, style_name)
        image_paths = self.local_images(library_name, image_limit, include_mock=False)
        if not image_paths:
            raise ValueError(f"本地媒体库没有可用图片: {library_name}")
        title, subtitle = title_for_library(self.config, library_name)
        render_config = self.render_config(style_config, library_name, style_name, custom_layout=scheme_layout)
        output_path = output_dir / f"{slugify(library_name)}_{style_name}{self.output_suffix(render_config, style_name)}"
        self.renderer().render(image_paths, title, subtitle, style_name, render_config, output_path)
        result = {
            "library": library_name,
            "library_id": slugify(library_name),
            "server": "local",
            "style": style_name,
            "scheme_id": scheme_id,
            "output": str(output_path),
            "url": f"/data/output/{output_path.name}",
            "source_count": len(image_paths),
            "uploaded": False,
        }
        self.record_batch_result(result, "local", "本地", "local", slugify(library_name), library_name)
        return result

    def local_images(self, library_name: str = "", limit: int = 9, include_mock: bool = True) -> list[Path]:
        input_dir = self.input_directory()
        if input_dir is None:
            return []
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
        input_dir = self.input_directory()
        libraries: list[dict[str, Any]] = []
        if input_dir is None or not input_dir.exists():
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
                    "server_id": "local",
                    "type": "local",
                    "value": f"local:{slugify(child.name)}",
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
                "server_id": "local",
                "type": "local",
                "value": "local:local",
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
        scheme_id = self.resolve_scheme_for_library(f"mock:{library.get('id') or library.get('name')}")
        style_name, scheme_layout = self.scheme_style_and_layout(scheme_id)
        image_limit = self.image_limit_for_style(style_config, style_name)
        input_dir = self.input_directory() or resolve_data_path(None, "/app/data/input")
        output_dir = resolve_data_path(self.config.get("covers_output"), "/app/data/output")
        title, subtitle = title_for_library(self.config, library["name"])
        image_paths = ensure_mock_images(input_dir, slugify(library["name"]), title, image_limit)
        render_config = self.render_config(style_config, library["name"], style_name, custom_layout=scheme_layout)
        output_path = output_dir / f"{slugify(library['name'])}_{style_name}{self.output_suffix(render_config, style_name)}"
        self.renderer().render(image_paths, title, subtitle or "Mock Library", style_name, render_config, output_path)
        result = {
            "library": library["name"],
            "library_id": library["id"],
            "server": "mock",
            "style": style_name,
            "scheme_id": scheme_id,
            "output": str(output_path),
            "url": f"/data/output/{output_path.name}",
            "source_count": len(image_paths),
            "uploaded": False,
        }
        self.record_batch_result(result, "mock", "测试模式", "mock", library["id"], library["name"])
        return result
