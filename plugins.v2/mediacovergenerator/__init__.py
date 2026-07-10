import base64
import datetime
import hashlib
import mimetypes
import os
import re
import ast
import threading
import time
import shutil
import random
from pathlib import Path
from urllib.parse import urlparse, quote, unquote
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import pytz
import yaml

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app import schemas
from app.chain.mediaserver import MediaServerChain
from app.core.config import settings
from app.core.event import eventmanager, Event
from app.core.meta import MetaBase
from app.helper.mediaserver import MediaServerHelper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import MediaInfo, TransferInfo
from app.schemas.types import EventType
from app.schemas import ServiceInfo
from app.utils.http import RequestUtils
from app.utils.url import UrlUtils
from app.plugins.mediacovergenerator.style.style_static_1 import create_style_static_1
from app.plugins.mediacovergenerator.style.style_static_2 import create_style_static_2
from app.plugins.mediacovergenerator.style.style_static_3  import create_style_static_3
from app.plugins.mediacovergenerator.style.style_static_4 import create_style_static_4
from app.plugins.mediacovergenerator.style.style_animated_1 import create_style_animated_1
from app.plugins.mediacovergenerator.style.style_animated_2 import create_style_animated_2
from app.plugins.mediacovergenerator.style.style_animated_3 import create_style_animated_3
from app.plugins.mediacovergenerator.style.style_animated_4 import create_style_animated_4
from app.plugins.mediacovergenerator.utils.image_manager import ResolutionConfig, ImageResourceManager
from app.plugins.mediacovergenerator.utils.network_helper import NetworkHelper, validate_font_file
from app.plugins.mediacovergenerator.utils.performance_helper import PerformanceMonitor, ProgressTracker, memory_efficient_operation
from app.plugins.mediacovergenerator.utils.color_helper import ColorHelper


class MediaCoverGenerator(_PluginBase):
    # 插件名称
    plugin_name = "Emby媒体库封面生成"
    # 插件描述
    plugin_desc = "生成媒体库动态/静态封面，支持 Emby/Jellyfin"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/icons/emby.png"
    # 插件版本
    plugin_version = "0.9.6"
    # 插件作者
    plugin_author = "justzerock"
    # 作者主页
    author_url = "https://github.com/justzerock/MoviePilot-Plugins"
    # 插件配置项ID前缀
    plugin_config_prefix = "mediacovergenerator_"
    # 加载顺序
    plugin_order = 2
    # 可使用的用户级别
    auth_level = 1

    # 退出事件
    _event = threading.Event()

    # 私有属性
    _scheduler = None
    mschain = None
    mediaserver_helper = None
    _enabled = False
    _update_now = False
    _transfer_monitor = True
    _cron = None
    _delay = 60
    _servers = None
    _selected_servers = []
    _all_libraries = []
    _include_libraries = []
    _sort_by = 'Random'
    _monitor_sort = ''
    _current_updating_items = set()
    _covers_output = ''
    _covers_input = ''
    _zh_font_url = ''
    _en_font_url = ''
    _zh_font_path = ''
    _en_font_path = ''
    _title_config = ''
    _current_config = {}
    _cover_style = 'static_1'
    _cover_style_base = 'static_1'
    _cover_style_variant = 'static'
    _font_path = ''
    _covers_path = ''
    _tab = 'style-tab'
    _multi_1_blur = True
    _zh_font_size = None
    _en_font_size = None
    _blur_size = 50
    _color_ratio = 0.8
    _use_primary = False
    _seen_keys = set()
    _zh_font_custom = ''
    _en_font_custom = ''
    _zh_font_preset = 'chaohei'
    _en_font_preset = 'EmblemaOne'
    _zh_font_offset = ''
    _title_spacing = ''
    _en_line_spacing = ''
    _title_scale = 1.0
    _resolution = '480p'
    _custom_width = 1920
    _custom_height = 1080
    _resolution_config = None
    _animation_duration = 8
    _animation_scroll = 'alternate'
    _animation_fps = 24
    _animation_format = 'apng'
    _animation_resolution = '320x180'
    _animation_reduce_colors = 'medium'
    _animated_2_image_count = 6
    _animated_2_departure_type = 'fly'
    _style_naming_v2 = True
    _sanitize_log_cache = set()
    _clean_images = False
    _clean_fonts = False
    _save_recent_covers = True
    _covers_history_limit_per_library = 10
    _covers_page_history_limit = 50
    _page_tab = "generate-tab"

    def __init__(self):
        super().__init__()

    def init_plugin(self, config: dict = None):
        self.mschain = MediaServerChain()
        self.mediaserver_helper = MediaServerHelper()   
        data_path = self.get_data_path()
        (data_path / 'fonts').mkdir(parents=True, exist_ok=True)
        (data_path / 'input').mkdir(parents=True, exist_ok=True)
        self._covers_path = data_path / 'input'
        self._font_path = data_path / 'fonts'
        if config:
            self._enabled = config.get("enabled")
            self._update_now = config.get("update_now")
            self._transfer_monitor = config.get("transfer_monitor")
            self._cron = config.get("cron")
            self._delay = config.get("delay")
            self._selected_servers = config.get("selected_servers")
            self._include_libraries = config.get("include_libraries")
            self._sort_by = config.get("sort_by")
            self._covers_output = config.get("covers_output")
            self._covers_input = config.get("covers_input")
            # self._title_config = self.get_data('title_config')
            self._title_config = config.get("title_config")
            self._zh_font_url = config.get("zh_font_url")
            self._en_font_url = config.get("en_font_url")
            self._zh_font_path = config.get("zh_font_path")
            self._en_font_path = config.get("en_font_path")
            self._cover_style = config.get("cover_style", "static_1")

            # 样式命名升级兼容（仅对旧配置执行一次迁移）
            if not config.get("style_naming_v2"):
                if self._cover_style == 'single_1':
                    self._cover_style = 'static_1'
                elif self._cover_style == 'single_2':
                    self._cover_style = 'static_2'
                elif self._cover_style == 'multi_1':
                    self._cover_style = 'static_3'
            default_base, default_variant = self.__resolve_cover_style_ui(self._cover_style)
            self._cover_style_base = config.get("cover_style_base", default_base)
            self._cover_style_variant = config.get("cover_style_variant", default_variant)
            self._cover_style = self.__compose_cover_style(self._cover_style_base, self._cover_style_variant)
            self._multi_1_blur = config.get("multi_1_blur", True)
            self._zh_font_size = config.get("zh_font_size", 170)
            self._en_font_size = config.get("en_font_size", 75)
            try:
                self._blur_size = int(config.get("blur_size", 50))
            except (ValueError, TypeError):
                self._blur_size = 50
            try:
                self._color_ratio = float(config.get("color_ratio", 0.8))
            except (ValueError, TypeError):
                self._color_ratio = 0.8
            self._use_primary = config.get("use_primary")
            self._zh_font_custom = config.get("zh_font_custom", "")
            self._en_font_custom = config.get("en_font_custom", "")
            self._zh_font_preset = config.get("zh_font_preset", "chaohei")
            self._en_font_preset = config.get("en_font_preset", "EmblemaOne")
            self._zh_font_offset = config.get("zh_font_offset")
            self._title_spacing = config.get("title_spacing")
            self._en_line_spacing = config.get("en_line_spacing")
            try:
                self._title_scale = float(config.get("title_scale", 1.0))
            except (ValueError, TypeError):
                self._title_scale = 1.0
            self._resolution = config.get("resolution", "480p")
            self._custom_width = config.get("custom_width", 1920)
            self._custom_height = config.get("custom_height", 1080)
            try:
                self._animation_duration = int(config.get("animation_duration", 12))
            except (ValueError, TypeError):
                self._animation_duration = 12
            self._animation_scroll = config.get("animation_scroll", "alternate")
            try:
                self._animation_fps = int(config.get("animation_fps", 12))
            except (ValueError, TypeError):
                self._animation_fps = 12
            self._animation_format = config.get("animation_format", "apng")
            if self._animation_format == "webp":
                self._animation_format = "gif"
            if self._animation_format not in ["apng", "gif"]:
                self._animation_format = "apng"
            self._animation_resolution = config.get("animation_resolution", "320x180")
            animation_reduce_colors = config.get("animation_reduce_colors", "medium")
            if isinstance(animation_reduce_colors, bool):
                self._animation_reduce_colors = "medium" if animation_reduce_colors else "off"
            elif animation_reduce_colors in ["off", "medium", "strong"]:
                self._animation_reduce_colors = animation_reduce_colors
            else:
                self._animation_reduce_colors = "medium"

            self._animated_2_image_count = config.get("animated_2_image_count", 6)
            self._animated_2_departure_type = config.get("animated_2_departure_type", "fly")
            self._clean_images = config.get("clean_images", False)
            self._clean_fonts = config.get("clean_fonts", False)
            self._save_recent_covers = config.get("save_recent_covers", True)
            self._covers_history_limit_per_library = self.__clamp_value(
                config.get("covers_history_limit_per_library", 10),
                1,
                100,
                10,
                "covers_history_limit_per_library[init_plugin]",
                int,
            )
            self._covers_page_history_limit = self.__clamp_value(
                config.get("covers_page_history_limit", 50),
                1,
                500,
                50,
                "covers_page_history_limit[init_plugin]",
                int,
            )
            self._page_tab = config.get("page_tab", "generate-tab")

            if self._resolution not in ["1080p", "720p", "480p"]:
                self._resolution = "480p"
            self._animation_resolution = "320x180"

        self._animated_2_image_count = self.__clamp_value(
            self._animated_2_image_count,
            3,
            9,
            5,
            "animated_2 image_count[init_plugin]",
            int,
        )
        if self._animated_2_departure_type not in ["fly", "fade", "crossfade"]:
            self._animated_2_departure_type = "fly"
        if self._animation_scroll not in ["down", "up", "alternate", "alternate_reverse"]:
            self._animation_scroll = "alternate"
        self._bg_color_mode = (config or {}).get("bg_color_mode", "auto")
        self._custom_bg_color = (config or {}).get("custom_bg_color", "")

        # 初始化分辨率配置（确保安全初始化）
        try:
            self._resolution_config = ResolutionConfig(self._resolution)
        except Exception as e:
            logger.warning(f"分辨率配置初始化失败，使用默认配置: {e}")
            self._resolution_config = ResolutionConfig("480p")

        if self._selected_servers:
            self._servers = self.mediaserver_helper.get_services(
                name_filters=self._selected_servers
            )
            self._all_libraries = []
            for server, service in self._servers.items():
                if not service.instance.is_inactive():
                    self._all_libraries.extend(self.__get_all_libraries(server, service))
                else:
                    logger.info(f"媒体服务器 {server} 未连接")
        else:
            logger.info("未选择媒体服务器")
        
        # 停止现有任务
        self.stop_service()

        cleanup_triggered = False
        if self._clean_images:
            self.__clean_generated_images()
            self._clean_images = False
            cleanup_triggered = True
        if self._clean_fonts:
            self.__clean_downloaded_fonts()
            self._clean_fonts = False
            cleanup_triggered = True
        if cleanup_triggered:
            self.__update_config()

        if self._update_now:
            self._scheduler = BackgroundScheduler(timezone=settings.TZ)
            self._scheduler.add_job(func=self.__update_all_libraries, trigger='date',
                                    run_date=datetime.datetime.now(
                                        tz=pytz.timezone(settings.TZ)) + datetime.timedelta(seconds=3)
                                    )
            logger.info(f"媒体库封面更新服务启动，立即运行一次")
            # 关闭一次性开关
            self._update_now = False
            # 保存配置
            self.__update_config()
            # 启动服务
            if self._scheduler.get_jobs():
                self._scheduler.print_jobs()
                self._scheduler.start()

    def __clamp_value(self, value, minimum, maximum, default_value, name, cast_type):
        try:
            parsed = cast_type(value)
        except (ValueError, TypeError):
            logger.warning(f"{name} 配置值非法 ({value})，已回退默认值 {default_value}")
            return default_value

        if parsed < minimum or parsed > maximum:
            clamped = max(minimum, min(maximum, parsed))
            logger.warning(f"{name} 配置值超出范围 ({parsed})，已限制为 {clamped}")
            return clamped

        return parsed

    def __get_animated_2_required_items(self) -> int:
        self._animated_2_image_count = self.__clamp_value(
            self._animated_2_image_count,
            3,
            9,
            5,
            "animated_2 image_count[runtime]",
            int,
        )
        return int(self._animated_2_image_count)

    def __compose_cover_style(self, base_style: str, variant: str) -> str:
        base = base_style if base_style in ["static_1", "static_2", "static_3", "static_4"] else "static_1"
        mode = variant if variant in ["static", "animated"] else "static"
        suffix = base.split("_")[-1]
        return base if mode == "static" else f"animated_{suffix}"

    def __resolve_cover_style_ui(self, cover_style: str) -> Tuple[str, str]:
        if cover_style in ["animated_1", "animated_2", "animated_3", "animated_4"]:
            suffix = cover_style.split("_")[-1]
            if suffix == "4":
                return "static_4", "animated"
            return f"static_{suffix}", "animated"
        if cover_style in ["static_1", "static_2", "static_3", "static_4"]:
            return cover_style, "static"
        return "static_1", "static"

    def __is_single_image_style(self) -> bool:
        return self._cover_style in ["static_1", "static_2", "static_4"]

    def __get_required_items(self) -> int:
        if self._cover_style in ["static_3", "animated_3"]:
            return 9
        if self._cover_style in ["animated_1", "animated_2", "animated_4"]:
            return self.__get_animated_2_required_items()
        return 1

    def __update_config(self):
        """
        更新配置
        """
        self._cover_style = self.__compose_cover_style(self._cover_style_base, self._cover_style_variant)
        self._animated_2_image_count = self.__clamp_value(
            self._animated_2_image_count,
            3,
            9,
            5,
            "animated_2 image_count[save]",
            int,
        )
        self.update_config({
            "enabled": self._enabled,
            "update_now": self._update_now,
            "transfer_monitor": self._transfer_monitor,
            "cron": self._cron,
            "delay": self._delay,
            "selected_servers": self._selected_servers,
            "include_libraries": self._include_libraries,
            "all_libraries": self._all_libraries,
            "sort_by": self._sort_by,
            "covers_output": self._covers_output,
            "covers_input": self._covers_input,
            "title_config": self._title_config,
            "zh_font_url": str(self._zh_font_url),
            "en_font_url": str(self._en_font_url),
            "zh_font_path": str(self._zh_font_path),
            "en_font_path": str(self._en_font_path),
            "cover_style": self._cover_style,
            "cover_style_base": self._cover_style_base,
            "cover_style_variant": self._cover_style_variant,
            "multi_1_blur": self._multi_1_blur,
            "zh_font_size": self._zh_font_size,
            "en_font_size": self._en_font_size,
            "blur_size": self._blur_size,
            "color_ratio": self._color_ratio,
            "use_primary": self._use_primary,
            "zh_font_custom": self._zh_font_custom,
            "en_font_custom": self._en_font_custom,
            "zh_font_preset": self._zh_font_preset,
            "en_font_preset": self._en_font_preset,
            "zh_font_offset": self._zh_font_offset,
            "title_spacing": self._title_spacing,
            "en_line_spacing": self._en_line_spacing,
            "title_scale": self._title_scale,
            "resolution": self._resolution,
            "custom_width": self._custom_width,
            "custom_height": self._custom_height,
            "animation_duration": self._animation_duration,
            "animation_scroll": self._animation_scroll,
            "animation_fps": self._animation_fps,
            "animation_format": self._animation_format,
            "animation_resolution": self._animation_resolution,
            "animation_reduce_colors": self._animation_reduce_colors,
            "animated_2_image_count": self._animated_2_image_count,
            "animated_2_departure_type": self._animated_2_departure_type,
            "bg_color_mode": self._bg_color_mode,
            "custom_bg_color": self._custom_bg_color,
            "clean_images": self._clean_images,
            "clean_fonts": self._clean_fonts,
            "save_recent_covers": self._save_recent_covers,
            "covers_history_limit_per_library": self._covers_history_limit_per_library,
            "covers_page_history_limit": self._covers_page_history_limit,
            "page_tab": self._page_tab,
            "style_naming_v2": True,
        })

    def get_state(self) -> bool:
        return self._enabled

    def __font_search_dirs(self) -> List[Path]:
        dirs: List[Path] = []
        if self._font_path:
            dirs.append(Path(self._font_path))
        repo_font_dir = Path(__file__).resolve().parents[2] / "fonts"
        dirs.append(repo_font_dir)
        unique_dirs: List[Path] = []
        seen = set()
        for directory in dirs:
            key = str(directory)
            if key in seen:
                continue
            seen.add(key)
            if directory.exists() and directory.is_dir():
                unique_dirs.append(directory)
        return unique_dirs

    def __find_font_file(self, aliases: List[str], exts: List[str]) -> Optional[str]:
        normalized_aliases = [item.lower() for item in aliases if item]
        normalized_aliases_compact = [re.sub(r'[\s_\-]+', '', item) for item in normalized_aliases]
        normalized_exts = [item.lower() for item in exts]
        for directory in self.__font_search_dirs():
            candidates = sorted(directory.iterdir(), key=lambda p: p.name.lower())
            for font_file in candidates:
                if not font_file.is_file():
                    continue
                suffix = font_file.suffix.lower()
                if suffix not in normalized_exts:
                    continue
                stem = font_file.stem.lower()
                name = font_file.name.lower()
                stem_compact = re.sub(r'[\s_\-]+', '', stem)
                name_compact = re.sub(r'[\s_\-]+', '', name)
                if any(
                    alias in stem or alias in name or compact in stem_compact or compact in name_compact
                    for alias, compact in zip(normalized_aliases, normalized_aliases_compact)
                ):
                    return str(font_file)
        return None

    def __get_font_presets(self) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, Optional[str]], Dict[str, Optional[str]]]:
        zh_specs = [
            {"title": "潮黑", "value": "chaohei", "aliases": ["chaohei", "wendao", "潮黑", "chao_hei"]},
            {"title": "粗雅宋", "value": "yasong", "aliases": ["yasong", "粗雅宋", "multi_1_zh", "ya_song"]},
        ]
        en_specs = [
            {"title": "EmblemaOne", "value": "EmblemaOne", "aliases": ["emblemaone", "emblema_one"]},
            {"title": "Melete", "value": "Melete", "aliases": ["melete", "multi_1_en"]},
            {"title": "Phosphate", "value": "Phosphate", "aliases": ["phosphate", "phosphat"]},
            {"title": "JosefinSans", "value": "JosefinSans", "aliases": ["josefinsans", "josefin_sans"]},
            {"title": "LilitaOne", "value": "LilitaOne", "aliases": ["lilitaone", "lilita_one"]},
            {"title": "Monoton", "value": "Monoton", "aliases": ["monoton"]},
            {"title": "Plaster", "value": "Plaster", "aliases": ["plaster"]},
        ]
        all_specs = []
        seen_values = set()
        for spec in zh_specs + en_specs:
            if spec["value"] in seen_values:
                continue
            seen_values.add(spec["value"])
            value_alias = spec["value"].lower()
            compact_value_alias = re.sub(r'[\s_\-]+', '', value_alias)
            if value_alias not in spec["aliases"]:
                spec["aliases"].append(value_alias)
            if compact_value_alias and compact_value_alias not in spec["aliases"]:
                spec["aliases"].append(compact_value_alias)
            title_alias = spec["title"].lower()
            compact_title_alias = re.sub(r'[\s_\-]+', '', title_alias)
            if title_alias not in spec["aliases"]:
                spec["aliases"].append(title_alias)
            if compact_title_alias and compact_title_alias not in spec["aliases"]:
                spec["aliases"].append(compact_title_alias)
            all_specs.append(spec)
        zh_paths: Dict[str, Optional[str]] = {}
        en_paths: Dict[str, Optional[str]] = {}
        zh_items: List[Dict[str, str]] = []
        en_items: List[Dict[str, str]] = []
        zh_exts = [".ttf", ".otf", ".woff2", ".woff"]
        en_exts = [".ttf", ".otf", ".woff2", ".woff"]

        for spec in all_specs:
            found = self.__find_font_file(spec["aliases"], zh_exts)
            zh_paths[spec["value"]] = found
            zh_items.append({"title": spec["title"], "value": spec["value"]})
        for spec in all_specs:
            found = self.__find_font_file(spec["aliases"], en_exts)
            en_paths[spec["value"]] = found
            en_items.append({"title": spec["title"], "value": spec["value"]})
        return zh_items, en_items, zh_paths, en_paths

    def __clean_generated_images(self):
        removed = 0
        cache_dirs: List[Path] = []
        if self._covers_path:
            cache_dirs.append(Path(self._covers_path))
        data_path = self.get_data_path()
        legacy_covers_dir = data_path / "covers"
        cache_dirs.append(legacy_covers_dir)

        handled = set()
        for cache_dir in cache_dirs:
            if not cache_dir.exists() or not cache_dir.is_dir():
                continue
            cache_key = str(cache_dir.resolve())
            if cache_key in handled:
                continue
            handled.add(cache_key)
            for entry in cache_dir.iterdir():
                if not entry.exists():
                    continue
                try:
                    if entry.is_dir():
                        shutil.rmtree(entry)
                        removed += 1
                    elif entry.is_file():
                        entry.unlink(missing_ok=True)
                        removed += 1
                except Exception as e:
                    logger.warning(f"清理图片失败 {entry}: {e}")
        logger.info(f"清理图片完成（含旧版 covers 兼容目录），共清理 {removed} 项")

    def __clean_downloaded_fonts(self):
        if not self._font_path or not Path(self._font_path).exists():
            logger.info("清理字体：未找到字体目录，跳过")
            return
        removed = 0
        for entry in Path(self._font_path).iterdir():
            if entry.name.startswith("."):
                continue
            try:
                if entry.is_file():
                    entry.unlink(missing_ok=True)
                    removed += 1
                elif entry.is_dir():
                    shutil.rmtree(entry)
                    removed += 1
            except Exception as e:
                logger.warning(f"清理字体失败 {entry}: {e}")
        self._zh_font_path = ""
        self._en_font_path = ""
        logger.info(f"清理字体完成，共清理 {removed} 项")

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        return [
            {
                "cmd": "/update_covers",
                "event": EventType.PluginAction,
                "desc": "更新媒体库封面",
                "category": "",
                "data": {"action": "update_covers"},
            }
        ]

    def get_api(self) -> List[Dict[str, Any]]:
        """
        获取插件API
        [{
            "path": "/xx",
            "endpoint": self.xxx,
            "methods": ["GET", "POST"],
            "summary": "API说明"
        }]
        """
        return [
            {
                "path": "/clean_images",
                "endpoint": self.api_clean_images,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "立即清理封面图片缓存",
            },
            {
                "path": "clean_images",
                "endpoint": self.api_clean_images,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "立即清理封面图片缓存(兼容无前导斜杠)",
            },
            {
                "path": "/clean_fonts",
                "endpoint": self.api_clean_fonts,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "立即清理字体缓存",
            },
            {
                "path": "clean_fonts",
                "endpoint": self.api_clean_fonts,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "立即清理字体缓存(兼容无前导斜杠)",
            },
            {
                "path": "/delete_saved_cover",
                "endpoint": self.api_delete_saved_cover,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "删除一张已保存封面",
            },
            {
                "path": "delete_saved_cover",
                "endpoint": self.api_delete_saved_cover,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "删除一张已保存封面(兼容无前导斜杠)",
            },
            {
                "path": "/generate_now",
                "endpoint": self.api_generate_now,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "立即生成媒体库封面",
            },
            {
                "path": "generate_now",
                "endpoint": self.api_generate_now,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "立即生成媒体库封面(兼容无前导斜杠)",
            },
            {
                "path": "/set_cover_style",
                "endpoint": self.api_set_cover_style,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "保存封面风格选择",
            },
            {
                "path": "set_cover_style",
                "endpoint": self.api_set_cover_style,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "保存封面风格选择(兼容无前导斜杠)",
            },
            {"path": "/toggle_style_variant", "endpoint": self.api_toggle_style_variant, "auth": "bear", "methods": ["POST"], "summary": "切换静态/动态"},
            {"path": "toggle_style_variant", "endpoint": self.api_toggle_style_variant, "auth": "bear", "methods": ["POST"], "summary": "切换静态/动态(兼容)"},
            {"path": "/select_style_1", "endpoint": self.api_select_style_1, "auth": "bear", "methods": ["POST"], "summary": "选择风格1"},
            {"path": "/select_style_2", "endpoint": self.api_select_style_2, "auth": "bear", "methods": ["POST"], "summary": "选择风格2"},
            {"path": "/select_style_3", "endpoint": self.api_select_style_3, "auth": "bear", "methods": ["POST"], "summary": "选择风格3"},
            {"path": "/select_style_4", "endpoint": self.api_select_style_4, "auth": "bear", "methods": ["POST"], "summary": "选择风格4"},
            {"path": "select_style_1", "endpoint": self.api_select_style_1, "auth": "bear", "methods": ["POST"], "summary": "选择风格1(兼容)"},
            {"path": "select_style_2", "endpoint": self.api_select_style_2, "auth": "bear", "methods": ["POST"], "summary": "选择风格2(兼容)"},
            {"path": "select_style_3", "endpoint": self.api_select_style_3, "auth": "bear", "methods": ["POST"], "summary": "选择风格3(兼容)"},
            {"path": "select_style_4", "endpoint": self.api_select_style_4, "auth": "bear", "methods": ["POST"], "summary": "选择风格4(兼容)"},
            {"path": "/set_page_tab_generate", "endpoint": self.api_set_page_tab_generate, "auth": "bear", "methods": ["POST"], "summary": "切换到生成页"},
            {"path": "/set_page_tab_history", "endpoint": self.api_set_page_tab_history, "auth": "bear", "methods": ["POST"], "summary": "切换到历史页"},
            {"path": "/set_page_tab_clean", "endpoint": self.api_set_page_tab_clean, "auth": "bear", "methods": ["POST"], "summary": "切换到清理页"},
            {"path": "set_page_tab_generate", "endpoint": self.api_set_page_tab_generate, "auth": "bear", "methods": ["POST"], "summary": "切换到生成页(兼容)"},
            {"path": "set_page_tab_history", "endpoint": self.api_set_page_tab_history, "auth": "bear", "methods": ["POST"], "summary": "切换到历史页(兼容)"},
            {"path": "set_page_tab_clean", "endpoint": self.api_set_page_tab_clean, "auth": "bear", "methods": ["POST"], "summary": "切换到清理页(兼容)"},
            {"path": "/saved_cover_image", "endpoint": self.api_saved_cover_image, "methods": ["GET"], "summary": "获取已保存封面图片"},
            {"path": "saved_cover_image", "endpoint": self.api_saved_cover_image, "methods": ["GET"], "summary": "获取已保存封面图片(兼容)"},
        ]

    def api_clean_images(self):
        try:
            logger.info("【MediaCoverGenerator】收到立即清理图片缓存请求")
            self.__clean_generated_images()
            self._clean_images = False
            self.__update_config()
            return {"code": 0, "msg": "图片缓存清理完成"}
        except Exception as e:
            logger.error(f"【MediaCoverGenerator】立即清理图片失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"图片缓存清理失败: {e}"}

    def api_clean_fonts(self):
        try:
            logger.info("【MediaCoverGenerator】收到立即清理字体缓存请求")
            self.__clean_downloaded_fonts()
            self._clean_fonts = False
            self.__update_config()
            return {"code": 0, "msg": "字体缓存清理完成"}
        except Exception as e:
            logger.error(f"【MediaCoverGenerator】立即清理字体失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"字体缓存清理失败: {e}"}

    def api_delete_saved_cover(self, file: str = ""):
        try:
            target_file = self.__resolve_saved_cover_path(file)
            if not target_file:
                return {"code": 1, "msg": "无效文件路径"}
            if not target_file.exists() or not target_file.is_file():
                return {"code": 1, "msg": "文件不存在"}
            target_file.unlink(missing_ok=True)
            logger.info(f"【MediaCoverGenerator】已删除封面文件: {target_file}")
            return {"code": 0, "msg": "封面文件删除成功"}
        except Exception as e:
            logger.error(f"【MediaCoverGenerator】删除封面文件失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"封面文件删除失败: {e}"}

    def api_generate_now(self, style: str = ""):
        old_style = self._cover_style
        try:
            if not self._enabled:
                logger.warning("【MediaCoverGenerator】立即生成失败：插件未启用，请先在设置页启用插件并保存")
                return {"code": 1, "msg": "插件未启用，请先在设置页启用插件并保存"}
            if not self._selected_servers:
                logger.warning("【MediaCoverGenerator】立即生成失败：未勾选媒体服务器，请先在设置页勾选服务器并保存")
                return {"code": 1, "msg": "未勾选媒体服务器，请先在设置页勾选服务器并保存"}
            if not self._servers:
                logger.warning("【MediaCoverGenerator】立即生成失败：服务器连接信息为空，请检查设置并保存后重试")
                return {"code": 1, "msg": "服务器连接信息为空，请检查设置并保存后重试"}

            target_style = (style or "").strip()
            allowed_styles = {
                "static_1", "static_2", "static_3", "static_4",
                "animated_1", "animated_2", "animated_3", "animated_4",
            }
            if target_style:
                if target_style not in allowed_styles:
                    return {"code": 1, "msg": f"不支持的风格: {target_style}"}
                self._cover_style = target_style
            logger.info(f"【MediaCoverGenerator】收到立即生成请求，风格: {self._cover_style}")
            tips = self.__update_all_libraries()
            return {"code": 0, "msg": tips or "封面生成任务已完成"}
        except Exception as e:
            logger.error(f"【MediaCoverGenerator】立即生成失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"封面生成失败: {e}"}
        finally:
            self._cover_style = old_style

    def api_set_cover_style(self, style: str = ""):
        try:
            target_style = (style or "").strip()
            allowed_styles = {
                "static_1", "static_2", "static_3", "static_4",
                "animated_1", "animated_2", "animated_3", "animated_4",
            }
            if target_style not in allowed_styles:
                return {"code": 1, "msg": f"不支持的风格: {target_style}"}
            self._cover_style = target_style
            base, variant = self.__resolve_cover_style_ui(target_style)
            self._cover_style_base = base
            self._cover_style_variant = variant
            self.__update_config()
            logger.info(f"【MediaCoverGenerator】已保存封面风格: {target_style}")
            return {"code": 0, "msg": f"已保存风格: {target_style}"}
        except Exception as e:
            logger.error(f"【MediaCoverGenerator】保存封面风格失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"保存风格失败: {e}"}

    def __get_cover_style_parts(self) -> Tuple[str, int]:
        style = (self._cover_style or "static_1").strip()
        variant = "animated" if style.startswith("animated_") else "static"
        try:
            index = int(style.split("_")[-1])
        except Exception:
            index = 1
        index = max(1, min(4, index))
        return variant, index

    def __set_cover_style_parts(self, variant: str, index: int):
        safe_variant = "animated" if variant == "animated" else "static"
        safe_index = max(1, min(4, int(index)))
        target_style = f"{safe_variant}_{safe_index}"
        self._cover_style = target_style
        self._cover_style_base = f"static_{safe_index}"
        self._cover_style_variant = safe_variant
        self.__update_config()
        logger.info(f"【MediaCoverGenerator】已保存封面风格: {target_style}")

    def api_toggle_style_variant(self):
        try:
            variant, index = self.__get_cover_style_parts()
            new_variant = "animated" if variant == "static" else "static"
            self.__set_cover_style_parts(new_variant, index)
            return {"code": 0, "msg": f"已切换为{new_variant}风格{index}"}
        except Exception as e:
            logger.error(f"【MediaCoverGenerator】切换静态/动态失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"切换失败: {e}"}

    def __api_select_style(self, index: int):
        try:
            variant, _ = self.__get_cover_style_parts()
            self.__set_cover_style_parts(variant, index)
            return {"code": 0, "msg": f"已选择{variant}风格{index}"}
        except Exception as e:
            logger.error(f"【MediaCoverGenerator】选择风格失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"选择风格失败: {e}"}

    def api_select_style_1(self):
        return self.__api_select_style(1)

    def api_select_style_2(self):
        return self.__api_select_style(2)

    def api_select_style_3(self):
        return self.__api_select_style(3)

    def api_select_style_4(self):
        return self.__api_select_style(4)

    def __set_page_tab(self, tab: str):
        self._page_tab = tab if tab in ["generate-tab", "history-tab", "clean-tab"] else "generate-tab"
        logger.info(f"【MediaCoverGenerator】已切换页面Tab: {self._page_tab}")

    def api_set_page_tab_generate(self):
        self.__set_page_tab("generate-tab")
        return {"code": 0, "msg": "已切换到封面生成"}

    def api_set_page_tab_history(self):
        self.__set_page_tab("history-tab")
        return {"code": 0, "msg": "已切换到历史封面"}

    def api_set_page_tab_clean(self):
        self.__set_page_tab("clean-tab")
        return {"code": 0, "msg": "已切换到清理缓存"}

    def api_saved_cover_image(self, file: str = ""):
        target_file = self.__resolve_saved_cover_path(file)
        if not target_file or not target_file.exists() or not target_file.is_file():
            return {"code": 1, "msg": "图片不存在"}
        mime_type, _ = mimetypes.guess_type(str(target_file))
        if not mime_type:
            mime_type = "image/jpeg"
        try:
            from fastapi.responses import FileResponse
            return FileResponse(path=str(target_file), media_type=mime_type)
        except Exception:
            try:
                from starlette.responses import FileResponse
                return FileResponse(path=str(target_file), media_type=mime_type)
            except Exception as e:
                logger.error(f"【MediaCoverGenerator】返回图片失败: {e}")
                return {"code": 1, "msg": "返回图片失败"}

    def get_service(self) -> List[Dict[str, Any]]:
        """
        注册插件公共服务
        """
        services = []
        if self._enabled and self._cron:
            services.append({
                "id": "MediaCoverGenerator",
                "name": "媒体库封面更新服务",
                "trigger": CronTrigger.from_crontab(self._cron),
                "func": self.__update_all_libraries,
                "kwargs": {}
            })
        
        # 总是显示停止按钮，以便中断长时间运行的任务
        services.append({
            "id": "StopMediaCoverGenerator",
            "name": "停止当前更新任务",
            "trigger": None,
            "func": self.stop_task,
            "kwargs": {}
        })
        return services

    def stop_task(self):
        """
        手动停止当前正在执行的任务
        """
        if not self._event.is_set():
            logger.info("正在发送停止任务信号...")
            self._event.set()
            return True, "已发送停止停止信号，请等待当前操作清理完成"
        return True, "任务已处于停止状态或正在停止中"

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面
        """
        # 每次用户打开插件设置页面时，强制重置回封面生成页签，满足不记忆页签的需求
        self._page_tab = "generate-tab"
        
        zh_font_items, en_font_items, _, _ = self.__get_font_presets()
        # 标题配置
        title_tab = [
            {
                'component': 'VRow',
                'content': [
                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12,
                        },
                        'content': [
                            {
                                'component': 'VAceEditor',
                                'props': {
                                    'modelvalue': 'title_config',
                                    'lang': 'yaml',
                                    'theme': 'monokai',
                                    'style': 'height: 30rem',
                                    'label': '中英标题配置',
                                    'placeholder': '''媒体库名称:
- 主标题
- 副标题
- "#FF5722"  # 可选：背景颜色（必须加引号）'''
                                 }
                             }
                         ]
                     },
                ]
            },
        ]

        # 其他设置标签
        others_tab = [
            
            {
                'component': 'VRow',
                'content': [
                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12,
                        },
                        'content': [
                            {
                                'component': 'VAlert',
                                'props': {
                                    'type': 'info',
                                    'variant': 'tonal',
                                    'text': '自定义图片目录：请将图片存于与媒体库同名的子目录下，例如：/mnt/custom_images/华语电影/1.jpg，填写 /mnt/custom_images 即可。多图模式下，文件名须为 1.jpg, 2.jpg, ...9.jpg，不满足的会被重命名，不够的会随机复制填满9张'
                                }
                            }
                        ]
                    },
                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12,
                            'md': 4
                        },
                        'content': [
                            {
                                'component': 'VTextField',
                                'props': {
                                    'model': 'covers_input',
                                    'label': '自定义图片目录（可选）',
                                    'prependInnerIcon': 'mdi-file-image',
                                    'hint': '使用你指定的图片生成封面，图片放在与媒体库同名的文件夹下',
                                    'persistentHint': True
                                }
                            }
                        ]
                    },

                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12,
                            'md': 4
                        },
                        'content': [
                            {
                                'component': 'VTextField',
                                'props': {
                                    'model': 'covers_output',
                                    'label': '历史封面保存目录（可选）',
                                    'prependInnerIcon': 'mdi-file-image',
                                    'hint': '生成的封面默认保存在本插件数据目录下',
                                    'persistentHint': True
                                }
                            }
                        ]
                    },
                                        {
                        'component': 'VCol',
                        'props': {
                            'cols': 12,
                            'md': 4
                        },
                        'content': [
                            {
                                'component': 'VSwitch',
                                'props': {
                                    'model': 'save_recent_covers',
                                    'label': '保存最近生成的封面',
                                    'hint': '默认开启，保存历史封面',
                                    'persistentHint': True
                                }
                            }
                        ]
                    },
                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12,
                            'md': 4
                        },
                        'content': [
                            {
                                'component': 'VTextField',
                                'props': {
                                    'model': 'covers_history_limit_per_library',
                                    'label': '媒体库历史封面数量',
                                    'prependInnerIcon': 'mdi-history',
                                    'hint': '单个媒体库封面保留上限，默认 10',
                                    'persistentHint': True
                                }
                            }
                        ]
                    },
                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12,
                            'md': 4
                        },
                        'content': [
                            {
                                'component': 'VTextField',
                                'props': {
                                    'model': 'covers_page_history_limit',
                                    'label': '历史封面显示数量',
                                    'prependInnerIcon': 'mdi-image-multiple-outline',
                                    'hint': '历史封面「显示数量」，默认 50',
                                    'persistentHint': True
                                },
                            }
                        ]
                    }
                ]
            },
            
        ]
        # 更多参数标签
        single_tab = [
            {
                'component': 'VRow',
                'content': [
                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12,
                        },
                        'content': [
                            {
                                'component': 'VAlert',
                                'props': {
                                    'type': 'info',
                                    'variant': 'tonal',
                                    'text': '字体设置为可选项。若字体无法下载，可以手动下载并填写本地路径。主标题和副标题可以使用不同的字体。'
                                }
                            }
                        ]
                    },
                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12,
                            'md': 6
                        },
                        'content': [
                            {
                                'component': 'VSelect',
                                'props': {
                                    'chips': False,
                                    'multiple': False,
                                    'model': 'zh_font_preset',
                                    'label': '主标题字体预设',
                                    'prependInnerIcon': 'mdi-ideogram-cjk',
                                    'items': zh_font_items
                                }
                            }
                        ]
                    },
                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12,
                            'md': 6
                        },
                        'content': [
                            {
                                'component': 'VSelect',
                                'props': {
                                    'chips': False,
                                    'multiple': False,
                                    'model': 'en_font_preset',
                                    'label': '副标题字体预设',
                                    'prependInnerIcon': 'mdi-format-font',
                                    'items': en_font_items
                                }
                            }
                        ]
                    },
                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12,
                            'md': 6
                        },
                        'content': [
                            {
                                'component': 'VTextField',
                                'props': {
                                    'model': 'zh_font_custom',
                                    'label': '自定义主标题字体',
                                    'prependInnerIcon': 'mdi-ideogram-cjk',
                                    'placeholder': '留空使用预设字体',
                                    'hint': '字体链接 / 路径',
                                    'persistentHint': True
                                }
                            }
                        ]
                    },
                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12,
                            'md': 6
                        },
                        'content': [
                            {
                                'component': 'VTextField',
                                'props': {
                                    'model': 'en_font_custom',
                                    'label': '自定义副标题字体',
                                    'prependInnerIcon': 'mdi-format-font',
                                    'placeholder': '留空使用预设字体',
                                    'hint': '字体链接 / 路径',
                                    'persistentHint': True
                                }
                            }
                        ]
                    },
                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12,
                            'md': 6
                        },
                        'content': [
                            {
                                'component': 'VTextField',
                                'props': {
                                    'model': 'zh_font_size',
                                    'label': '主标题字体大小',
                                    'prependInnerIcon': 'mdi-format-size',
                                    'placeholder': '留空使用预设尺寸',
                                    'hint': '根据自己喜好设置，默认 180',
                                    'persistentHint': True
                                }
                            }
                        ]
                    },
                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12,
                            'md': 6
                        },
                        'content': [
                            {
                                'component': 'VTextField',
                                'props': {
                                    'model': 'en_font_size',
                                    'label': '副标题字体大小',
                                    'prependInnerIcon': 'mdi-format-size',
                                    'placeholder': '留空使用预设尺寸',
                                    'hint': '根据自己喜好设置，默认 75',
                                    'persistentHint': True
                                }
                            }
                        ]
                    },
                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12,
                            'md': 6
                        },
                        'content': [
                            {
                                'component': 'VTextField',
                                'props': {
                                    'model': 'blur_size',
                                    'label': '背景模糊尺寸',
                                    'prependInnerIcon': 'mdi-blur',
                                    'placeholder': '留空使用预设尺寸',
                                    'hint': '数字越大越模糊，默认 50',
                                    'persistentHint': True
                                }
                            }
                        ]
                    },
                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12,
                            'md': 6
                        },
                        'content': [
                            {
                                'component': 'VTextField',
                                'props': {
                                    'model': 'color_ratio',
                                    'label': '背景颜色混合占比',
                                    'prependInnerIcon': 'mdi-format-color-fill',
                                    'placeholder': '留空使用预设占比',
                                    'hint': '颜色所占的比例，0-1，默认 0.8',
                                    'persistentHint': True
                                }
                            }
                        ]
                    },
                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12,
                            'md': 6
                        },
                        'content': [
                            {
                                'component': 'VTextField',
                                'props': {
                                    'model': 'title_scale',
                                    'label': '标题整体缩放',
                                    'prependInnerIcon': 'mdi-arrow-expand-all',
                                    'placeholder': '留空使用预设比例',
                                    'hint': '以 1080p 为基准，1.0 为默认',
                                    'persistentHint': True
                                }
                            }
                        ]
                    },
                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12,
                            'md': 4
                        },
                        'content': [
                            {
                                'component': 'VTextField',
                                'props': {
                                    'model': 'zh_font_offset',
                                    'label': '主标题偏移量',
                                    'prependInnerIcon': 'mdi-arrow-up-down',
                                    'placeholder': '留空使用预设尺寸',
                                    'hint': '上移为负值，下移为正值',
                                    'persistentHint': True
                                }
                            }
                        ]
                    },
                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12,
                            'md': 4
                        },
                        'content': [
                            {
                                'component': 'VTextField',
                                'props': {
                                    'model': 'title_spacing',
                                    'label': '主副标题间距',
                                    'prependInnerIcon': 'mdi-arrow-up-down',
                                    'placeholder': '留空使用预设尺寸',
                                    'hint': '大于 0，默认 40',
                                    'persistentHint': True
                                }
                            }
                        ]
                    },
                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12,
                            'md': 4
                        },
                        'content': [
                            {
                                'component': 'VTextField',
                                'props': {
                                    'model': 'en_line_spacing',
                                    'label': '副标题行间距',
                                    'prependInnerIcon': 'mdi-format-line-height',
                                    'placeholder': '留空使用预设尺寸',
                                    'hint': '大于 0，默认 40',
                                    'persistentHint': True
                                }
                            }
                        ]
                    },
                ]
            },
        ]

        more_tab = single_tab + others_tab

        styles = [
            {
                "value": "static_1",
                "src": self.__style_preview_src(1)
            },
            {
                "value": "static_2",
                "src": self.__style_preview_src(2)
            },
            {
                "value": "static_3",
                "src": self.__style_preview_src(3)
            },
            {
                "value": "static_4",
                "src": self.__style_preview_src(4)
            }
        ]

        style_variant_items = [
            {
                'component': 'VBtn',
                'props': {
                    'value': 'static',
                    'variant': 'outlined',
                    'color': 'primary',
                    'prependIcon': 'mdi-image-outline',
                    'class': 'text-none',
                },
                'text': '静态'
            },
            {
                'component': 'VBtn',
                'props': {
                    'value': 'animated',
                    'variant': 'outlined',
                    'color': 'primary',
                    'prependIcon': 'mdi-play-box-multiple-outline',
                    'class': 'text-none',
                },
                'text': '动态'
            }
        ]

        preview_style_content = []

        for style in styles:
            preview_style_content.append(
                {
                    'component': 'VCol',
                    'props': {
                        'cols': 12,
                        'md': 3,
                    },
                    'content': [
                        {
                            'component': 'VLabel',
                            'props': {
                                'class': 'd-block w-100 cursor-pointer'
                            },
                            'content': [
                                {
                                    'component': 'VCard',
                                    'props': {
                                        'variant': 'flat',
                                        'class': 'rounded-lg overflow-hidden',
                                        'style': f'position: relative; background-image: linear-gradient(rgba(80,80,80,0.25), rgba(80,80,80,0.25)), url({style.get("src")}); background-size: cover; background-position: center; background-repeat: no-repeat;'
                                    },
                                    'content': [
                                        {
                                            'component': 'VImg',
                                            'props': {
                                                'src': style.get('src'),
                                                'aspect-ratio': '16/9',
                                                'cover': True,
                                            }
                                        },
                                        {
                                            'component': 'VRadio',
                                            'props': {
                                                'value': style.get('value'),
                                                'color': '#FFFFFF',
                                                'baseColor': '#FFFFFF',
                                                'density': 'default',
                                                'hideDetails': True,
                                                'class': 'position-absolute',
                                                'style': 'top: 8px; right: 8px; z-index: 2; margin: 0; transform: scale(1.2); transform-origin: top right;'
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            )

        # 封面风格设置标签
        style_tab = [
            {
                'component': 'VAlert',
                'props': {
                    'type': 'info',
                    'variant': 'tonal',
                    'text': '先选基础样式，再选静态或动态。点击整张预览图即可切换。',
                    'class': 'mb-3'
                }
            },
            {
                'component': 'VRadioGroup',
                'props': {
                    'model': 'cover_style_base',
                },
                'content': [
                    {
                        'component': 'VRow',
                        'content': preview_style_content
                    }
                ]
            },
            {
                'component': 'VBtnToggle',
                'props': {
                    'model': 'cover_style_variant',
                    'mandatory': True,
                    'class': 'mt-3',
                    'divided': True
                },
                'content': style_variant_items
            },
            {
                'component': 'VExpansionPanels',
                'props': {
                    'multiple': True,
                    'class': 'mt-3'
                },
                'content': [
                    {
                        'component': 'VExpansionPanel',
                        'props': {
                            'elevation': 0,
                            'class': 'rounded-lg',
                            'style': 'background-color: rgba(var(--v-theme-surface), 0.38); border: 1px solid rgba(var(--v-border-color), 0.35); backdrop-filter: blur(6px);'
                        },
                        'content': [
                            {
                                'component': 'VExpansionPanelTitle',
                                'props': {
                                    'class': 'font-weight-medium'
                                },
                                'text': '基本参数'
                            },
                            {
                                'component': 'VExpansionPanelText',
                                'content': [
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {
                                                'component': 'VCol',
                                                'props': {'cols': 12, 'md': 4},
                                                'content': [
                                                    {
                                                        'component': 'VBtnToggle',
                                                        'props': {
                                                            'model': 'use_primary',
                                                            'mandatory': True,
                                                            'divided': True,
                                                            'class': 'w-100'
                                                        },
                                                        'content': [
                                                            {
                                                                'component': 'VBtn',
                                                                'props': {
                                                                    'value': True,
                                                                    'variant': 'outlined',
                                                                    'color': 'primary',
                                                                    'class': 'text-none'
                                                                },
                                                                'text': '海报图'
                                                            },
                                                            {
                                                                'component': 'VBtn',
                                                                'props': {
                                                                    'value': False,
                                                                    'variant': 'outlined',
                                                                    'color': 'primary',
                                                                    'class': 'text-none'
                                                                },
                                                                'text': '背景图'
                                                            }
                                                        ]
                                                    },
                                                    {
                                                        'component': 'VLabel',
                                                        'props': {
                                                            'class': 'text-caption text-medium-emphasis mt-1 d-inline-block'
                                                        }
                                                        ,
                                                        'text': '选图优先来源'
                                                    }
                                                ]
                                            },
                                            {
                                                'component': 'VCol',
                                                'props': {'cols': 12, 'md': 4},
                                                'content': [
                                                    {
                                                        'component': 'VBtnToggle',
                                                        'props': {
                                                            'model': 'multi_1_blur',
                                                            'mandatory': True,
                                                            'divided': True,
                                                            'class': 'w-100'
                                                        },
                                                        'content': [
                                                            {
                                                                'component': 'VBtn',
                                                                'props': {
                                                                    'value': True,
                                                                    'variant': 'outlined',
                                                                    'color': 'primary',
                                                                    'class': 'text-none'
                                                                },
                                                                'text': '模糊背景'
                                                            },
                                                            {
                                                                'component': 'VBtn',
                                                                'props': {
                                                                    'value': False,
                                                                    'variant': 'outlined',
                                                                    'color': 'primary',
                                                                    'class': 'text-none'
                                                                },
                                                                'text': '纯色渐变'
                                                            }
                                                        ]
                                                    },
                                                    {
                                                        'component': 'VLabel',
                                                        'props': {
                                                            'class': 'text-caption text-medium-emphasis mt-1 d-inline-block'
                                                        }
                                                        ,
                                                        'text': '针对九宫格海报'
                                                    }
                                                ]
                                            },
                                            {
                                                'component': 'VCol',
                                                'props': {'cols': 12, 'md': 4},
                                                'content': [
                                                    {
                                                        'component': 'VSelect',
                                                        'props': {
                                                            'chips': False,
                                                            'multiple': False,
                                                            'model': 'resolution',
                                                            'label': '静态分辨率',
                                                            'prependInnerIcon': 'mdi-monitor-screenshot',
                                                            'items': [
                                                                {'title': '1080p (1920x1080)', 'value': '1080p'},
                                                                {'title': '720p (1280x720)', 'value': '720p'},
                                                                {'title': '480p (854x480)', 'value': '480p'}
                                                            ],
                                                            'hint': '动态分辨率默认320*180',
                                                            'persistentHint': True
                                                        }
                                                    }
                                                ]
                                            }
                                        ]
                                    },
                                    {
                                        'component': 'VExpansionPanels',
                                        'props': {
                                            'multiple': True,
                                            'class': 'mt-2'
                                        },
                                        'content': [
                                            {
                                                'component': 'VExpansionPanel',
                                                'props': {
                                                    'elevation': 0,
                                                    'class': 'rounded-lg',
                                                    'style': 'background-color: rgba(255,255,255,0.55); border: 1px dashed rgba(0,0,0,0.18);'
                                                },
                                                'content': [
                                                    {
                                                        'component': 'VExpansionPanelTitle',
                                                        'text': '背景颜色设置（全部风格生效）'
                                                    },
                                                    {
                                                        'component': 'VExpansionPanelText',
                                                        'content': [
                                                            {
                                                                'component': 'VRow',
                                                                'content': [
                                                                    {
                                                                        'component': 'VCol',
                                                                        'props': {'cols': 12, 'md': 4},
                                                                        'content': [
                                                                            {
                                                                                'component': 'VSelect',
                                                                                'props': {
                                                                                    'model': 'bg_color_mode',
                                                                                    'label': '背景颜色来源',
                                                                                    'prependInnerIcon': 'mdi-palette',
                                                                                    'items': [
                                                                                        {'title': '自动从图片提取', 'value': 'auto'},
                                                                                        {'title': '自定义（全局统一）', 'value': 'custom'},
                                                                                        {'title': '从配置获取', 'value': 'config'}
                                                                                    ]
                                                                                }
                                                                            }
                                                                        ]
                                                                    },
                                                                    {
                                                                        'component': 'VCol',
                                                                        'props': {'cols': 12, 'md': 8},
                                                                        'content': [
                                                                            {
                                                                                'component': 'VTextField',
                                                                                'props': {
                                                                                    'model': 'custom_bg_color',
                                                                                    'label': '自定义背景色',
                                                                                    'prependInnerIcon': 'mdi-eyedropper',
                                                                                    'placeholder': '#FF5722',
                                                                                    'hint': '支持 #十六进制、rgb(...)、颜色英文名',
                                                                                    'persistentHint': True
                                                                                }
                                                                            },
                                                                            {
                                                                                'component': 'VColorPicker',
                                                                                'props': {
                                                                                    'model': 'custom_bg_color',
                                                                                    'mode': 'hexa',
                                                                                    'showSwatches': True,
                                                                                    'hideCanvas': False,
                                                                                    'hideInputs': True,
                                                                                    'elevation': 0,
                                                                                    'class': 'mt-2'
                                                                                }
                                                                            }
                                                                        ]
                                                                    }
                                                                ]
                                                            }
                                                        ]
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VExpansionPanel',
                        'props': {
                            'elevation': 0,
                            'class': 'rounded-lg',
                            'style': 'background-color: rgba(var(--v-theme-surface), 0.32); border: 1px solid rgba(var(--v-border-color), 0.32); backdrop-filter: blur(6px);'
                        },
                        'content': [
                            {
                                'component': 'VExpansionPanelTitle',
                                'props': {
                                    'class': 'font-weight-medium'
                                },
                                'text': '动态图参数'
                            },
                            {
                                'component': 'VExpansionPanelText',
                                'content': [
                                    {
                                        'component': 'VRow',
                                        'props': {'class': 'mt-1'},
                                        'content': [
                                            {
                                                'component': 'VCol',
                                                'props': {'cols': 12, 'md': 3},
                                                'content': [
                                                    {
                                                        'component': 'VTextField',
                                                        'props': {
                                                            'model': 'animation_duration',
                                                            'label': '动画循环周期 (秒)',
                                                            'type': 'number',
                                                            'prependInnerIcon': 'mdi-clock-outline'
                                                        }
                                                    }
                                                ]
                                            },
                                            {
                                                'component': 'VCol',
                                                'props': {'cols': 12, 'md': 3},
                                                'content': [
                                                    {
                                                        'component': 'VTextField',
                                                        'props': {
                                                            'model': 'animation_fps',
                                                            'label': '帧率 (FPS)',
                                                            'type': 'number',
                                                            'prependInnerIcon': 'mdi-speedometer'
                                                        }
                                                    }
                                                ]
                                            },
                                            {
                                                'component': 'VCol',
                                                'props': {'cols': 12, 'md': 3},
                                                'content': [
                                                    {
                                                        'component': 'VSelect',
                                                        'props': {
                                                            'model': 'animation_format',
                                                            'label': '输出格式',
                                                            'items': [
                                                                {'title': 'APNG', 'value': 'apng'},
                                                                {'title': 'GIF', 'value': 'gif'}
                                                            ],
                                                            'prependInnerIcon': 'mdi-file-video'
                                                        }
                                                    }
                                                ]
                                            },
                                            {
                                                'component': 'VCol',
                                                'props': {'cols': 12, 'md': 3},
                                                'content': [
                                                    {
                                                        'component': 'VSelect',
                                                        'props': {
                                                            'model': 'animation_reduce_colors',
                                                            'label': '颜色压缩等级',
                                                            'items': [
                                                                {'title': '关闭（保真优先）', 'value': 'off'},
                                                                {'title': '中等压缩', 'value': 'medium'},
                                                                {'title': '强压缩（体积最小）', 'value': 'strong'}
                                                            ],
                                                            'prependInnerIcon': 'mdi-palette-outline'
                                                        }
                                                    }
                                                ]
                                            },
                                        ]
                                    },
                                    {
                                        'component': 'VRow',
                                        'props': {'class': 'mt-2'},
                                        'content': [
                                            {
                                                'component': 'VCol',
                                                'props': {'cols': 12, 'md': 4},
                                                'content': [
                                                    {
                                                        'component': 'VTextField',
                                                        'props': {
                                                            'model': 'animated_2_image_count',
                                                            'label': '样式1/2 图片数量 (3~9)',
                                                            'type': 'number',
                                                            'min': 3,
                                                            'max': 9,
                                                            'hint': '仅样式1/2有效',
                                                            'persistentHint': True,
                                                            'prependInnerIcon': 'mdi-image-multiple'
                                                        }
                                                    }
                                                ]
                                            },
                                            {
                                                'component': 'VCol',
                                                'props': {'cols': 12, 'md': 4},
                                                'content': [
                                                    {
                                                        'component': 'VSelect',
                                                        'props': {
                                                            'model': 'animated_2_departure_type',
                                                            'label': '样式1动画风格',
                                                            'hint': '仅样式1有效',
                                                            'persistentHint': True,
                                                            'items': [
                                                                {'title': '旋转-飞出', 'value': 'fly'},
                                                                {'title': '旋转-渐隐', 'value': 'fade'},
                                                                {'title': '渐变', 'value': 'crossfade'}
                                                            ],
                                                            'prependInnerIcon': 'mdi-transition'
                                                        }
                                                    }
                                                ]
                                            },
                                            {
                                                'component': 'VCol',
                                                'props': {'cols': 12, 'md': 4},
                                                'content': [
                                                    {
                                                        'component': 'VSelect',
                                                        'props': {
                                                            'model': 'animation_scroll',
                                                            'label': '样式3滚动方向',
                                                            'hint': '仅样式3有效',
                                                            'persistentHint': True,
                                                            'items': [
                                                                {'title': '向下', 'value': 'down'},
                                                                {'title': '向上', 'value': 'up'},
                                                                {'title': '交替 (两边下/中间上)', 'value': 'alternate'},
                                                                {'title': '交替反向 (两边上/中间下)', 'value': 'alternate_reverse'}
                                                            ],
                                                            'prependInnerIcon': 'mdi-swap-vertical'
                                                        }
                                                    }
                                                ]
                                            }
                                        ]
                                    },
 
                                ]
                            }
                        ]
                    }
                ]
            }
        ]


        return [
            {
                "component": "VCard",
                "props": {"variant": "outlined", "class": "mb-3"},
                "content": [
                    {
                        "component": "VCardTitle",
                        "props": {"class": "d-flex align-center"},
                        "content": [
                            {
                                "component": "VIcon",
                                "props": {
                                    "icon": "mdi-cog",
                                    "color": "primary",
                                    "class": "mr-2",
                                },
                            },
                            {"component": "span", "text": "基础设置"},
                        ],
                    },
                    {"component": "VDivider"},
                    {
                        "component": "VCardText",
                        "content": [
                            {
                                'component': 'VForm',
                                'content': [
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {
                                                'component': 'VCol',
                                                'props': {
                                                    'cols': 12,
                                                    'md': 3
                                                },
                                                'content': [
                                                    {
                                                        'component': 'VSwitch',
                                                        'props': {
                                                            'model': 'enabled',
                                                            'label': '启用插件',
                                                        }
                                                    }
                                                ]
                                            },
                                            {
                                                'component': 'VCol',
                                                'props': {
                                                    'cols': 12,
                                                    'md': 3
                                                },
                                                'content': [
                                                    {
                                                        'component': 'VSwitch',
                                                        'props': {
                                                            'model': 'update_now',
                                                            'label': '立即更新封面',
                                                        }
                                                    }
                                                ]
                                            },
                                            {
                                                'component': 'VCol',
                                                'props': {
                                                    'cols': 12,
                                                    'md': 3
                                                },
                                                'content': [
                                                    {
                                                        'component': 'VSwitch',
                                                        'props': {
                                                            'model': 'transfer_monitor',
                                                            'label': '入库监控',
                                                            'hint': '自动更新入库媒体所在媒体库封面',
                                                            'persistentHint': True
                                                        }
                                                    }
                                                ]
                                            },
                                            {
                                                'component': 'VCol',
                                                'props': {
                                                    'cols': 12,
                                                    'md': 3
                                                },
                                                'content': [
                                                    {
                                                        'component': 'VTextField',
                                                        'props': {
                                                            'model': 'delay',
                                                            'label': '入库延迟（秒）',
                                                            'placeholder': '60',
                                                            'hint': '根据实际情况调整延迟时间',
                                                            'persistentHint': True
                                                        }
                                                    }
                                                ]
                                            },
                                        ]
                                    },
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {
                                                'component': 'VCol',
                                                'props': {
                                                    'cols': 12,
                                                    'md': 6
                                                },
                                                'content': [
                                                    {
                                                        'component': 'VSelect',
                                                        'props': {
                                                            'multiple': True,
                                                            'chips': True,
                                                            'clearable': True,
                                                            'model': 'selected_servers',
                                                            'label': '媒体服务器',
                                                            'items': [{"title": config.name, "value": config.name}
                                                                    for config in self.mediaserver_helper.get_configs().values()
                                                                    if config.type in ("emby", "jellyfin")
                                                                    ]
                                                        }
                                                    }
                                                ]
                                            },
                                            {
                                                'component': 'VCol',
                                                'props': {
                                                    'cols': 12,
                                                    'md': 3
                                                },
                                                'content': [
                                                    {
                                                        'component': 'VSelect',
                                                        'props': {
                                                            'chips': False,
                                                            'multiple': False,
                                                            'model': 'sort_by',
                                                            'label': '封面来源排序，默认随机',
                                                            'items': [
                                                                {"title": "随机", "value": "Random"},
                                                                {"title": "最新入库", "value": "DateCreated"},
                                                                {"title": "最新发行", "value": "PremiereDate"}
                                                                ]
                                                        }
                                                    }
                                                ]
                                            },
                                            {
                                                'component': 'VCol',
                                                'props': {
                                                    'cols': 12,
                                                    'md': 3
                                                },
                                                'content': [
                                                    {
                                                        'component': 'VCronField',
                                                        'props': {
                                                            'model': 'cron',
                                                            'label': '定时更新封面',
                                                            'placeholder': '5位cron表达式'
                                                        }
                                                    }
                                                ]
                                            },
                                            
                                        ]
                                    },
                                    {
                                        'component': 'VRow',
                                        'content': [
                                            {
                                                'component': 'VCol',
                                                'props': {
                                                    'cols': 12,
                                                },
                                                'content': [
                                                    {
                                                        'component': 'VSelect',
                                                        'props': {
                                                            'multiple': True,
                                                            'chips': True,
                                                            'clearable': True,
                                                            'model': 'include_libraries',
                                                            'label': '更新媒体库',
                                                            'items': [
                                                                {"title": config['name'], "value": config['value']}
                                                                    for config in self._all_libraries
                                                            ],
                                                            'hint': '默认更新全部，或只更新勾选的媒体库',
                                                            'persistentHint': True
                                                        }
                                                    }
                                                ]
                                            },
                                        ]
                                    }
                                    
                                ]
                            },
                        ]
                    }
                ]
            },
            {
                "component": "VCard",
                "props": {"variant": "outlined"},
                "content": [
                    {
                        "component": "VTabs",
                        "props": {"model": "tab", "grow": True, "color": "primary"},
                        "content": [
                            {
                                "component": "VTab",
                                "props": {"value": "style-tab"},
                                "content": [
                                    {
                                        "component": "VIcon",
                                        "props": {
                                            "icon": "mdi-palette-swatch",
                                            "start": True,
                                            "color": "#cc76d1",
                                        },
                                    },
                                    {"component": "span", "text": "封面风格"},
                                ],
                            },
                            {
                                "component": "VTab",
                                "props": {"value": "title-tab"},
                                "content": [
                                    {
                                        "component": "VIcon",
                                        "props": {
                                            "icon": "mdi-text-box-edit",
                                            "start": True,
                                            "color": "#1976D2",
                                        },
                                    },
                                    {"component": "span", "text": "封面标题"},
                                ],
                            },
                            {
                                "component": "VTab",
                                "props": {"value": "more-tab"},
                                "content": [
                                    {
                                        "component": "VIcon",
                                        "props": {
                                            "icon": "mdi-palette-swatch-variant",
                                            "start": True,
                                            "color": "#f3afe4",
                                        },
                                    },
                                    {"component": "span", "text": "更多参数"},
                                ],
                            },
                        ],
                    },
                    {"component": "VDivider"},
                    {
                        "component": "VWindow",
                        "props": {"model": "tab"},
                        "content": [
                            {
                                "component": "VWindowItem",
                                "props": {"value": "style-tab"},
                                "content": [
                                    {"component": "VCardText", "content": style_tab}
                                ],
                            },
                            {
                                "component": "VWindowItem",
                                "props": {"value": "title-tab"},
                                "content": [
                                    {
                                        "component": "VCardText",
                                        "content": title_tab,
                                    }
                                ],
                            },
                            {
                                "component": "VWindowItem",
                                "props": {"value": "more-tab"},
                                "content": [
                                    {"component": "VCardText", "content": more_tab}
                                ],
                            }
                        ],
                    },
                ],
            }
        ], {
            "enabled": True,
            "update_now": False,
            "transfer_monitor": True,
            "cron": "",
            "delay": 60,
            "selected_servers": [],
            "include_libraries": [],
            "sort_by": "Random",
            "title_config": '''# 配置封面标题（按媒体库名称对应）
# 支持两种格式：
#
# 格式1 - 两行配置（主标题+副标题）：
# 媒体库名称:
#   - 主标题
#   - 副标题
#
# 格式2 - 三行配置（主标题+副标题+背景颜色）：
# 媒体库名称:
#   - 主标题
#   - 副标题
#   - "#FF5722"  # 背景颜色（可选，必须加引号）
#
''',
            "tab": "style-tab",
            "cover_style": "static_1",
            "cover_style_base": "static_1",
            "cover_style_variant": "static",
            "multi_1_blur": True,
            "zh_font_preset": "chaohei",
            "en_font_preset": "EmblemaOne",
            "zh_font_custom": "",
            "en_font_custom": "",
            "zh_font_size": None,
            "en_font_size": None,
            "blur_size": 50,
            "color_ratio": 0.8,
            "title_scale": 1.0,
            "use_primary": False,
            "resolution": "480p",
            "custom_width": 1920,
            "custom_height": 1080,
            "bg_color_mode": "auto",
            "custom_bg_color": "",
            "animation_duration": 8,
            "animation_scroll": "alternate",
            "animation_fps": 24,
            "animation_format": "apng",
            "animation_resolution": "320x180",
            "animation_reduce_colors": "medium",
            "animated_2_image_count": 6,
            "animated_2_departure_type": "fly",
            "clean_images": False,
            "clean_fonts": False,
            "save_recent_covers": True,
            "covers_history_limit_per_library": 10,
            "covers_page_history_limit": 50,
            "page_tab": "generate-tab",
            "style_naming_v2": True,
        }

    def get_page(self) -> List[dict]:
        limit = self.__clamp_value(
            self._covers_page_history_limit,
            1,
            500,
            50,
            "covers_page_history_limit[get_page]",
            int,
        )
        style_variant, style_index = self.__get_cover_style_parts()
        style_preview_cards = self.__build_page_style_cards(style_variant=style_variant, selected_index=style_index)
        setup_warnings: List[str] = []
        if not self._enabled:
            setup_warnings.append("插件未启用，请先在设置页启用插件并保存。")
        if not self._selected_servers:
            setup_warnings.append("未勾选媒体服务器，请先在设置页勾选服务器并保存。")
        elif not self._servers:
            setup_warnings.append("服务器配置尚未生效，请在设置页保存后重试。")

        # 永远默认首先访问封面生成页，不记忆用户的最后一次Tab选择，以提升开启速度
        page_tab = "generate-tab"
        
        # 仅当明确切换到了历史封面页时，才执行耗时的图片加载逻辑
        cover_rows = []
        if self._page_tab == "history-tab":
            page_tab = "history-tab"
            recent_covers = self.__get_recent_generated_covers(limit=limit)
            if recent_covers:
                for item in recent_covers:
                    delete_api = f"plugin/MediaCoverGenerator/delete_saved_cover?file={quote(item['path'])}"
                    cover_rows.append(
                        {
                            "component": "VCol",
                            "props": {"cols": 12, "sm": 6, "md": 3},
                            "content": [
                                {
                                    "component": "VCard",
                                    "props": {
                                        "variant": "flat",
                                        "elevation": 2,
                                        "class": "rounded-lg",
                                    },
                                    "content": [
                                        {
                                            "component": "VImg",
                                            "props": {
                                                "src": item["src"],
                                                "aspect-ratio": "16/9",
                                                "cover": True,
                                            },
                                        },
                                        {
                                            "component": "VCardText",
                                            "props": {"class": "py-2"},
                                            "content": [
                                                {
                                                    "component": "VRow",
                                                    "props": {"class": "align-center", "noGutters": True},
                                                    "content": [
                                                        {
                                                            "component": "VCol",
                                                            "props": {"cols": 9},
                                                            "content": [
                                                                {
                                                                    "component": "div",
                                                                    "props": {
                                                                        "class": "text-body-2",
                                                                        "style": "display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.2rem; min-height: 2.4rem;"
                                                                    },
                                                                    "text": item["name"],
                                                                },
                                                                {
                                                                    "component": "div",
                                                                    "props": {"class": "text-caption text-medium-emphasis mt-1"},
                                                                    "text": item["size"],
                                                                },
                                                            ],
                                                        },
                                                        {
                                                            "component": "VCol",
                                                            "props": {"cols": 3, "class": "text-right"},
                                                            "content": [
                                                                {
                                                                    "component": "VBtn",
                                                                    "props": {
                                                                        "color": "error",
                                                                        "variant": "text",
                                                                        "size": "small",
                                                                        "title": "删除",
                                                                        "class": "text-none",
                                                                    },
                                                                    "text": "删除",
                                                                    "events": {
                                                                        "click": {
                                                                            "api": delete_api,
                                                                            "method": "post",
                                                                        }
                                                                    },
                                                                }
                                                            ],
                                                        },
                                                    ],
                                                }
                                            ],
                                        },
                                    ],
                                }
                            ],
                        }
                    )
        elif self._page_tab == "history-tab":
            cover_rows.append(
                {
                    "component": "VAlert",
                    "props": {
                        "type": "info",
                        "variant": "tonal",
                        "density": "compact",
                    },
                    "text": "未发现最近生成的封面文件。请先执行一次封面生成，或检查“封面另存目录”是否已配置。",
                }
            )
            
        if self._page_tab == "clean-tab":
            page_tab = "clean-tab"

        return [
            {
                "component": "VCard",
                "content": [
                    {
                        "component": "VTabs",
                        "props": {"grow": True, "modelValue": page_tab},
                        "content": [
                            {
                                "component": "VTab",
                                "props": {"value": "generate-tab"},
                                "text": "封面生成",
                                "events": {"click": {"api": "plugin/MediaCoverGenerator/set_page_tab_generate", "method": "post"}},
                            },
                            {
                                "component": "VTab",
                                "props": {"value": "history-tab"},
                                "text": "历史封面",
                                "events": {"click": {"api": "plugin/MediaCoverGenerator/set_page_tab_history", "method": "post"}},
                            },
                            {
                                "component": "VTab",
                                "props": {"value": "clean-tab"},
                                "text": "清理缓存",
                                "events": {"click": {"api": "plugin/MediaCoverGenerator/set_page_tab_clean", "method": "post"}},
                            },
                        ],
                    },
                    {"component": "VDivider"},
                ],
            },
        ] + (
            [
                {
                    "component": "VCard",
                    "props": {"variant": "outlined", "class": "mt-3"},
                    "content": [
                                    {
                                        "component": "VCardText",
                                        "content": [
                                            {
                                                "component": "VAlert",
                                                "props": {
                                                    "type": "warning",
                                                    "variant": "tonal",
                                                    "density": "compact",
                                                    "class": "mb-3",
                                                },
                                                "text": "首次运行请先完成设置",
                                            },
                                            {
                                                "component": "div",
                                                "props": {"class": "text-caption text-medium-emphasis mb-2"},
                                                "text": "；".join(setup_warnings),
                                            },
                                            {
                                                "component": "VRow",
                                                "content": [
                                                    {
                                                        "component": "VCol",
                                            "props": {"cols": 12, "md": 9},
                                            "content": [
                                                            {
                                                                "component": "VBtn",
                                                                "props": {
                                                                    "variant": "flat",
                                                                    "color": "primary",
                                                                    "class": "text-none mr-2 mb-2",
                                                                    "prepend-icon": "mdi-swap-horizontal",
                                                                },
                                                    "text": f"切换到{'动态' if style_variant == 'static' else '静态'}",
                                                    "events": {"click": {"api": "plugin/MediaCoverGenerator/toggle_style_variant", "method": "post"}},
                                                },
                                                            {
                                                                "component": "VBtn",
                                                                "props": {
                                                                    "variant": "flat",
                                                                    "color": "primary",
                                                                    "class": "text-none mb-2",
                                                                    "prepend-icon": "mdi-play-circle-outline",
                                                                },
                                                    "text": "立即生成当前风格",
                                                    "events": {"click": {"api": "plugin/MediaCoverGenerator/generate_now", "method": "post"}},
                                                },
                                                {
                                                    "component": "div",
                                                    "props": {"class": "text-caption text-medium-emphasis ml-2 mb-2 d-inline-block"},
                                                    "text": "更多参数请点击右下角齿轮设置",
                                                },
                                            ],
                                        }
                                    ],
                                },
                                {
                                    "component": "VRow",
                                    "content": style_preview_cards,
                                },
                            ],
                        }
                    ],
                }
            ] if page_tab == "generate-tab" and setup_warnings else
            [
                {
                    "component": "VCard",
                    "props": {"variant": "outlined", "class": "mt-3"},
                    "content": [
                                    {
                                        "component": "VCardText",
                                        "content": [
                                            {
                                                "component": "VRow",
                                                "content": [
                                                    {
                                                        "component": "VCol",
                                            "props": {"cols": 12, "md": 9},
                                            "content": [
                                                            {
                                                                "component": "VBtn",
                                                                "props": {
                                                                    "variant": "flat",
                                                                    "color": "primary",
                                                                    "class": "text-none mr-2 mb-2",
                                                                    "prepend-icon": "mdi-swap-horizontal",
                                                                },
                                                    "text": f"切换到{'动态' if style_variant == 'static' else '静态'}",
                                                    "events": {"click": {"api": "plugin/MediaCoverGenerator/toggle_style_variant", "method": "post"}},
                                                },
                                                            {
                                                                "component": "VBtn",
                                                                "props": {
                                                                    "variant": "flat",
                                                                    "color": "primary",
                                                                    "class": "text-none mb-2",
                                                                    "prepend-icon": "mdi-play-circle-outline",
                                                                },
                                                    "text": "立即生成当前风格",
                                                    "events": {"click": {"api": "plugin/MediaCoverGenerator/generate_now", "method": "post"}},
                                                }
                                            ],
                                        }
                                    ],
                                },
                                {
                                    "component": "VRow",
                                    "content": style_preview_cards,
                                },
                            ],
                        }
                    ],
                }
            ] if page_tab == "generate-tab" else
            [
                {
                    "component": "VCard",
                    "props": {"variant": "outlined", "class": "mt-3"},
                    "content": [
                        {"component": "VCardTitle", "text": f"最近生成的封面（最多 {limit} 条）"},
                        {"component": "VCardText", "content": [{"component": "VRow", "content": cover_rows}]},
                    ],
                }
            ] if page_tab == "history-tab" else
            [
                {
                    "component": "VCard",
                    "props": {"variant": "outlined", "class": "mt-3"},
                    "content": [
                        {
                            "component": "VCardText",
                            "props": {"class": "pa-6 d-flex flex-column align-center"},
                            "content": [
                                            {
                                                "component": "VBtn",
                                                "props": {
                                                    "color": "error",
                                                    "variant": "flat",
                                                    "size": "large",
                                                    "prepend-icon": "mdi-image-remove",
                                                    "class": "mb-3 text-none",
                                                },
                                    "text": "立即清理图片缓存",
                                    "events": {"click": {"api": "plugin/MediaCoverGenerator/clean_images", "method": "post"}},
                                },
                                            {
                                                "component": "VBtn",
                                                "props": {
                                                    "color": "error",
                                                    "variant": "flat",
                                                    "size": "large",
                                                    "prepend-icon": "mdi-format-font",
                                                    "class": "mb-3 text-none",
                                                },
                                    "text": "立即清理字体缓存",
                                    "events": {"click": {"api": "plugin/MediaCoverGenerator/clean_fonts", "method": "post"}},
                                },
                                {
                                    "component": "div",
                                    "props": {"class": "text-caption text-medium-emphasis"},
                                    "text": "点击后立即执行，无需保存配置。",
                                },
                            ],
                        }
                    ],
                }
            ]
        )
    def __build_page_style_cards(self, style_variant: str, selected_index: int) -> List[Dict[str, Any]]:
        styles = [
            {"name": "风格1", "index": 1, "src": self.__style_preview_src(1)},
            {"name": "风格2", "index": 2, "src": self.__style_preview_src(2)},
            {"name": "风格3", "index": 3, "src": self.__style_preview_src(3)},
            {"name": "风格4", "index": 4, "src": self.__style_preview_src(4)},
        ]
        cards: List[Dict[str, Any]] = []
        for style in styles:
            cards.append(
                {
                    "component": "VCol",
                    "props": {"cols": 12, "sm": 6, "md": 3},
                    "content": [
                        {
                            "component": "VCard",
                            "props": {
                                "variant": "flat",
                                "elevation": 3 if style["index"] == selected_index else 1,
                                "color": "primary" if style["index"] == selected_index else None,
                                "class": "cursor-pointer",
                            },
                            "events": {
                                "click": {
                                    "api": f"plugin/MediaCoverGenerator/select_style_{style['index']}",
                                    "method": "post",
                                }
                            },
                            "content": [
                                {
                                    "component": "VImg",
                                    "props": {
                                        "src": style["src"],
                                        "aspect-ratio": "16/9",
                                        "cover": True,
                                    },
                                },
                                {
                                    "component": "VCardText",
                                    "props": {"class": "py-2 text-center"},
                                    "text": f"{style['name']}（{'静态' if style_variant == 'static' else '动态'}{style['index']}）" if style["index"] == selected_index else style["name"],
                                },
                            ],
                        }
                    ],
                }
            )
        return cards

    @staticmethod
    def __style_preview_src(index: int) -> str:
        safe_index = max(1, min(4, int(index)))
        return f"https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/images/style_{safe_index}.jpeg"

    def __get_recent_generated_covers(self, limit: int = 20) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        cover_dirs: List[Path] = []

        if self._covers_output:
            cover_dirs.append(Path(self._covers_output))
        data_path = self.get_data_path()
        default_output = data_path / "output"
        if default_output.exists():
            cover_dirs.append(default_output)

        allowed_ext = {".jpg", ".jpeg", ".png", ".gif", ".apng", ".webp"}
        seen = set()
        for directory in cover_dirs:
            key = str(directory)
            if key in seen:
                continue
            seen.add(key)
            if not directory.exists() or not directory.is_dir():
                continue
            for file_path in directory.iterdir():
                if not file_path.is_file():
                    continue
                if file_path.suffix.lower() not in allowed_ext:
                    continue
                try:
                    stat = file_path.stat()
                    
                    try:
                        from PIL import Image
                        from io import BytesIO
                        import base64
                        
                        # 动态生成缩略图进行 Base64 传输
                        # 1. 彻底绕开 /api/v1/plugin 外部接口存在的 401 鉴权问题
                        # 2. 将几十 MB 的动图压缩为了几十 KB 的缩略图，解决前端加载卡死问题
                        with Image.open(file_path) as img:
                            if hasattr(img, 'is_animated') and img.is_animated:
                                img.seek(0)
                                
                            thumb = img.copy()
                            if thumb.mode != 'RGB':
                                thumb = thumb.convert('RGB')
                                
                            thumb.thumbnail((480, 270))
                            buf = BytesIO()
                            thumb.save(buf, format="JPEG", quality=75)
                            image_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                            image_src = f"data:image/jpeg;base64,{image_b64}"
                            
                    except Exception as img_err:
                        logger.debug(f"生成缩略图失败 {file_path}: {img_err}")
                        continue

                    items.append(
                        {
                            "name": file_path.name,
                            "path": str(file_path),
                            "mtime_ts": float(stat.st_mtime),
                            "mtime": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                            "size": self.__format_size(stat.st_size),
                            "src": image_src,
                        }
                    )
                except Exception as e:
                    logger.debug(f"读取封面文件信息失败: {file_path} -> {e}")

        items.sort(key=lambda x: x.get("mtime_ts", 0.0), reverse=True)
        return items[:max(1, int(limit))]

    @staticmethod
    def __format_size(size_bytes: int) -> str:
        try:
            size = float(size_bytes)
        except (TypeError, ValueError):
            return "0 B"
        units = ["B", "KB", "MB", "GB"]
        for unit in units:
            if size < 1024 or unit == units[-1]:
                return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
            size /= 1024
        return f"{int(size_bytes)} B"

    def __get_saved_cover_dirs(self) -> List[Path]:
        result: List[Path] = []
        if self._covers_output:
            result.append(Path(self._covers_output))
        data_path = self.get_data_path()
        default_output = data_path / "output"
        result.append(default_output)
        unique: List[Path] = []
        seen = set()
        for directory in result:
            key = str(directory)
            if key in seen:
                continue
            seen.add(key)
            unique.append(directory)
        return unique

    def __resolve_saved_cover_path(self, raw_path: str) -> Optional[Path]:
        if not raw_path:
            return None
        decoded = unquote(str(raw_path)).strip()
        target = Path(decoded).expanduser()
        if not target.is_absolute():
            return None
        allowed_dirs = self.__get_saved_cover_dirs()
        for directory in allowed_dirs:
            try:
                root = directory.resolve()
                file_path = target.resolve()
                if str(file_path).startswith(str(root) + os.sep) or file_path == root:
                    return file_path
            except Exception:
                continue
        return None

    def __get_recent_cover_output_dir(self) -> Path:
        if self._covers_output:
            return Path(self._covers_output).expanduser()
        return self.get_data_path() / "output"

    @eventmanager.register(EventType.PluginAction)
    def update_covers(self, event: Event):
        """
        远程全量同步
        """
        if event:
            event_data = event.event_data
            if not event_data or event_data.get("action") != "update_covers":
                return
            self.post_message(
                channel=event.event_data.get("channel"),
                title="开始更新媒体库封面 ...",
                userid=event.event_data.get("user"),
            )
        tips = self.__update_all_libraries()
        if event:
            self.post_message(
                channel=event.event_data.get("channel"),
                title=tips,
                userid=event.event_data.get("user"),
            )

    @eventmanager.register(EventType.TransferComplete)
    def update_library_cover(self, event: Event):
        """
        媒体整理完成后，更新所在库封面
        """
        if not self._enabled:
            return
        if not self._transfer_monitor:
            return
        
        event_data = event.event_data    
        if not event_data:
            return
        
        # transfer: TransferInfo = event_data.get("transferinfo")        
        # Event data
        mediainfo: MediaInfo = event_data.get("mediainfo")

        # logger.info(f"转移信息：{transfer}")
        # logger.info(f"元数据：{meta}")
        # logger.info(f"媒体信息：{mediainfo}")
        # logger.info(f"监控到的媒体信息：{mediainfo}")
        if not mediainfo:
            return
            
        # 开始前清理可能遗留的停止信号，防止阻塞监控
        self._event.clear()

        # Delay
        if self._delay:
            logger.info(f"延迟 {self._delay} 秒后开始更新封面")
            time.sleep(int(self._delay))
            
        # Query the item in media server
        existsinfo = self.mschain.media_exists(mediainfo=mediainfo)
        if not existsinfo or not existsinfo.itemid:
            self.mschain.sync()
            existsinfo = self.mschain.media_exists(mediainfo=mediainfo)
            if not existsinfo:
                logger.warning(f"{mediainfo.title_year} 不存在媒体库中，可能服务器还未扫描完成，建议设置合适的延迟时间")
                return
        
        # Get item details including backdrop
        iteminfo = self.mschain.iteminfo(server=existsinfo.server, item_id=existsinfo.itemid)
        # logger.info(f"获取到媒体项 {mediainfo.title_year} 详情：{iteminfo}")
        if not iteminfo:
            logger.warning(f"获取 {mediainfo.title_year} 详情失败")
            return
            
        # Try to get library ID
        library_id = None
        library = {}
        item_id = existsinfo.itemid
        server = existsinfo.server
        service = self._servers.get(server)
        if service:
            libraries = self.__get_server_libraries(service)
        if libraries and not library_id:
            library = next(
                (library
                 for library in libraries if library.get('Locations', []) 
                 and any(iteminfo.path.startswith(path) for path in library.get('Locations', []))),
                None
            )
        
        if not library:
            logger.warning(f"找不到 {mediainfo.title_year} 所在媒体库")
            return
        if service.type == 'emby':
            library_id = library.get("Id")
        else:
            library_id = library.get("ItemId")
        if self._include_libraries and f"{server}-{library_id}" not in self._include_libraries:
            logger.info(f"{server}：{library['Name']} 不在列表中，跳过更新封面")
            return

        update_key = (server, item_id)
        if update_key in self._current_updating_items:
            logger.info(f"媒体库 {server}：{library['Name']} 的项目 {mediainfo.title_year} 正在更新中，跳过此次更新")
            return
        # self.clean_cover_history(save=True)
        old_history = self.get_data('cover_history') or []
        # 新增去重判断逻辑
        latest_item = max(
            (item for item in old_history if str(item.get("library_id")) == str(library_id)),
            key=lambda x: x["timestamp"],
            default=None
        )
        if latest_item and str(latest_item.get("item_id")) == str(item_id):
            logger.info(f"媒体 {mediainfo.title_year} 在库中是最新记录，不更新封面图")
            return
        
        # 安全地获取字体和翻译
        try:
            self.__get_fonts()
        except Exception as e:
            logger.error(f"初始化字体或翻译时出错: {e}")
            # 继续执行，但可能会影响封面生成质量
        new_history = self.update_cover_history(
            server=server, 
            library_id=library_id, 
            item_id=item_id
        )
        # logger.info(f"最新数据： {new_history}")
        self._monitor_sort = 'DateCreated'
        self._current_updating_items.add(update_key)
        if self.__update_library(service, library):
            self._monitor_sort = ''
            self._current_updating_items.remove(update_key)
            logger.info(f"媒体库 {server}：{library['Name']} 封面更新成功")

    
    def __update_all_libraries(self):
        """
        更新所有媒体库封面
        """
        if not self._enabled:
            return
        # 所有媒体服务器
        if not self._servers:
            return
        logger.info("开始检查字体 ...")
        try:
            self.__get_fonts()
        except Exception as e:
            logger.error(f"初始化过程中出错: {e}")
            logger.warning("将尝试继续执行，但可能影响封面生成质量")
        logger.info("开始更新媒体库封面 ...")
        # 开始前确保停止信号已清除
        self._event.clear()
        for server, service in self._servers.items():
            # 扫描所有媒体库
            logger.info(f"当前服务器 {server}")
            cover_style = {
                "static_1": "静态 1",
                "static_2": "静态 2",
                "static_3": "静态 3",
                "static_4": "静态 4（全屏模糊）",
                "animated_1": "卡片翻转动画",
                "animated_2": "帷幕切换动画",
                "animated_3": "斜向滚动动画",
                "animated_4": "全屏模糊渐变"
            }.get(self._cover_style, "静态 1")
            logger.info(f"当前风格 {cover_style}")
            # 获取媒体库列表
            libraries = self.__get_server_libraries(service)
            if not libraries:
                logger.warning(f"服务器 {server} 的媒体库列表获取失败")
                continue
            success_count = 0
            fail_count = 0
            for library in libraries:
                if self._event.is_set():
                    logger.info("媒体库封面更新服务停止")
                    self._event.clear()
                    return
                if service.type == 'emby':
                    library_id = library.get("Id")
                else:
                    library_id = library.get("ItemId")
                if self._include_libraries and f"{server}-{library_id}" not in self._include_libraries:
                    logger.info(f"{server}：{library['Name']} 不在列表中，跳过更新封面")
                    continue
                if self.__update_library(service, library):
                    logger.info(f"媒体库 {server}：{library['Name']} 封面更新成功")
                    success_count += 1
                else:
                    logger.warning(f"媒体库 {server}：{library['Name']} 封面更新失败")
                    fail_count += 1
        tips = f"媒体库封面更新任务结束，成功 {success_count} 个，失败 {fail_count} 个"
        logger.info(tips)
        return tips
                 

    def __update_library(self, service, library):
        library_name = library['Name']
        logger.info(f"媒体库 {service.name}：{library_name} 开始准备更新封面")
        # 自定义图像路径
        image_path = self.__check_custom_image(library_name)
        # 从配置获取标题和背景颜色
        title_result = self.__get_title_from_config(library_name)
        if len(title_result) == 3:
            title = (title_result[0], title_result[1])
            config_bg_color = title_result[2]
        else:
            title = title_result
            config_bg_color = None
        if image_path:
            logger.info(f"媒体库 {service.name}：{library_name} 从自定义路径获取封面")
            image_data = self.__generate_image_from_path(service.name, library_name, title, image_path[0], config_bg_color)
        else:
            image_data = self.__generate_from_server(service, library, title)

        if image_data:
            return self.__set_library_image(service, library, image_data)

    def __check_custom_image(self, library_name):
        if not self._covers_input:
            return None

        # 使用安全的文件名
        safe_library_name = self.__sanitize_filename(library_name)
        library_dir = os.path.join(self._covers_input, safe_library_name)
        if not os.path.isdir(library_dir):
            return None

        images = sorted([
            os.path.join(library_dir, f)
            for f in os.listdir(library_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"))
        ])
        
        return images if images else None  # 或改为 return images if images else False

    @memory_efficient_operation
    def __generate_image_from_path(self, server, library_name, title, image_path=None, config_bg_color=None):
        logger.info(f"媒体库 {server}：{library_name} 正在生成封面图 ...")

        # 执行健康检查
        if not self.health_check():
            logger.error("插件健康检查失败，无法生成封面")
            return False

        # 确保分辨率配置已初始化
        if not hasattr(self, '_resolution_config') or self._resolution_config is None:
            logger.warning("分辨率配置未初始化，重新初始化")
            # 使用用户设置的分辨率，而不是硬编码的1080p
            if self._resolution == "custom":
                try:
                    custom_w = int(self._custom_width)
                    custom_h = int(self._custom_height)
                    self._resolution_config = ResolutionConfig((custom_w, custom_h))
                except ValueError:
                    logger.warning(f"自定义分辨率参数无效: {self._custom_width}x{self._custom_height}, 使用默认1080p")
                    self._resolution_config = ResolutionConfig("1080p")
            else:
                self._resolution_config = ResolutionConfig(self._resolution)

        # 使用分辨率配置计算字体大小
        try:
            base_zh_font_size = float(self._zh_font_size) if self._zh_font_size else 170
        except ValueError:
            base_zh_font_size = 170
            
        try:
            base_en_font_size = float(self._en_font_size) if self._en_font_size else 75
        except ValueError:
            base_en_font_size = 75

        try:
            title_scale = float(self._title_scale) if self._title_scale else 1.0
        except (ValueError, TypeError):
            title_scale = 1.0
        if title_scale <= 0:
            title_scale = 1.0
        if self._cover_style.startswith("animated"):
            zh_font_size = float(base_zh_font_size) * title_scale
            en_font_size = float(base_en_font_size) * title_scale
        else:
            # 静态风格按当前分辨率缩放
            zh_font_size = self._resolution_config.get_font_size(base_zh_font_size) * title_scale
            en_font_size = self._resolution_config.get_font_size(base_en_font_size) * title_scale

        blur_size = self._blur_size or 50
        color_ratio = self._color_ratio or 0.8

        # 检查字体路径是否有效
        if not self._zh_font_path or not self._en_font_path:
            logger.error("字体路径未设置或无效，无法生成封面")
            return False

        # 验证字体文件是否存在
        if not validate_font_file(Path(self._zh_font_path)):
            logger.error(f"主标题字体文件无效: {self._zh_font_path}")
            return False

        if not validate_font_file(Path(self._en_font_path)):
            logger.error(f"副标题字体文件无效: {self._en_font_path}")
            return False

        font_path = (str(self._zh_font_path), str(self._en_font_path))
        font_size = (float(zh_font_size), float(en_font_size))

        zh_font_offset = float(self._zh_font_offset or 0)
        title_spacing = float(self._title_spacing or 40) * title_scale
        en_line_spacing = float(self._en_line_spacing or 40) * title_scale
        font_offset = (float(zh_font_offset), float(title_spacing), float(en_line_spacing))

        # 记录分辨率配置信息
        logger.info(f"当前分辨率配置: {self._resolution_config}")

        # 准备背景颜色配置
        bg_color_config = {
            'mode': self._bg_color_mode,
            'custom_color': self._custom_bg_color,
            'config_color': config_bg_color
        }

        # 传递分辨率配置给图像生成函数
        if self._cover_style == 'static_1':
            image_data = create_style_static_1(image_path, title, font_path,
                                                font_size=font_size,
                                                font_offset=font_offset,
                                                blur_size=blur_size,
                                                color_ratio=color_ratio,
                                                resolution_config=self._resolution_config,
                                                bg_color_config=bg_color_config)
        elif self._cover_style == 'static_2':
            image_data = create_style_static_2(image_path, title, font_path,
                                                font_size=font_size,
                                                font_offset=font_offset,
                                                blur_size=blur_size,
                                                color_ratio=color_ratio,
                                                resolution_config=self._resolution_config,
                                                bg_color_config=bg_color_config)
        elif self._cover_style == 'static_4':
            image_data = create_style_static_4(image_path, title, font_path,
                                                font_size=font_size,
                                                font_offset=font_offset,
                                                blur_size=blur_size,
                                                color_ratio=color_ratio,
                                                resolution_config=self._resolution_config,
                                                bg_color_config=bg_color_config)
        elif self._cover_style == 'static_3':
            # 使用安全的文件名
            safe_library_name = self.__sanitize_filename(library_name)
            if image_path:
                library_dir = Path(self._covers_input) / safe_library_name
            else:
                library_dir = Path(self._covers_path) / safe_library_name
            logger.info(f"static_3: 准备图片目录 {library_dir}")
            if self.prepare_library_images(library_dir, required_items=9):
                logger.info("static_3: 图片目录准备完成，开始生成封面")
                image_data = create_style_static_3(library_dir, title, font_path,
                                                    font_size=font_size,
                                                    font_offset=font_offset,
                                                    is_blur=self._multi_1_blur,
                                                    blur_size=blur_size,
                                                    color_ratio=color_ratio,
                                                    resolution_config=self._resolution_config,
                                                    bg_color_config=bg_color_config)
            else:
                logger.warning(f"static_3: 图片目录准备失败 {library_dir}")
        elif self._cover_style == 'animated_3':
            # 动态封面强制使用 320x180 分辨率以保证性能
            anim_res = '320x180'
            logger.info(f"强制动图生成分辨率为: {anim_res}")
            
            # 动态封面逻辑，类似于 multi_1
            safe_library_name = self.__sanitize_filename(library_name)
            if image_path:
                library_dir = Path(self._covers_input) / safe_library_name
            else:
                library_dir = Path(self._covers_path) / safe_library_name
            
            logger.info(f"正在准备库图片目录: {library_dir}")
            if self.prepare_library_images(library_dir, required_items=9):
                logger.info("库图片准备完成，开始调用 create_style_animated_3")
                image_data = create_style_animated_3(library_dir, title, font_path,
                                                    font_size=font_size,
                                                    font_offset=font_offset,
                                                    is_blur=self._multi_1_blur,
                                                    blur_size=blur_size,
                                                    color_ratio=color_ratio,
                                                    resolution_config=self._resolution_config,
                                                    bg_color_config=bg_color_config,
                                                    animation_duration=self._animation_duration,
                                                    animation_scroll=self._animation_scroll,
                                                    animation_fps=self._animation_fps,
                                                    animation_format=self._animation_format,
                                                    animation_resolution=anim_res,
                                                    animation_reduce_colors=self._animation_reduce_colors,
                                                    stop_event=self._event)
        elif self._cover_style == 'animated_1':
            # 动态封面强制使用 320x180 分辨率以保证性能
            anim_res = '320x180'
            logger.info(f"强制动图生成分辨率为: {anim_res}")

            animated_2_image_count = self.__get_animated_2_required_items()

            # 动态封面逻辑，类似于 multi_1
            safe_library_name = self.__sanitize_filename(library_name)
            if image_path:
                library_dir = Path(self._covers_input) / safe_library_name
            else:
                library_dir = Path(self._covers_path) / safe_library_name

            logger.info(f"正在准备库图片目录: {library_dir}")
            if self.prepare_library_images(library_dir, required_items=animated_2_image_count):
                logger.info("库图片准备完成，开始调用 create_style_animated_1")
                image_data = create_style_animated_1(library_dir, title, font_path,
                                                    font_size=font_size,
                                                    font_offset=font_offset,
                                                    is_blur=self._multi_1_blur,
                                                    blur_size=blur_size,
                                                    color_ratio=color_ratio,
                                                    resolution_config=self._resolution_config,
                                                    bg_color_config=bg_color_config,
                                                    animation_duration=self._animation_duration,
                                                    animation_fps=self._animation_fps,
                                                    animation_format=self._animation_format,
                                                    animation_resolution=anim_res,
                                                    animation_reduce_colors=self._animation_reduce_colors,
                                                    image_count=animated_2_image_count,
                                                    departure_type=self._animated_2_departure_type,
                                                    stop_event=self._event)
        elif self._cover_style == 'animated_2':
            # 动态封面强制使用 320x180 分辨率以保证性能
            anim_res = '320x180'
            logger.info(f"强制动图生成分辨率为: {anim_res}")

            safe_library_name = self.__sanitize_filename(library_name)
            if image_path:
                library_dir = Path(self._covers_input) / safe_library_name
            else:
                library_dir = Path(self._covers_path) / safe_library_name

            logger.info(f"正在准备库图片目录: {library_dir}")
            if self.prepare_library_images(library_dir, required_items=9):
                logger.info("库图片准备完成，开始调用 create_style_animated_2")
                image_data = create_style_animated_2(library_dir, title, font_path,
                                                    font_size=font_size,
                                                    font_offset=font_offset,
                                                    is_blur=self._multi_1_blur,
                                                    blur_size=blur_size,
                                                    color_ratio=color_ratio,
                                                    resolution_config=self._resolution_config,
                                                    bg_color_config=bg_color_config,
                                                    animation_duration=self._animation_duration,
                                                    animation_fps=self._animation_fps,
                                                    animation_format=self._animation_format,
                                                    animation_resolution=anim_res,
                                                    animation_reduce_colors=self._animation_reduce_colors,
                                                    image_count=self.__get_animated_2_required_items(),
                                                    stop_event=self._event)
        elif self._cover_style == 'animated_4':
            anim_res = '320x180'
            logger.info(f"强制动图生成分辨率为: {anim_res}")

            animated_2_image_count = self.__get_animated_2_required_items()

            safe_library_name = self.__sanitize_filename(library_name)
            if image_path:
                library_dir = Path(self._covers_input) / safe_library_name
            else:
                library_dir = Path(self._covers_path) / safe_library_name

            logger.info(f"正在准备库图片目录: {library_dir}")
            if self.prepare_library_images(library_dir, required_items=animated_2_image_count):
                logger.info("库图片准备完成，开始调用 create_style_animated_4")
                image_data = create_style_animated_4(library_dir, title, font_path,
                                                    font_size=font_size,
                                                    font_offset=font_offset,
                                                    is_blur=self._multi_1_blur,
                                                    blur_size=blur_size,
                                                    color_ratio=color_ratio,
                                                    resolution_config=self._resolution_config,
                                                    bg_color_config=bg_color_config,
                                                    animation_duration=self._animation_duration,
                                                    animation_fps=self._animation_fps,
                                                    animation_format=self._animation_format,
                                                    animation_resolution=anim_res,
                                                    animation_reduce_colors=self._animation_reduce_colors,
                                                    image_count=animated_2_image_count,
                                                    stop_event=self._event)
        return image_data
    
    def __generate_from_server(self, service, library, title):

        logger.info(f"媒体库 {service.name}：{library['Name']} 开始筛选媒体项")
        required_items = self.__get_required_items()
        
        # 获取项目集合
        items = []
        offset = 0
        batch_size = 50  # 每次获取的项目数量
        max_attempts = 20  # 最大尝试次数，防止无限循环
        
        library_type = library.get('CollectionType')
        if service.type == 'emby':
            library_id = library.get("Id")
        else:
            library_id = library.get("ItemId")
        parent_id = library_id
        
        # 处理合集类型的特殊情况
        if library_type == "boxsets":
            return self.__handle_boxset_library(service, library, title)
        elif library_type == "playlists":
            return self.__handle_playlist_library(service, library, title)
        elif library_type == "music":
            include_types = 'MusicAlbum,Audio'
        else:
            # 基础类型映射
            if self.__is_single_image_style():
                include_types = {
                    "PremiereDate": "Movie,Series",
                    "DateCreated": "Movie,Episode",
                    "Random": "Movie,Series"
                }.get(self._sort_by, "Movie,Series")
            else:
                # 对于多图样式，如果按最新入库排序（DateCreated），也要包含 Episode 以展示剧集的最新动态
                if self._sort_by == "DateCreated":
                    include_types = "Movie,Episode"
                else:
                    # 其他排序方式默认使用 Series 获取海报
                    include_types = "Movie,Series"
            logger.debug(f"媒体库筛选类型: {include_types}, 排序方式: {self._sort_by}")
        self._seen_keys = set()
        for attempt in range(max_attempts):
            if self._event.is_set():
                logger.info("检测到停止信号，中断媒体项获取 ...")
                return False
                
            batch_items = self.__get_items_batch(service, parent_id,
                                              offset=offset, limit=batch_size,
                                              include_types=include_types)
            
            if not batch_items:
                break  # 没有更多项目可获取
                
            # 筛选有效项目（有所需图片的项目）
            valid_items = self.__filter_valid_items(batch_items)
            items.extend(valid_items)
            
            # 如果已经有足够的有效项目，则停止获取
            if len(items) >= required_items:
                break
                
            offset += batch_size
        
        # 使用获取到的有效项目更新封面
        if len(items) > 0:
            logger.info(f"媒体库 {service.name}：{library['Name']} 找到 {len(items)} 个有效项目")
            if self.__is_single_image_style():
                return self.__update_single_image(service, library, title, items[0])
            else:
                return self.__update_grid_image(service, library, title, items[:required_items])
        else:
            logger.warning(f"媒体库 {service.name}：{library['Name']} 无法找到有效的图片项目 (筛选类型: {include_types})")
            return False
        
    def __handle_boxset_library(self, service, library, title):

        include_types = 'BoxSet,Movie'
        if service.type == 'emby':
            library_id = library.get("Id")
        else:
            library_id = library.get("ItemId")
        parent_id = library_id
        boxsets = self.__get_items_batch(service, parent_id,
                                      include_types=include_types)
        
        required_items = self.__get_required_items()
        valid_items = []
        
        # 首先检查BoxSet本身是否有合适的图片
        self._seen_keys = set()

        valid_boxsets = self.__filter_valid_items(boxsets)
        valid_items.extend(valid_boxsets)
        
        # 如果BoxSet本身没有足够的图片，则获取其中的电影
        if len(valid_items) < required_items:
            for boxset in boxsets:
                if len(valid_items) >= required_items:
                    break
                    
                # 获取此BoxSet中的电影
                movies = self.__get_items_batch(service,
                                             parent_id=boxset['Id'], 
                                             include_types=include_types)
                
                valid_movies = self.__filter_valid_items(movies)
                valid_items.extend(valid_movies)
                
                if len(valid_items) >= required_items:
                    break
        
        # 使用获取到的有效项目更新封面
        if len(valid_items) > 0:
            if self.__is_single_image_style():
                return self.__update_single_image(service, library, title, valid_items[0])
            else:
                return self.__update_grid_image(service, library, title, valid_items[:required_items])
        else:
            print(f"媒体库 {service.name}：{library['Name']} 无法找到有效的图片项目")
            return False
        
    def __handle_playlist_library(self, service, library, title):
        """ 
        播放列表图片获取 
        """
        include_types = 'Playlist,Movie,Series,Episode,Audio'
        if service.type == 'emby':
            library_id = library.get("Id")
        else:
            library_id = library.get("ItemId")
        parent_id = library_id
        playlists = self.__get_items_batch(service, parent_id,
                                      include_types=include_types)
        
        required_items = self.__get_required_items()
        valid_items = []
        
        # 首先检查 playlist 本身是否有合适的图片
        self._seen_keys = set()

        valid_playlists = self.__filter_valid_items(playlists)
        valid_items.extend(valid_playlists)
        
        # 如果 playlist 本身没有足够的图片，则获取其中的电影
        if len(valid_items) < required_items:
            for playlist in playlists:
                if len(valid_items) >= required_items:
                    break
                    
                # 获取此 playlist 中的电影
                movies = self.__get_items_batch(service,
                                             parent_id=playlist['Id'], 
                                             include_types=include_types)
                
                valid_movies = self.__filter_valid_items(movies)
                valid_items.extend(valid_movies)
                
                if len(valid_items) >= required_items:
                    break
        
        # 使用获取到的有效项目更新封面
        if len(valid_items) > 0:
            if self.__is_single_image_style():
                return self.__update_single_image(service, library, title, valid_items[0])
            else:
                return self.__update_grid_image(service, library, title, valid_items[:required_items])
        else:
            print(f"警告: 无法为播放列表 {service.name}：{library['Name']} 找到有效的图片项目")
            return False
        
    def __get_items_batch(self, service, parent_id, offset=0, limit=20, include_types=None):
        # 调用API获取项目
        try:
            if not service:
                return []
            
            try:
                if not self._sort_by:
                    sort_by = 'Random'
                else:
                    sort_by = self._sort_by
                if self._monitor_sort:
                    sort_by = 'DateCreated'
                    # 转移监控模式下强制包含 Episode 以获取最新入库的内容
                    include_types = 'Movie,Episode'
                if not include_types:
                    include_types = 'Movie,Series'

                url = f'[HOST]emby/Items/?api_key=[APIKEY]' \
                      f'&ParentId={parent_id}&SortBy={sort_by}&Limit={limit}' \
                      f'&StartIndex={offset}&IncludeItemTypes={include_types}' \
                      f'&Recursive=True&SortOrder=Descending'

                res = service.instance.get_data(url=url)
                if res:
                    data = res.json()
                    return data.get("Items", [])
            except Exception as err:
                logger.error(f"获取媒体项失败：{str(err)}")
            return []
                
        except Exception as err:
            logger.error(f"Failed to get latest items: {str(err)}")
            return []
        
    def __filter_valid_items(self, items):
        """筛选有效的项目（包含所需图片的项目），并按图片标签去重"""
        valid_items = []

        for item in items:
            # 1) 根据当前样式计算真实会使用的图片URL
            image_url = self.__get_image_url(item)
            if not image_url:
                continue

            # 2) 两层去重：
            #    - content_key: 内容层（如同一剧集的多集使用同一Series图）
            #    - image_key:   图片层（同一图片tag或同一路径）
            content_key = self.__build_content_key(item)
            image_key = self.__build_image_key(image_url)

            if not content_key and not image_key:
                continue

            if (content_key and content_key in self._seen_keys) or (image_key and image_key in self._seen_keys):
                continue

            # 3) 加入有效列表并记录已处理的 Key
            valid_items.append(item)
            if content_key:
                self._seen_keys.add(content_key)
            if image_key:
                self._seen_keys.add(image_key)

        return valid_items

    def __build_content_key(self, item: dict) -> Optional[str]:
        """构建内容去重Key，尽量让同一来源内容只入选一次。"""
        item_type = item.get("Type")

        if item_type == "Episode":
            if item.get("SeriesId"):
                return f"series:{item.get('SeriesId')}"
            if item.get("ParentBackdropItemId"):
                return f"parent:{item.get('ParentBackdropItemId')}"

        if item_type in ["MusicAlbum", "Audio"]:
            if item.get("AlbumId"):
                return f"album:{item.get('AlbumId')}"
            if item.get("ParentBackdropItemId"):
                return f"parent:{item.get('ParentBackdropItemId')}"

        if item.get("Id"):
            return f"item:{item.get('Id')}"

        return None

    def __build_image_key(self, image_url: str) -> Optional[str]:
        """构建图片去重Key，忽略api_key，避免同图重复。"""
        if not image_url:
            return None

        try:
            # 统一移除 api_key 参数，避免同图不同密钥导致重复
            normalized = re.sub(r"([?&])api_key=[^&]*", "", image_url).rstrip("?&")

            # 优先用路径 + tag 作为去重关键字（能精准区分图像版本）
            # 例如: /Items/{id}/Images/Backdrop/0?tag=xxx
            tag_match = re.search(r"[?&]tag=([^&]+)", image_url)
            tag = tag_match.group(1) if tag_match else ""

            parsed = urlparse(normalized)
            path = parsed.path if parsed.path else normalized
            return f"img:{path}|tag:{tag}"
        except Exception:
            return f"img:{image_url}"


    
    def __update_single_image(self, service, library, title, item):
        """更新单图封面"""
        logger.info(f"媒体库 {service.name}：{library['Name']} 从媒体项获取图片")
        updated_item_id = ''
        image_url = self.__get_image_url(item)
        if not image_url:
            return False
            
        image_path = self.__download_image(service, image_url, library['Name'], count=1)
        if not image_path:
            return False
        updated_item_id = self.__get_item_id(item)
        # 从配置获取背景颜色
        title_result = self.__get_title_from_config(library['Name'])
        config_bg_color = title_result[2] if len(title_result) == 3 else None
        image_data = self.__generate_image_from_path(service.name, library['Name'], title, image_path, config_bg_color)
            
        if not image_data:
            return False
        if service.type == 'emby':
            library_id = library.get("Id")
        else:
            library_id = library.get("ItemId")
        # 更新id
        self.update_cover_history(
            server=service.name, 
            library_id=library_id, 
            item_id=updated_item_id
        )

        return image_data
    
    def __update_grid_image(self, service, library, title, items):
        """更新九宫格封面"""
        logger.info(f"媒体库 {service.name}：{library['Name']} 从媒体项获取图片")

        image_paths = []
        
        updated_item_ids = []
        for i, item in enumerate(items):
            if self._event.is_set():
                logger.info("检测到停止信号，中断图片下载 ...")
                return False
            image_url = self.__get_image_url(item)
            if image_url:
                image_path = self.__download_image(service, image_url, library['Name'], count=i+1)
                if image_path:
                    image_paths.append(image_path)
                    updated_item_ids.append(self.__get_item_id(item))
        
        if len(image_paths) < 1:
            return False
            
        # 生成九宫格图片
        # 从配置获取背景颜色
        title_result = self.__get_title_from_config(library['Name'])
        config_bg_color = title_result[2] if len(title_result) == 3 else None
        image_data = self.__generate_image_from_path(service.name, library['Name'], title, None, config_bg_color)
        if not image_data:
            return False
        if service.type == 'emby':
            library_id = library.get("Id")
        else:
            library_id = library.get("ItemId")
        # 更新ids
        for item_id in reversed(updated_item_ids):
            self.update_cover_history(
                server=service.name, 
                library_id=library_id, 
                item_id=item_id
            )
            
        return image_data
    
    def __load_title_config(self, yaml_str: str) -> dict:
        try:
            # 替换全角冒号为半角
            yaml_str = yaml_str.replace("：", ":")
            # 替换制表符为两个空格，统一缩进
            yaml_str = yaml_str.replace("\t", "  ")

            # 处理数字或字母开头的媒体库名，确保它们被正确解析为字符串键
            # 在YAML中，数字开头的键可能被解析为数字，需要加引号
            lines = yaml_str.split('\n')
            processed_lines = []
            for line in lines:
                # 检查是否是键值对行（包含冒号且不是注释）
                if ':' in line and not line.strip().startswith('#'):
                    # 分割键和值
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key_part = parts[0].strip()
                        value_part = parts[1]

                        # 如果键不是以引号开头，且包含数字或特殊字符，则添加引号
                        if key_part and not (key_part.startswith('"') or key_part.startswith("'")):
                            # 检查是否需要加引号（数字开头、包含特殊字符等）
                            if (key_part[0].isdigit() or
                                any(char in key_part for char in [' ', '-', '.', '(', ')', '[', ']'])):
                                key_part = f'"{key_part}"'

                        processed_lines.append(f"{key_part}:{value_part}")
                    else:
                        processed_lines.append(line)
                else:
                    processed_lines.append(line)

            processed_yaml = '\n'.join(processed_lines)
            preview_limit = 800
            flat_yaml = " ".join(part.strip() for part in processed_yaml.splitlines() if part.strip())
            if len(flat_yaml) > preview_limit:
                logger.debug(f"处理后的YAML(扁平, 前{preview_limit}字): {flat_yaml[:preview_limit]}... (已截断)")
            else:
                logger.debug(f"处理后的YAML(扁平): {flat_yaml}")

            title_config = yaml.safe_load(processed_yaml) or {}
            if not isinstance(title_config, dict):
                return {}
            filtered = {}
            for key, value in title_config.items():
                if isinstance(value, list) and len(value) >= 2 and isinstance(value[0], str) and isinstance(value[1], str):
                    # 支持两行或三行配置（第三行可选）
                    if len(value) >= 3 and isinstance(value[2], str):
                        filtered[str(key)] = [value[0], value[1], value[2]]
                    else:
                        filtered[str(key)] = [value[0], value[1]]
                    if len(value) > 3:
                        logger.info(f"配置项 {key} 包含多行，只使用前三行")
                else:
                    # 忽略格式不正确的项
                    logger.warning(f"标题配置项格式不正确，已忽略: {key} -> {value}")
                    continue

            logger.debug(f"解析后的配置: {filtered}")
            return filtered
        except Exception as e:
            # 整体 YAML 无法解析（比如语法错误），返回空配置
            logger.warning(f"YAML 解析失败，使用空配置: {e}")
            return {}

    def __get_title_from_config(self, library_name):
        """
        从 yaml 配置中获取媒体库的主副标题和背景颜色
        """
        zh_title = library_name
        en_title = ''
        bg_color = None
        title_config = {}
        if self._current_config:
            title_config = self._current_config
        elif self._title_config:
            title_config = self.__load_title_config(self._title_config)

        # 添加调试信息
        logger.debug(f"查找媒体库名称: '{library_name}' (类型: {type(library_name)})")
        logger.debug(f"可用的配置键: {list(title_config.keys())}")

        # 多种匹配策略，确保数字或字母开头的媒体库名能够正确匹配
        for lib_name, config_values in title_config.items():
            # 策略1: 直接字符串比较
            if str(lib_name) == str(library_name):
                zh_title = config_values[0]
                en_title = config_values[1] if len(config_values) > 1 else ''
                bg_color = config_values[2] if len(config_values) > 2 else None
                logger.debug(f"找到匹配的配置(直接匹配): {lib_name} -> {zh_title}, {en_title}, {bg_color}")
                break

            # 策略2: 去除空格后比较
            if str(lib_name).strip() == str(library_name).strip():
                zh_title = config_values[0]
                en_title = config_values[1] if len(config_values) > 1 else ''
                bg_color = config_values[2] if len(config_values) > 2 else None
                logger.debug(f"找到匹配的配置(去空格匹配): {lib_name} -> {zh_title}, {en_title}, {bg_color}")
                break

            # 策略3: 忽略大小写比较
            if str(lib_name).lower() == str(library_name).lower():
                zh_title = config_values[0]
                en_title = config_values[1] if len(config_values) > 1 else ''
                bg_color = config_values[2] if len(config_values) > 2 else None
                logger.debug(f"找到匹配的配置(忽略大小写匹配): {lib_name} -> {zh_title}, {en_title}, {bg_color}")
                break
        else:
            logger.debug(f"未找到媒体库 '{library_name}' 的配置，使用默认标题")
            # 如果没有找到配置，检查是否是数字开头的媒体库名导致的问题
            if library_name and (library_name[0].isdigit() or library_name[0].isalpha()):
                logger.info(f"媒体库名 '{library_name}' 以数字或字母开头，如果需要自定义标题，请在配置中使用引号包围媒体库名，例如: \"{library_name}\":")

        return (zh_title, en_title, bg_color)
    
    def __get_server_libraries(self, service):
        try:
            if not service:
                return []
            try:
                if service.type == 'emby':
                    url = f'[HOST]emby/Library/VirtualFolders/Query?api_key=[APIKEY]'
                else:
                    url = f'[HOST]emby/Library/VirtualFolders/?api_key=[APIKEY]'
                res = service.instance.get_data(url=url)
                if res:
                    data = res.json()
                    if service.type == 'emby':
                        return data.get("Items", [])
                    else:
                        return data
            except Exception as err:
                logger.error(f"获取媒体库列表失败：{str(err)}")
            return []
        except Exception as err:
            logger.error(f"获取媒体库列表失败：{str(err)}")
            return []
    
    def __get_all_libraries(self, server, service):
        try:
            lib_items = []
            libraries = self.__get_server_libraries(service)
            for library in libraries:
                if service.type == 'emby':
                    library_id = library.get("Id")
                else:
                    library_id = library.get("ItemId")
                if library['Name'] and library_id:
                    lib_item = {
                        "name": f"{server}: {library['Name']}",
                        "value": f"{server}-{library_id}"
                    }
                    lib_items.append(lib_item)
            return lib_items
        except Exception as err:
            logger.error(f"获取所有媒体库失败：{str(err)}")
            return []
        
    def __get_image_url(self, item):
        """
        从媒体项信息中获取图片URL
        """
        # Emby/Jellyfin
        if item['Type'] in 'MusicAlbum,Audio':
            if item.get("ParentBackdropImageTags") and len(item["ParentBackdropImageTags"]) > 0:
                item_id = item.get("ParentBackdropItemId")
                tag = item["ParentBackdropImageTags"][0]
                return f'[HOST]emby/Items/{item_id}/Images/Backdrop/0?tag={tag}&api_key=[APIKEY]'
            elif item.get("PrimaryImageTag"):
                item_id = item.get("PrimaryImageItemId")
                tag = item.get("PrimaryImageTag")
                return f'[HOST]emby/Items/{item_id}/Images/Primary?tag={tag}&api_key=[APIKEY]'
            elif item.get("AlbumPrimaryImageTag"):
                item_id = item.get("AlbumId")
                tag = item.get("AlbumPrimaryImageTag")
                return f'[HOST]emby/Items/{item_id}/Images/Primary?tag={tag}&api_key=[APIKEY]'

        elif self._cover_style == 'static_3' or self._cover_style in ['animated_1', 'animated_2', 'animated_3', 'animated_4']:
            if self._use_primary:
                if item.get("Type") == 'Episode':
                    if item.get("SeriesPrimaryImageTag"):
                        item_id = item.get("SeriesId")
                        tag = item.get("SeriesPrimaryImageTag")
                        return f'[HOST]emby/Items/{item_id}/Images/Primary?tag={tag}&api_key=[APIKEY]'
                    elif item.get("ParentBackdropImageTags") and len(item["ParentBackdropImageTags"]) > 0:
                        item_id = item.get("ParentBackdropItemId")
                        tag = item["ParentBackdropImageTags"][0]
                        return f'[HOST]emby/Items/{item_id}/Images/Backdrop/0?tag={tag}&api_key=[APIKEY]'
                elif item.get("ImageTags") and item.get("ImageTags").get("Primary"):
                    item_id = item.get("Id")
                    tag = item.get("ImageTags").get("Primary")
                    return f'[HOST]emby/Items/{item_id}/Images/Primary?tag={tag}&api_key=[APIKEY]'
                elif item.get("ParentBackdropImageTags") and len(item["ParentBackdropImageTags"]) > 0:
                    item_id = item.get("ParentBackdropItemId")
                    tag = item["ParentBackdropImageTags"][0]
                    return f'[HOST]emby/Items/{item_id}/Images/Backdrop/0?tag={tag}&api_key=[APIKEY]'
                elif item.get("BackdropImageTags") and len(item["BackdropImageTags"]) > 0:
                    item_id = item.get("Id")
                    tag = item["BackdropImageTags"][0]
                    return f'[HOST]emby/Items/{item_id}/Images/Backdrop/0?tag={tag}&api_key=[APIKEY]'
            else:
                if item.get("Type") == 'Episode':
                    if item.get("ParentBackdropImageTags") and len(item["ParentBackdropImageTags"]) > 0:
                        item_id = item.get("ParentBackdropItemId")
                        tag = item["ParentBackdropImageTags"][0]
                        return f'[HOST]emby/Items/{item_id}/Images/Backdrop/0?tag={tag}&api_key=[APIKEY]'
                    elif item.get("SeriesPrimaryImageTag"):
                        item_id = item.get("SeriesId")
                        tag = item.get("SeriesPrimaryImageTag")
                        return f'[HOST]emby/Items/{item_id}/Images/Primary?tag={tag}&api_key=[APIKEY]'
                if item.get("ParentBackdropImageTags") and len(item["ParentBackdropImageTags"]) > 0:
                    item_id = item.get("ParentBackdropItemId")
                    tag = item["ParentBackdropImageTags"][0]
                    return f'[HOST]emby/Items/{item_id}/Images/Backdrop/0?tag={tag}&api_key=[APIKEY]'
                elif item.get("BackdropImageTags") and len(item["BackdropImageTags"]) > 0:
                    item_id = item.get("Id")
                    tag = item["BackdropImageTags"][0]
                    return f'[HOST]emby/Items/{item_id}/Images/Backdrop/0?tag={tag}&api_key=[APIKEY]'
                elif item.get("ImageTags") and item.get("ImageTags").get("Primary"):
                    item_id = item.get("Id")
                    tag = item.get("ImageTags").get("Primary")
                    return f'[HOST]emby/Items/{item_id}/Images/Primary?tag={tag}&api_key=[APIKEY]'

        elif self._cover_style.startswith('static'):
            if self._use_primary:
                if item.get("Type") == 'Episode':
                    if item.get("SeriesPrimaryImageTag"):
                        item_id = item.get("SeriesId")
                        tag = item.get("SeriesPrimaryImageTag")
                        return f'[HOST]emby/Items/{item_id}/Images/Primary?tag={tag}&api_key=[APIKEY]'
                    elif item.get("ParentBackdropImageTags") and len(item["ParentBackdropImageTags"]) > 0:
                        item_id = item.get("ParentBackdropItemId")
                        tag = item["ParentBackdropImageTags"][0]
                        return f'[HOST]emby/Items/{item_id}/Images/Backdrop/0?tag={tag}&api_key=[APIKEY]'
                elif item.get("ImageTags") and item.get("ImageTags").get("Primary"):
                    item_id = item.get("Id")
                    tag = item.get("ImageTags").get("Primary")
                    return f'[HOST]emby/Items/{item_id}/Images/Primary?tag={tag}&api_key=[APIKEY]'
                elif item.get("ParentBackdropImageTags") and len(item["ParentBackdropImageTags"]) > 0:
                    item_id = item.get("ParentBackdropItemId")
                    tag = item["ParentBackdropImageTags"][0]
                    return f'[HOST]emby/Items/{item_id}/Images/Backdrop/0?tag={tag}&api_key=[APIKEY]'
                elif item.get("BackdropImageTags") and len(item["BackdropImageTags"]) > 0:
                    item_id = item.get("Id")
                    tag = item["BackdropImageTags"][0]
                    return f'[HOST]emby/Items/{item_id}/Images/Backdrop/0?tag={tag}&api_key=[APIKEY]'
            else:
                if item.get("Type") == 'Episode':
                    if item.get("ParentBackdropImageTags") and len(item["ParentBackdropImageTags"]) > 0:
                        item_id = item.get("ParentBackdropItemId")
                        tag = item["ParentBackdropImageTags"][0]
                        return f'[HOST]emby/Items/{item_id}/Images/Backdrop/0?tag={tag}&api_key=[APIKEY]'
                    elif item.get("SeriesPrimaryImageTag"):
                        item_id = item.get("SeriesId")
                        tag = item.get("SeriesPrimaryImageTag")
                        return f'[HOST]emby/Items/{item_id}/Images/Primary?tag={tag}&api_key=[APIKEY]'
                elif item.get("ParentBackdropImageTags") and len(item["ParentBackdropImageTags"]) > 0:
                    item_id = item.get("ParentBackdropItemId")
                    tag = item["ParentBackdropImageTags"][0]
                    return f'[HOST]emby/Items/{item_id}/Images/Backdrop/0?tag={tag}&api_key=[APIKEY]'
                elif item.get("BackdropImageTags") and len(item["BackdropImageTags"]) > 0:
                    item_id = item.get("Id")
                    tag = item["BackdropImageTags"][0]
                    return f'[HOST]emby/Items/{item_id}/Images/Backdrop/0?tag={tag}&api_key=[APIKEY]'
                elif item.get("ImageTags") and item.get("ImageTags").get("Primary"):
                    item_id = item.get("Id")
                    tag = item.get("ImageTags").get("Primary")
                    return f'[HOST]emby/Items/{item_id}/Images/Primary?tag={tag}&api_key=[APIKEY]'
            
    def __get_item_id(self, item):
        """
        从媒体项信息中获取项目ID
        """
        # Emby/Jellyfin
        if item['Type'] in 'MusicAlbum,Audio':
            if item.get("ParentBackdropImageTags") and len(item["ParentBackdropImageTags"]) > 0:
                item_id = item.get("ParentBackdropItemId")
            elif item.get("PrimaryImageTag"):
                item_id = item.get("PrimaryImageItemId")
            elif item.get("AlbumPrimaryImageTag"):
                item_id = item.get("AlbumId")

        elif self._cover_style == 'static_3' or self._cover_style in ['animated_1', 'animated_2', 'animated_3', 'animated_4']:
            if self._use_primary:
                if (item.get("ImageTags") and item.get("ImageTags").get("Primary")) \
                    or (item.get("BackdropImageTags") and len(item["BackdropImageTags"]) > 0):
                    item_id = item.get("Id")
                elif item.get("ParentBackdropImageTags") and len(item["ParentBackdropImageTags"]) > 0:
                    item_id = item.get("ParentBackdropItemId")
            else:
                if item.get("ParentBackdropImageTags") and len(item["ParentBackdropImageTags"]) > 0:
                    item_id = item.get("ParentBackdropItemId")
                elif (item.get("ImageTags") and item.get("ImageTags").get("Primary")) \
                    or (item.get("BackdropImageTags") and len(item["BackdropImageTags"]) > 0):
                    item_id = item.get("Id")

        elif self._cover_style.startswith('static'):
            if self._use_primary:
                if (item.get("BackdropImageTags") and len(item["BackdropImageTags"]) > 0) \
                    or (item.get("ImageTags") and item.get("ImageTags").get("Primary")):
                    item_id = item.get("Id")
                elif item.get("ParentBackdropImageTags") and len(item["ParentBackdropImageTags"]) > 0:
                    item_id = item.get("ParentBackdropItemId")
            else:
                if item.get("ParentBackdropImageTags") and len(item["ParentBackdropImageTags"]) > 0:
                    item_id = item.get("ParentBackdropItemId")
                elif (item.get("BackdropImageTags") and len(item["BackdropImageTags"]) > 0) \
                    or (item.get("ImageTags") and item.get("ImageTags").get("Primary")):
                    item_id = item.get("Id")

        return item_id

    def __download_image(self, service, imageurl, library_name, count=None, retries=3, delay=1):
        """
        下载图片，保存到本地目录 self._covers_path/library_name/ 下，文件名为 1-9.jpg
        若已存在则跳过下载，直接返回图片路径。
        下载失败时重试若干次。
        """
        try:
            # 确保媒体库名称是安全的文件名（处理数字或字母开头的名称）
            safe_library_name = self.__sanitize_filename(library_name)

            # 创建目标子目录
            subdir = os.path.join(self._covers_path, safe_library_name)
            os.makedirs(subdir, exist_ok=True)

            # 文件命名：item_id 为主，适合排序
            if count is not None:
                filename = f"{count}.jpg"
            else:
                filename = f"img_{int(time.time())}.jpg"

            filepath = os.path.join(subdir, filename)

            # 如果文件已存在，直接返回路径
            # if os.path.exists(filepath):
            #     return filepath

            # 重试机制
            for attempt in range(1, retries + 1):
                image_content = None

                if '[HOST]' in imageurl:
                    if not service:
                        return None

                    r = service.instance.get_data(url=imageurl)
                    if r and r.status_code == 200:
                        image_content = r.content
                else:
                    r = RequestUtils().get_res(url=imageurl)
                    if r and r.status_code == 200:
                        image_content = r.content

                # 如果成功，保存并返回
                if image_content:
                    with open(filepath, 'wb') as f:
                        f.write(image_content)
                    return filepath

                # 如果失败，记录并等待后重试
                logger.warning(f"第 {attempt} 次尝试下载失败：{imageurl}")
                if attempt < retries:
                    time.sleep(delay)

            logger.error(f"图片下载失败（重试 {retries} 次）：{imageurl}")
            return None

        except Exception as err:
            logger.error(f"下载图片异常：{str(err)}")
            return None


    def __save_image_to_local(self, image_content, server_name: str, library_name: str, extension: str):
        """
        保存图片到本地路径
        """
        try:
            if not self._save_recent_covers:
                return
            # 确保目录存在
            local_path = str(self.__get_recent_cover_output_dir())
            os.makedirs(local_path, exist_ok=True)

            safe_server = self.__sanitize_filename(server_name) or "server"
            safe_library = self.__sanitize_filename(library_name) or "library"
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = extension.strip(".").lower() if extension else "jpg"
            filename = f"{safe_server}_{safe_library}_{timestamp}.{ext}"

            file_path = os.path.join(local_path, filename)
            with open(file_path, "wb") as f:
                f.write(image_content)
            logger.info(f"图片已保存到本地: {file_path}")
            self.__trim_saved_cover_history(local_path, safe_server, safe_library)
        except Exception as err:
            logger.error(f"保存图片到本地失败: {str(err)}")

    def __trim_saved_cover_history(self, local_path: str, safe_server: str, safe_library: str):
        limit = self.__clamp_value(
            self._covers_history_limit_per_library,
            1,
            100,
            10,
            "covers_history_limit_per_library[trim]",
            int,
        )
        pattern = f"{safe_server}_{safe_library}_"
        candidate_files: List[Path] = []
        try:
            for file_name in os.listdir(local_path):
                lower_name = file_name.lower()
                if not lower_name.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".apng")):
                    continue
                if not file_name.startswith(pattern):
                    continue
                file_path = Path(local_path) / file_name
                if file_path.is_file():
                    candidate_files.append(file_path)
            if len(candidate_files) <= limit:
                return
            candidate_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            for old_file in candidate_files[limit:]:
                old_file.unlink(missing_ok=True)
                logger.info(f"已按历史数量限制删除旧封面: {old_file}")
        except Exception as e:
            logger.warning(f"清理历史封面失败: {e}")
        

    def __set_library_image(self, service, library, image_base64):
        """
        设置媒体库封面
        """

        """设置Emby媒体库封面"""
        try:
            if service.type == 'emby':
                library_id = library.get("Id")
            else:
                library_id = library.get("ItemId")
            
            url = f'[HOST]emby/Items/{library_id}/Images/Primary?api_key=[APIKEY]'
            # 根据 base64 前几个字节简单判断格式
            content_type = "image/png"
            extension = "png"
            if image_base64.startswith("R0lG"):
                content_type = "image/gif"
                extension = "gif"
            elif image_base64.startswith("UklG"):
                content_type = "image/webp"
                extension = "webp"
            elif image_base64.startswith("iVBOR"):
                content_type = "image/png"
                extension = "png"
            elif image_base64.startswith("/9j/"):
                content_type = "image/jpeg"
                extension = "jpg"

            # 在发送前保存一份图片到本地
            if self._save_recent_covers:
                try:
                    image_bytes = base64.b64decode(image_base64)
                    self.__save_image_to_local(image_bytes, service.name, library['Name'], extension)
                except Exception as save_err:
                    logger.error(f"保存发送前图片失败: {str(save_err)}")
            
            res = service.instance.post_data(
                url=url,
                data=image_base64,
                headers={
                    "Content-Type": content_type
                }
            )
            
            if res and res.status_code in [200, 204]:
                return True
            else:
                logger.error(f"设置「{library['Name']}」封面失败，错误码：{res.status_code if res else 'No response'}")
                return False
        except Exception as err:
            logger.error(f"设置「{library['Name']}」封面失败：{str(err)}")
        return False

    def clean_cover_history(self, save=True):
        history = self.get_data('cover_history') or []
        cleaned = []

        for item in history:
            try:
                cleaned_item = {
                    "server": item["server"],
                    "library_id": str(item["library_id"]),
                    "item_id": str(item["item_id"]),
                    "timestamp": float(item["timestamp"])
                }
                cleaned.append(cleaned_item)
            except (KeyError, ValueError, TypeError):
                # 如果字段缺失或格式错误则跳过该项
                continue

        if save:
            self.save_data('cover_history', cleaned)

        return cleaned


    def update_cover_history(self, server, library_id, item_id):
        now = time.time()
        item_id = str(item_id)
        library_id = str(library_id)

        history_item = {
            "server": server,
            "library_id": library_id,
            "item_id": item_id,
            "timestamp": now
        }

        # 原始数据
        history = self.get_data('cover_history') or []

        # 用于分组管理：(server, library_id) => list of items
        grouped = defaultdict(list)
        for item in history:
            key = (item["server"], str(item["library_id"]))
            grouped[key].append(item)

        key = (server, library_id)
        items = grouped[key]

        # 查找是否已有该 item_id
        existing = next((i for i in items if str(i["item_id"]) == item_id), None)

        if existing:
            # 若已存在且是最新的，跳过
            if existing["timestamp"] >= max(i["timestamp"] for i in items):
                return
            else:
                existing["timestamp"] = now
        else:
            items.append(history_item)

        # 排序 + 截取前9
        grouped[key] = sorted(items, key=lambda x: x["timestamp"], reverse=True)[:9]

        # 重新整合所有分组的数据
        new_history = []
        for item_list in grouped.values():
            new_history.extend(item_list)

        self.save_data('cover_history', new_history)
        return [ 
            item for item in new_history
            if str(item.get("library_id")) == str(library_id)
        ]

    def prepare_library_images(self, library_dir: str, required_items: int = 9):
        """
        准备目录下的 1~required_items.jpg 图片文件:
        1. 检查已有的目标编号文件
        2. 保留已有的文件，只补足缺失的编号
        3. 补充文件时尽量避免连续使用相同的源图片
        """
        os.makedirs(library_dir, exist_ok=True)

        required_items = max(1, int(required_items))

        # 检查哪些编号的文件已存在，哪些缺失
        existing_numbers = []
        missing_numbers = []
        for i in range(1, required_items + 1):
            target_file_path = os.path.join(library_dir, f"{i}.jpg")
            if os.path.exists(target_file_path):
                existing_numbers.append(i)
            else:
                missing_numbers.append(i)

        # 如果已经存在所有文件，直接返回
        if not missing_numbers:
            return True

        logger.info(f"信息: {library_dir} 中缺少以下编号的图片: {missing_numbers}，将进行补充。")

        target_name_pattern = rf"^[1-9][0-9]*\.jpg$"

        # 获取可用作源的图片（排除已有的目标编号文件）
        # 使用 scandir 并限制采样数量，避免超大目录扫描导致长时间无日志
        source_image_filenames = []
        max_source_scan = 512
        scanned_entries = 0
        for entry in os.scandir(library_dir):
            scanned_entries += 1
            if not entry.is_file():
                continue

            f = entry.name
            # 排除 N.jpg（N 为正整数）作为源
            if re.match(target_name_pattern, f, re.IGNORECASE):
                continue
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                source_image_filenames.append(f)
                if len(source_image_filenames) >= max_source_scan:
                    break

        if scanned_entries > 2000:
            logger.info(f"信息: {library_dir} 文件较多，已快速采样 {len(source_image_filenames)} 张作为补图源")

        # 如果没有源图片可用
        if not source_image_filenames:
            # 如果已经有部分目标编号图片，可以从这些现有文件中选择
            if existing_numbers:
                logger.info(f"信息: {library_dir} 中没有其他图片可用，将从现有目标编号图片中随机选择进行复制。")
                existing_file_paths = [os.path.join(library_dir, f"{i}.jpg") for i in existing_numbers]
                source_image_paths = existing_file_paths
            else:
                logger.info(f"警告: {library_dir} 中没有任何可用的图片来生成 1-{required_items}.jpg。")
                return False
        else:
            # 将文件名转换为完整路径
            source_image_paths = [os.path.join(library_dir, f) for f in sorted(source_image_filenames)]

        # 如果源图片数量不足，需要重复使用
        if len(source_image_paths) < len(missing_numbers):
            logger.info(f"信息: 源图片数量({len(source_image_paths)})小于缺失数量({len(missing_numbers)})，某些图片将被重复使用。")
        
        # 为每个缺失的编号选择一个源图片，尽量避免连续重复
        last_used_source = None
        for missing_num in missing_numbers:
            target_path = os.path.join(library_dir, f"{missing_num}.jpg")
            
            # 如果只有一个源文件，没有选择，直接使用
            if len(source_image_paths) == 1:
                selected_source = source_image_paths[0]
            else:
                # 尝试选择一个与上次不同的源文件
                available_sources = [s for s in source_image_paths if s != last_used_source]
                
                # 如果没有其他选择（可能上次用了唯一的源文件），则使用所有源
                if not available_sources:
                    available_sources = source_image_paths
                    
                # 随机选择一个源文件
                selected_source = random.choice(available_sources)
                
            # 记录本次使用的源文件，用于下次比较
            last_used_source = selected_source
            
            try:
                if not os.path.exists(selected_source):
                    logger.info(f"错误: 源文件 {selected_source} 在尝试复制前找不到了！")
                    return False
                    
                shutil.copy(selected_source, target_path)
                logger.info(f"信息: 已创建 {missing_num}.jpg (源自: {os.path.basename(selected_source)})")
                
            except Exception as e:
                logger.info(f"错误: 复制文件 {selected_source} 到 {target_path} 时发生错误: {e}")
                return False

        logger.info(f"信息: {library_dir} 已成功补充所有缺失的图片，现在包含完整的 1-{required_items}.jpg")
        return True

    def __get_fonts(self):
        def detect_string_type(s: str):
            if not s:
                return None
            s = s.strip()

            # 判断是否是 HTTP(S) 链接
            if re.match(r'^https?://[^\s]+$', s, re.IGNORECASE):
                return 'url'

            # 判断是否像路径（包含 / 或 \，或以 ~、.、/ 开头）
            if os.path.isabs(s) or s.startswith(('.', '~', '/')) or re.search(r'[\\/]', s):
                return 'path'

            return None
        
        font_dir_path = self._font_path
        Path(font_dir_path).mkdir(parents=True, exist_ok=True)

        _, _, zh_preset_paths, en_preset_paths = self.__get_font_presets()

        if not self._zh_font_preset:
            self._zh_font_preset = "chaohei"

        default_font_url = {
            "chaohei": "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/chaohei.ttf",
            "yasong": "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/yasong.ttf",
            "EmblemaOne": "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/EmblemaOne.woff2",
            "Melete": "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/Melete.otf",
            "Phosphate": "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/phosphate.ttf",
            "JosefinSans": "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/josefinsans.woff2",
            "LilitaOne": "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/lilitaone.woff2",
            "Monoton": "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/Monoton.woff2",
            "Plaster": "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/Plaster.woff2",
        }
        default_zh_url = default_font_url.get(self._zh_font_preset, "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/chaohei.ttf")

        if not self._en_font_preset:
            self._en_font_preset = "EmblemaOne"

        default_en_url = default_font_url.get(self._en_font_preset, "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/EmblemaOne.woff2")
        
        log_prefix = "默认"
        zh_custom_type = detect_string_type(self._zh_font_custom)
        en_custom_type = detect_string_type(self._en_font_custom)
        current_zh_font_url = self._zh_font_custom if zh_custom_type == 'url' else default_zh_url
        current_en_font_url = self._en_font_custom if en_custom_type == 'url' else default_en_url
        zh_local_path_config = self._zh_font_custom if zh_custom_type == 'path' else zh_preset_paths.get(self._zh_font_preset)
        en_local_path_config = self._en_font_custom if en_custom_type == 'path' else en_preset_paths.get(self._en_font_preset)

        downloaded_zh_font_base = f"{self._zh_font_preset}_custom" if zh_custom_type == 'url' else self._zh_font_preset
        downloaded_en_font_base = f"{self._en_font_preset}_custom" if en_custom_type == 'url' else self._en_font_preset
        hash_zh_file_name = f"{downloaded_zh_font_base}_url.hash"
        hash_en_file_name = f"{downloaded_en_font_base}_url.hash"
        final_zh_font_path_attr = "_zh_font_path"
        final_en_font_path_attr = "_en_font_path"

        logger.info(f"当前主标题字体URL: {current_zh_font_url} (本地路径: {zh_local_path_config})")

        active_fonts_to_process = [
            {
                "lang": "主标题",
                "url": current_zh_font_url,
                "local_path_config": zh_local_path_config,
                "download_base_name": downloaded_zh_font_base,
                "hash_file_name": hash_zh_file_name,
                "final_attr_name": final_zh_font_path_attr,
                "fallback_ext": ".ttf"
            },
            {
                "lang": "副标题",
                "url": current_en_font_url,
                "local_path_config": en_local_path_config,
                "download_base_name": downloaded_en_font_base,
                "hash_file_name": hash_en_file_name,
                "final_attr_name": final_en_font_path_attr,
                "fallback_ext": ".ttf"
            }
        ]


        for font_info in active_fonts_to_process:
            lang = font_info["lang"]
            url = font_info["url"]
            local_path_cfg = font_info["local_path_config"]
            download_base = font_info["download_base_name"]
            hash_filename = font_info["hash_file_name"]
            final_attr = font_info["final_attr_name"]
            fallback_ext = font_info["fallback_ext"]


            extension = self.get_file_extension_from_url(url, fallback_ext=fallback_ext)
            downloaded_font_file_path = Path(font_dir_path) / f"{download_base}{extension}"
            hash_file_path = Path(font_dir_path) / hash_filename
            
            current_font_path = None
            using_local_font = False
            if local_path_cfg:
                local_font_p = Path(local_path_cfg)
                if validate_font_file(local_font_p):
                    logger.info(f"{lang}字体: 使用本地指定路径 {local_font_p}")
                    current_font_path = local_font_p
                    using_local_font = True
                else:
                    logger.warning(f"{log_prefix}{lang}字体: 本地指定路径 {local_font_p} 无效或文件不存在。")

            if not using_local_font:
                url_hash = hashlib.md5(url.encode()).hexdigest()
                url_has_changed = True
                if hash_file_path.exists():
                    try:
                        if hash_file_path.read_text() == url_hash:
                            url_has_changed = False
                    except Exception as e:
                        logger.warning(f"读取哈希文件失败 {hash_file_path}: {e}。将重新下载。")
                
                font_file_is_valid = validate_font_file(downloaded_font_file_path)

                if url_has_changed or not font_file_is_valid:
                    if url_has_changed:
                        logger.info(f"{log_prefix}{lang}字体URL已更改或首次下载。")
                    if not font_file_is_valid and downloaded_font_file_path.exists():
                         logger.info(f"{log_prefix}{lang}字体文件 {downloaded_font_file_path} 无效或损坏，将重新下载。")
                    elif not downloaded_font_file_path.exists():
                         logger.info(f"{log_prefix}{lang}字体文件 {downloaded_font_file_path} 不存在，将下载。")

                    # 使用安全的字体下载方法
                    if self.download_font_safely_with_timeout(url, downloaded_font_file_path):
                        try:
                            hash_file_path.write_text(url_hash)
                        except Exception as e:
                            logger.error(f"写入哈希文件失败 {hash_file_path}: {e}")
                        current_font_path = downloaded_font_file_path
                    else:
                        logger.critical(f"无法获取必要的{log_prefix}{lang}支持字体: {url}")
                        if font_file_is_valid :
                             logger.warning(f"下载失败，但找到一个已存在的（可能旧版本）有效字体文件 {downloaded_font_file_path}，将尝试使用。")
                             current_font_path = downloaded_font_file_path
                        else:
                             current_font_path = None
                else:
                    logger.info(f"{log_prefix}{lang}字体: 使用已下载/缓存的有效字体 {downloaded_font_file_path}")
                    current_font_path = downloaded_font_file_path
            
            # 安全设置字体路径
            if current_font_path and current_font_path.exists():
                setattr(self, final_attr, current_font_path)
                status_log = '(本地路径)' if using_local_font else '(已下载/缓存)'
                logger.info(f"{log_prefix}{lang}字体最终路径: {getattr(self,final_attr)} {status_log}")
            else:
                # 字体获取失败，设置为None并记录错误
                setattr(self, final_attr, None)
                logger.error(f"{log_prefix}{lang}字体获取失败，这可能导致封面生成失败")

        # 检查是否所有必要的字体都已获取
        if not self._zh_font_path or not self._en_font_path:
            logger.critical("关键字体文件缺失，插件可能无法正常工作。请检查网络连接或手动下载字体文件。")

    def __sanitize_filename(self, filename: str) -> str:
        """
        将媒体库名称转换为安全的文件名，特别处理数字或字母开头的名称
        """
        if not filename:
            return "unknown"

        # 移除或替换不安全的字符
        import re
        # 替换Windows和Unix系统中不允许的字符
        unsafe_chars = r'[<>:"/\\|?*]'
        safe_name = re.sub(unsafe_chars, '_', filename)

        # 移除前后空格
        safe_name = safe_name.strip()

        # 如果名称为空，使用默认名称
        if not safe_name:
            return "unknown"

        # 确保不以点开头（在某些系统中是隐藏文件）
        if safe_name.startswith('.'):
            safe_name = '_' + safe_name[1:]

        # 限制长度（避免路径过长）
        if len(safe_name) > 100:
            safe_name = safe_name[:100]

        if safe_name != filename and filename not in self._sanitize_log_cache:
            self._sanitize_log_cache.add(filename)
            logger.debug(f"文件名安全化: '{filename}' -> '{safe_name}'")
        return safe_name

    def health_check(self) -> bool:
        """
        插件健康检查，确保关键组件正常
        """
        try:
            # 检查分辨率配置
            if not hasattr(self, '_resolution_config') or self._resolution_config is None:
                logger.warning("分辨率配置缺失，重新初始化")
                # 使用用户设置的分辨率，而不是硬编码的1080p
                if self._resolution == "custom":
                    self._resolution_config = ResolutionConfig((self._custom_width, self._custom_height))
                else:
                    self._resolution_config = ResolutionConfig(self._resolution)

            # 检查字体文件
            if not self._zh_font_path or not self._en_font_path:
                logger.warning("字体文件缺失，尝试重新获取")
                self.__get_fonts()

            # 验证字体文件有效性
            if self._zh_font_path and not validate_font_file(Path(self._zh_font_path)):
                logger.warning("主标题字体文件无效，尝试重新下载")
                return False

            if self._en_font_path and not validate_font_file(Path(self._en_font_path)):
                logger.warning("副标题字体文件无效，尝试重新下载")
                return False

            logger.info("插件健康检查通过")
            return True

        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False

    def download_font_safely_with_timeout(self, font_url: str, font_path: Path, timeout: int = 60) -> bool:
        """
        带超时的安全字体下载方法，避免首次下载时阻塞过久
        """
        try:
            logger.info(f"开始下载字体（超时限制: {timeout}秒）: {font_url}")
            return self.download_font_safely(font_url, font_path, retries=1, timeout=timeout)

        except Exception as e:
            logger.error(f"字体下载过程中出现异常: {e}")
            return False

    def download_font_safely(self, font_url: str, font_path: Path, retries: int = 2, timeout: int = 30):
        """
        从链接下载字体文件到指定目录，使用优化的网络助手
        :param font_url: 字体文件URL
        :param font_path: 保存路径
        :param retries: 每种策略的最大重试次数（减少重试次数）
        :param timeout: 下载超时时间
        :return: 是否下载成功
        """
        logger.info(f"准备下载字体: {font_url} -> {font_path}")

        # 确保在开始下载前删除任何可能存在的损坏文件
        if font_path.exists():
            try:
                font_path.unlink()
                logger.info(f"删除之前的字体文件以便重新下载: {font_path}")
            except OSError as unlink_error:
                logger.error(f"无法删除现有字体文件 {font_path}: {unlink_error}")
                return False
        
        # 使用优化的网络助手进行下载
        network_helper = NetworkHelper(timeout=timeout, max_retries=retries)

        # 准备下载策略
        strategies = []

        # 判断是否为GitHub链接
        is_github_url = "github.com" in font_url or "raw.githubusercontent.com" in font_url

        # 对于GitHub链接，优先使用GitHub镜像站
        if is_github_url and settings.GITHUB_PROXY:
            github_proxy_url = f"{UrlUtils.standardize_base_url(settings.GITHUB_PROXY)}{font_url}"
            strategies.append(("GitHub镜像站", github_proxy_url))

        # 直接使用原始URL
        strategies.append(("直连", font_url))

        # 遍历所有策略
        for strategy_name, target_url in strategies:
            logger.info(f"尝试使用策略：{strategy_name} 下载字体: {target_url}")

            # 创建临时文件路径
            temp_path = font_path.with_suffix('.temp')

            try:
                # 使用网络助手下载
                if network_helper.download_file_sync(target_url, temp_path):
                    # 验证下载的字体文件
                    if validate_font_file(temp_path):
                        # 验证通过后，将临时文件移动到正确位置
                        temp_path.replace(font_path)
                        logger.info(f"字体下载成功: 使用策略 {strategy_name}")
                        return True
                    else:
                        logger.warning(f"下载的字体文件验证失败，可能已损坏")
                        if temp_path.exists():
                            temp_path.unlink()
                else:
                    logger.warning(f"策略 {strategy_name} 下载失败")

            except Exception as e:
                logger.warning(f"策略 {strategy_name} 下载出错: {e}")
                # 清理可能的临时文件
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except OSError:
                        pass
        
        # 所有策略都失败
        logger.error(f"所有下载策略均失败，无法下载字体，建议手动下载字体: {font_url}")
        # 确保目标路径没有损坏的文件
        if font_path.exists():
            try:
                font_path.unlink()
                logger.info(f"已删除部分下载的文件: {font_path}")
            except OSError as unlink_error:
                logger.error(f"无法删除部分下载的文件 {font_path}: {unlink_error}")
        
        return False

    def get_file_extension_from_url(self, url: str, fallback_ext: str = ".ttf") -> str:
        """
        从链接获取字体扩展名扩展名
        """
        try:
            parsed_url = urlparse(url)
            path_part = parsed_url.path
            if path_part:
                filename = os.path.basename(path_part)
                _ , ext = os.path.splitext(filename)
                return ext if ext else fallback_ext
            else:
                logger.warning(f"无法从URL中提取路径部分: {url}. 使用备用扩展名: {fallback_ext}")
                return fallback_ext
        except Exception as e:
            logger.error(f"解析URL时出错 '{url}': {e}. 使用备用扩展名: {fallback_ext}")
            return fallback_ext
        
    def _validate_font_file(self, font_path: Path):
        if not font_path or not font_path.exists() or not font_path.is_file():
            return False
        
        try:
            with open(font_path, "rb") as f:
                header = f.read(4) 
                if (header.startswith(b'\x00\x01\x00\x00') or
                    header.startswith(b'OTTO') or
                    header.startswith(b'true') or
                    header.startswith(b'wOFF') or
                    header.startswith(b'wOF2')):
                    return True
                if font_path.suffix.lower() == ".svg":
                    f.seek(0)
                    sample = f.read(100).decode(errors='ignore').strip()
                    if sample.startswith('<svg') or sample.startswith('<?xml'):
                        return True
                if font_path.suffix.lower() == ".bdf":
                    f.seek(0)
                    sample = f.read(9).decode(errors='ignore')
                    if sample == "STARTFONT":
                        return True
            logger.warning(f"字体文件存在但可能已损坏或格式无法识别: {font_path}")
            return False
        except Exception as e:
            logger.warning(f"验证字体文件时出错 {font_path}: {e}")
            return False

    def stop_service(self):
        """
        停止服务
        """
        try:
            if self._scheduler:
                self._scheduler.remove_all_jobs()
                if self._scheduler.running:
                    self._event.set()
                    self._scheduler.shutdown()
                    self._event.clear()
                self._scheduler = None
        except Exception as e:
            logger.error(f"停止服务失败: {str(e)}")
