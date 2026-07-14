import base64
import datetime
import hashlib
import io
import json
import mimetypes
import os
import re
import ast
import threading
import time
import shutil
import random
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse, parse_qs, quote, unquote
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import pytz
import yaml

from fastapi import Body, Request
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
from app.plugins.yahahacoverstudio.style.style_static_template import (
    create_style_static_1,
    create_style_static_2,
    create_style_static_3,
    create_style_static_4,
)
from app.plugins.yahahacoverstudio.style.style_static_custom import create_style_static_custom, measure_text_layer
from app.plugins.yahahacoverstudio.style.style_animated_1 import create_style_animated_1
from app.plugins.yahahacoverstudio.style.style_animated_2 import create_style_animated_2
from app.plugins.yahahacoverstudio.style.style_animated_3 import create_style_animated_3
from app.plugins.yahahacoverstudio.style.style_animated_4 import create_style_animated_4
from app.plugins.yahahacoverstudio.utils.image_manager import ResolutionConfig, ImageResourceManager
from app.plugins.yahahacoverstudio.history_store import HistoryStore
try:
    from app.plugins.yahahacoverstudio.utils.network_helper import NetworkHelper, validate_font_file
except Exception as import_err:
    logger.warning(f"NetworkHelper 导入失败，将使用兼容下载实现: {import_err}")

    try:
        from app.plugins.yahahacoverstudio.utils.network_helper import validate_font_file
    except Exception:
        def validate_font_file(font_path: Path) -> bool:
            try:
                if not font_path.exists() or font_path.stat().st_size == 0:
                    return False
                from PIL import ImageFont
                ImageFont.truetype(str(font_path), 12)
                return True
            except Exception as err:
                logger.warning(f"字体文件验证失败: {font_path}, 错误: {err}")
                return False

    class NetworkHelper:
        """兼容旧版 network_helper.py 的同步下载助手。"""

        def __init__(self, timeout: int = 30, max_retries: int = 3):
            self.timeout = timeout
            self.max_retries = max_retries

        def download_file_sync(self, url: str, save_path: Path, expected_size: Optional[int] = None) -> bool:
            for attempt in range(max(1, int(self.max_retries or 1))):
                try:
                    logger.info(f"开始下载文件 (兼容实现 {attempt + 1}/{self.max_retries}): {url}")
                    response = RequestUtils(
                        headers={'User-Agent': 'MoviePilot-YahahaCoverStudio/1.0'},
                        timeout=self.timeout,
                    ).get_res(url)
                    if not response or response.status_code != 200:
                        status_code = getattr(response, "status_code", "无响应")
                        logger.warning(f"下载失败，HTTP状态码: {status_code}")
                    else:
                        content = response.content
                        if expected_size and len(content) != expected_size:
                            logger.warning(f"文件大小不匹配: 期望 {expected_size}, 实际 {len(content)}")
                        else:
                            save_path.parent.mkdir(parents=True, exist_ok=True)
                            save_path.write_bytes(content)
                            logger.info(f"文件下载成功: {save_path}")
                            return True
                except Exception as err:
                    logger.warning(f"下载出错 (兼容实现 {attempt + 1}/{self.max_retries}): {err}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
            return False
from app.plugins.yahahacoverstudio.utils.performance_helper import PerformanceMonitor, ProgressTracker, memory_efficient_operation
from app.plugins.yahahacoverstudio.utils.color_helper import ColorHelper


class CoverUpdateOutcome(str, Enum):
    """Explicit update result; never confuse a monitor skip with image data."""

    UPDATED = "updated"
    SKIPPED = "skipped"
    FAILED = "failed"


class YahahaCoverStudio(_PluginBase):
    # 插件名称
    plugin_name = "呀哈哈封面工坊"
    # 插件描述
    plugin_desc = "全新vue前端,支持可编辑静态封面、动态方案、历史封面、Webhook 入库监控"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/icons/yahaha-cover-studio.png"
    # 插件版本
    plugin_version = "2.0.14"
    # 插件作者
    plugin_author = "呀哈哈"
    # 作者主页
    author_url = "https://github.com/justzerock/MoviePilot-Plugins"
    # 插件配置项ID前缀
    plugin_config_prefix = "yahaha_cover_studio_"
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
    _auto_save_config = False
    _update_now = False
    _transfer_monitor = True
    _monitor_source = "transfer"
    _lock_latest_sort = False
    _cron = None
    _delay = 60
    _servers = None
    _selected_servers = []
    _all_libraries = []
    _include_libraries = []
    _sort_by = 'Random'
    _monitor_sort = ''
    _current_updating_items = set()
    _generation_thread = None
    _history_batch = None
    _generation_run_lock = threading.Lock()
    _generation_state_lock = threading.Lock()
    _is_generating = False
    _generation_source = None
    _generation_style = None
    _generation_current = 0
    _generation_total = 0
    _generation_label = ""
    _covers_output = ''
    _covers_input = ''
    _main_title_font_url = ''
    _subtitle_font_url = ''
    _custom_text_font_url = ''
    _main_title_font_path = ''
    _subtitle_font_path = ''
    _custom_text_font_path = ''
    _title_config = ''
    _title_config_strict = False
    _distinguish_same_name_libraries = False
    _current_config = {}
    _cover_style = 'static_1'
    _cover_style_base = 'static_1'
    _cover_style_variant = 'static'
    _font_path = ''
    _covers_path = ''
    _tab = 'style-tab'
    _multi_1_blur = True
    _main_title_font_size = None
    _subtitle_font_size = None
    _blur_size = 50
    _color_ratio = 0.8
    _use_primary = False
    _seen_keys = set()
    _main_title_font_custom = ''
    _subtitle_font_custom = ''
    _custom_text_font_custom = ''
    _main_title_font_preset = 'chaohei'
    _subtitle_font_preset = 'EmblemaOne'
    _custom_text_font_preset = 'EmblemaOne'
    _main_title_font_offset = ''
    _title_spacing = ''
    _subtitle_line_spacing = ''
    _title_scale = 1.0
    _resolution = '480p'
    _custom_width = 1920
    _custom_height = 1080
    _image_count_mode = 'auto'
    _image_count = 9
    _resolution_config = None
    _animation_duration = 8
    _animation_scroll = 'alternate'
    _animation_fps = 24
    _animation_format = 'apng'
    _animation_resolution = '320x180'
    _animation_reduce_colors = 'medium'
    _animated_2_image_count = 6
    _animated_2_departure_type = 'fly'
    _animated_settings: Dict[str, Dict[str, Any]] = {}
    _style_naming_v2 = True
    _sanitize_log_cache = set()
    _clean_images = False
    _clean_fonts = False
    _backup_enabled = False
    _backup_cron = ""
    _backup_path = ""
    _save_recent_covers = True
    _covers_history_limit_per_library = 10
    _covers_page_history_limit = 50
    _history_retention_batches = 30
    _page_tab = "generate-tab"
    _custom_static_layout = None
    _custom_static_layouts: List[Dict[str, Any]] = []
    _custom_static_active_id: Optional[str] = None

    def get_render_mode(self) -> Tuple[str, str]:
        """获取插件渲染模式

        :return: 1、渲染模式，支持：vue/vuetify，默认vuetify
        :return: 2、组件路径，默认 dist/assets
        """
        return "vue", "dist/assets"

    def __init__(self):
        super().__init__()

    def get_state(self) -> bool:
        return bool(self._enabled)

    def init_plugin(self, config: dict = None):
        self.mschain = MediaServerChain()
        self.mediaserver_helper = MediaServerHelper()   
        data_path = self.get_data_path()
        (data_path / 'fonts').mkdir(parents=True, exist_ok=True)
        (data_path / 'input').mkdir(parents=True, exist_ok=True)
        self._covers_path = data_path / 'input'
        self._font_path = data_path / 'fonts'
        custom_static_state_loaded = False
        self._animated_settings = {}
        if config:
            def get_compat_value(new_key: str, old_key: str, default=None):
                value = config.get(new_key)
                if value is None:
                    value = config.get(old_key, default)
                return value

            self._enabled = config.get("enabled")
            self._auto_save_config = bool(config.get("auto_save_config", False))
            self._update_now = config.get("update_now")
            self._transfer_monitor = config.get("transfer_monitor")
            self._monitor_source = config.get("monitor_source", "transfer")
            if self._monitor_source not in ["transfer", "emby"]:
                self._monitor_source = "transfer"
            self._lock_latest_sort = bool(config.get("lock_latest_sort", False))
            self._cron = config.get("cron")
            self._delay = config.get("delay")
            self._selected_servers = config.get("selected_servers")
            self._include_libraries = config.get("include_libraries")
            self._sort_by = config.get("sort_by")
            self._covers_output = config.get("covers_output")
            self._covers_input = config.get("covers_input")
            # self._title_config = self.get_data('title_config')
            self._title_config = config.get("title_config")
            self._title_config_strict = bool(config.get("title_config_strict", False))
            self._distinguish_same_name_libraries = bool(config.get("distinguish_same_name_libraries", False))
            self._main_title_font_url = get_compat_value("main_title_font_url", "zh_font_url", "")
            self._subtitle_font_url = get_compat_value("subtitle_font_url", "en_font_url", "")
            self._custom_text_font_url = config.get("custom_text_font_url", self._subtitle_font_url)
            self._main_title_font_path = get_compat_value("main_title_font_path", "zh_font_path", "")
            self._subtitle_font_path = get_compat_value("subtitle_font_path", "en_font_path", "")
            self._custom_text_font_path = config.get("custom_text_font_path", self._subtitle_font_path)
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
            self._main_title_font_size = get_compat_value("main_title_font_size", "zh_font_size", 170)
            self._subtitle_font_size = get_compat_value("subtitle_font_size", "en_font_size", 75)
            try:
                self._blur_size = int(config.get("blur_size", 50))
            except (ValueError, TypeError):
                self._blur_size = 50
            try:
                self._color_ratio = float(config.get("color_ratio", 0.8))
            except (ValueError, TypeError):
                self._color_ratio = 0.8
            self._use_primary = config.get("use_primary")
            self._main_title_font_custom = get_compat_value("main_title_font_custom", "zh_font_custom", "")
            self._subtitle_font_custom = get_compat_value("subtitle_font_custom", "en_font_custom", "")
            self._custom_text_font_custom = config.get("custom_text_font_custom", self._subtitle_font_custom)
            self._main_title_font_preset = get_compat_value("main_title_font_preset", "zh_font_preset", "chaohei")
            self._subtitle_font_preset = get_compat_value("subtitle_font_preset", "en_font_preset", "EmblemaOne")
            self._custom_text_font_preset = config.get("custom_text_font_preset", self._subtitle_font_preset or "EmblemaOne")
            self._main_title_font_offset = get_compat_value("main_title_font_offset", "zh_font_offset", "")
            self._title_spacing = config.get("title_spacing")
            self._subtitle_line_spacing = get_compat_value("subtitle_line_spacing", "en_line_spacing", "")
            try:
                self._title_scale = float(config.get("title_scale", 1.0))
            except (ValueError, TypeError):
                self._title_scale = 1.0
            self._resolution = config.get("resolution", "480p")
            self._custom_width = config.get("custom_width", 1920)
            self._custom_height = config.get("custom_height", 1080)
            self._image_count_mode = config.get("image_count_mode", "auto")
            if self._image_count_mode not in ["auto", "fixed"]:
                self._image_count_mode = "auto"
            self._image_count = self.__clamp_value(
                config.get("image_count", 9),
                1,
                60,
                9,
                "image_count[init]",
                int,
            )
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
            self._backup_enabled = bool(config.get("backup_enabled", False))
            self._backup_cron = str(config.get("backup_cron", "") or "").strip()
            self._backup_path = str(config.get("backup_path", "") or "").strip()
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
            self._history_retention_batches = self.__clamp_value(config.get("history_retention_batches", 30), 1, 1000, 30, "history_retention_batches[init]", int)
            self._page_tab = config.get("page_tab", "generate-tab")

            raw_layout = config.get("custom_static_layout")
            raw_templates = config.get("custom_static_layouts")
            raw_active_id = config.get("custom_static_active_id")

            # 自定义静态布局：兼容字符串存储和直接存 dict/list
            self._custom_static_layout = None
            self._custom_static_layouts = []
            self._custom_static_active_id = raw_active_id or None

            try:
                import json  # type: ignore
            except Exception:  # pragma: no cover - 极端情况
                json = None  # type: ignore

            raw_animated_settings = config.get("animated_settings")
            parsed_animated_settings = {}
            if isinstance(raw_animated_settings, dict):
                parsed_animated_settings = raw_animated_settings
            elif isinstance(raw_animated_settings, str) and raw_animated_settings:
                try:
                    if json is not None:
                        parsed = json.loads(raw_animated_settings)
                        if isinstance(parsed, dict):
                            parsed_animated_settings = parsed
                except Exception:
                    parsed_animated_settings = {}
            self._animated_settings = self.__normalize_animated_settings_map(parsed_animated_settings)

            if isinstance(raw_layout, dict):
                self._custom_static_layout = raw_layout
            elif isinstance(raw_layout, str) and raw_layout:
                try:
                    if json is not None:
                        parsed = json.loads(raw_layout)
                        if isinstance(parsed, dict):
                            self._custom_static_layout = parsed
                except Exception:
                    self._custom_static_layout = None

            if isinstance(raw_templates, list):
                self._custom_static_layouts = raw_templates
            elif isinstance(raw_templates, str) and raw_templates:
                try:
                    if json is not None:
                        parsed = json.loads(raw_templates)
                        if isinstance(parsed, list):
                            self._custom_static_layouts = parsed
                except Exception:
                    self._custom_static_layouts = []

            # 自定义布局以独立状态文件为准，避免 MoviePilot 配置字段过滤或
            # save_data 序列化差异导致重新打开插件后读回默认布局。
            self.__load_custom_static_state()
            custom_static_state_loaded = True
            if self._custom_static_active_id and self._custom_static_layouts:
                active_tpl = next(
                    (
                        tpl
                        for tpl in self._custom_static_layouts
                        if str(tpl.get("id", "")) == str(self._custom_static_active_id)
                    ),
                    None,
                )
                if isinstance(active_tpl, dict) and isinstance(active_tpl.get("layout"), dict):
                    self._custom_static_layout = active_tpl.get("layout")
            elif self._custom_static_layout and not self._custom_static_layouts:
                self._custom_static_layouts = [
                    {
                        "id": str(uuid.uuid4()),
                        "name": "默认方案",
                        "layout": self._custom_static_layout,
                        "baseStyle": "custom_static",
                    }
                ]
                self._custom_static_active_id = self._custom_static_layouts[0]["id"]
            if self._resolution not in ["1080p", "720p", "480p"]:
                self._resolution = "480p"
            self._animation_resolution = "320x180"

        if not custom_static_state_loaded:
            self.__load_custom_static_state()

        self._animated_2_image_count = self.__clamp_value(
            self._animated_2_image_count,
            3,
            60,
            5,
            "animated_2 image_count[init_plugin]",
            int,
        )
        if self._animated_2_departure_type not in ["fly", "fade", "crossfade"]:
            self._animated_2_departure_type = "fly"
        if self._animation_scroll not in ["down", "up", "alternate", "alternate_reverse"]:
            self._animation_scroll = "alternate"
        self._animated_settings = self.__normalize_animated_settings_map(self._animated_settings)
        if self._cover_style.startswith("animated_"):
            self.__apply_animated_settings_for_style(self._cover_style)
        self._bg_color_mode = (config or {}).get("bg_color_mode", "auto")
        self._custom_bg_color = (config or {}).get("custom_bg_color", "")

        # 初始化分辨率配置（确保安全初始化）
        try:
            self._resolution_config = ResolutionConfig(self._resolution)
        except Exception as e:
            logger.warning(f"分辨率配置初始化失败，使用默认配置: {e}")
            self._resolution_config = ResolutionConfig("480p")

        self.__refresh_media_server_context(force=True)
        if self._enabled:
            self.__ensure_fonts_ready(force_refresh=False)

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

        if self._enabled and self._backup_enabled and self._backup_cron:
            try:
                logger.info(f"媒体库封面配置备份服务已启用: {self._backup_cron}")
            except Exception:
                pass

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

    def __get_animated_style_key(self, style: Optional[str] = None) -> str:
        source = (style or self._cover_style or "").strip()
        if source in ["animated_1", "animated_2", "animated_3", "animated_4"]:
            return source
        if source in ["static_1", "static_2", "static_3", "static_4"]:
            return f"animated_{source.split('_')[-1]}"
        if source in ["1", "2", "3", "4"]:
            return f"animated_{source}"
        return "animated_1"

    def __get_default_animated_settings(self) -> Dict[str, Any]:
        return {
            "animation_duration": self.__clamp_value(
                self._animation_duration,
                1,
                60,
                8,
                "animation_duration[default]",
                int,
            ),
            "animation_fps": self.__clamp_value(
                self._animation_fps,
                1,
                60,
                24,
                "animation_fps[default]",
                int,
            ),
            "animation_format": self._animation_format if self._animation_format in ["apng", "gif"] else "apng",
            "animation_scroll": self._animation_scroll
            if self._animation_scroll in ["down", "up", "alternate", "alternate_reverse"]
            else "alternate",
            "animation_reduce_colors": self._animation_reduce_colors
            if self._animation_reduce_colors in ["off", "medium", "strong"]
            else "medium",
            "animated_2_image_count": self.__clamp_value(
                self._animated_2_image_count,
                3,
                60,
                6,
                "animated_2_image_count[default]",
                int,
            ),
            "animated_2_departure_type": self._animated_2_departure_type
            if self._animated_2_departure_type in ["fly", "fade", "crossfade"]
            else "fly",
            "main_title_font_preset": self._main_title_font_preset or "chaohei",
            "subtitle_font_preset": self._subtitle_font_preset or "EmblemaOne",
            "custom_text_font_preset": self._custom_text_font_preset or self._subtitle_font_preset or "EmblemaOne",
            "main_title_font_size": self.__clamp_value(
                self._main_title_font_size or 170,
                24,
                320,
                170,
                "main_title_font_size[default]",
                int,
            ),
            "subtitle_font_size": self.__clamp_value(
                self._subtitle_font_size or 75,
                12,
                220,
                75,
                "subtitle_font_size[default]",
                int,
            ),
            "blur_size": self.__clamp_value(
                self._blur_size or 50,
                0,
                100,
                50,
                "blur_size[default]",
                int,
            ),
            "color_ratio": self.__clamp_value(
                self._color_ratio or 0.8,
                0,
                1,
                0.8,
                "color_ratio[default]",
                float,
            ),
            "title_scale": self.__clamp_value(
                self._title_scale or 1.0,
                0.2,
                3.0,
                1.0,
                "title_scale[default]",
                float,
            ),
        }

    def __normalize_animated_setting(
        self,
        setting: Optional[Dict[str, Any]],
        fallback: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        base = dict(fallback or self.__get_default_animated_settings())
        raw = setting if isinstance(setting, dict) else {}
        return {
            "animation_duration": self.__clamp_value(
                raw.get("animation_duration", base.get("animation_duration", 8)),
                1,
                60,
                int(base.get("animation_duration", 8) or 8),
                "animation_duration[style]",
                int,
            ),
            "animation_fps": self.__clamp_value(
                raw.get("animation_fps", base.get("animation_fps", 24)),
                1,
                60,
                int(base.get("animation_fps", 24) or 24),
                "animation_fps[style]",
                int,
            ),
            "animation_format": str(raw.get("animation_format", base.get("animation_format", "apng"))).lower()
            if str(raw.get("animation_format", base.get("animation_format", "apng"))).lower() in ["apng", "gif"]
            else "apng",
            "animation_scroll": raw.get("animation_scroll", base.get("animation_scroll", "alternate"))
            if raw.get("animation_scroll", base.get("animation_scroll", "alternate")) in ["down", "up", "alternate", "alternate_reverse"]
            else "alternate",
            "animation_reduce_colors": raw.get("animation_reduce_colors", base.get("animation_reduce_colors", "medium"))
            if raw.get("animation_reduce_colors", base.get("animation_reduce_colors", "medium")) in ["off", "medium", "strong"]
            else "medium",
            "animated_2_image_count": self.__clamp_value(
                raw.get("animated_2_image_count", base.get("animated_2_image_count", 6)),
                3,
                60,
                int(base.get("animated_2_image_count", 6) or 6),
                "animated_2_image_count[style]",
                int,
            ),
            "animated_2_departure_type": raw.get("animated_2_departure_type", base.get("animated_2_departure_type", "fly"))
            if raw.get("animated_2_departure_type", base.get("animated_2_departure_type", "fly")) in ["fly", "fade", "crossfade"]
            else "fly",
            "main_title_font_preset": str(raw.get("main_title_font_preset", base.get("main_title_font_preset", "chaohei")) or "chaohei"),
            "subtitle_font_preset": str(raw.get("subtitle_font_preset", base.get("subtitle_font_preset", "EmblemaOne")) or "EmblemaOne"),
            "custom_text_font_preset": str(raw.get("custom_text_font_preset", base.get("custom_text_font_preset", "EmblemaOne")) or "EmblemaOne"),
            "main_title_font_size": self.__clamp_value(
                raw.get("main_title_font_size", base.get("main_title_font_size", 170)),
                24,
                320,
                int(base.get("main_title_font_size", 170) or 170),
                "main_title_font_size[style]",
                int,
            ),
            "subtitle_font_size": self.__clamp_value(
                raw.get("subtitle_font_size", base.get("subtitle_font_size", 75)),
                12,
                220,
                int(base.get("subtitle_font_size", 75) or 75),
                "subtitle_font_size[style]",
                int,
            ),
            "blur_size": self.__clamp_value(
                raw.get("blur_size", base.get("blur_size", 50)),
                0,
                100,
                int(base.get("blur_size", 50) or 50),
                "blur_size[style]",
                int,
            ),
            "color_ratio": self.__clamp_value(
                raw.get("color_ratio", base.get("color_ratio", 0.8)),
                0,
                1,
                float(base.get("color_ratio", 0.8) or 0.8),
                "color_ratio[style]",
                float,
            ),
            "title_scale": self.__clamp_value(
                raw.get("title_scale", base.get("title_scale", 1.0)),
                0.2,
                3.0,
                float(base.get("title_scale", 1.0) or 1.0),
                "title_scale[style]",
                float,
            ),
        }

    def __normalize_animated_settings_map(self, settings: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        normalized: Dict[str, Dict[str, Any]] = {}
        fallback = self.__get_default_animated_settings()
        source = settings if isinstance(settings, dict) else {}
        for index in range(1, 5):
            key = f"animated_{index}"
            normalized[key] = self.__normalize_animated_setting(source.get(key), fallback)
        return normalized

    def __export_animated_settings(self) -> Dict[str, Dict[str, Any]]:
        self._animated_settings = self.__normalize_animated_settings_map(self._animated_settings)
        return {key: dict(value) for key, value in self._animated_settings.items()}

    def __get_animated_settings_for_style(self, style: Optional[str] = None) -> Dict[str, Any]:
        key = self.__get_animated_style_key(style)
        self._animated_settings = self.__normalize_animated_settings_map(self._animated_settings)
        return dict(self._animated_settings.get(key) or self.__get_default_animated_settings())

    def __apply_animated_settings_for_style(self, style: Optional[str] = None) -> Dict[str, Any]:
        settings = self.__get_animated_settings_for_style(style)
        self._animation_duration = settings["animation_duration"]
        self._animation_fps = settings["animation_fps"]
        self._animation_format = settings["animation_format"]
        self._animation_scroll = settings["animation_scroll"]
        self._animation_reduce_colors = settings["animation_reduce_colors"]
        self._animated_2_image_count = settings["animated_2_image_count"]
        self._animated_2_departure_type = settings["animated_2_departure_type"]
        return settings

    def __refresh_media_server_context(self, force: bool = False) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        if not self.mediaserver_helper:
            self.mediaserver_helper = MediaServerHelper()

        should_refresh = (
            force
            or self._servers is None
            or (bool(self._selected_servers) and not self._all_libraries)
        )
        if not should_refresh:
            return self._servers or {}, self._all_libraries or []

        if self._selected_servers:
            servers = self.mediaserver_helper.get_services(
                name_filters=self._selected_servers
            )
        else:
            servers = self.mediaserver_helper.get_services()

        all_libraries: List[Dict[str, Any]] = []
        if servers:
            for server, service in servers.items():
                try:
                    if not service or service.instance.is_inactive():
                        logger.info(f"媒体服务器 {server} 未连接")
                        continue
                    all_libraries.extend(self.__get_all_libraries(server, service))
                except Exception as e:
                    logger.warning(f"刷新媒体服务器 {server} 失败: {e}")
        else:
            logger.info("未检测到任何可用媒体服务器")

        self._servers = servers
        self._all_libraries = all_libraries
        return self._servers or {}, self._all_libraries or []

    def __refresh_generation_state(self):
        thread = self._generation_thread
        if thread and not thread.is_alive():
            with self._generation_state_lock:
                if self._generation_thread is thread:
                    self._generation_thread = None
                if not self._generation_run_lock.locked():
                    self._is_generating = False
                    self._generation_source = None
                    self._generation_style = None

    def __set_generation_state(self, running: bool, source: Optional[str] = None, style: Optional[str] = None):
        with self._generation_state_lock:
            self._is_generating = running
            if running:
                self._generation_source = source or self._generation_source or "system"
                self._generation_style = style or self._cover_style
                if self._generation_total <= 0:
                    self._generation_current = 0
                    self._generation_total = 0
                    self._generation_label = "准备生成"
            else:
                self._generation_source = None
                self._generation_style = None
                self._generation_current = 0
                self._generation_total = 0
                self._generation_label = ""

    def __set_generation_progress(self, current: int = 0, total: int = 0, label: str = ""):
        with self._generation_state_lock:
            self._generation_current = max(0, int(current or 0))
            self._generation_total = max(0, int(total or 0))
            self._generation_label = str(label or "")

    def __is_generation_running(self) -> bool:
        self.__refresh_generation_state()
        thread = self._generation_thread
        return bool(
            self._is_generating
            or self._generation_run_lock.locked()
            or (thread and thread.is_alive())
        )

    def __run_background_generation(self, target_style: Optional[str] = None):
        old_style = self._cover_style
        history_store = HistoryStore(self.get_data_path()) if self._save_recent_covers else None
        self._history_batch = history_store.create("manual", "remote") if history_store else None
        try:
            if target_style:
                self._cover_style = target_style
            tips = self.__update_all_libraries(source="manual")
            logger.info(f"【YahahaCoverStudio】后台封面生成结束: {tips}")
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】后台封面生成异常: {e}", exc_info=True)
        finally:
            if history_store and self._history_batch:
                try:
                    history_store.finalize(self._history_batch, "success")
                    history_store.cleanup(self._history_retention_batches)
                except Exception as history_err:
                    logger.error(f"【YahahaCoverStudio】历史批次归档失败: {history_err}", exc_info=True)
                self._history_batch = None
            self._cover_style = old_style
            with self._generation_state_lock:
                if self._generation_thread is threading.current_thread():
                    self._generation_thread = None
            self.__refresh_generation_state()

    def __start_background_generation(self, target_style: Optional[str] = None) -> Tuple[bool, str]:
        if self.__is_generation_running():
            return False, "封面生成任务正在执行中"

        self._event.clear()
        worker = threading.Thread(
            target=self.__run_background_generation,
            kwargs={"target_style": target_style},
            daemon=True,
            name="YahahaCoverStudioManual",
        )
        try:
            self._generation_thread = worker
            self.__set_generation_state(True, source="manual", style=target_style or self._cover_style)
            worker.start()
            return True, "封面生成任务已开始"
        except Exception as e:
            self._generation_thread = None
            self.__set_generation_state(False)
            logger.error(f"【YahahaCoverStudio】启动后台封面生成失败: {e}", exc_info=True)
            return False, f"启动封面生成失败: {e}"

    def __get_animated_2_required_items(self) -> int:
        self._animated_2_image_count = self.__clamp_value(
            self._animated_2_image_count,
            3,
            60,
            5,
            "animated_2 image_count[runtime]",
            int,
        )
        return int(self._animated_2_image_count)

    def __compose_cover_style(self, base_style: str, variant: str) -> str:
        if base_style == "custom_static":
            # 自定义静态风格始终视为静态样式，内部使用独立标识避免与现有编号样式冲突
            return "static_custom"
        base = base_style if base_style in ["static_1", "static_2", "static_3", "static_4"] else "static_1"
        mode = variant if variant in ["static", "animated"] else "static"
        suffix = base.split("_")[-1]
        return base if mode == "static" else f"animated_{suffix}"

    def __resolve_cover_style_ui(self, cover_style: str) -> Tuple[str, str]:
        if cover_style == "static_custom":
            return "custom_static", "static"
        if cover_style in ["animated_1", "animated_2", "animated_3", "animated_4"]:
            suffix = cover_style.split("_")[-1]
            if suffix == "4":
                return "static_4", "animated"
            return f"static_{suffix}", "animated"
        if cover_style in ["static_1", "static_2", "static_3", "static_4"]:
            return cover_style, "static"
        return "static_1", "static"

    def __get_layout_required_items(self, layout: Optional[Dict[str, Any]]) -> int:
        layers = layout.get("layers") if isinstance(layout, dict) else []
        source_indexes: List[int] = []
        background = layout.get("background") if isinstance(layout, dict) and isinstance(layout.get("background"), dict) else {}
        background_type = str(background.get("type") or "blurred-image-color")
        if background_type == "blurred-image-color":
            image_source = background.get("imageSource") if isinstance(background.get("imageSource"), dict) else {}
            try:
                bg_slot = int(image_source.get("slot", 1) or 1)
            except (TypeError, ValueError):
                bg_slot = 1
            if bg_slot > 0:
                source_indexes.append(bg_slot)

        def visit(items: List[Any]):
            for layer in items or []:
                if not isinstance(layer, dict):
                    continue
                if layer.get("type") == "group" and isinstance(layer.get("children"), list):
                    visit(layer.get("children") or [])
                    continue
                if layer.get("type") != "image":
                    continue
                if layer.get("assetKind") == "sticker" or any(
                    str(layer.get(key) or "").strip()
                    for key in ("stickerDataUrl", "stickerPath", "stickerUrl")
                ):
                    continue
                try:
                    source_index = int(layer.get("sourceIndex", 1))
                except (TypeError, ValueError):
                    source_index = 1
                if source_index > 0:
                    source_indexes.append(source_index)

        visit(layers if isinstance(layers, list) else [])
        return max(source_indexes) if source_indexes else 0

    def __get_custom_static_required_items(self) -> int:
        return self.__get_layout_required_items(self._custom_static_layout or {})

    def __get_static_preset_required_items(self, style: str) -> int:
        if style == "static_3":
            return 9
        layout = self.__get_static_preset_layout_config(style)
        return self.__get_layout_required_items(layout) if layout else 1

    def __get_preview_required_items(self, requested_items: Optional[int] = None) -> int:
        required_items = self.__get_required_items()
        try:
            if requested_items is not None:
                required_items = max(required_items, int(requested_items))
        except (TypeError, ValueError):
            pass
        if self._image_count_mode != "fixed" and (self._cover_style_variant == "static" or self._cover_style.startswith("static_")):
            required_items = max(required_items, 9)
        return self.__clamp_value(required_items, 1, 60, 9, "preview required_items", int)

    def __is_single_image_style(self) -> bool:
        if self._cover_style == "static_custom":
            return self.__get_custom_static_required_items() <= 1
        if self._cover_style in ["static_1", "static_2", "static_4"]:
            return self.__get_static_preset_required_items(self._cover_style) <= 1
        return self._cover_style in ["static_1", "static_2", "static_4"]

    def __get_auto_required_items(self) -> int:
        if self._cover_style == "static_custom":
            return self.__get_custom_static_required_items()
        if self._cover_style in ["static_1", "static_2", "static_4"]:
            return self.__get_static_preset_required_items(self._cover_style)
        if self._cover_style in ["static_3", "animated_3"]:
            return 9
        if self._cover_style in ["animated_1", "animated_2", "animated_4"]:
            return int(self.__get_animated_settings_for_style(self._cover_style)["animated_2_image_count"])
        return 1

    def __get_required_items(self) -> int:
        auto_required = max(1, int(self.__get_auto_required_items() or 1))
        if self._image_count_mode == "fixed":
            return self.__clamp_value(
                self._image_count,
                1,
                60,
                auto_required,
                "image_count[required]",
                int,
            )
        return auto_required

    def __update_config(self):
        """
        更新配置
        """
        import json

        self._cover_style = self.__compose_cover_style(self._cover_style_base, self._cover_style_variant)
        if self._cover_style.startswith("animated_"):
            self.__apply_animated_settings_for_style(self._cover_style)
        self._animated_2_image_count = self.__clamp_value(
            self._animated_2_image_count,
            3,
            60,
            5,
            "animated_2 image_count[save]",
            int,
        )
        animated_settings_payload = json.dumps(self.__export_animated_settings(), ensure_ascii=False)
        self.update_config({
            "enabled": self._enabled,
            "auto_save_config": self._auto_save_config,
            "update_now": self._update_now,
            "transfer_monitor": self._transfer_monitor,
            "monitor_source": self._monitor_source,
            "lock_latest_sort": self._lock_latest_sort,
            "cron": self._cron,
            "delay": self._delay,
            "selected_servers": self._selected_servers,
            "include_libraries": self._include_libraries,
            "all_libraries": self._all_libraries,
            "sort_by": self._sort_by,
            "covers_output": self._covers_output,
            "covers_input": self._covers_input,
            "title_config": self._title_config,
            "title_config_strict": self._title_config_strict,
            "distinguish_same_name_libraries": self._distinguish_same_name_libraries,
            "main_title_font_url": str(self._main_title_font_url),
            "subtitle_font_url": str(self._subtitle_font_url),
            "custom_text_font_url": str(self._custom_text_font_url),
            "zh_font_url": str(self._main_title_font_url),
            "en_font_url": str(self._subtitle_font_url),
            "main_title_font_path": str(self._main_title_font_path),
            "subtitle_font_path": str(self._subtitle_font_path),
            "custom_text_font_path": str(self._custom_text_font_path),
            "zh_font_path": str(self._main_title_font_path),
            "en_font_path": str(self._subtitle_font_path),
            "cover_style": self._cover_style,
            "cover_style_base": self._cover_style_base,
            "cover_style_variant": self._cover_style_variant,
            "multi_1_blur": self._multi_1_blur,
            "main_title_font_size": self._main_title_font_size,
            "subtitle_font_size": self._subtitle_font_size,
            "zh_font_size": self._main_title_font_size,
            "en_font_size": self._subtitle_font_size,
            "blur_size": self._blur_size,
            "color_ratio": self._color_ratio,
            "use_primary": self._use_primary,
            "main_title_font_custom": self._main_title_font_custom,
            "subtitle_font_custom": self._subtitle_font_custom,
            "custom_text_font_custom": self._custom_text_font_custom,
            "zh_font_custom": self._main_title_font_custom,
            "en_font_custom": self._subtitle_font_custom,
            "main_title_font_preset": self._main_title_font_preset,
            "subtitle_font_preset": self._subtitle_font_preset,
            "custom_text_font_preset": self._custom_text_font_preset,
            "zh_font_preset": self._main_title_font_preset,
            "en_font_preset": self._subtitle_font_preset,
            "main_title_font_offset": self._main_title_font_offset,
            "zh_font_offset": self._main_title_font_offset,
            "title_spacing": self._title_spacing,
            "subtitle_line_spacing": self._subtitle_line_spacing,
            "en_line_spacing": self._subtitle_line_spacing,
            "title_scale": self._title_scale,
            "resolution": self._resolution,
            "custom_width": self._custom_width,
            "custom_height": self._custom_height,
            "image_count_mode": self._image_count_mode,
            "image_count": self._image_count,
            "animation_duration": self._animation_duration,
            "animation_scroll": self._animation_scroll,
            "animation_fps": self._animation_fps,
            "animation_format": self._animation_format,
            "animation_resolution": self._animation_resolution,
            "animation_reduce_colors": self._animation_reduce_colors,
            "animated_2_image_count": self._animated_2_image_count,
            "animated_2_departure_type": self._animated_2_departure_type,
            "animated_settings": animated_settings_payload,
            "bg_color_mode": self._bg_color_mode,
            "custom_bg_color": self._custom_bg_color,
            "clean_images": self._clean_images,
            "clean_fonts": self._clean_fonts,
            "backup_enabled": self._backup_enabled,
            "backup_cron": self._backup_cron,
            "backup_path": self._backup_path,
            "save_recent_covers": self._save_recent_covers,
            "covers_history_limit_per_library": self._covers_history_limit_per_library,
            "covers_page_history_limit": self._covers_page_history_limit,
            "history_retention_batches": self._history_retention_batches,
            "custom_static_layout": json.dumps(self._custom_static_layout, ensure_ascii=False)
            if self._custom_static_layout is not None
            else "",
            "custom_static_layouts": json.dumps(self._custom_static_layouts, ensure_ascii=False)
            if self._custom_static_layouts
            else "",
            "custom_static_active_id": self._custom_static_active_id or "",
            "style_naming_v2": True,
        })

    def __extract_request_payload(self, data: Optional[Any] = None, kwargs: Optional[Any] = None) -> Dict[str, Any]:
        try:
            import json
        except Exception:
            json = None  # type: ignore

        wrapper_keys = [
            "data",
            "body",
            "payload",
            "params",
            "request",
            "json",
            "content",
            "form",
            "kwargs",
            "args",
            "query",
        ]

        def _normalize(candidate: Any, depth: int = 0) -> Dict[str, Any]:
            if depth > 5 or candidate is None:
                return {}

            if isinstance(candidate, str) and candidate:
                try:
                    if json is not None:
                        parsed = json.loads(candidate)
                        return _normalize(parsed, depth + 1)
                except Exception:
                    return {}

            if isinstance(candidate, dict):
                direct_keys = {
                    "active_id",
                    "custom_static_active_id",
                    "layout",
                    "custom_static_layout",
                    "templates",
                    "custom_static_layouts",
                    "layout_json",
                    "templates_json",
                    "style",
                    "id",
                    "files",
                    "file",
                    "name",
                    "path",
                    "url",
                    "font_url",
                    "fontUrl",
                    "value",
                    "new_name",
                    "newName",
                    "data_url",
                    "dataUrl",
                    "chunk_data",
                    "chunkData",
                    "chunk_index",
                    "chunkIndex",
                    "chunk_total",
                    "chunkTotal",
                    "upload_id",
                    "uploadId",
                    "backup_path",
                    "title_config",
                    "title_config_strict",
                    "distinguish_same_name_libraries",
                    "strict",
                    "yaml",
                    "content",
                    "poster_source",
                    "use_primary",
                    "sort_by",
                    "image_count_mode",
                    "image_count",
                    "resolution",
                    "animation_resolution",
                    "enabled",
                    "auto_save_config",
                    "update_now",
                    "transfer_monitor",
                    "monitor_source",
                    "lock_latest_sort",
                    "cron",
                    "delay",
                    "selected_servers",
                    "include_libraries",
                    "covers_output",
                    "covers_input",
                    "main_title_font_preset",
                    "subtitle_font_preset",
                    "custom_text_font_preset",
                    "save_recent_covers",
                    "covers_history_limit_per_library",
                    "covers_page_history_limit",
                }
                if any(key in candidate for key in direct_keys):
                    return candidate

                for key in wrapper_keys:
                    nested = candidate.get(key)
                    nested_payload = _normalize(nested, depth + 1)
                    if nested_payload:
                        return nested_payload
                if any(key in candidate for key in wrapper_keys):
                    non_wrapper_values = [
                        value
                        for key, value in candidate.items()
                        if key not in wrapper_keys and value not in (None, "", [], {})
                    ]
                    if not non_wrapper_values:
                        return {}
                return candidate

            for attr in ("dict", "model_dump"):
                method = getattr(candidate, attr, None)
                if callable(method):
                    try:
                        return _normalize(method(), depth + 1)
                    except Exception:
                        pass

            if hasattr(candidate, "__dict__"):
                try:
                    return _normalize(vars(candidate), depth + 1)
                except Exception:
                    pass

            return {}

        for raw in (data, kwargs):
            payload = _normalize(raw)
            if payload:
                return payload
        return {}

    async def __read_api_payload(self, request: Optional[Request] = None, data: Optional[Any] = None, kwargs: Optional[Any] = None) -> Dict[str, Any]:
        body_payload: Any = None
        if request is not None:
            try:
                body_payload = await request.json()
            except Exception:
                body_payload = None
        raw = self.__extract_request_payload(data=body_payload, kwargs={"data": data, "kwargs": kwargs})
        if raw:
            return raw
        return self.__extract_request_payload(data=data, kwargs=kwargs)

    @staticmethod
    def __decode_json_value(value: Any, fallback: Any = None) -> Any:
        if isinstance(value, str) and value:
            try:
                import json
                return json.loads(value)
            except Exception:
                return fallback
        return value if value is not None else fallback

    def __custom_static_state_file(self) -> Path:
        return self.get_data_path() / "custom_static_layout_state.json"

    def __custom_static_sticker_dir(self) -> Path:
        return self.get_data_path() / "stickers"

    def __custom_font_library_dir(self) -> Path:
        return self.get_data_path() / "fonts" / "custom"

    def __custom_font_upload_temp_dir(self) -> Path:
        return self.get_data_path() / "fonts" / ".upload"

    @staticmethod
    def __is_custom_font_asset(file_path: Path) -> bool:
        return file_path.is_file() and file_path.suffix.lower() in {".ttf", ".ttc", ".otf", ".woff", ".woff2"}

    @staticmethod
    def __sanitize_font_filename(name: str, fallback: str = "font") -> str:
        safe_name = re.sub(r"[^\w_.-]+", "_", str(name or fallback), flags=re.UNICODE).strip("._") or fallback
        suffix = Path(safe_name).suffix.lower()
        allowed_exts = {".ttf", ".ttc", ".otf", ".woff", ".woff2"}
        if suffix not in allowed_exts:
            safe_name = f"{Path(safe_name).stem or fallback}.ttf"
        return safe_name

    def __next_custom_font_path(self, name: str) -> Path:
        target_dir = self.__custom_font_library_dir()
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_name = self.__sanitize_font_filename(name)
        suffix = Path(safe_name).suffix.lower()
        stem = Path(safe_name).stem[:44] or "font"
        target_file = target_dir / f"{stem}{suffix}"
        if target_file.exists():
            target_file = target_dir / f"{stem}_{uuid.uuid4().hex[:8]}{suffix}"
        return target_file

    def __finalize_uploaded_font_file(self, source_file: Path, name: str) -> Dict[str, Any]:
        target_file = self.__next_custom_font_path(name)
        try:
            source_file.replace(target_file)
        except Exception:
            shutil.copy2(source_file, target_file)
            source_file.unlink(missing_ok=True)
        if not self.__is_custom_font_asset(target_file) or target_file.stat().st_size <= 0:
            target_file.unlink(missing_ok=True)
            raise ValueError("字体文件无效")
        logger.info(
            "【YahahaCoverStudio】自定义字体已保存: %s (%s bytes)",
            target_file,
            target_file.stat().st_size,
        )
        return self.__build_font_library_item(target_file)

    @staticmethod
    def __custom_static_state_key() -> str:
        return "custom_static_state"

    def __save_custom_static_sticker(self, layer: Dict[str, Any]) -> Dict[str, Any]:
        data_url = str(layer.get("stickerDataUrl") or "").strip()
        existing_path = str(layer.get("stickerPath") or "").strip()
        if not existing_path:
            try:
                sticker_url = str(layer.get("stickerUrl") or "").strip()
                file_values = parse_qs(urlparse(sticker_url).query).get("file") if sticker_url else None
                if file_values:
                    existing_path = unquote(str(file_values[0] or "")).strip()
            except Exception:
                existing_path = ""
        if existing_path and Path(existing_path).is_file():
            layer["stickerPath"] = str(Path(existing_path).resolve())
            layer["stickerUrl"] = self.__get_preview_file_url(layer["stickerPath"])
            layer.pop("stickerDataUrl", None)
            return layer
        if not data_url.startswith("data:image/") or "," not in data_url:
            return layer
        try:
            header, encoded = data_url.split(",", 1)
            mime_match = re.match(r"^data:(image/[a-zA-Z0-9.+-]+);base64$", header)
            mime_type = mime_match.group(1) if mime_match else "image/png"
            extension = {
                "image/jpeg": ".jpg",
                "image/jpg": ".jpg",
                "image/png": ".png",
                "image/webp": ".webp",
                "image/gif": ".gif",
                "image/svg+xml": ".svg",
            }.get(mime_type.lower(), ".png")
            content = base64.b64decode(encoded)
            if not content:
                return layer
            digest = hashlib.sha256(content).hexdigest()[:20]
            safe_name = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(layer.get("stickerName") or "sticker")).strip("._")
            stem = Path(safe_name).stem[:40] or "sticker"
            target_dir = self.__custom_static_sticker_dir()
            target_dir.mkdir(parents=True, exist_ok=True)
            target_file = target_dir / f"{stem}_{digest}{extension}"
            if not target_file.exists():
                target_file.write_bytes(content)
            layer["stickerPath"] = str(target_file.resolve())
            layer["stickerUrl"] = self.__get_preview_file_url(layer["stickerPath"])
            layer.pop("stickerDataUrl", None)
        except Exception as err:
            logger.warning("【YahahaCoverStudio】保存贴图文件失败: %s", err)
        return layer

    def __build_custom_static_state_payload(self) -> Dict[str, Any]:
        return {
            "custom_static_layout": self._custom_static_layout,
            "custom_static_layouts": self._custom_static_layouts or [],
            "custom_static_active_id": self._custom_static_active_id or "",
            "schema": "mcr-custom-static-state/v1",
            "updated_at": datetime.datetime.now().isoformat(),
        }

    @staticmethod
    def __count_custom_static_layers(layout: Any) -> int:
        if not isinstance(layout, dict):
            return 0
        layers = layout.get("layers")
        if not isinstance(layers, list):
            return 0

        def _count(items: List[Any]) -> int:
            total = 0
            for item in items:
                if not isinstance(item, dict):
                    continue
                total += 1
                children = item.get("children")
                if isinstance(children, list):
                    total += _count(children)
            return total

        return _count(layers)

    def __apply_custom_static_state_payload(self, payload: Dict[str, Any]) -> bool:
        layout = self.__decode_json_value(payload.get("custom_static_layout"), None)
        templates = self.__decode_json_value(payload.get("custom_static_layouts"), None)
        active_id = payload.get("custom_static_active_id")

        changed = False
        if isinstance(layout, dict):
            self._custom_static_layout = self.__normalize_custom_static_template(layout)
            changed = True
        if isinstance(templates, list):
            normalized_templates: List[Dict[str, Any]] = []
            for template in templates:
                if not isinstance(template, dict):
                    continue
                next_template = dict(template)
                if isinstance(next_template.get("layout"), dict):
                    next_template["layout"] = self.__normalize_custom_static_template(next_template.get("layout"))
                normalized_templates.append(next_template)
            self._custom_static_layouts = normalized_templates
            changed = True
        if active_id is not None:
            self._custom_static_active_id = str(active_id) if active_id else None
            changed = True

        if self._custom_static_active_id and self._custom_static_layouts and not isinstance(layout, dict):
            active_tpl = next(
                (
                    tpl
                    for tpl in self._custom_static_layouts
                    if str(tpl.get('id', '')) == str(self._custom_static_active_id)
                ),
                None,
            )
            if isinstance(active_tpl, dict) and isinstance(active_tpl.get('layout'), dict):
                self._custom_static_layout = active_tpl.get('layout')
        self.__sync_active_custom_static_template()
        return changed

    def __sync_active_custom_static_template(self):
        """Keep active layout and template list in lockstep before persisting."""
        if not isinstance(self._custom_static_layout, dict):
            return

        if not self._custom_static_active_id:
            if self._custom_static_layouts:
                first_template = next(
                    (tpl for tpl in self._custom_static_layouts if isinstance(tpl, dict) and tpl.get("id")),
                    None,
                )
                self._custom_static_active_id = str(first_template.get("id")) if first_template else None
            if not self._custom_static_active_id:
                self._custom_static_active_id = str(uuid.uuid4())

        active_id = str(self._custom_static_active_id)
        templates = [
            dict(tpl)
            for tpl in (self._custom_static_layouts or [])
            if isinstance(tpl, dict) and tpl.get("id")
        ]
        matched = False
        for index, template in enumerate(templates):
            if str(template.get("id", "")) != active_id:
                continue
            templates[index] = {
                **template,
                "id": active_id,
                "name": template.get("name") or "自定义方案",
                "layout": self.__normalize_custom_static_template(self._custom_static_layout),
                "baseStyle": template.get("baseStyle") or "custom_static",
            }
            matched = True
            break

        if not matched:
            templates.append({
                "id": active_id,
                "name": "自定义方案",
                "layout": self.__normalize_custom_static_template(self._custom_static_layout),
                "baseStyle": "custom_static",
            })

        self._custom_static_layouts = templates

    def __load_custom_static_state(self):
        try:
            import json

            mp_payload = self.__decode_json_value(self.get_data(self.__custom_static_state_key()), None)
            if isinstance(mp_payload, dict) and self.__apply_custom_static_state_payload(mp_payload):
                logger.info("【YahahaCoverStudio】已从 MoviePilot 插件数据读取自定义静态布局")
                return

            state_file = self.__custom_static_state_file()
            if state_file.exists() and state_file.is_file():
                try:
                    payload = json.loads(state_file.read_text(encoding="utf-8"))
                    if isinstance(payload, dict) and self.__apply_custom_static_state_payload(payload):
                        logger.info("【YahahaCoverStudio】已从独立状态文件读取自定义静态布局")
                        return
                except Exception as file_err:
                    logger.warning(f"【YahahaCoverStudio】读取自定义布局状态文件失败: {file_err}")

            if not self._custom_static_layout and not self._custom_static_layouts:
                self.__apply_custom_static_state_payload({
                    "custom_static_layout": self.get_data('custom_static_layout'),
                    "custom_static_layouts": self.get_data('custom_static_layouts'),
                    "custom_static_active_id": self.get_data('custom_static_active_id'),
                })
        except Exception as e:
            logger.warning(f"【YahahaCoverStudio】读取自定义静态布局持久化数据失败: {e}")

    def __save_custom_static_state(self):
        import json

        self.__sync_active_custom_static_template()
        state_file = self.__custom_static_state_file()
        state_file.parent.mkdir(parents=True, exist_ok=True)
        payload = self.__build_custom_static_state_payload()
        self.save_data(self.__custom_static_state_key(), payload)
        saved_payload = self.__decode_json_value(self.get_data(self.__custom_static_state_key()), None)
        if not isinstance(saved_payload, dict):
            raise RuntimeError("MoviePilot 插件数据写入后读回为空或格式错误")
        saved_templates = saved_payload.get("custom_static_layouts")
        if not isinstance(saved_templates, list):
            raise RuntimeError("MoviePilot 插件数据写入后 custom_static_layouts 格式错误")
        if str(saved_payload.get("custom_static_active_id") or "") != str(self._custom_static_active_id or ""):
            raise RuntimeError("MoviePilot 插件数据写入后 active_id 不一致")
        saved_layout = saved_payload.get("custom_static_layout")
        expected_layer_count = self.__count_custom_static_layers(self._custom_static_layout)
        saved_layer_count = self.__count_custom_static_layers(saved_layout)
        if expected_layer_count and saved_layer_count != expected_layer_count:
            raise RuntimeError(
                f"MoviePilot 插件数据写入后图层数量不一致: expected={expected_layer_count}, saved={saved_layer_count}"
            )

        tmp_file = state_file.with_suffix(".json.tmp")
        tmp_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_file.replace(state_file)
        self.save_data('custom_static_layout', self._custom_static_layout)
        self.save_data('custom_static_layouts', self._custom_static_layouts or [])
        self.save_data('custom_static_active_id', self._custom_static_active_id or '')
        logger.info(
            "【YahahaCoverStudio】自定义静态布局已写入 MoviePilot 插件数据和独立状态文件: %s",
            state_file,
        )

    def __normalize_custom_static_layer(self, layer: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(layer or {})
        def pick_value(*values, default=None):
            for value in values:
                if value is not None:
                    return value
            return default

        layer_type = str(normalized.get("type") or "image")
        if layer_type == "group":
            children = normalized.get("children") if isinstance(normalized.get("children"), list) else []
            normalized["children"] = [
                self.__normalize_custom_static_layer(child)
                for child in children
                if isinstance(child, dict)
            ]
        elif layer_type in ("title_zh", "main_title"):
            normalized["type"] = "main_title"
        elif layer_type in ("title_en", "subtitle"):
            normalized["type"] = "subtitle"
        elif layer_type not in ("image", "text"):
            normalized["type"] = "image"
        frame = normalized.get("frame") if isinstance(normalized.get("frame"), dict) else {}
        transform = normalized.get("transform") if isinstance(normalized.get("transform"), dict) else {}
        effects = normalized.get("effects") if isinstance(normalized.get("effects"), dict) else {}
        shadow = normalized.get("shadow") if isinstance(normalized.get("shadow"), dict) else {}
        effect_shadow = effects.get("shadow") if isinstance(effects.get("shadow"), dict) else {}
        text_style = normalized.get("textStyle") if isinstance(normalized.get("textStyle"), dict) else {}

        normalized["x"] = pick_value(normalized.get("x"), frame.get("x"), default=0)
        normalized["y"] = pick_value(normalized.get("y"), frame.get("y"), default=0)
        normalized["width"] = pick_value(normalized.get("width"), frame.get("width"), default=0)
        normalized["height"] = pick_value(normalized.get("height"), frame.get("height"), default=0)
        normalized["rotation"] = pick_value(normalized.get("rotation"), transform.get("rotation"), default=0)
        normalized["pivotX"] = pick_value(normalized.get("pivotX"), transform.get("pivotX"), default=0.5)
        normalized["pivotY"] = pick_value(normalized.get("pivotY"), transform.get("pivotY"), default=0.5)
        normalized["opacity"] = pick_value(normalized.get("opacity"), transform.get("opacity"), default=1)
        normalized["radius"] = pick_value(normalized.get("radius"), normalized.get("cornerRadius"), default=0)
        normalized["cropFocusX"] = pick_value(normalized.get("cropFocusX"), default=0.5)
        normalized["cropFocusY"] = pick_value(normalized.get("cropFocusY"), default=0.5)
        normalized["blur"] = pick_value(normalized.get("blur"), effects.get("blur"), default=0)
        normalized["shadowBlur"] = pick_value(normalized.get("shadowBlur"), effect_shadow.get("blur"), shadow.get("blur"), default=0)
        normalized["shadowOffsetX"] = pick_value(normalized.get("shadowOffsetX"), effect_shadow.get("offsetX"), shadow.get("offsetX"), shadow.get("x"), default=0)
        normalized["shadowOffsetY"] = pick_value(normalized.get("shadowOffsetY"), effect_shadow.get("offsetY"), shadow.get("offsetY"), shadow.get("y"), default=0)
        normalized["shadowOpacity"] = pick_value(normalized.get("shadowOpacity"), effect_shadow.get("opacity"), shadow.get("opacity"), default=0.28)
        normalized["fontFamily"] = pick_value(normalized.get("fontFamily"), text_style.get("fontFamily"))
        normalized["fontSize"] = pick_value(normalized.get("fontSize"), text_style.get("fontSize"), default=0)
        normalized["content"] = pick_value(normalized.get("content"), text_style.get("content"))
        content_source = pick_value(normalized.get("contentSource"), text_style.get("contentSource"), default="fixed")
        normalized["contentSource"] = content_source if content_source in ("fixed", "library") else "fixed"
        normalized["contentKey"] = str(pick_value(normalized.get("contentKey"), text_style.get("contentKey"), default="")).strip()
        mask_mode = pick_value(normalized.get("maskMode"), text_style.get("maskMode"), default="normal")
        normalized["maskMode"] = mask_mode if mask_mode in ("normal", "knockout-text", "show-text") else "normal"
        if normalized.get("type") == "image":
            source = normalized.get("source") if isinstance(normalized.get("source"), dict) else {}
            try:
                source_index = int(normalized.get("sourceIndex", source.get("slot", 1)) or 1)
            except (TypeError, ValueError):
                source_index = 1
            normalized["sourceIndex"] = source_index
            normalized["source"] = {"kind": "slot", "slot": source_index}
            has_sticker_ref = any(
                str(normalized.get(key) or "").strip()
                for key in ("stickerDataUrl", "stickerPath", "stickerUrl")
            )
            normalized["assetKind"] = "sticker" if normalized.get("assetKind") == "sticker" or has_sticker_ref else "source"
            if normalized["assetKind"] == "sticker":
                normalized = self.__save_custom_static_sticker(normalized)
            normalized["fit"] = normalized.get("fit") if normalized.get("fit") in ("cover", "contain", "stretch") else "cover"
        normalized["frame"] = {
            "x": normalized.get("x", 0),
            "y": normalized.get("y", 0),
            "width": normalized.get("width", 0),
            "height": normalized.get("height", 0),
        }
        normalized["transform"] = {
            "rotation": normalized.get("rotation", 0),
            "pivotX": normalized.get("pivotX", 0.5),
            "pivotY": normalized.get("pivotY", 0.5),
            "opacity": normalized.get("opacity", 1),
        }
        normalized["shadow"] = {
            "x": normalized.get("shadowOffsetX", 0),
            "y": normalized.get("shadowOffsetY", 0),
            "blur": normalized.get("shadowBlur", 0),
            "opacity": normalized.get("shadowOpacity", 0.28),
        }
        normalized["effects"] = {
            "blur": normalized.get("blur", 0),
            "shadow": {
                "blur": normalized.get("shadowBlur", 0),
                "offsetX": normalized.get("shadowOffsetX", 0),
                "offsetY": normalized.get("shadowOffsetY", 0),
                "opacity": normalized.get("shadowOpacity", 0.28),
                "color": effect_shadow.get("color", "#000000"),
            },
        }
        if normalized.get("type") in ("main_title", "title_zh", "subtitle", "title_en", "text"):
            normalized["textStyle"] = {
                "fontFamily": normalized.get("fontFamily"),
                "fontSize": normalized.get("fontSize", 0),
                "textAlign": normalized.get("textAlign", "center"),
                "maskMode": normalized.get("maskMode", "normal"),
            }
            if normalized.get("type") == "text":
                normalized["textStyle"]["content"] = normalized.get("content", "")
                normalized["textStyle"]["contentSource"] = normalized.get("contentSource", "fixed")
                normalized["textStyle"]["contentKey"] = normalized.get("contentKey", "")
        return normalized

    def __normalize_custom_static_template(self, layout: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        template = dict(layout or {})
        document = template.get("canvas") if isinstance(template.get("canvas"), dict) else template.get("document") if isinstance(template.get("document"), dict) else {}
        width = int(document.get("width", 1920) or 1920)
        height = int(document.get("height", 1080) or 1080)
        raw_layers = template.get("layers") if isinstance(template.get("layers"), list) else []
        normalized_layers = [
            self.__normalize_custom_static_layer(layer)
            for layer in raw_layers
            if isinstance(layer, dict)
        ]
        computed = template.get("computed") if isinstance(template.get("computed"), dict) else {}
        background = template.get("background") if isinstance(template.get("background"), dict) else {
            "type": "blurred-image-color",
            "imageSource": {"kind": "slot", "slot": 1},
            "colorSource": "auto",
            "color": "#5f7185",
            "color2": "#0a1628",
            "colorRatio": 0.8,
            "opacity": 1,
            "blur": 50,
            "grain": 0.18,
            "zIndex": 0,
        }
        background = dict(background)
        try:
            background["zIndex"] = int(float(background.get("zIndex", 0) or 0))
        except (TypeError, ValueError):
            background["zIndex"] = 0
        return {
            "schema": "mcr-template/v1",
            "version": template.get("version", "1.0"),
            "canvas": {
                "width": width,
                "height": height,
                "unit": document.get("unit", "px"),
            },
            "document": {
                "width": width,
                "height": height,
                "unit": document.get("unit", "px"),
            },
            "background": background,
            "assets": template.get("assets") if isinstance(template.get("assets"), dict) else {},
            "layers": normalized_layers,
            "computed": computed,
        }

    @staticmethod
    def __resolve_configurable_text_layer_value(layer: Dict[str, Any], custom_texts: Optional[Dict[str, str]] = None) -> str:
        custom_texts = custom_texts or {}
        fallback = str(layer.get("content") or "")
        if str(layer.get("contentSource") or "fixed") != "library":
            return fallback
        key = str(layer.get("contentKey") or "").strip()
        if key and key in custom_texts:
            return str(custom_texts.get(key) or fallback)
        for default_key in ("default", "text", "custom_text", "content"):
            if default_key in custom_texts:
                return str(custom_texts.get(default_key) or fallback)
        return fallback

    def __build_custom_static_text_layout(
        self,
        layout: Optional[Dict[str, Any]],
        title: Tuple[str, str],
        custom_texts: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        normalized_layout = self.__normalize_custom_static_template(layout)
        custom_texts = custom_texts or {}
        text_layout: Dict[str, Any] = {}
        if not self.__ensure_fonts_ready(force_refresh=False):
            return self.__hydrate_custom_static_stickers_for_preview(normalized_layout)

        for layer in normalized_layout.get("layers", []):
            if not isinstance(layer, dict):
                continue
            layer_type = str(layer.get("type") or "")
            text_value = ""
            font_path = ""
            if layer_type in ("main_title", "title_zh"):
                text_value = title[0] if len(title) > 0 else ""
                font_path = self.__resolve_template_font_path("main_title", text_value)
            elif layer_type in ("subtitle", "title_en"):
                text_value = title[1] if len(title) > 1 else ""
                font_path = self.__resolve_template_font_path("subtitle", text_value)
            elif layer_type == "text":
                text_value = self.__resolve_configurable_text_layer_value(layer, custom_texts)
                layer["content"] = text_value
                font_family = str(layer.get("fontFamily") or "custom_text")
                font_path = self.__resolve_template_font_path(font_family, text_value)
            if not text_value or not font_path:
                continue
            measured = measure_text_layer(
                layer=layer,
                text=text_value,
                font_path=font_path,
                scale_x=1.0,
                scale_y=1.0,
            )
            if measured:
                text_layout[str(layer.get("id") or uuid.uuid4().hex)] = measured

        normalized_layout["computed"] = {
            **(normalized_layout.get("computed") if isinstance(normalized_layout.get("computed"), dict) else {}),
            "textLayout": text_layout,
        }
        return self.__hydrate_custom_static_stickers_for_preview(normalized_layout)

    def __sticker_data_url_from_file(self, sticker_path: str) -> str:
        try:
            target_file = Path(str(sticker_path or "")).resolve()
            if not target_file.is_file():
                return ""
            mime_type, _ = mimetypes.guess_type(str(target_file))
            if not mime_type or not mime_type.startswith("image/"):
                mime_type = "image/png"
            encoded = base64.b64encode(target_file.read_bytes()).decode("utf-8")
            return f"data:{mime_type};base64,{encoded}"
        except Exception as err:
            logger.warning("【YahahaCoverStudio】读取贴图预览数据失败: %s", err)
            return ""

    def __hydrate_custom_static_stickers_for_preview(self, layout: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        hydrated = dict(layout or {})

        def visit(layer: Dict[str, Any]) -> Dict[str, Any]:
            next_layer = dict(layer or {})
            if next_layer.get("type") == "group" and isinstance(next_layer.get("children"), list):
                next_layer["children"] = [
                    visit(child)
                    for child in next_layer.get("children") or []
                    if isinstance(child, dict)
                ]
                return next_layer
            has_sticker_ref = any(
                str(next_layer.get(key) or "").strip()
                for key in ("stickerDataUrl", "stickerPath", "stickerUrl")
            )
            if next_layer.get("type") != "image" or not (next_layer.get("assetKind") == "sticker" or has_sticker_ref):
                return next_layer
            next_layer["assetKind"] = "sticker"
            next_layer = self.__save_custom_static_sticker(next_layer)
            sticker_path = str(next_layer.get("stickerPath") or "").strip()
            if sticker_path:
                next_layer["stickerUrl"] = self.__get_preview_file_url(sticker_path)
            if sticker_path and not str(next_layer.get("stickerDataUrl") or "").startswith("data:image/"):
                data_url = self.__sticker_data_url_from_file(sticker_path)
                if data_url:
                    next_layer["stickerDataUrl"] = data_url
            return next_layer

        layers = hydrated.get("layers") if isinstance(hydrated.get("layers"), list) else []
        hydrated["layers"] = [visit(layer) for layer in layers if isinstance(layer, dict)]
        return hydrated

    def __hydrate_custom_static_templates_for_preview(self, templates: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        hydrated_templates: List[Dict[str, Any]] = []
        for template in templates or []:
            if not isinstance(template, dict):
                continue
            next_template = dict(template)
            if isinstance(next_template.get("layout"), dict):
                next_template["layout"] = self.__hydrate_custom_static_stickers_for_preview(next_template.get("layout"))
            hydrated_templates.append(next_template)
        return hydrated_templates

    def __custom_static_preview_payload(self) -> Dict[str, Any]:
        return {
            "custom_static_layout": self.__hydrate_custom_static_stickers_for_preview(self._custom_static_layout)
            if isinstance(self._custom_static_layout, dict)
            else self._custom_static_layout,
            "custom_static_layouts": self.__hydrate_custom_static_templates_for_preview(self._custom_static_layouts),
            "custom_static_active_id": self._custom_static_active_id,
        }

    def __resolve_custom_static_sticker_path(self, raw_path: str = "", name: str = "") -> Optional[Path]:
        sticker_dir = self.__custom_static_sticker_dir().resolve()
        candidates: List[Path] = []
        if raw_path:
            candidates.append(Path(str(raw_path)).expanduser())
        if name:
            candidates.append(sticker_dir / Path(str(name)).name)
        for candidate in candidates:
            try:
                resolved = candidate.resolve()
                if not resolved.is_file():
                    continue
                if resolved == sticker_dir or sticker_dir not in resolved.parents:
                    continue
                return resolved
            except Exception:
                continue
        return None

    def __build_sticker_library_item(self, file_path: Path) -> Dict[str, Any]:
        stat = file_path.stat()
        width = 0
        height = 0
        try:
            from PIL import Image
            with Image.open(file_path) as image:
                width = int(image.width or 0)
                height = int(image.height or 0)
        except Exception:
            pass
        return {
            "name": file_path.name,
            "path": str(file_path.resolve()),
            "url": self.__get_preview_file_url(str(file_path.resolve())),
            "dataUrl": self.__sticker_data_url_from_file(str(file_path.resolve())),
            "size": int(stat.st_size),
            "mtime": float(stat.st_mtime),
            "width": width,
            "height": height,
        }

    def __font_data_url_from_file(self, font_path: str) -> str:
        try:
            target_file = Path(str(font_path or "")).resolve()
            if not target_file.is_file():
                return ""
            mime_type, _ = mimetypes.guess_type(str(target_file))
            if not mime_type:
                suffix = target_file.suffix.lower()
                mime_type = "font/ttf" if suffix in [".ttf", ".ttc"] else "font/otf" if suffix == ".otf" else "font/woff2"
            encoded = base64.b64encode(target_file.read_bytes()).decode("utf-8")
            return f"data:{mime_type};base64,{encoded}"
        except Exception as err:
            logger.warning("【YahahaCoverStudio】读取字体预览数据失败: %s", err)
            return ""

    def __font_library_value(self, file_path: Path) -> str:
        return f"font:{file_path.name}"

    def __resolve_custom_font_path(self, raw_value: str = "", name: str = "") -> Optional[Path]:
        font_dir = self.__custom_font_library_dir().resolve()
        candidates: List[Path] = []
        value = str(raw_value or "").strip()
        if value.startswith("font:"):
            candidates.append(font_dir / value.split(":", 1)[1])
        elif value:
            candidates.append(Path(value).expanduser())
            candidates.append(font_dir / Path(value).name)
        if name:
            candidates.append(font_dir / Path(str(name)).name)
        for candidate in candidates:
            try:
                resolved = candidate.resolve()
                if resolved == font_dir or font_dir not in resolved.parents:
                    continue
                if self.__is_custom_font_asset(resolved):
                    return resolved
            except Exception:
                continue
        return None

    def __build_font_library_item(self, file_path: Path) -> Dict[str, Any]:
        stat = file_path.stat()
        value = self.__font_library_value(file_path)
        title = file_path.stem[:48] or file_path.name
        return {
            "title": title,
            "name": file_path.name,
            "value": value,
            "path": str(file_path.resolve()),
            "url": self.__get_preview_file_url(str(file_path.resolve())),
            "dataUrl": "",
            "size": int(stat.st_size),
            "mtime": float(stat.st_mtime),
            "renderable": bool(file_path.suffix.lower() in {".ttf", ".ttc", ".otf"} and validate_font_file(file_path)),
        }

    def api_fonts(self):
        """返回可选字体库，包含用户上传字体。"""
        try:
            font_dir = self.__custom_font_library_dir()
            font_dir.mkdir(parents=True, exist_ok=True)
            allowed_exts = {".ttf", ".ttc", ".otf", ".woff", ".woff2"}
            custom_items = [
                self.__build_font_library_item(file_path)
                for file_path in sorted(
                    font_dir.iterdir(),
                    key=lambda path: path.stat().st_mtime if path.exists() else 0,
                    reverse=True,
                )
                if file_path.is_file() and file_path.suffix.lower() in allowed_exts
            ]
            return {"code": 0, "data": {"custom": custom_items}}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】获取字体库失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"获取字体库失败: {e}"}

    def api_delete_font(self, file: str = "", name: str = "", data: Optional[Dict[str, Any]] = Body(default=None), kwargs: Optional[Any] = Body(default=None)):
        """删除一个已上传字体。"""
        try:
            raw = self.__extract_request_payload(data=data, kwargs=kwargs)
            raw_file = str(file or raw.get("file") or raw.get("path") or raw.get("value") or "").strip()
            raw_name = str(name or raw.get("name") or "").strip()
            target_file = self.__resolve_custom_font_path(raw_file, raw_name)
            if not target_file or not target_file.exists():
                return {"code": 1, "msg": "字体不存在或路径无效"}
            target_file.unlink(missing_ok=True)
            self.__ensure_fonts_ready(force_refresh=True)
            self.__update_config()
            return {"code": 0, "msg": "字体已删除"}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】删除字体失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"删除字体失败: {e}"}

    async def api_rename_font(self, request: Request, data: Optional[Dict[str, Any]] = Body(default=None), kwargs: Optional[Any] = Body(default=None)):
        """重命名一个已上传字体文件。"""
        try:
            raw = await self.__read_api_payload(request=request, data=data, kwargs=kwargs)
            raw_file = str(raw.get("file") or raw.get("path") or raw.get("value") or "").strip()
            raw_name = str(raw.get("name") or "").strip()
            new_name = str(raw.get("new_name") or raw.get("newName") or raw.get("title") or "").strip()
            if not new_name:
                return {"code": 1, "msg": "新字体名称不能为空"}
            target_file = self.__resolve_custom_font_path(raw_file, raw_name)
            if not target_file or not target_file.exists():
                return {"code": 1, "msg": "字体不存在或路径无效"}
            original_value = self.__font_library_value(target_file)
            suffix = target_file.suffix.lower()
            if Path(new_name).suffix.lower() not in {".ttf", ".ttc", ".otf", ".woff", ".woff2"}:
                new_name = f"{new_name}{suffix}"
            safe_name = self.__sanitize_font_filename(new_name, fallback=target_file.stem)
            if safe_name == target_file.name:
                return {"code": 0, "msg": "字体名称未变化", "data": self.__build_font_library_item(target_file)}
            new_file = self.__next_custom_font_path(safe_name)
            target_file.replace(new_file)
            new_value = self.__font_library_value(new_file)
            for attr in ("_main_title_font_preset", "_subtitle_font_preset", "_custom_text_font_preset"):
                if getattr(self, attr, "") == original_value:
                    setattr(self, attr, new_value)
            self.__ensure_fonts_ready(force_refresh=True)
            self.__update_config()
            return {"code": 0, "msg": "字体已重命名", "data": self.__build_font_library_item(new_file)}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】重命名字体失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"重命名字体失败: {e}"}

    async def api_upload_font(
        self,
        request: Request,
        data: Optional[Dict[str, Any]] = Body(default=None),
        kwargs: Optional[Any] = Body(default=None),
    ):
        """保存自定义字体到插件数据目录。"""
        try:
            body_payload: Any = None
            try:
                body_payload = await request.json()
            except Exception:
                body_payload = None
            raw = self.__extract_request_payload(data=body_payload, kwargs={"data": data, "kwargs": kwargs})
            if not raw:
                raw = self.__extract_request_payload(data=data, kwargs=kwargs)

            data_url = str(raw.get("data_url") or raw.get("dataUrl") or "").strip()
            chunk_data = str(raw.get("chunk_data") or raw.get("chunkData") or "").strip()
            font_url = str(raw.get("url") or raw.get("font_url") or raw.get("fontUrl") or "").strip()
            name = str(raw.get("name") or "font").strip() or "font"
            logger.info(
                "【YahahaCoverStudio】字体上传请求: name=%s, mode=%s, keys=%s",
                name,
                "chunk" if chunk_data else "url" if font_url else "data_url" if data_url else "empty",
                sorted(raw.keys())[:12] if isinstance(raw, dict) else [],
            )
            target_dir = self.__custom_font_library_dir()
            target_dir.mkdir(parents=True, exist_ok=True)
            allowed_exts = {".ttf", ".ttc", ".otf", ".woff", ".woff2"}

            if chunk_data:
                upload_id = re.sub(
                    r"[^a-zA-Z0-9_.-]+",
                    "_",
                    str(raw.get("upload_id") or raw.get("uploadId") or uuid.uuid4().hex),
                ).strip("._") or uuid.uuid4().hex
                try:
                    chunk_index = int(raw.get("chunk_index") if raw.get("chunk_index") is not None else raw.get("chunkIndex"))
                    chunk_total = int(raw.get("chunk_total") if raw.get("chunk_total") is not None else raw.get("chunkTotal"))
                except (TypeError, ValueError):
                    return {"code": 1, "msg": "字体分片参数无效"}
                if chunk_index < 0 or chunk_total <= 0 or chunk_index >= chunk_total:
                    return {"code": 1, "msg": "字体分片序号无效"}
                temp_root = self.__custom_font_upload_temp_dir()
                temp_dir = temp_root / upload_id
                temp_dir.mkdir(parents=True, exist_ok=True)
                (temp_dir / "name.txt").write_text(name, encoding="utf-8")
                (temp_dir / f"{chunk_index:06d}.part").write_bytes(base64.b64decode(chunk_data))

                part_files = [temp_dir / f"{index:06d}.part" for index in range(chunk_total)]
                if not all(part.exists() for part in part_files):
                    return {
                        "code": 0,
                        "msg": "字体分片已接收",
                        "data": {
                            "done": False,
                            "received": len([part for part in part_files if part.exists()]),
                            "total": chunk_total,
                        },
                    }

                assembled = temp_dir / "assembled.font"
                with assembled.open("wb") as output:
                    for part in part_files:
                        output.write(part.read_bytes())
                item = self.__finalize_uploaded_font_file(assembled, name)
                shutil.rmtree(temp_dir, ignore_errors=True)
                return {"code": 0, "msg": "字体已保存", "data": {**item, "done": True}}

            if font_url:
                parsed_url = urlparse(font_url)
                if parsed_url.scheme not in ("http", "https"):
                    return {"code": 1, "msg": "字体链接仅支持 http/https"}
                url_name = unquote(Path(parsed_url.path or "").name or "")
                safe_name = re.sub(r"[^a-zA-Z0-9_.-]+", "_", name if name != "font" else url_name or "font").strip("._") or "font"
                suffix = Path(safe_name).suffix.lower()
                if suffix not in allowed_exts:
                    url_suffix = Path(url_name).suffix.lower()
                    suffix = url_suffix if url_suffix in allowed_exts else ".ttf"
                    safe_name = f"{Path(safe_name).stem or 'font'}{suffix}"
                target_file = self.__next_custom_font_path(safe_name)
                network_helper = NetworkHelper(timeout=60, max_retries=1)
                if not network_helper.download_file_sync(font_url, target_file):
                    target_file.unlink(missing_ok=True)
                    return {"code": 1, "msg": "字体链接下载失败"}
                logger.info("【YahahaCoverStudio】自定义网络字体已保存: %s (%s bytes)", target_file, target_file.stat().st_size)
                item = self.__build_font_library_item(target_file)
                return {"code": 0, "msg": "字体已保存", "data": item}

            if not data_url.startswith("data:") or ";base64," not in data_url:
                return {"code": 1, "msg": "字体数据无效"}
            header, encoded = data_url.split(";base64,", 1)
            safe_name = re.sub(r"[^a-zA-Z0-9_.-]+", "_", name).strip("._") or "font"
            suffix = Path(safe_name).suffix.lower()
            if suffix not in allowed_exts:
                mime = header.lower()
                suffix = ".woff2" if "woff2" in mime else ".woff" if "woff" in mime else ".otf" if "opentype" in mime or "otf" in mime else ".ttf"
                safe_name = f"{Path(safe_name).stem or 'font'}{suffix}"
            temp_dir = self.__custom_font_upload_temp_dir()
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_file = temp_dir / f"{uuid.uuid4().hex}.font"
            temp_file.write_bytes(base64.b64decode(encoded))
            item = self.__finalize_uploaded_font_file(temp_file, safe_name)
            return {"code": 0, "msg": "字体已保存", "data": item}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】上传字体失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"上传字体失败: {e}"}

    def __resolve_backup_output_path(self, raw_path: str = "") -> Path:
        raw_path = str(raw_path or self._backup_path or "").strip()
        if raw_path:
            target = Path(raw_path).expanduser()
            if not target.is_absolute():
                target = self.get_data_path() / target
        else:
            target = self.get_data_path() / "backups"

        if target.suffix.lower() == ".json":
            target.parent.mkdir(parents=True, exist_ok=True)
            return target

        target.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return target / f"yahahacoverstudio_config_{timestamp}.json"

    def __backup_dirs(self) -> List[Path]:
        dirs: List[Path] = [self.get_data_path() / "backups"]
        raw_path = str(self._backup_path or "").strip()
        if raw_path:
            target = Path(raw_path).expanduser()
            if not target.is_absolute():
                target = self.get_data_path() / target
            dirs.append(target.parent if target.suffix.lower() == ".json" else target)
        unique: List[Path] = []
        seen = set()
        for directory in dirs:
            try:
                resolved = directory.resolve()
            except Exception:
                resolved = directory
            key = str(resolved)
            if key not in seen:
                seen.add(key)
                unique.append(resolved)
        return unique

    def __resolve_backup_file(self, raw_value: str = "") -> Optional[Path]:
        value = str(raw_value or "").strip()
        if not value:
            return None
        candidates: List[Path] = []
        raw_path = Path(value).expanduser()
        if raw_path.is_absolute():
            candidates.append(raw_path)
        for directory in self.__backup_dirs():
            candidates.append(directory / Path(value).name)
        allowed_dirs = []
        for directory in self.__backup_dirs():
            try:
                allowed_dirs.append(directory.resolve())
            except Exception:
                pass
        for candidate in candidates:
            try:
                resolved = candidate.resolve()
                if not resolved.is_file() or resolved.suffix.lower() != ".json":
                    continue
                if any(resolved == allowed or allowed in resolved.parents for allowed in allowed_dirs):
                    return resolved
            except Exception:
                continue
        return None

    def __build_backup_file_item(self, file_path: Path) -> Dict[str, Any]:
        stat = file_path.stat()
        meta: Dict[str, Any] = {}
        try:
            import json
            loaded = json.loads(file_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                meta = loaded
        except Exception:
            meta = {}
        exported_at = str(meta.get("exported_at") or "")
        version = str(meta.get("version") or meta.get("plugin_version") or "")
        return {
            "name": file_path.name,
            "path": str(file_path.resolve()),
            "title": file_path.stem,
            "size": int(stat.st_size),
            "mtime": float(stat.st_mtime),
            "mtime_label": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "exported_at": exported_at,
            "version": version,
            "schema": str(meta.get("schema") or ""),
        }

    def __build_backup_payload(self) -> Dict[str, Any]:
        try:
            custom_fonts = self.api_fonts().get("data", {}).get("custom", [])
        except Exception:
            custom_fonts = []
        try:
            sticker_data = self.api_stickers().get("data", [])
            custom_stickers = sticker_data if isinstance(sticker_data, list) else []
        except Exception:
            custom_stickers = []

        return {
            "schema": "mcr-full-config-backup/v1",
            "plugin": "YahahaCoverStudio",
            "version": self.plugin_version,
            "exported_at": datetime.datetime.now().isoformat(),
            "config": {
                "enabled": self._enabled,
                "auto_save_config": self._auto_save_config,
                "update_now": False,
                "transfer_monitor": self._transfer_monitor,
                "monitor_source": self._monitor_source,
                "lock_latest_sort": self._lock_latest_sort,
                "cron": self._cron,
                "delay": self._delay,
                "selected_servers": self._selected_servers,
                "include_libraries": self._include_libraries,
                "all_libraries": self._all_libraries,
                "sort_by": self._sort_by,
                "covers_output": self._covers_output,
                "covers_input": self._covers_input,
                "title_config": self._title_config,
                "title_config_strict": self._title_config_strict,
                "main_title_font_preset": self._main_title_font_preset,
                "subtitle_font_preset": self._subtitle_font_preset,
                "custom_text_font_preset": self._custom_text_font_preset,
                "main_title_font_custom": self._main_title_font_custom,
                "subtitle_font_custom": self._subtitle_font_custom,
                "custom_text_font_custom": self._custom_text_font_custom,
                "main_title_font_url": self._main_title_font_url,
                "subtitle_font_url": self._subtitle_font_url,
                "custom_text_font_url": self._custom_text_font_url,
                "main_title_font_path": self._main_title_font_path,
                "subtitle_font_path": self._subtitle_font_path,
                "custom_text_font_path": self._custom_text_font_path,
                "cover_style": self._cover_style,
                "cover_style_base": self._cover_style_base,
                "cover_style_variant": self._cover_style_variant,
                "multi_1_blur": self._multi_1_blur,
                "main_title_font_size": self._main_title_font_size,
                "subtitle_font_size": self._subtitle_font_size,
                "blur_size": self._blur_size,
                "color_ratio": self._color_ratio,
                "use_primary": self._use_primary,
                "main_title_font_offset": self._main_title_font_offset,
                "title_spacing": self._title_spacing,
                "subtitle_line_spacing": self._subtitle_line_spacing,
                "title_scale": self._title_scale,
                "resolution": self._resolution,
                "custom_width": self._custom_width,
                "custom_height": self._custom_height,
                "image_count_mode": self._image_count_mode,
                "image_count": self._image_count,
                "animation_duration": self._animation_duration,
                "animation_scroll": self._animation_scroll,
                "animation_fps": self._animation_fps,
                "animation_format": self._animation_format,
                "animation_resolution": self._animation_resolution,
                "animation_reduce_colors": self._animation_reduce_colors,
                "animated_2_image_count": self._animated_2_image_count,
                "animated_2_departure_type": self._animated_2_departure_type,
                "animated_settings": self.__export_animated_settings(),
                "bg_color_mode": self._bg_color_mode,
                "custom_bg_color": self._custom_bg_color,
                "backup_enabled": self._backup_enabled,
                "backup_cron": self._backup_cron,
                "backup_path": self._backup_path,
                "save_recent_covers": self._save_recent_covers,
                "covers_history_limit_per_library": self._covers_history_limit_per_library,
                "covers_page_history_limit": self._covers_page_history_limit,
                "page_tab": self._page_tab,
                "style_naming_v2": True,
            },
            "custom_static_state": self.__build_custom_static_state_payload(),
            "cover_history": self.get_data("cover_history") or [],
            "assets": {
                "custom_fonts": custom_fonts,
                "stickers": custom_stickers,
            },
        }

    def __backup_full_config(self, backup_path: str = "") -> Path:
        import json

        self.__update_config()
        output_path = self.__resolve_backup_output_path(backup_path)
        payload = self.__build_backup_payload()
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"【YahahaCoverStudio】完整配置已备份到: {output_path}")
        return output_path

    async def api_backup_config(self, request: Request, data: Optional[Dict[str, Any]] = Body(default=None), kwargs: Optional[Any] = Body(default=None)):
        """立即备份完整配置到本地路径。"""
        try:
            raw = await self.__read_api_payload(request=request, data=data, kwargs=kwargs)
            backup_path = str(raw.get("backup_path") or raw.get("path") or self._backup_path or "").strip()
            if backup_path and backup_path != self._backup_path:
                self._backup_path = backup_path
                self.__update_config()
            output_path = self.__backup_full_config(backup_path)
            return {"code": 0, "msg": "配置已备份", "data": {"path": str(output_path)}}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】备份完整配置失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"备份完整配置失败: {e}"}

    async def api_save_config(self, request: Request, data: Optional[Dict[str, Any]] = Body(default=None), kwargs: Optional[Any] = Body(default=None)):
        """保存 Vue 设置页配置，不触发宿主设置弹窗关闭。"""
        try:
            raw = await self.__read_api_payload(request=request, data=data, kwargs=kwargs)
            if not isinstance(raw, dict) or not raw:
                return {"code": 1, "msg": "配置数据为空"}
            title_config = str(raw.get("title_config") or "")
            strict_raw = raw.get("title_config_strict", False)
            strict = bool(strict_raw) if not isinstance(strict_raw, str) else strict_raw.lower() in ("1", "true", "yes", "on")
            _, errors, _ = self.__parse_title_config(title_config, strict=strict)
            if errors:
                return {"code": 1, "msg": errors[0], "data": {"valid": False, "errors": errors}}
            raw["update_now"] = False
            raw["main_title_font_custom"] = ""
            raw["subtitle_font_custom"] = ""
            raw["custom_text_font_custom"] = ""
            if raw.get("transfer_monitor") and raw.get("lock_latest_sort"):
                raw["sort_by"] = "DateCreated"
            def as_bool(value: Any, default: bool = False) -> bool:
                if isinstance(value, str):
                    return value.lower() in ("1", "true", "yes", "on")
                if value is None:
                    return default
                return bool(value)

            self._enabled = as_bool(raw.get("enabled"), bool(self._enabled))
            self._auto_save_config = as_bool(raw.get("auto_save_config"), bool(self._auto_save_config))
            self._update_now = False
            self._transfer_monitor = as_bool(raw.get("transfer_monitor"), bool(self._transfer_monitor))
            self._monitor_source = "emby" if raw.get("monitor_source") == "emby" else "transfer"
            self._lock_latest_sort = as_bool(raw.get("lock_latest_sort"), bool(self._lock_latest_sort))
            self._cron = str(raw.get("cron") or "").strip()
            self._delay = self.__clamp_value(raw.get("delay", self._delay or 60), 0, 3600, 60, "delay[save_config]", int)
            self._selected_servers = raw.get("selected_servers") if isinstance(raw.get("selected_servers"), list) else []
            self._include_libraries = raw.get("include_libraries") if isinstance(raw.get("include_libraries"), list) else []
            self._sort_by = str(raw.get("sort_by") or self._sort_by or "Random")
            self._covers_output = str(raw.get("covers_output") or "")
            self._covers_input = str(raw.get("covers_input") or "")
            self._title_config = title_config
            self._title_config_strict = strict
            self._distinguish_same_name_libraries = as_bool(
                raw.get("distinguish_same_name_libraries"),
                bool(self._distinguish_same_name_libraries),
            )
            self._main_title_font_preset = str(raw.get("main_title_font_preset") or self._main_title_font_preset or "chaohei")
            self._subtitle_font_preset = str(raw.get("subtitle_font_preset") or self._subtitle_font_preset or "EmblemaOne")
            self._custom_text_font_preset = str(raw.get("custom_text_font_preset") or self._custom_text_font_preset or self._subtitle_font_preset or "EmblemaOne")
            self._main_title_font_custom = ""
            self._subtitle_font_custom = ""
            self._custom_text_font_custom = ""
            self._backup_enabled = as_bool(raw.get("backup_enabled"), bool(self._backup_enabled))
            self._backup_cron = str(raw.get("backup_cron") or "").strip()
            self._backup_path = str(raw.get("backup_path") or "").strip()
            self._save_recent_covers = as_bool(raw.get("save_recent_covers"), True)
            self._covers_history_limit_per_library = self.__clamp_value(
                raw.get("covers_history_limit_per_library", self._covers_history_limit_per_library or 10),
                1,
                100,
                10,
                "covers_history_limit_per_library[save_config]",
                int,
            )
            self._covers_page_history_limit = self.__clamp_value(
                raw.get("covers_page_history_limit", self._covers_page_history_limit or 50),
                1,
                500,
                50,
                "covers_page_history_limit[save_config]",
                int,
            )
            self._history_retention_batches = self.__clamp_value(raw.get("history_retention_batches", self._history_retention_batches), 1, 1000, 30, "history_retention_batches[save]", int)
            self.__update_config()
            logger.info("【YahahaCoverStudio】Vue 设置页配置已保存")
            return {"code": 0, "msg": "配置已保存", "data": {"config": raw}}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】保存 Vue 设置页配置失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"保存配置失败: {e}"}

    async def api_validate_title_config(self, request: Request, data: Optional[Dict[str, Any]] = Body(default=None), kwargs: Optional[Any] = Body(default=None)):
        """验证标题 YAML 配置，供前端保存前拦截。"""
        try:
            raw = await self.__read_api_payload(request=request, data=data, kwargs=kwargs)
            yaml_text = str(raw.get("title_config") or raw.get("yaml") or raw.get("content") or "")
            strict_raw = raw.get("strict")
            if strict_raw is None:
                strict_raw = raw.get("title_config_strict")
            strict = bool(strict_raw) if not isinstance(strict_raw, str) else strict_raw.lower() in ("1", "true", "yes", "on")
            parsed, errors, processed_yaml = self.__parse_title_config(yaml_text, strict=strict)
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
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】验证标题配置失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"验证标题配置失败: {e}", "data": {"valid": False, "errors": [str(e)]}}

    async def api_title_config_template(self, request: Request, data: Optional[Dict[str, Any]] = Body(default=None), kwargs: Optional[Any] = Body(default=None)):
        """根据当前媒体库列表生成缺失的标题配置 YAML 模板。"""
        try:
            raw = await self.__read_api_payload(request=request, data=data, kwargs=kwargs)
            yaml_text = str(raw.get("title_config") or raw.get("yaml") or raw.get("content") or "")
            strict_raw = raw.get("strict")
            if strict_raw is None:
                strict_raw = raw.get("title_config_strict")
            strict = bool(strict_raw) if not isinstance(strict_raw, str) else strict_raw.lower() in ("1", "true", "yes", "on")
            distinguish_raw = raw.get("distinguish_same_name_libraries", self._distinguish_same_name_libraries)
            distinguish_same_name = bool(distinguish_raw) if not isinstance(distinguish_raw, str) else distinguish_raw.lower() in ("1", "true", "yes", "on")
            parsed, errors, processed_yaml = self.__parse_title_config(yaml_text, strict=strict)
            if errors:
                return {
                    "code": 1,
                    "msg": errors[0],
                    "data": {
                        "valid": False,
                        "errors": errors,
                        "processed_yaml": processed_yaml,
                    },
                }

            def normalize_template_key(value: Any) -> str:
                key = str(value or "").replace("：", ":").strip().strip("\"'")
                if ":" in key:
                    key = key.split(":", 1)[-1].strip()
                key = re.sub(r"\s+", "", key).lower()
                return key

            def collect_raw_top_level_keys(text: str) -> set:
                keys = set()
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

            _, libraries = self.__refresh_media_server_context(force=True)
            library_names: List[Tuple[str, str]] = []
            seen_libraries = set()
            for item in libraries or []:
                raw_name = str(item.get("name") or item.get("title") or item.get("label") or "").strip()
                server_name = ""
                if ":" in raw_name:
                    server_name, raw_name = (part.strip() for part in raw_name.split(":", 1))
                if not raw_name:
                    raw_name = str(item.get("library") or item.get("value") or "").strip()
                if not raw_name:
                    continue
                template_name = f"{server_name}_{raw_name}" if distinguish_same_name and server_name else raw_name
                key = normalize_template_key(template_name)
                if key in seen_libraries:
                    continue
                seen_libraries.add(key)
                library_names.append((template_name, raw_name))

            existing_keys = {normalize_template_key(key) for key in (parsed or {}).keys() if normalize_template_key(key)}
            existing_keys.update(collect_raw_top_level_keys(yaml_text))
            missing = [item for item in library_names if normalize_template_key(item[0]) not in existing_keys]

            def quote_yaml_value(value: str) -> str:
                return json.dumps(str(value or ""), ensure_ascii=False)

            blocks = [
                "\n".join([
                    f"{template_name}:",
                    f"  title: {quote_yaml_value(library_name)}",
                    "  subtitle: \"\"",
                    "  background: \"\"",
                    "  texts:",
                    "    slogan: \"\"",
                    "    note: \"\"",
                ])
                for template_name, library_name in missing
            ]
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
            return {
                "code": 0,
                "msg": "已生成媒体库标题模板",
                "data": {
                    "valid": True,
                    "libraries": [name for name, _library_name in library_names],
                    "existing": sorted(existing_keys),
                    "missing": [name for name, _library_name in missing],
                    "yaml": "\n\n".join(blocks),
                    "reference": reference,
                    "processed_yaml": processed_yaml,
                },
            }
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】生成标题配置模板失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"生成标题配置模板失败: {e}", "data": {"valid": False, "errors": [str(e)]}}

    def api_backups(self):
        """返回可用备份文件列表。"""
        try:
            items: List[Dict[str, Any]] = []
            seen = set()
            for directory in self.__backup_dirs():
                directory.mkdir(parents=True, exist_ok=True)
                for file_path in sorted(directory.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True):
                    resolved = str(file_path.resolve())
                    if resolved in seen:
                        continue
                    seen.add(resolved)
                    items.append(self.__build_backup_file_item(file_path))
            return {"code": 0, "data": items}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】获取备份列表失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"获取备份列表失败: {e}"}

    def api_download_backup(self, file: str = "", data: Optional[Dict[str, Any]] = Body(default=None), kwargs: Optional[Any] = Body(default=None)):
        """下载一个备份文件。"""
        try:
            raw = self.__extract_request_payload(data=data, kwargs=kwargs)
            target_file = self.__resolve_backup_file(file or raw.get("file") or raw.get("path") or raw.get("name") or "")
            if not target_file:
                return {"code": 1, "msg": "备份文件不存在或路径无效"}
            content = target_file.read_bytes()
            return {
                "code": 0,
                "data": {
                    "name": target_file.name,
                    "mime": "application/json",
                    "b64": base64.b64encode(content).decode("ascii"),
                },
            }
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】下载备份失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"下载备份失败: {e}"}

    async def api_upload_backup(
        self,
        request: Request,
        data: Optional[Dict[str, Any]] = Body(default=None),
        kwargs: Optional[Any] = Body(default=None),
    ):
        """上传一个备份 JSON 文件到备份目录。"""
        try:
            body_payload: Any = None
            try:
                body_payload = await request.json()
            except Exception:
                body_payload = None
            raw = self.__extract_request_payload(data=body_payload, kwargs={"data": data, "kwargs": kwargs})
            if not raw:
                raw = self.__extract_request_payload(data=data, kwargs=kwargs)

            data_url = str(raw.get("data_url") or raw.get("dataUrl") or "").strip()
            name = str(raw.get("name") or "backup.json").strip() or "backup.json"
            if not data_url.startswith("data:") or "," not in data_url:
                return {"code": 1, "msg": "备份文件数据无效"}
            _, encoded = data_url.split(",", 1)
            content = base64.b64decode(encoded)
            import json
            payload = json.loads(content.decode("utf-8"))
            if not isinstance(payload, dict) or not isinstance(payload.get("config"), dict):
                return {"code": 1, "msg": "备份文件格式无效"}

            safe_name = re.sub(r"[^a-zA-Z0-9_.-]+", "_", name).strip("._") or "backup.json"
            if Path(safe_name).suffix.lower() != ".json":
                safe_name = f"{Path(safe_name).stem or 'backup'}.json"
            backup_dir = self.__backup_dirs()[0]
            backup_dir.mkdir(parents=True, exist_ok=True)
            target_file = backup_dir / safe_name
            if target_file.exists():
                target_file = backup_dir / f"{Path(safe_name).stem}_{uuid.uuid4().hex[:8]}.json"
            target_file.write_bytes(content)
            return {"code": 0, "msg": "备份文件已上传", "data": self.__build_backup_file_item(target_file)}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】上传备份失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"上传备份失败: {e}"}

    def __restore_backup_payload(self, payload: Dict[str, Any]):
        config_payload = payload.get("config")
        if not isinstance(config_payload, dict):
            raise ValueError("备份文件缺少 config")

        restorable_keys = [
            "enabled",
            "auto_save_config",
            "transfer_monitor",
            "monitor_source",
            "cron",
            "delay",
            "selected_servers",
            "include_libraries",
            "all_libraries",
            "sort_by",
            "covers_output",
            "covers_input",
            "title_config",
            "title_config_strict",
            "main_title_font_preset",
            "subtitle_font_preset",
            "custom_text_font_preset",
            "main_title_font_custom",
            "subtitle_font_custom",
            "custom_text_font_custom",
            "main_title_font_url",
            "subtitle_font_url",
            "custom_text_font_url",
            "main_title_font_path",
            "subtitle_font_path",
            "custom_text_font_path",
            "cover_style",
            "cover_style_base",
            "cover_style_variant",
            "multi_1_blur",
            "main_title_font_size",
            "subtitle_font_size",
            "blur_size",
            "color_ratio",
            "use_primary",
            "main_title_font_offset",
            "title_spacing",
            "subtitle_line_spacing",
            "title_scale",
            "resolution",
            "custom_width",
            "custom_height",
            "image_count_mode",
            "image_count",
            "animation_duration",
            "animation_scroll",
            "animation_fps",
            "animation_format",
            "animation_resolution",
            "animation_reduce_colors",
            "animated_2_image_count",
            "animated_2_departure_type",
            "animated_settings",
            "bg_color_mode",
            "custom_bg_color",
            "backup_enabled",
            "backup_cron",
            "backup_path",
            "save_recent_covers",
            "covers_history_limit_per_library",
            "covers_page_history_limit",
            "page_tab",
        ]
        for key in restorable_keys:
            if key in config_payload:
                setattr(self, f"_{key}", config_payload.get(key))

        if self._monitor_source not in ["transfer", "emby"]:
            self._monitor_source = "transfer"
        if self._cover_style_variant not in ["static", "animated"]:
            self._cover_style_variant = "static"
        self._animated_settings = self.__normalize_animated_settings_map(self._animated_settings)

        custom_static_state = payload.get("custom_static_state")
        if isinstance(custom_static_state, dict):
            self._custom_static_layout = custom_static_state.get("custom_static_layout")
            self._custom_static_layouts = custom_static_state.get("custom_static_layouts") or []
            self._custom_static_active_id = custom_static_state.get("custom_static_active_id") or None
            self.__save_custom_static_state()

        cover_history = payload.get("cover_history")
        if isinstance(cover_history, list):
            self.save_data("cover_history", cover_history)

        self._update_now = False
        self.__update_config()
        self.__refresh_media_server_context(force=True)
        if self._enabled:
            self.__ensure_fonts_ready(force_refresh=True)

    def api_restore_backup(self, file: str = "", data: Optional[Dict[str, Any]] = Body(default=None), kwargs: Optional[Any] = Body(default=None)):
        """从备份文件恢复完整配置。"""
        try:
            raw = self.__extract_request_payload(data=data, kwargs=kwargs)
            target_file = self.__resolve_backup_file(file or raw.get("file") or raw.get("path") or raw.get("name") or "")
            if not target_file:
                return {"code": 1, "msg": "备份文件不存在或路径无效"}
            import json
            payload = json.loads(target_file.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                return {"code": 1, "msg": "备份文件格式无效"}
            self.__restore_backup_payload(payload)
            return {"code": 0, "msg": "配置已恢复", "data": {"config": payload.get("config", {})}}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】恢复备份失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"恢复备份失败: {e}"}

    def api_delete_backup(self, file: str = "", data: Optional[Dict[str, Any]] = Body(default=None), kwargs: Optional[Any] = Body(default=None)):
        """删除一个备份文件。"""
        try:
            raw = self.__extract_request_payload(data=data, kwargs=kwargs)
            target_file = self.__resolve_backup_file(file or raw.get("file") or raw.get("path") or raw.get("name") or "")
            if not target_file:
                return {"code": 1, "msg": "备份文件不存在或路径无效"}
            target_file.unlink(missing_ok=True)
            return {"code": 0, "msg": "备份文件已删除"}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】删除备份失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"删除备份失败: {e}"}

    def api_stickers(self):
        """返回已上传贴图库。"""
        try:
            sticker_dir = self.__custom_static_sticker_dir()
            sticker_dir.mkdir(parents=True, exist_ok=True)
            allowed_exts = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}
            items = [
                self.__build_sticker_library_item(file_path)
                for file_path in sorted(
                    sticker_dir.iterdir(),
                    key=lambda path: path.stat().st_mtime if path.exists() else 0,
                    reverse=True,
                )
                if file_path.is_file() and file_path.suffix.lower() in allowed_exts
            ]
            return {"code": 0, "data": items}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】获取贴图库失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"获取贴图库失败: {e}"}

    def api_delete_sticker(self, file: str = "", name: str = "", data: Optional[Dict[str, Any]] = Body(default=None), kwargs: Optional[Any] = Body(default=None)):
        """删除一个已上传贴图。"""
        try:
            raw = self.__extract_request_payload(data=data, kwargs=kwargs)
            raw_file = file or raw.get("file") or raw.get("path") or ""
            raw_name = name or raw.get("name") or ""
            target_file = self.__resolve_custom_static_sticker_path(raw_file, raw_name)
            if not target_file:
                return {"code": 1, "msg": "贴图不存在或路径无效"}
            target_file.unlink(missing_ok=True)
            return {"code": 0, "msg": "贴图已删除"}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】删除贴图失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"删除贴图失败: {e}"}

    async def api_upload_sticker(
        self,
        request: Request,
        data: Optional[Dict[str, Any]] = Body(default=None),
        kwargs: Optional[Any] = Body(default=None),
    ):
        """保存画布贴图到插件数据目录，并返回前端可直接预览的数据。"""
        try:
            body_payload: Any = None
            try:
                body_payload = await request.json()
            except Exception:
                body_payload = None
            raw = self.__extract_request_payload(data=body_payload, kwargs={"data": data, "kwargs": kwargs})
            if not raw:
                raw = self.__extract_request_payload(data=data, kwargs=kwargs)

            data_url = str(raw.get("data_url") or raw.get("dataUrl") or raw.get("stickerDataUrl") or "").strip()
            name = str(raw.get("name") or raw.get("stickerName") or "sticker").strip() or "sticker"
            width = raw.get("width") or raw.get("stickerWidth") or 0
            height = raw.get("height") or raw.get("stickerHeight") or 0
            if not data_url.startswith("data:image/"):
                return {"code": 1, "msg": "贴图数据无效"}

            layer = self.__save_custom_static_sticker(
                {
                    "type": "image",
                    "assetKind": "sticker",
                    "stickerDataUrl": data_url,
                    "stickerName": name,
                    "stickerWidth": width,
                    "stickerHeight": height,
                }
            )
            sticker_path = str(layer.get("stickerPath") or "").strip()
            if not sticker_path:
                return {"code": 1, "msg": "贴图保存失败"}
            layer["stickerDataUrl"] = self.__sticker_data_url_from_file(sticker_path)
            layer["stickerUrl"] = self.__get_preview_file_url(sticker_path)
            return {
                "code": 0,
                "msg": "贴图已保存",
                "data": {
                    "stickerPath": sticker_path,
                    "stickerUrl": layer.get("stickerUrl") or "",
                    "stickerDataUrl": layer.get("stickerDataUrl") or "",
                    "stickerName": name,
                    "stickerWidth": width,
                    "stickerHeight": height,
                },
            }
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】上传贴图失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"上传贴图失败: {e}"}

    def __get_static_preset_layout_config(self, style: str) -> Optional[Dict[str, Any]]:
        """Return the saved editable layout for a built-in static preset."""
        if style not in {"static_1", "static_2", "static_3", "static_4"}:
            return None
        preset_id = f"__preset_{style}"
        for template in self._custom_static_layouts or []:
            if not isinstance(template, dict):
                continue
            template_style = str(template.get("baseStyle") or "")
            template_id = str(template.get("id") or "")
            if template_style != style and template_id != preset_id:
                continue
            layout = template.get("layout")
            if isinstance(layout, dict) and layout.get("layers"):
                return self.__normalize_custom_static_template(layout)
        return None

    async def api_set_custom_static_layout(
        self,
        request: Request,
        data: Optional[Dict[str, Any]] = Body(default=None),
        layout: Optional[Dict[str, Any]] = Body(default=None),
        templates: Optional[List[Dict[str, Any]]] = Body(default=None),
        active_id: Optional[str] = Body(default=None),
        kwargs: Optional[Any] = Body(default=None),
        layout_json: Optional[str] = Body(default=None),
        templates_json: Optional[str] = Body(default=None),
    ):
        """保存自定义静态布局配置

        兼容多种入参方式：
        - kwargs / data 为整个请求 JSON，里面包含 layout/templates/active_id
        - 或直接传 layout / templates / active_id
        - layout / templates 也可能是 JSON 字符串
        """
        try:
            import json

            body_payload: Any = None
            body_text = ""
            try:
                body_payload = await request.json()
            except Exception:
                try:
                    body_bytes = await request.body()
                    body_text = body_bytes.decode("utf-8", errors="ignore") if body_bytes else ""
                    if body_text:
                        body_payload = json.loads(body_text)
                except Exception:
                    body_payload = None

            raw = self.__extract_request_payload(data=body_payload, kwargs={"data": data, "kwargs": kwargs})
            if not raw:
                raw = self.__extract_request_payload(data=data, kwargs=kwargs)
            if not active_id:
                active_id = raw.get("active_id") or raw.get("custom_static_active_id")
            if layout_json is None:
                layout_json = raw.get("layout_json")
            if templates_json is None:
                templates_json = raw.get("templates_json")
            if layout is None:
                layout = raw.get("layout") or raw.get("custom_static_layout")
            if templates is None:
                templates = raw.get("templates") or raw.get("custom_static_layouts")

            if isinstance(layout_json, str) and layout_json:
                try:
                    layout = json.loads(layout_json)
                except Exception:
                    pass

            if isinstance(templates_json, str) and templates_json:
                try:
                    templates = json.loads(templates_json)
                except Exception:
                    pass

            if isinstance(layout, str) and layout:
                try:
                    layout = json.loads(layout)
                except Exception:
                    pass

            if isinstance(templates, str) and templates:
                try:
                    templates = json.loads(templates)
                except Exception:
                    pass

            if not isinstance(layout, dict) and not isinstance(templates, list):
                logger.warning(
                    "【YahahaCoverStudio】保存自定义静态布局收到无效 POST 数据: body_type=%s, body_keys=%s, data_type=%s, raw_keys=%s",
                    type(body_payload).__name__,
                    list(body_payload.keys()) if isinstance(body_payload, dict) else [],
                    type(data).__name__,
                    list(raw.keys()) if isinstance(raw, dict) else [],
                )
                return {"code": 1, "msg": "保存失败: 后端未从 POST body 解析到 layout/templates"}

            layout_provided = isinstance(layout, dict)
            if layout_provided:
                self._custom_static_layout = self.__normalize_custom_static_template(layout)
            if isinstance(templates, list):
                normalized_templates = []
                for template in templates:
                    if not isinstance(template, dict):
                        continue
                    next_template = dict(template)
                    if isinstance(next_template.get("layout"), dict):
                        next_template["layout"] = self.__normalize_custom_static_template(next_template.get("layout"))
                    normalized_templates.append(next_template)
                self._custom_static_layouts = normalized_templates
            if active_id is not None:
                self._custom_static_active_id = active_id or None

            if self._custom_static_active_id and not layout_provided:
                active_tpl = next(
                    (
                        tpl
                        for tpl in (self._custom_static_layouts or [])
                        if str(tpl.get("id", "")) == str(self._custom_static_active_id)
                    ),
                    None,
                )
                if isinstance(active_tpl, dict) and isinstance(active_tpl.get("layout"), dict):
                    self._custom_static_layout = active_tpl.get("layout")
            self.__sync_active_custom_static_template()

            self.__save_custom_static_state()
            persisted_payload = self.__decode_json_value(self.get_data(self.__custom_static_state_key()), None)
            persisted_layout_count = self.__count_custom_static_layers(
                persisted_payload.get("custom_static_layout") if isinstance(persisted_payload, dict) else None
            )
            self.__update_config()
            logger.info(
                "【YahahaCoverStudio】已保存自定义静态布局配置[v7]，active_id=%s, templates=%s, layers=%s, persisted_layers=%s, body_keys=%s",
                self._custom_static_active_id,
                len(self._custom_static_layouts or []),
                self.__count_custom_static_layers(self._custom_static_layout),
                persisted_layout_count,
                list(body_payload.keys()) if isinstance(body_payload, dict) else [],
            )
            return {
                "code": 0,
                "msg": "自定义静态布局已保存",
                "data": {
                    **self.__custom_static_preview_payload(),
                    "persisted": {
                        "storage_key": self.__custom_static_state_key(),
                        "active_id": persisted_payload.get("custom_static_active_id") if isinstance(persisted_payload, dict) else None,
                        "layout_layers": persisted_layout_count,
                        "templates": len(persisted_payload.get("custom_static_layouts") or []) if isinstance(persisted_payload, dict) else 0,
                    },
                },
            }
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】保存自定义静态布局失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"保存失败: {e}"}

    def api_measure_custom_static_layout(
        self,
        data: Optional[dict] = None,
        layout: Optional[dict] = None,
        kwargs: Optional[Any] = None,
    ):
        """以后端 Pillow 规则测量自定义模板中的文本排版结果"""
        try:
            raw = self.__extract_request_payload(data=data, kwargs=kwargs)
            if layout is None:
                layout = raw.get("layout")
            if isinstance(layout, str) and layout:
                import json
                layout = json.loads(layout)
            normalized_layout = self.__normalize_custom_static_template(layout or self._custom_static_layout or {})
            preview_targets = self.__get_preview_targets()
            if not preview_targets:
                return {"code": 1, "msg": "未找到可用于测量的媒体库"}
            preview_target = preview_targets[0]
            measured_layout = self.__build_custom_static_text_layout(normalized_layout, preview_target["title"])
            return {"code": 0, "msg": "ok", "data": measured_layout}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】测量自定义模板文本排版失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"测量失败: {e}"}

    def api_delete_custom_static_template(self, id: str = ""):
        """删除一个自定义静态布局方案"""
        try:
            template_id = (id or "").strip()
            if not template_id:
                return {"code": 1, "msg": "缺少方案ID"}

            templates = self._custom_static_layouts or []
            next_templates = [tpl for tpl in templates if str(tpl.get("id", "")) != template_id]

            if len(next_templates) == len(templates):
                return {"code": 1, "msg": "未找到要删除的方案"}

            self._custom_static_layouts = next_templates

            if not next_templates:
                self._custom_static_active_id = None
                self._custom_static_layout = None
            else:
                current_active_id = self._custom_static_active_id
                active_tpl = next(
                    (tpl for tpl in next_templates if str(tpl.get("id", "")) == str(current_active_id or "")),
                    None,
                )
                if active_tpl is None:
                    active_tpl = next_templates[0]
                    self._custom_static_active_id = active_tpl.get("id")
                self._custom_static_layout = active_tpl.get("layout") if isinstance(active_tpl.get("layout"), dict) else None

            self.__save_custom_static_state()
            self.__update_config()
            logger.info("【YahahaCoverStudio】已删除自定义静态布局方案: %s", template_id)
            return {
                "code": 0,
                "msg": "自定义方案已删除",
                "data": self.__custom_static_preview_payload(),
            }
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】删除自定义静态布局方案失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"删除失败: {e}"}

    def __font_search_dirs(self) -> List[Path]:
        dirs: List[Path] = []
        if self._font_path:
            dirs.append(Path(self._font_path))
        plugin_font_dir = Path(__file__).resolve().parent / "fonts"
        dirs.append(plugin_font_dir)
        repo_font_dir = Path(__file__).resolve().parents[2] / "fonts"
        dirs.append(repo_font_dir)
        dirs.extend([
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            Path("/usr/share/fonts/truetype"),
            Path("/usr/share/fonts/opentype"),
        ])
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

    def __builtin_font_urls(self) -> Dict[str, str]:
        return {
            "chaohei": "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/chaohei.ttf",
            "yasong": "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/yasong.ttf",
            "EmblemaOne": "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/EmblemaOne.woff2",
            "Melete": "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/Melete.otf",
            "Phosphate": "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/phosphate.ttf",
            "JosefinSans": "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/josefinsans.woff2",
            "LilitaOne": "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/lilitaone.woff2",
        }

    def __find_font_file(self, aliases: List[str], exts: List[str]) -> Optional[str]:
        normalized_aliases = [item.lower() for item in aliases if item]
        normalized_aliases_compact = [re.sub(r'[\s_\-]+', '', item) for item in normalized_aliases]
        normalized_exts = [item.lower() for item in exts]
        for directory in self.__font_search_dirs():
            try:
                candidates = sorted(
                    (path for path in directory.rglob("*") if path.is_file()),
                    key=lambda p: str(p).lower(),
                )
            except Exception:
                continue
            for font_file in candidates:
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

    def __find_system_font_fallback(self, lang: str) -> Optional[str]:
        font_exts = [".ttf", ".ttc", ".otf", ".woff2", ".woff"]
        preferred_candidates = {
            "主标题": [
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
                "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
                "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
                "/usr/share/fonts/opentype/unifont/unifont.otf",
                "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
            ],
            "副标题": [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            ],
            "自定义文本": [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            ],
        }
        fallback_aliases = {
            "主标题": [
                "wqyzenhei",
                "wenquanyizenhei",
                "notosanscjksc",
                "notoserifcjksc",
                "sourcehansanssc",
                "sourcehanserifsc",
                "sarasagothicsc",
                "sarasa",
                "unifont",
                "ipag",
            ],
            "副标题": [
                "dejavusans",
                "liberationsans",
                "freesans",
                "nimbussans",
                "arial",
                "notosans",
                "dejavuserif",
                "liberationserif",
            ],
            "自定义文本": [
                "dejavusans",
                "liberationsans",
                "notosans",
                "wqyzenhei",
                "notosanscjk",
            ],
        }
        for candidate in preferred_candidates.get(lang, []):
            candidate_path = Path(candidate)
            if validate_font_file(candidate_path):
                logger.info(f"{lang}字体: 优先使用系统候选字体 {candidate_path}")
                return str(candidate_path)
        aliases = fallback_aliases.get(lang, [])
        found = self.__find_font_file(aliases, font_exts)
        if found and validate_font_file(Path(found)):
            logger.info(f"{lang}字体: 使用系统回退字体 {found}")
            return found
        return None

    def __get_font_presets(self) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, Optional[str]], Dict[str, Optional[str]]]:
        zh_specs = [
            {"title": "潮黑", "value": "chaohei", "aliases": ["chaohei", "wendao", "潮黑", "chao_hei"]},
            {"title": "粗雅宋", "value": "yasong", "aliases": ["yasong", "粗雅宋", "multi_1_zh", "ya_song"]},
            {"title": "系统文泉驿正黑", "value": "WenQuanYiZenHei", "aliases": ["wqyzenhei", "wenquanyizenhei", "文泉驿正黑", "文泉驛正黑"]},
            {"title": "系统思源黑体", "value": "NotoSansCJKSC", "aliases": ["notosanscjksc", "notosanscjk", "思源黑体", "noto sans cjk sc"]},
        ]
        en_specs = [
            {"title": "EmblemaOne", "value": "EmblemaOne", "aliases": ["emblemaone", "emblema_one"]},
            {"title": "Melete", "value": "Melete", "aliases": ["melete", "multi_1_en"]},
            {"title": "Phosphate", "value": "Phosphate", "aliases": ["phosphate", "phosphat"]},
            {"title": "JosefinSans", "value": "JosefinSans", "aliases": ["josefinsans", "josefin_sans"]},
            {"title": "LilitaOne", "value": "LilitaOne", "aliases": ["lilitaone", "lilita_one"]},
            {"title": "系统 DejaVu Sans", "value": "DejaVuSans", "aliases": ["dejavusans", "dejavu sans"]},
            {"title": "系统 Liberation Sans", "value": "LiberationSans", "aliases": ["liberationsans", "liberation sans"]},
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
        main_title_font_paths: Dict[str, Optional[str]] = {}
        subtitle_font_paths: Dict[str, Optional[str]] = {}
        main_title_font_items: List[Dict[str, str]] = []
        subtitle_font_items: List[Dict[str, str]] = []
        main_title_font_exts = [".ttf", ".otf", ".woff2", ".woff"]
        subtitle_font_exts = [".ttf", ".otf", ".woff2", ".woff"]

        for spec in all_specs:
            found = self.__find_font_file(spec["aliases"], main_title_font_exts)
            main_title_font_paths[spec["value"]] = found
            main_title_font_items.append({"title": spec["title"], "value": spec["value"]})
        for spec in all_specs:
            found = self.__find_font_file(spec["aliases"], subtitle_font_exts)
            subtitle_font_paths[spec["value"]] = found
            subtitle_font_items.append({"title": spec["title"], "value": spec["value"]})
        return main_title_font_items, subtitle_font_items, main_title_font_paths, subtitle_font_paths

    def __ensure_fonts_ready(self, force_refresh: bool = False) -> bool:
        try:
            main_title_font_path = Path(self._main_title_font_path) if self._main_title_font_path else None
            subtitle_font_path = Path(self._subtitle_font_path) if self._subtitle_font_path else None
            custom_text_font_path = Path(self._custom_text_font_path) if self._custom_text_font_path else None
            main_title_font_valid = bool(main_title_font_path and validate_font_file(main_title_font_path))
            subtitle_font_valid = bool(subtitle_font_path and validate_font_file(subtitle_font_path))
            custom_text_font_valid = bool(custom_text_font_path and validate_font_file(custom_text_font_path))

            if force_refresh or not main_title_font_valid or not subtitle_font_valid or not custom_text_font_valid:
                if not main_title_font_valid and self._main_title_font_path:
                    logger.warning(f"主标题字体路径失效，准备自动恢复: {self._main_title_font_path}")
                if not subtitle_font_valid and self._subtitle_font_path:
                    logger.warning(f"副标题字体路径失效，准备自动恢复: {self._subtitle_font_path}")
                if not custom_text_font_valid and self._custom_text_font_path:
                    logger.warning(f"自定义文本字体路径失效，准备自动恢复: {self._custom_text_font_path}")

                if not main_title_font_valid:
                    self._main_title_font_path = ""
                if not subtitle_font_valid:
                    self._subtitle_font_path = ""
                if not custom_text_font_valid:
                    self._custom_text_font_path = ""

                self.__get_fonts()

                main_title_font_path = Path(self._main_title_font_path) if self._main_title_font_path else None
                subtitle_font_path = Path(self._subtitle_font_path) if self._subtitle_font_path else None
                custom_text_font_path = Path(self._custom_text_font_path) if self._custom_text_font_path else None
                main_title_font_valid = bool(main_title_font_path and validate_font_file(main_title_font_path))
                subtitle_font_valid = bool(subtitle_font_path and validate_font_file(subtitle_font_path))
                custom_text_font_valid = bool(custom_text_font_path and validate_font_file(custom_text_font_path))

                if not main_title_font_valid:
                    fallback_main_title_font = self.__find_system_font_fallback("主标题")
                    if fallback_main_title_font:
                        self._main_title_font_path = fallback_main_title_font
                        main_title_font_valid = validate_font_file(Path(fallback_main_title_font))
                if not subtitle_font_valid:
                    fallback_subtitle_font = self.__find_system_font_fallback("副标题")
                    if fallback_subtitle_font:
                        self._subtitle_font_path = fallback_subtitle_font
                        subtitle_font_valid = validate_font_file(Path(fallback_subtitle_font))
                if not custom_text_font_valid:
                    fallback_custom_text_font = self.__find_system_font_fallback("自定义文本") or self._subtitle_font_path
                    if fallback_custom_text_font:
                        self._custom_text_font_path = fallback_custom_text_font
                        custom_text_font_valid = validate_font_file(Path(fallback_custom_text_font))

            if not main_title_font_valid or not subtitle_font_valid or not custom_text_font_valid:
                logger.error(
                    "字体自动恢复失败: zh=%s(valid=%s), en=%s(valid=%s), custom=%s(valid=%s)",
                    self._main_title_font_path,
                    main_title_font_valid,
                    self._subtitle_font_path,
                    subtitle_font_valid,
                    self._custom_text_font_path,
                    custom_text_font_valid,
                )
                return False

            return True
        except Exception as e:
            logger.error(f"字体自恢复检查失败: {e}", exc_info=True)
            return False

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
            if entry.resolve() == self.__custom_font_library_dir().resolve():
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
        self._main_title_font_path = ""
        self._subtitle_font_path = ""
        self._custom_text_font_path = ""
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
                "path": "/set_custom_static_layout",
                "endpoint": self.api_set_custom_static_layout,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "保存自定义静态布局配置",
            },
            {
                "path": "set_custom_static_layout",
                "endpoint": self.api_set_custom_static_layout,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "保存自定义静态布局配置(兼容无前导斜杠)",
            },
            {
                "path": "/upload_sticker",
                "endpoint": self.api_upload_sticker,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "上传画布贴图",
            },
            {
                "path": "upload_sticker",
                "endpoint": self.api_upload_sticker,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "上传画布贴图(兼容无前导斜杠)",
            },
            {
                "path": "/stickers",
                "endpoint": self.api_stickers,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "获取画布贴图库",
            },
            {
                "path": "stickers",
                "endpoint": self.api_stickers,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "获取画布贴图库(兼容无前导斜杠)",
            },
            {
                "path": "/fonts",
                "endpoint": self.api_fonts,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "获取自定义字体库",
            },
            {
                "path": "fonts",
                "endpoint": self.api_fonts,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "获取自定义字体库(兼容无前导斜杠)",
            },
            {
                "path": "/upload_font",
                "endpoint": self.api_upload_font,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "上传自定义字体",
            },
            {
                "path": "upload_font",
                "endpoint": self.api_upload_font,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "上传自定义字体(兼容无前导斜杠)",
            },
            {
                "path": "/delete_font",
                "endpoint": self.api_delete_font,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "删除自定义字体",
            },
            {
                "path": "delete_font",
                "endpoint": self.api_delete_font,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "删除自定义字体(兼容无前导斜杠)",
            },
            {
                "path": "/rename_font",
                "endpoint": self.api_rename_font,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "重命名自定义字体",
            },
            {
                "path": "rename_font",
                "endpoint": self.api_rename_font,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "重命名自定义字体(兼容无前导斜杠)",
            },
            {
                "path": "/backup_config",
                "endpoint": self.api_backup_config,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "备份完整配置",
            },
            {
                "path": "backup_config",
                "endpoint": self.api_backup_config,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "备份完整配置(兼容无前导斜杠)",
            },
            {
                "path": "/save_config",
                "endpoint": self.api_save_config,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "保存 Vue 设置页配置",
            },
            {
                "path": "save_config",
                "endpoint": self.api_save_config,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "保存 Vue 设置页配置(兼容无前导斜杠)",
            },
            {
                "path": "/validate_title_config",
                "endpoint": self.api_validate_title_config,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "验证标题 YAML 配置",
            },
            {
                "path": "validate_title_config",
                "endpoint": self.api_validate_title_config,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "验证标题 YAML 配置(兼容无前导斜杠)",
            },
            {
                "path": "/title_config_template",
                "endpoint": self.api_title_config_template,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "根据媒体库生成标题配置模板",
            },
            {
                "path": "title_config_template",
                "endpoint": self.api_title_config_template,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "根据媒体库生成标题配置模板(兼容无前导斜杠)",
            },
            {
                "path": "/backups",
                "endpoint": self.api_backups,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "获取配置备份列表",
            },
            {
                "path": "backups",
                "endpoint": self.api_backups,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "获取配置备份列表(兼容无前导斜杠)",
            },
            {
                "path": "/download_backup",
                "endpoint": self.api_download_backup,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "下载配置备份",
            },
            {
                "path": "download_backup",
                "endpoint": self.api_download_backup,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "下载配置备份(兼容无前导斜杠)",
            },
            {
                "path": "/upload_backup",
                "endpoint": self.api_upload_backup,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "上传配置备份",
            },
            {
                "path": "upload_backup",
                "endpoint": self.api_upload_backup,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "上传配置备份(兼容无前导斜杠)",
            },
            {
                "path": "/restore_backup",
                "endpoint": self.api_restore_backup,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "恢复配置备份",
            },
            {
                "path": "restore_backup",
                "endpoint": self.api_restore_backup,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "恢复配置备份(兼容无前导斜杠)",
            },
            {
                "path": "/delete_backup",
                "endpoint": self.api_delete_backup,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "删除配置备份",
            },
            {
                "path": "delete_backup",
                "endpoint": self.api_delete_backup,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "删除配置备份(兼容无前导斜杠)",
            },
            {
                "path": "/delete_sticker",
                "endpoint": self.api_delete_sticker,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "删除画布贴图",
            },
            {
                "path": "delete_sticker",
                "endpoint": self.api_delete_sticker,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "删除画布贴图(兼容无前导斜杠)",
            },
            {
                "path": "/delete_custom_static_template",
                "endpoint": self.api_delete_custom_static_template,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "删除一个自定义静态布局方案",
            },
            {
                "path": "/measure_custom_static_layout",
                "endpoint": self.api_measure_custom_static_layout,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "按后端规则测量自定义模板中的文本排版",
            },
            {
                "path": "measure_custom_static_layout",
                "endpoint": self.api_measure_custom_static_layout,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "按后端规则测量自定义模板中的文本排版(兼容无前导斜杠)",
            },
            {
                "path": "delete_custom_static_template",
                "endpoint": self.api_delete_custom_static_template,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "删除一个自定义静态布局方案(兼容无前导斜杠)",
            },
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
                "path": "/delete_saved_covers",
                "endpoint": self.api_delete_saved_covers,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "批量删除已保存封面",
            },
            {
                "path": "delete_saved_covers",
                "endpoint": self.api_delete_saved_covers,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "批量删除已保存封面(兼容无前导斜杠)",
            },
            {
                "path": "/download_saved_cover",
                "endpoint": self.api_download_saved_cover,
                "auth": "bear",
                "methods": ["GET", "POST"],
                "summary": "下载一张已保存封面",
            },
            {
                "path": "download_saved_cover",
                "endpoint": self.api_download_saved_cover,
                "auth": "bear",
                "methods": ["GET", "POST"],
                "summary": "下载一张已保存封面(兼容无前导斜杠)",
            },
            {
                "path": "/download_saved_covers",
                "endpoint": self.api_download_saved_covers,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "批量下载已保存封面",
            },
            {
                "path": "download_saved_covers",
                "endpoint": self.api_download_saved_covers,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "批量下载已保存封面(兼容无前导斜杠)",
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
                "path": "/start_generation",
                "endpoint": self.api_start_generation,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "开始后台生成媒体库封面",
            },
            {
                "path": "start_generation",
                "endpoint": self.api_start_generation,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "开始后台生成媒体库封面(兼容无前导斜杠)",
            },
            {
                "path": "/stop_generation",
                "endpoint": self.api_stop_generation,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "停止当前媒体库封面生成任务",
            },
            {
                "path": "stop_generation",
                "endpoint": self.api_stop_generation,
                "auth": "bear",
                "methods": ["POST", "GET"],
                "summary": "停止当前媒体库封面生成任务(兼容无前导斜杠)",
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
            {
                "path": "/set_animated_settings",
                "endpoint": self.api_set_animated_settings,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "保存动态封面参数",
            },
            {
                "path": "set_animated_settings",
                "endpoint": self.api_set_animated_settings,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "保存动态封面参数(兼容无前导斜杠)",
            },
            {
                "path": "/set_render_options",
                "endpoint": self.api_set_render_options,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "保存生成页素材参数",
            },
            {
                "path": "set_render_options",
                "endpoint": self.api_set_render_options,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "保存生成页素材参数(兼容无前导斜杠)",
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
            {"path": "/set_page_tab_custom", "endpoint": self.api_set_page_tab_custom, "auth": "bear", "methods": ["POST"], "summary": "切换到自定义风格页"},
            {"path": "/set_page_tab_history", "endpoint": self.api_set_page_tab_history, "auth": "bear", "methods": ["POST"], "summary": "切换到历史页"},
            {"path": "/set_page_tab_clean", "endpoint": self.api_set_page_tab_clean, "auth": "bear", "methods": ["POST"], "summary": "切换到清理页"},
            {"path": "set_page_tab_generate", "endpoint": self.api_set_page_tab_generate, "auth": "bear", "methods": ["POST"], "summary": "切换到生成页(兼容)"},
            {"path": "set_page_tab_custom", "endpoint": self.api_set_page_tab_custom, "auth": "bear", "methods": ["POST"], "summary": "切换到自定义风格页(兼容)"},
            {"path": "set_page_tab_history", "endpoint": self.api_set_page_tab_history, "auth": "bear", "methods": ["POST"], "summary": "切换到历史页(兼容)"},
            {"path": "set_page_tab_clean", "endpoint": self.api_set_page_tab_clean, "auth": "bear", "methods": ["POST"], "summary": "切换到清理页(兼容)"},
            {"path": "/saved_cover_image", "endpoint": self.api_saved_cover_image, "methods": ["GET"], "summary": "获取已保存封面图片"},
            {"path": "saved_cover_image", "endpoint": self.api_saved_cover_image, "methods": ["GET"], "summary": "获取已保存封面图片(兼容)"},
            {
                "path": "/history",
                "endpoint": self.api_history,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "查询最近生成的封面列表",
            },
            {
                "path": "history",
                "endpoint": self.api_history,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "查询最近生成的封面列表(兼容无前导斜杠)",
            },
            {"path": "/restore_history_batch", "endpoint": self.api_restore_history_batch, "auth": "bear", "methods": ["POST"], "summary": "恢复历史批次封面"},
            {"path": "restore_history_batch", "endpoint": self.api_restore_history_batch, "auth": "bear", "methods": ["POST"], "summary": "恢复历史批次封面(兼容)"},
            {
                "path": "/status",
                "endpoint": self.api_status,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "查询封面生成状态与环境告警",
            },
            {
                "path": "status",
                "endpoint": self.api_status,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "查询封面生成状态与环境告警(兼容无前导斜杠)",
            },
            {
                "path": "/preview_sources",
                "endpoint": self.api_preview_sources,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "获取前端模拟预览素材",
            },
            {
                "path": "preview_sources",
                "endpoint": self.api_preview_sources,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "获取前端模拟预览素材(兼容无前导斜杠)",
            },
            {
                "path": "/preview",
                "endpoint": self.api_preview,
                "auth": "bear",
                "methods": ["GET", "POST"],
                "summary": "生成封面预览图",
            },
            {
                "path": "preview",
                "endpoint": self.api_preview,
                "auth": "bear",
                "methods": ["GET", "POST"],
                "summary": "生成封面预览图(兼容无前导斜杠)",
            },
        ]

    def api_history(self):
        """查询最近生成的封面列表，供前端历史封面页签使用"""
        try:
            store = HistoryStore(self.get_data_path(), self.plugin_version)
            covers = []
            for summary in store.list_batches()[:1000]:
                manifest = store.get_batch(str(summary.get("batch_id") or "")) or {}
                for item in manifest.get("items") or []:
                    path = store.file_path(str(manifest.get("batch_id") or ""), str(item.get("file") or ""))
                    if not path:
                        continue
                    thumbnail_path = store.file_path(str(manifest.get("batch_id") or ""), str(item.get("thumbnail") or "")) if item.get("thumbnail") else None
                    version = str(item.get("sha256") or int(path.stat().st_mtime_ns))
                    original_url = f"/api/v1/plugin/YahahaCoverStudio/saved_cover_image?file={quote(str(path))}&v={quote(version)}"
                    thumbnail_url = f"/api/v1/plugin/YahahaCoverStudio/saved_cover_image?file={quote(str(thumbnail_path))}&v={quote(version)}" if thumbnail_path else original_url
                    source_file = thumbnail_path or path
                    try:
                        from PIL import Image
                        with Image.open(source_file) as image:
                            image = image.convert("RGB")
                            image.thumbnail((480, 270))
                            buffer = io.BytesIO()
                            image.save(buffer, format="WEBP", quality=78, method=4)
                        image_src = "data:image/webp;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
                    except Exception as error:
                        logger.warning("【YahahaCoverStudio】历史缩略图编码失败: %s", error)
                        image_src = thumbnail_url
                    covers.append({"name": path.name, "size": item.get("size", 0), "src": image_src, "url": original_url, "thumbnail": image_src, "path": str(path), "server": item.get("server_name", ""), "library": item.get("library_name", ""), "date": str(manifest.get("created_at", ""))[:10], "date_label": str(manifest.get("created_at", ""))[5:16].replace("T", " "), "mtime": manifest.get("created_at", ""), "mtime_ts": 0, "created_at": manifest.get("created_at", ""), "batch_id": manifest.get("batch_id", "")})
            return {
                "code": 0,
                "data": [
                    {
                        "name": item.get("name", ""),
                        "size": item.get("size", ""),
                        "src": item.get("src", ""),
                        "url": item.get("url", ""),
                        "thumbnail": item.get("thumbnail", ""),
                        "path": item.get("path", ""),
                        "server": item.get("server", ""),
                        "library": item.get("library", ""),
                        "date": item.get("date", ""),
                        "date_label": item.get("date_label", ""),
                        "mtime": item.get("mtime", ""),
                        "mtime_ts": item.get("mtime_ts", 0),
                        "batch_id": item.get("batch_id", ""),
                        "created_at": item.get("created_at", ""),
                    }
                    for item in covers
                ],
            }
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】获取历史封面失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"获取历史封面失败: {e}"}

    async def api_restore_history_batch(self, request: Request, data: Optional[Dict[str, Any]] = Body(default=None), kwargs: Optional[Any] = Body(default=None)):
        try:
            raw = await self.__read_api_payload(request=request, data=data, kwargs=kwargs)
            batch_id = str(raw.get("batch_id") or "")
            store = HistoryStore(self.get_data_path(), self.plugin_version)
            manifest = store.get_batch(batch_id)
            if not manifest:
                return {"code": 1, "msg": "历史批次不存在"}
            self.__refresh_media_server_context(force=True)
            restored = skipped = failed = 0
            for item in manifest.get("items") or []:
                path = store.file_path(batch_id, str(item.get("file") or ""))
                service = next((value for value in (self._servers or {}).values() if value and value.name == item.get("server_name")), None)
                if not path or not service:
                    skipped += 1
                    continue
                expected_hash = str(item.get("sha256") or "")
                if expected_hash and hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
                    logger.warning(f"跳过校验失败的历史封面: {item.get('server_name')} / {item.get('library_name')}")
                    skipped += 1
                    continue
                library = next((value for value in self.__get_server_libraries(service) if value.get("Name") == item.get("library_name")), None)
                if not library:
                    skipped += 1
                    continue
                try:
                    restored += 1 if self.__set_library_image(service, library, base64.b64encode(path.read_bytes()).decode("ascii")) else 0
                except Exception:
                    failed += 1
            return {"code": 0, "data": {"batch_id": batch_id, "restored": restored, "skipped": skipped, "failed": failed}}
        except Exception as e:
            logger.error(f"恢复历史批次失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"恢复历史批次失败: {e}"}

    def api_status(self):
        """返回封面生成相关的状态与初始化告警(供前端 setupWarnings 使用)"""
        try:
            if self._enabled:
                self.__refresh_media_server_context(force=True)
            is_generating = self.__is_generation_running()
            warnings: List[str] = []
            if not self._enabled:
                warnings.append("插件未启用，请先在设置页启用插件并保存。")
            if not self._servers:
                warnings.append("未检测到任何可用媒体服务器，请在设置页配置媒体服务器并确保连接正常。")
            if not self.mediaserver_helper:
                self.mediaserver_helper = MediaServerHelper()
            animated_settings = self.__export_animated_settings()
            active_animated_settings = self.__get_animated_settings_for_style(self._cover_style)
            preview_custom_static = self.__custom_static_preview_payload()

            return {
                "code": 0,
                "data": {
                    "warnings": warnings,
                    "enabled": bool(self._enabled),
                    "plugin_version": self.plugin_version,
                    "auto_save_config": bool(self._auto_save_config),
                    "has_selected_servers": bool(self._selected_servers),
                    "servers_ready": bool(self._servers),
                    "is_generating": is_generating,
                    "generation_source": self._generation_source,
                    "generation_style": self._generation_style,
                    "generation_current": self._generation_current if is_generating else 0,
                    "generation_total": self._generation_total if is_generating else 0,
                    "generation_label": self._generation_label if is_generating else "",
                    "all_servers": [
                        config.name for config in self.mediaserver_helper.get_configs().values()
                        if getattr(config, "type", None) in ("emby", "jellyfin")
                    ] if self.mediaserver_helper else [],
                    "selected_servers": self._selected_servers,
                    "include_libraries": self._include_libraries,
                    "all_libraries": self._all_libraries,
                    "transfer_monitor": bool(self._transfer_monitor),
                    "monitor_source": self._monitor_source,
                    "lock_latest_sort": bool(self._lock_latest_sort),
                    "cover_style_base": self._cover_style_base,
                    "cover_style_variant": self._cover_style_variant,
                    "poster_source": "poster" if self._use_primary else "backdrop",
                    "use_primary": bool(self._use_primary),
                    "sort_by": self._sort_by or "Random",
                    "lock_latest_sort": bool(self._lock_latest_sort),
                    "image_count_mode": self._image_count_mode,
                    "image_count": self._image_count,
                    "auto_image_count": self.__get_auto_required_items(),
                    "resolution": self._resolution,
                    "animation_resolution": self._animation_resolution or "320x180",
                    "custom_width": self._custom_width,
                    "custom_height": self._custom_height,
                    "animation_duration": active_animated_settings["animation_duration"],
                    "animation_fps": active_animated_settings["animation_fps"],
                    "animation_format": active_animated_settings["animation_format"],
                    "animation_scroll": active_animated_settings["animation_scroll"],
                    "animation_reduce_colors": active_animated_settings["animation_reduce_colors"],
                    "animated_2_image_count": active_animated_settings["animated_2_image_count"],
                    "animated_2_departure_type": active_animated_settings["animated_2_departure_type"],
                    "main_title_font_preset": active_animated_settings["main_title_font_preset"],
                    "subtitle_font_preset": active_animated_settings["subtitle_font_preset"],
                    "custom_text_font_preset": active_animated_settings["custom_text_font_preset"],
                    "main_title_font_size": active_animated_settings["main_title_font_size"],
                    "subtitle_font_size": active_animated_settings["subtitle_font_size"],
                    "blur_size": active_animated_settings["blur_size"],
                    "color_ratio": active_animated_settings["color_ratio"],
                    "title_scale": active_animated_settings["title_scale"],
                    "animated_settings": animated_settings,
                    **preview_custom_static,
                },
            }
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】获取状态失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"获取状态失败: {e}"}

    def api_preview_sources(self, required_items: Optional[int] = None, force_refresh: Optional[bool] = False):
        """返回前端模拟预览所需的真实素材信息，不执行后端合成"""
        try:
            preview_targets = self.__get_preview_targets()
            if not preview_targets:
                logger.warning("【YahahaCoverStudio】预览素材获取失败：未找到可用的媒体库")
                return {"code": 1, "msg": "未找到可用的媒体库用于预览，请检查媒体库设置"}

            for preview_target in preview_targets:
                service = preview_target["service"]
                library_name = preview_target["library_name"]
                title = preview_target["title"]
                config_bg_color = preview_target["config_bg_color"]
                custom_texts = self.__get_custom_texts_from_config(library_name, service.name)
                force = str(force_refresh).strip().lower() in {"1", "true", "yes", "on"}
                if force and not preview_target.get("custom_images"):
                    cleared = self.__clear_preview_cache_for_library(library_name)
                    if cleared:
                        logger.info("【YahahaCoverStudio】已清理预览素材缓存: %s：%s", service.name, library_name)
                source_mode, images = self.__resolve_preview_source_images(
                    preview_target,
                    required_items=self.__get_preview_required_items(required_items),
                    force_refresh=force,
                )
                if force and len(images) > 1:
                    offset = int(time.time() * 1000) % len(images)
                    images = images[offset:] + images[:offset]
                if force:
                    version = int(time.time() * 1000)
                    for image in images:
                        src = str(image.get("src") or "")
                        # Local and proxied plugin previews use data URLs. Appending a
                        # query string to one corrupts the base64 payload and becomes a
                        # browser broken-image placeholder. Data URLs are uncached, so
                        # they do not need a cache-busting version in the first place.
                        if src and not src.startswith("data:"):
                            image["src"] = f"{src}{'&' if '?' in src else '?'}preview_version={version}"
                if not images:
                    logger.info(f"媒体库 {service.name}：{library_name} 无可用预览素材，继续尝试下一个媒体库")
                    continue

                logger.info(
                    f"【YahahaCoverStudio】预览素材获取成功，媒体库: {service.name}：{library_name}，来源: {source_mode}"
                )
                return {
                    "code": 0,
                    "data": {
                        "server": service.name,
                        "library": library_name,
                        "style": self._cover_style,
                        "cover_style_base": self._cover_style_base,
                        "cover_style_variant": self._cover_style_variant,
                        "source_mode": source_mode,
                        "titles": {
                            "zh": title[0] if len(title) > 0 else "",
                            "en": title[1] if len(title) > 1 else "",
                        },
                        "custom_texts": custom_texts,
                        "images": images,
                        "custom_static_layout": self.__build_custom_static_text_layout(self._custom_static_layout, title, custom_texts),
                        "bg_color": config_bg_color,
                        "font_faces": self.__build_preview_font_faces(),
                    },
                }

            return {"code": 1, "msg": "当前媒体库没有可用的预览素材"}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】预览素材获取异常: {e}", exc_info=True)
            return {"code": 1, "msg": f"预览素材获取失败: {e}"}

    def __get_preview_targets(self) -> List[Dict[str, Any]]:
        if not self._enabled:
            logger.warning("【YahahaCoverStudio】预览请求失败：插件未启用")
            raise RuntimeError("插件未启用，请先在设置页启用插件并保存")
        self.__refresh_media_server_context(force=False)
        if not self._servers:
            logger.warning("【YahahaCoverStudio】预览请求失败：未检测到任何可用媒体服务器")
            raise RuntimeError("未检测到任何可用媒体服务器，请检查设置并保存后重试")

        preview_targets: List[Dict[str, Any]] = []
        for server, service in (self._servers or {}).items():
            if not service or service.instance.is_inactive():
                continue
            libraries = self.__get_server_libraries(service)
            if not libraries:
                continue
            for library in libraries:
                if service.type == "emby":
                    library_id = library.get("Id")
                else:
                    library_id = library.get("ItemId")
                if not library_id:
                    continue

                if self._include_libraries and f"{server}-{library_id}" not in self._include_libraries:
                    continue

                library_name = library.get("Name") or ""
                title_result = self.__get_title_from_config(library_name, service.name)
                if len(title_result) == 3:
                    title = (title_result[0], title_result[1])
                    config_bg_color = title_result[2]
                else:
                    title = title_result
                    config_bg_color = None

                custom_images = self.__check_custom_image(library_name)
                cache_info = self.__check_cached_preview_images(library_name)
                preview_targets.append({
                    "server_key": f"{server}-{library_id}",
                    "server": server,
                    "service": service,
                    "library": library,
                    "library_id": library_id,
                    "library_name": library_name,
                    "title": title,
                    "config_bg_color": config_bg_color,
                    "custom_images": custom_images,
                    "cache_images": cache_info["images"] if cache_info else None,
                    "cache_root": cache_info["root"] if cache_info else None,
                })

        if self._include_libraries:
            include_order = {
                str(value): index for index, value in enumerate(self._include_libraries or [])
            }
            preview_targets.sort(
                key=lambda item: include_order.get(item.get("server_key", ""), len(include_order))
            )
        else:
            # Keep the initially selected library stable. A random target on every
            # page entry defeats the persistent preview cache and looks like an
            # unsolicited poster refresh to the user.
            preview_targets.sort(key=lambda item: (str(item.get("server") or ""), str(item.get("library_name") or "")))

        if not preview_targets and self._include_libraries:
            logger.warning(
                "【YahahaCoverStudio】预览目标为空，selected_servers=%s, include_libraries=%s, all_libraries=%s",
                self._selected_servers,
                self._include_libraries,
                [item.get("value") for item in (self._all_libraries or [])],
            )

        return preview_targets

    def __build_preview_font_faces(self) -> Dict[str, str]:
        font_faces: Dict[str, str] = {}
        semantic_paths = {
            "main_title": self._main_title_font_path,
            "subtitle": self._subtitle_font_path,
            "custom_text": self._custom_text_font_path,
        }
        semantic_urls = {
            "main_title": self._main_title_font_custom or self._main_title_font_url,
            "subtitle": self._subtitle_font_custom or self._subtitle_font_url,
            "custom_text": self._custom_text_font_custom or self._custom_text_font_url,
        }
        for key, path_value in semantic_paths.items():
            if path_value and Path(path_value).is_file():
                font_faces[key] = self.__get_preview_file_url(str(path_value))
                continue
            url_value = str(semantic_urls.get(key) or "").strip()
            if url_value and re.match(r'^https?://', url_value, re.IGNORECASE):
                font_faces[key] = url_value

        _, _, main_title_font_preset_paths, _ = self.__get_font_presets()
        builtin_urls = self.__builtin_font_urls()
        for key, url in builtin_urls.items():
            local_path = main_title_font_preset_paths.get(key)
            if local_path and Path(local_path).is_file():
                font_faces[key] = self.__get_preview_file_url(local_path)
                continue
            fallback_path = self.__ensure_builtin_font_path(key)
            if fallback_path and Path(fallback_path).is_file():
                font_faces[key] = self.__get_preview_file_url(fallback_path)
            else:
                font_faces[key] = url
        try:
            font_dir = self.__custom_font_library_dir()
            if font_dir.is_dir():
                for font_file in font_dir.iterdir():
                    if font_file.is_file() and validate_font_file(font_file):
                        font_faces[self.__font_library_value(font_file)] = self.__get_preview_file_url(str(font_file.resolve()))
        except Exception as err:
            logger.warning("【YahahaCoverStudio】构建自定义字体预览映射失败: %s", err)
        return font_faces

    def __ensure_builtin_font_path(self, preset_key: str) -> str:
        if not preset_key:
            return ""
        _, _, main_title_font_preset_paths, _ = self.__get_font_presets()
        existing = main_title_font_preset_paths.get(preset_key)
        if existing and validate_font_file(Path(existing)):
            return str(existing)

        url = self.__builtin_font_urls().get(preset_key)
        if not url or not self._font_path:
            return ""
        extension = self.get_file_extension_from_url(url, fallback_ext=".ttf")
        target = Path(self._font_path) / f"{preset_key}{extension}"
        if validate_font_file(target):
            return str(target)
        if self.download_font_safely_with_timeout(url, target):
            return str(target) if validate_font_file(target) else ""
        if preset_key in ("chaohei", "yasong"):
            fallback_font = self.__find_system_font_fallback("主标题")
            if fallback_font:
                logger.warning("内置中文字体 %s 获取失败，使用系统中文字体回退: %s", preset_key, fallback_font)
                return fallback_font
        return ""

    @staticmethod
    def __contains_cjk_text(value: Any) -> bool:
        return bool(re.search(r"[\u3400-\u9fff]", str(value or "")))

    @staticmethod
    def __is_cjk_font_family(font_family: str) -> bool:
        normalized = re.sub(r"[\s_\-]+", "", str(font_family or "").lower())
        return any(
            token in normalized
            for token in (
                "chaohei",
                "yasong",
                "wenquanyi",
                "wqy",
                "notosanscjk",
                "notoserifcjk",
                "sourcehansans",
                "sourcehanserif",
                "sarasa",
                "unifont",
                "ipag",
            )
        )

    def __get_cjk_font_fallback(self) -> str:
        for preset_key in ("chaohei", "yasong"):
            path = self.__ensure_builtin_font_path(preset_key)
            if path:
                return path
        return self.__find_system_font_fallback("主标题") or ""

    def __semantic_font_family_for_alias(self, alias: str) -> str:
        if alias == "main_title":
            return str(self._main_title_font_preset or "chaohei")
        if alias == "subtitle":
            return str(self._subtitle_font_preset or "EmblemaOne")
        if alias == "custom_text":
            return str(self._custom_text_font_preset or self._subtitle_font_preset or "EmblemaOne")
        return alias

    def __resolve_custom_layer_text(self, layer: Dict[str, Any], title: Tuple[str, str]) -> str:
        layer_type = str(layer.get("type") or "")
        if layer_type in ("main_title", "title_zh"):
            return title[0] if len(title) > 0 else ""
        if layer_type in ("subtitle", "title_en"):
            return title[1] if len(title) > 1 else ""
        if layer_type == "text":
            return str(layer.get("content") or "")
        return ""

    def __layout_with_resolved_custom_texts(self, layout: Optional[Dict[str, Any]], custom_texts: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        normalized_layout = self.__normalize_custom_static_template(layout or {})
        custom_texts = custom_texts or {}

        def visit(layer: Dict[str, Any]) -> Dict[str, Any]:
            next_layer = dict(layer or {})
            if next_layer.get("type") == "group" and isinstance(next_layer.get("children"), list):
                next_layer["children"] = [
                    visit(child)
                    for child in next_layer.get("children") or []
                    if isinstance(child, dict)
                ]
                return next_layer
            if str(next_layer.get("type") or "") == "text":
                next_layer["content"] = self.__resolve_configurable_text_layer_value(next_layer, custom_texts)
                text_style = next_layer.get("textStyle") if isinstance(next_layer.get("textStyle"), dict) else {}
                next_layer["textStyle"] = {
                    **text_style,
                    "content": next_layer["content"],
                }
            return next_layer

        normalized_layout["layers"] = [
            visit(layer)
            for layer in normalized_layout.get("layers") or []
            if isinstance(layer, dict)
        ]
        return normalized_layout

    def __iter_custom_text_layers(self, layers: List[Dict[str, Any]]):
        for layer in layers or []:
            if not isinstance(layer, dict):
                continue
            if layer.get("type") == "group":
                yield from self.__iter_custom_text_layers(layer.get("children") or [])
            elif str(layer.get("type") or "") in ("main_title", "title_zh", "subtitle", "title_en", "text"):
                yield layer

    def __resolve_template_font_path(self, font_family: str, text_value: str = "") -> str:
        font_family = str(font_family or "main_title")
        custom_font_path = self.__resolve_custom_font_path(font_family)
        if custom_font_path:
            return str(custom_font_path)
        semantic_family = self.__semantic_font_family_for_alias(font_family)
        if self.__contains_cjk_text(text_value) and not self.__is_cjk_font_family(semantic_family):
            fallback_font = self.__get_cjk_font_fallback()
            if fallback_font:
                logger.warning("文本包含中文但字体 %s 不含中文字符，使用中文字体回退: %s", semantic_family, fallback_font)
                return fallback_font
        if font_family == "main_title":
            return str(self._main_title_font_path or "")
        if font_family == "subtitle":
            return str(self._subtitle_font_path or "")
        if font_family == "custom_text":
            return str(self._custom_text_font_path or self._subtitle_font_path or "")

        builtin_path = self.__ensure_builtin_font_path(font_family)
        if builtin_path:
            return builtin_path

        if self.__contains_cjk_text(text_value):
            fallback_font = self.__find_system_font_fallback("主标题")
            if fallback_font:
                logger.warning("字体 %s 获取失败且文本包含中文，使用系统中文字体回退: %s", font_family, fallback_font)
                return fallback_font
        fallback_font = self.__find_system_font_fallback("副标题") or self.__find_system_font_fallback("主标题")
        return str(self._custom_text_font_path or self._subtitle_font_path or self._main_title_font_path or fallback_font or "")

    def __build_template_font_paths(self, layout: Optional[Dict[str, Any]] = None, title: Tuple[str, str] = ("", "")) -> Dict[str, str]:
        font_paths: Dict[str, str] = {}
        if self._main_title_font_path:
            font_paths["main_title"] = str(self._main_title_font_path)
        if self._subtitle_font_path:
            font_paths["subtitle"] = str(self._subtitle_font_path)
        if self._custom_text_font_path:
            font_paths["custom_text"] = str(self._custom_text_font_path)

        for key in self.__builtin_font_urls().keys():
            path = self.__ensure_builtin_font_path(key)
            if path:
                font_paths[key] = path
        try:
            font_dir = self.__custom_font_library_dir()
            if font_dir.is_dir():
                for font_file in font_dir.iterdir():
                    if font_file.is_file() and validate_font_file(font_file):
                        font_paths[self.__font_library_value(font_file)] = str(font_file.resolve())
        except Exception as err:
            logger.warning("【YahahaCoverStudio】构建自定义字体路径映射失败: %s", err)

        normalized_layout = self.__normalize_custom_static_template(layout or {}) if isinstance(layout, dict) else {}
        for layer in self.__iter_custom_text_layers(normalized_layout.get("layers") or []):
            text_value = self.__resolve_custom_layer_text(layer, title)
            font_family = str(layer.get("fontFamily") or ("subtitle" if layer.get("type") in ("subtitle", "title_en") else "custom_text" if layer.get("type") == "text" else "main_title"))
            resolved = self.__resolve_template_font_path(font_family, text_value)
            if resolved:
                font_paths[font_family] = resolved
        return font_paths

    def __get_preview_target(self):
        preview_targets = self.__get_preview_targets()
        return preview_targets[0] if preview_targets else None

    def __get_preview_source_file_url(self, image_path: str) -> str:
        safe_path = quote(str(Path(image_path).resolve()), safe="")
        return f"plugin/YahahaCoverStudio/saved_cover_image?file={safe_path}"

    def __get_preview_file_url(self, file_path: str) -> str:
        safe_path = quote(str(Path(file_path).resolve()), safe="")
        return f"plugin/YahahaCoverStudio/saved_cover_image?file={safe_path}"

    def __build_local_preview_image_data_url(self, image_path: str, max_size: Tuple[int, int] = (960, 540)) -> str:
        try:
            target_file = Path(image_path)
            if not target_file.exists() or not target_file.is_file():
                return ""

            try:
                from PIL import Image
                from io import BytesIO

                with Image.open(target_file) as img:
                    if hasattr(img, "is_animated") and img.is_animated:
                        img.seek(0)

                    thumb = img.copy()
                    if thumb.mode not in ("RGB", "L"):
                        thumb = thumb.convert("RGB")

                    thumb.thumbnail(max_size)
                    if thumb.mode != "RGB":
                        thumb = thumb.convert("RGB")

                    buf = BytesIO()
                    thumb.save(buf, format="JPEG", quality=85)
                    image_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                    return f"data:image/jpeg;base64,{image_b64}"
            except Exception as img_err:
                logger.debug(f"生成本地预览缩略图失败 {target_file}: {img_err}")

            mime_type, _ = mimetypes.guess_type(str(target_file))
            if not mime_type:
                mime_type = "image/jpeg"
            content = target_file.read_bytes()
            if not content:
                return ""
            image_b64 = base64.b64encode(content).decode("utf-8")
            return f"data:{mime_type};base64,{image_b64}"
        except Exception as e:
            logger.warning(f"读取本地预览图片失败 {image_path}: {e}")
            return ""

    @staticmethod
    def __preview_source_sort_key(path: Path) -> Tuple[int, int, str]:
        stem = path.stem or ""
        if stem.isdigit():
            return (0, int(stem), path.name.lower())
        match = re.match(r"^(\d+)", stem)
        if match:
            return (0, int(match.group(1)), path.name.lower())
        return (1, 0, path.name.lower())

    def __get_library_image_dir(self, root_dir: Optional[Any], library_name: str) -> Optional[Path]:
        if not root_dir:
            return None
        safe_library_name = self.__sanitize_filename(library_name)
        library_dir = Path(root_dir).expanduser() / safe_library_name
        if not library_dir.exists() or not library_dir.is_dir():
            return None
        return library_dir

    def __collect_library_images_from_root(self, root_dir: Optional[Any], library_name: str) -> List[str]:
        library_dir = self.__get_library_image_dir(root_dir, library_name)
        if not library_dir:
            return []

        allowed_exts = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".apng"}
        images = [
            str(path.resolve())
            for path in sorted(library_dir.iterdir(), key=self.__preview_source_sort_key)
            if path.is_file() and path.suffix.lower() in allowed_exts
        ]
        return images

    def __check_cached_preview_images(self, library_name: str) -> Optional[Dict[str, Any]]:
        cache_roots: List[Path] = [self.__preview_cache_root()]
        if self._covers_path:
            cache_roots.append(Path(self._covers_path))
        cache_roots.append(self.get_data_path() / "covers")

        handled = set()
        for root_dir in cache_roots:
            try:
                root_path = Path(root_dir).expanduser().resolve()
            except Exception:
                continue
            root_key = str(root_path)
            if root_key in handled:
                continue
            handled.add(root_key)
            images = self.__collect_library_images_from_root(root_path, library_name)
            if images:
                return {
                    "root": root_path,
                    "images": images,
                }
        return None

    def __preview_cache_root(self) -> Path:
        return self.get_data_path() / "preview_cache"

    def __clear_preview_cache_for_library(self, library_name: str) -> int:
        """Remove only persistent preview data, never generation or user assets."""
        removed = 0
        cache_roots: List[Path] = [self.__preview_cache_root()]
        safe_name = self.__sanitize_filename(library_name)
        for root_dir in cache_roots:
            try:
                root = Path(root_dir).expanduser().resolve()
            except Exception:
                continue
            target = root / safe_name
            if not target.exists() or not target.is_dir():
                continue
            try:
                shutil.rmtree(target)
                removed += 1
            except Exception as error:
                logger.warning("清理预览素材缓存失败 %s: %s", target, error)
        return removed

    def __build_local_preview_source_images(self, image_paths: Optional[List[str]], source_mode: str, required_items: Optional[int] = None):
        required_items = required_items or self.__get_required_items()
        images: List[Dict[str, Any]] = []

        selected_paths = [str(path) for path in (image_paths or []) if path][:required_items]
        for index, image_path in enumerate(selected_paths, start=1):
            resolved = Path(image_path)
            if not resolved.is_file():
                continue
            src = self.__build_local_preview_image_data_url(str(resolved))
            if not src:
                continue
            image_width = 0
            image_height = 0
            try:
                from PIL import Image
                with Image.open(resolved) as image:
                    image_width, image_height = image.size
            except Exception:
                image_width = 0
                image_height = 0
            images.append({
                "slot": index,
                "src": src,
                "kind": source_mode,
                "label": resolved.name,
                "width": image_width,
                "height": image_height,
            })
        return images

    def __build_preview_source_images(self, service, library, required_items: Optional[int] = None, force_refresh: bool = False):
        required_items = required_items or self.__get_required_items()
        images: List[Dict[str, Any]] = []
        image_data = self.__collect_preview_server_images(
            service,
            library,
            required_items=required_items,
            force_refresh=force_refresh,
        )
        for index, item in enumerate(image_data[:required_items], start=1):
            images.append({
                "slot": index,
                "src": item.get("src", ""),
                "kind": "media_server",
                "label": item.get("label", ""),
            })
        return [image for image in images if image.get("src")]

    def __resolve_preview_source_images(self, preview_target: Dict[str, Any], required_items: Optional[int] = None, force_refresh: bool = False) -> Tuple[str, List[Dict[str, Any]]]:
        required_items = required_items or self.__get_required_items()
        combined: List[Dict[str, Any]] = []
        seen = set()

        def append_images(candidates: List[Dict[str, Any]]) -> None:
            for item in candidates:
                if len(combined) >= required_items:
                    break
                src = str(item.get("src") or "")
                label = str(item.get("label") or "")
                key = src or label
                if key and key in seen:
                    continue
                if key:
                    seen.add(key)
                next_item = dict(item)
                next_item["slot"] = len(combined) + 1
                combined.append(next_item)

        source_mode = "media_server"
        custom_images = preview_target.get("custom_images")
        if custom_images:
            images = self.__build_local_preview_source_images(custom_images, "custom", required_items=required_items)
            append_images(images)
            if combined:
                source_mode = "custom"
            if len(combined) >= required_items:
                return source_mode, combined

        cache_images = None if force_refresh else preview_target.get("cache_images")
        if cache_images:
            images = self.__build_local_preview_source_images(cache_images, "cache", required_items=required_items)
            append_images(images)
            if source_mode == "media_server" and combined:
                source_mode = "cache"
            if len(combined) >= required_items:
                return source_mode, combined

        images = self.__build_preview_source_images(
            preview_target["service"],
            preview_target["library"],
            required_items=required_items,
            force_refresh=force_refresh,
        )
        append_images(images)
        if combined:
            return source_mode, combined
        return "media_server", []

    def __collect_preview_server_images(self, service, library, required_items: Optional[int] = None, force_refresh: bool = False):
        logger.info(f"媒体库 {service.name}：{library['Name']} 开始收集预览素材")
        required_items = required_items or self.__get_required_items()
        library_type = library.get('CollectionType')
        if service.type == 'emby':
            library_id = library.get("Id")
        else:
            library_id = library.get("ItemId")
        parent_id = library_id

        if library_type == "boxsets":
            items = self.__collect_boxset_preview_items(service, library, required_items)
        elif library_type == "playlists":
            items = self.__collect_playlist_preview_items(service, library, required_items)
        else:
            items = self.__collect_regular_preview_items(service, parent_id, required_items)

        cached_entries = self.__cache_preview_server_images(
            service,
            str(library.get("Name") or ""),
            items[:required_items],
        )
        if cached_entries:
            return cached_entries
        return self.__build_preview_image_entries(service, items[:required_items])

    @staticmethod
    def __preview_image_request_url(image_url: str) -> str:
        delimiter = '&' if '?' in image_url else '?'
        return f"{image_url}{delimiter}maxWidth=960&maxHeight=540&quality=82"

    def __download_preview_image_to_cache(self, service, image_url: str, output_path: Path) -> Optional[Path]:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cache_key = hashlib.sha256(image_url.encode("utf-8")).hexdigest()
            meta_path = output_path.with_suffix(f"{output_path.suffix}.urlhash")
            if output_path.is_file() and output_path.stat().st_size > 0 and meta_path.is_file():
                if meta_path.read_text(encoding="utf-8").strip() == cache_key:
                    return output_path
            response = service.instance.get_data(url=image_url) if '[HOST]' in image_url else RequestUtils(
                headers={'User-Agent': 'MoviePilot-YahahaCoverStudio/1.0'}, timeout=30,
            ).get_res(url=image_url)
            if not response or response.status_code != 200 or not response.content:
                return None
            temporary_path = output_path.with_suffix(f"{output_path.suffix}.part")
            temporary_path.write_bytes(response.content)
            temporary_path.replace(output_path)
            meta_path.write_text(cache_key, encoding="utf-8")
            return output_path
        except Exception as error:
            logger.warning("写入预览素材缓存失败 %s: %s", output_path, error)
            return None

    def __cache_preview_server_images(self, service, library_name: str, items: List[Dict[str, Any]]):
        candidates: List[Tuple[int, Dict[str, Any], str, Path]] = []
        cache_dir = self.__preview_cache_root() / self.__sanitize_filename(library_name)
        for index, item in enumerate(items, start=1):
            image_url = self.__get_image_url(item)
            if not image_url:
                continue
            candidates.append((
                index,
                item,
                self.__preview_image_request_url(image_url),
                cache_dir / f"{index:02d}.jpg",
            ))
        if not candidates:
            return []

        cached_paths: Dict[int, Path] = {}
        # MoviePilot media-server clients are less tolerant of broad concurrent access
        # than httpx. Two workers retain a noticeable speed-up and a sequential retry
        # makes manual refresh reliable on stricter Emby/Jellyfin deployments.
        with ThreadPoolExecutor(max_workers=min(2, len(candidates))) as executor:
            futures = {
                executor.submit(self.__download_preview_image_to_cache, service, image_url, target): index
                for index, _, image_url, target in candidates
            }
            for future in as_completed(futures):
                index = futures[future]
                try:
                    path = future.result()
                except Exception as error:
                    logger.warning("下载预览素材失败: %s", error)
                    continue
                if path:
                    cached_paths[index] = path
        for index, _, image_url, target in candidates:
            if index in cached_paths:
                continue
            path = self.__download_preview_image_to_cache(service, image_url, target)
            if path:
                cached_paths[index] = path

        entries: List[Dict[str, Any]] = []
        for index, item, _, _ in candidates:
            path = cached_paths.get(index)
            if not path:
                continue
            src = self.__build_local_preview_image_data_url(str(path))
            if src:
                entries.append({
                    "src": src,
                    "label": item.get("Name") or item.get("SeriesName") or item.get("Album") or "",
                })
        return entries

    def __collect_regular_preview_items(self, service, parent_id, required_items):
        items = []
        offset = 0
        batch_size = 50
        max_attempts = 20

        if self._cover_style == 'static_custom':
            include_types = 'Movie,Series,Episode,MusicAlbum,Audio'
        elif self.__is_single_image_style():
            include_types = {
                "PremiereDate": "Movie,Series",
                "DateCreated": "Movie,Episode",
                "Random": "Movie,Series"
            }.get(self._sort_by, "Movie,Series")
        else:
            include_types = "Movie,Episode" if self._sort_by == "DateCreated" else "Movie,Series"

        self._seen_keys = set()
        for _ in range(max_attempts):
            batch_items = self.__get_items_batch(
                service,
                parent_id,
                offset=offset,
                limit=batch_size,
                include_types=include_types,
            )
            if not batch_items:
                break
            valid_items = self.__filter_valid_items(batch_items)
            items.extend(valid_items)
            if len(items) >= required_items:
                break
            offset += batch_size
        return items

    def __collect_boxset_preview_items(self, service, library, required_items):
        include_types = 'BoxSet,Movie'
        if service.type == 'emby':
            library_id = library.get("Id")
        else:
            library_id = library.get("ItemId")
        boxsets = self.__get_items_batch(service, library_id, include_types=include_types)
        valid_items = []
        self._seen_keys = set()
        valid_items.extend(self.__filter_valid_items(boxsets))
        if len(valid_items) >= required_items:
            return valid_items
        for boxset in boxsets:
            if len(valid_items) >= required_items:
                break
            movies = self.__get_items_batch(service, parent_id=boxset['Id'], include_types=include_types)
            valid_items.extend(self.__filter_valid_items(movies))
        return valid_items

    def __collect_playlist_preview_items(self, service, library, required_items):
        include_types = 'Playlist,Movie,Series,Episode,Audio'
        if service.type == 'emby':
            library_id = library.get("Id")
        else:
            library_id = library.get("ItemId")
        playlists = self.__get_items_batch(service, library_id, include_types=include_types)
        valid_items = []
        self._seen_keys = set()
        valid_items.extend(self.__filter_valid_items(playlists))
        if len(valid_items) >= required_items:
            return valid_items
        for playlist in playlists:
            if len(valid_items) >= required_items:
                break
            media_items = self.__get_items_batch(service, parent_id=playlist['Id'], include_types=include_types)
            valid_items.extend(self.__filter_valid_items(media_items))
        return valid_items

    def __build_preview_image_entries(self, service, items):
        candidates: List[Tuple[int, Dict[str, Any], str]] = []
        for index, item in enumerate(items):
            image_url = self.__get_image_url(item)
            if not image_url:
                continue
            delimiter = '&' if '?' in image_url else '?'
            # Both Emby and Jellyfin implement these ImageService query parameters.
            # The MoviePilot proxy still returns a data URL for authenticated browsers.
            preview_url = f"{image_url}{delimiter}maxWidth=960&maxHeight=540&quality=82"
            candidates.append((index, item, preview_url))

        sources: Dict[int, str] = {}
        max_workers = min(2, len(candidates))
        if max_workers:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.__download_preview_image_data_url, service, image_url): index
                    for index, _, image_url in candidates
                }
                for future in as_completed(futures):
                    index = futures[future]
                    try:
                        src = future.result()
                    except Exception as err:
                        logger.warning(f"下载预览素材失败: {err}")
                        continue
                    if src:
                        sources[index] = src

        # Some MoviePilot media-server adapters share mutable request state. Retry any
        # missed candidates serially so the refresh control remains reliable even when
        # a server rejects concurrent image reads.
        for index, _, image_url in candidates:
            if index in sources:
                continue
            src = self.__download_preview_image_data_url(service, image_url)
            if src:
                sources[index] = src

        entries: List[Dict[str, Any]] = []
        for index, item, _ in candidates:
            # The MoviePilot page can authenticate API calls but a browser <img> cannot
            # reliably send the media-server credentials. Always proxy preview artwork
            # through the plugin and return a data URL so a forced refresh never leaves
            # an unauthenticated server URL behind as a broken-image placeholder.
            src = sources.get(index)
            if not src:
                continue
            entries.append({
                "src": src,
                "label": item.get("Name") or item.get("SeriesName") or item.get("Album") or "",
            })
        return entries

    def __download_preview_image_data_url(self, service, image_url: str) -> str:
        try:
            if '[HOST]' in image_url:
                if not service:
                    return ""
                response = service.instance.get_data(url=image_url)
            else:
                response = RequestUtils(
                    headers={'User-Agent': 'MoviePilot-YahahaCoverStudio/1.0'},
                    timeout=30,
                ).get_res(url=image_url)
            if not response or response.status_code != 200:
                return ""
            content = response.content
            if not content:
                return ""
            content_type = response.headers.get("content-type") if hasattr(response, "headers") else None
            if not content_type:
                content_type = "image/jpeg"
            content_type = str(content_type).split(";", 1)[0].strip().lower() or "image/jpeg"
            encoded = base64.b64encode(content).decode("utf-8")
            return f"data:{content_type};base64,{encoded}"
        except Exception as e:
            logger.warning(f"下载预览素材失败: {e}")
            return ""

    def api_preview(
        self,
        style: str = "",
        data: Optional[Any] = None,
        kwargs: Optional[Any] = None,
        layout: Optional[dict] = None,
    ):
        """生成当前风格的预览封面，仅返回 base64 图片，不修改媒体库封面"""
        old_style = self._cover_style
        old_layout = self._custom_static_layout
        old_templates = self._custom_static_layouts
        try:
            payload = self.__extract_request_payload(data=data, kwargs=kwargs)
            target_style = (style or payload.get("style") or "").strip()
            layout_payload = layout if layout is not None else payload.get("layout")
            allowed_styles = {
                "static_1", "static_2", "static_3", "static_4",
                "animated_1", "animated_2", "animated_3", "animated_4",
                "static_custom", "custom_static",
            }
            if target_style:
                if target_style not in allowed_styles:
                    return {"code": 1, "msg": f"不支持的风格: {target_style}"}
                if target_style == "custom_static":
                    target_style = "static_custom"
                self._cover_style = target_style

            if isinstance(layout_payload, str) and layout_payload:
                import json
                layout_payload = json.loads(layout_payload)
            if self._cover_style == "static_custom" and isinstance(layout_payload, dict):
                self._custom_static_layout = self.__normalize_custom_static_template(layout_payload)
            elif self._cover_style in {"static_1", "static_2", "static_3", "static_4"} and isinstance(layout_payload, dict):
                preset_id = f"__preset_{self._cover_style}"
                normalized_layout = self.__normalize_custom_static_template(layout_payload)
                self._custom_static_layouts = [
                    template
                    for template in (old_templates or [])
                    if not (
                        isinstance(template, dict)
                        and (
                            str(template.get("id") or "") == preset_id
                            or str(template.get("baseStyle") or "") == self._cover_style
                        )
                    )
                ] + [{
                    "id": preset_id,
                    "name": f"{self._cover_style} preview",
                    "layout": normalized_layout,
                    "baseStyle": self._cover_style,
                    "system": True,
                }]

            preview_targets = self.__get_preview_targets()
            if not preview_targets:
                logger.warning("【YahahaCoverStudio】预览生成失败：未找到可用的媒体库")
                return {"code": 1, "msg": "未找到可用的媒体库用于生成预览，请检查媒体库设置"}

            for preview_target in preview_targets:
                service = preview_target["service"]
                server = preview_target["server"]
                library_name = preview_target["library_name"]
                title = preview_target["title"]
                config_bg_color = preview_target["config_bg_color"]
                custom_images = preview_target.get("custom_images")
                cache_images = preview_target.get("cache_images")

                image_data = None
                if custom_images:
                    custom_image_input = self.__build_preview_local_image_input(custom_images)
                    image_data = self.__generate_image_from_path(
                        service.name,
                        library_name,
                        title,
                        custom_image_input,
                        config_bg_color,
                        source_root=self._covers_input,
                    )
                elif cache_images:
                    cache_image_input = self.__build_preview_local_image_input(cache_images)
                    image_data = self.__generate_image_from_path(
                        service.name,
                        library_name,
                        title,
                        cache_image_input,
                        config_bg_color,
                        source_root=preview_target.get("cache_root"),
                    )
                else:
                    image_data = self.__generate_from_server(service, preview_target["library"], title)

                if not image_data:
                    logger.info(f"媒体库 {server}：{library_name} 无法生成预览，继续尝试下一个媒体库")
                    continue

                mime_type = "image/png"
                if image_data.startswith("R0lG"):
                    mime_type = "image/gif"
                elif image_data.startswith("UklG"):
                    mime_type = "image/webp"
                elif image_data.startswith("iVBOR"):
                    mime_type = "image/png"
                elif image_data.startswith("/9j/"):
                    mime_type = "image/jpeg"

                src = f"data:{mime_type};base64,{image_data}"
                logger.info(f"【YahahaCoverStudio】预览封面生成成功，媒体库: {server}：{library_name}")
                return {
                    "code": 0,
                    "data": {
                        "src": src,
                        "server": server,
                        "library": library_name,
                        "style": self._cover_style,
                    },
                }

            return {"code": 1, "msg": "当前媒体库无法生成预览"}
        except RuntimeError as e:
            return {"code": 1, "msg": str(e)}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】预览生成异常: {e}", exc_info=True)
            return {"code": 1, "msg": f"预览生成失败: {e}"}
        finally:
            self._cover_style = old_style
            self._custom_static_layout = old_layout
            self._custom_static_layouts = old_templates

    def api_clean_images(self):
        try:
            logger.info("【YahahaCoverStudio】收到立即清理图片缓存请求")
            self.__clean_generated_images()
            self._clean_images = False
            self.__update_config()
            return {"code": 0, "msg": "图片缓存清理完成"}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】立即清理图片失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"图片缓存清理失败: {e}"}

    def api_clean_fonts(self):
        try:
            logger.info("【YahahaCoverStudio】收到立即清理字体缓存请求")
            self.__clean_downloaded_fonts()
            self._clean_fonts = False
            self.__update_config()
            return {"code": 0, "msg": "字体缓存清理完成"}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】立即清理字体失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"字体缓存清理失败: {e}"}

    def api_delete_saved_cover(self, file: str = ""):
        try:
            target_file = self.__resolve_saved_cover_path(file)
            if not target_file:
                return {"code": 1, "msg": "无效文件路径"}
            if not target_file.exists() or not target_file.is_file():
                return {"code": 1, "msg": "文件不存在"}
            target_file.unlink(missing_ok=True)
            logger.info(f"【YahahaCoverStudio】已删除封面文件: {target_file}")
            return {"code": 0, "msg": "封面文件删除成功"}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】删除封面文件失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"封面文件删除失败: {e}"}

    def api_delete_saved_covers(self, data: Optional[Any] = Body(None), kwargs: Optional[Any] = None, files: Optional[Any] = None):
        try:
            payload = self.__extract_request_payload(data=data, kwargs=kwargs)
            raw_files = files if files is not None else payload.get("files")
            if isinstance(raw_files, str):
                raw_files = [raw_files]
            if not isinstance(raw_files, list) or not raw_files:
                return {"code": 1, "msg": "未提供需要删除的封面文件"}

            deleted = 0
            failed: List[str] = []
            for raw_file in raw_files:
                target_file = self.__resolve_saved_cover_path(str(raw_file or ""))
                if not target_file or not target_file.exists() or not target_file.is_file():
                    failed.append(str(raw_file))
                    continue
                try:
                    target_file.unlink(missing_ok=True)
                    deleted += 1
                    logger.info(f"【YahahaCoverStudio】已删除封面文件: {target_file}")
                except Exception:
                    failed.append(str(raw_file))

            return {
                "code": 0 if deleted else 1,
                "msg": f"已删除 {deleted} 个封面文件" if deleted else "没有可删除的封面文件",
                "data": {
                    "deleted": deleted,
                    "failed": failed,
                },
            }
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】批量删除封面文件失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"批量删除封面文件失败: {e}"}

    def api_download_saved_cover(self, file: str = "", data: Optional[Any] = None, kwargs: Optional[Any] = None):
        try:
            payload = self.__extract_request_payload(data=data, kwargs=kwargs)
            raw_file = file or payload.get("file") or payload.get("path") or ""
            target_file = self.__resolve_saved_cover_path(str(raw_file))
            if not target_file:
                return {"code": 1, "msg": "无效文件路径"}
            if not target_file.exists() or not target_file.is_file():
                return {"code": 1, "msg": "文件不存在"}

            mime_type, _ = mimetypes.guess_type(str(target_file))
            if not mime_type:
                mime_type = "application/octet-stream"
            encoded = base64.b64encode(target_file.read_bytes()).decode("utf-8")
            return {
                "code": 0,
                "data": {
                    "name": target_file.name,
                    "mime": mime_type,
                    "b64": encoded,
                    "size": self.__format_size(target_file.stat().st_size),
                },
            }
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】下载封面文件失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"下载封面文件失败: {e}"}

    def api_download_saved_covers(self, data: Optional[Any] = Body(None), kwargs: Optional[Any] = None, files: Optional[Any] = None):
        try:
            payload = self.__extract_request_payload(data=data, kwargs=kwargs)
            raw_files = files if files is not None else payload.get("files")
            if isinstance(raw_files, str):
                raw_files = [raw_files]
            if not isinstance(raw_files, list) or not raw_files:
                return {"code": 1, "msg": "未提供需要下载的封面文件"}

            archive_buffer = io.BytesIO()
            added = 0
            used_names = set()
            failed: List[str] = []

            with zipfile.ZipFile(archive_buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for raw_file in raw_files:
                    target_file = self.__resolve_saved_cover_path(str(raw_file or ""))
                    if not target_file or not target_file.exists() or not target_file.is_file():
                        failed.append(str(raw_file))
                        continue

                    archive_name = target_file.name
                    duplicate_index = 2
                    while archive_name in used_names:
                        archive_name = f"{target_file.stem}_{duplicate_index}{target_file.suffix}"
                        duplicate_index += 1
                    used_names.add(archive_name)
                    archive.write(target_file, archive_name)
                    added += 1

            if not added:
                return {"code": 1, "msg": "没有可下载的封面文件"}

            archive_bytes = archive_buffer.getvalue()
            archive_name = f"yahahacoverstudio_covers_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            return {
                "code": 0,
                "msg": f"已打包 {added} 个封面文件",
                "data": {
                    "name": archive_name,
                    "mime": "application/zip",
                    "b64": base64.b64encode(archive_bytes).decode("utf-8"),
                    "size": self.__format_size(len(archive_bytes)),
                    "added": added,
                    "failed": failed,
                },
            }
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】批量下载封面文件失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"批量下载封面文件失败: {e}"}

    def api_generate_now(self, style: str = "", data: Optional[Any] = None, kwargs: Optional[Any] = None):
        try:
            if not self._enabled:
                logger.warning("【YahahaCoverStudio】立即生成失败：插件未启用，请先在设置页启用插件并保存")
                return {"code": 1, "msg": "插件未启用，请先在设置页启用插件并保存"}
            self.__refresh_media_server_context(force=True)
            if not self._servers:
                logger.warning("【YahahaCoverStudio】立即生成失败：未检测到任何可用媒体服务器，请检查设置并保存后重试")
                return {"code": 1, "msg": "未检测到任何可用媒体服务器，请检查设置并保存后重试"}

            payload = self.__extract_request_payload(data=data, kwargs=kwargs)
            target_style = (style or payload.get("style") or "").strip()
            allowed_styles = {
                "static_1", "static_2", "static_3", "static_4",
                "animated_1", "animated_2", "animated_3", "animated_4",
                "static_custom", "custom_static",
            }
            if target_style:
                if target_style not in allowed_styles:
                    return {"code": 1, "msg": f"不支持的风格: {target_style}"}
                if target_style == "custom_static":
                    target_style = "static_custom"
            logger.info(f"【YahahaCoverStudio】收到立即生成请求，风格: {target_style or self._cover_style}")
            started, msg = self.__start_background_generation(target_style=target_style or None)
            return {"code": 0 if started else 1, "msg": msg}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】立即生成失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"封面生成失败: {e}"}

    def api_start_generation(self, style: str = "", data: Optional[Any] = None, kwargs: Optional[Any] = None):
        try:
            if not self._enabled:
                return {"code": 1, "msg": "插件未启用，请先在设置页启用插件并保存"}
            self.__refresh_media_server_context(force=True)
            if not self._servers:
                return {"code": 1, "msg": "未检测到任何可用媒体服务器，请检查设置并保存后重试"}

            payload = self.__extract_request_payload(data=data, kwargs=kwargs)
            target_style = (style or payload.get("style") or "").strip()
            allowed_styles = {
                "static_1", "static_2", "static_3", "static_4",
                "animated_1", "animated_2", "animated_3", "animated_4",
                "static_custom", "custom_static",
            }
            if target_style:
                if target_style not in allowed_styles:
                    return {"code": 1, "msg": f"不支持的风格: {target_style}"}
                if target_style == "custom_static":
                    target_style = "static_custom"

            started, msg = self.__start_background_generation(target_style=target_style or None)
            return {"code": 0 if started else 1, "msg": msg}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】启动后台生成失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"启动后台生成失败: {e}"}

    def api_stop_generation(self):
        try:
            if not self.__is_generation_running():
                return {"code": 0, "msg": "当前没有正在执行的封面生成任务"}
            success, msg = self.stop_task()
            return {"code": 0 if success else 1, "msg": msg}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】停止后台生成失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"停止后台生成失败: {e}"}

    def api_set_cover_style(self, style: str = "", data: Optional[Any] = None, kwargs: Optional[Any] = None):
        try:
            payload = self.__extract_request_payload(data=data, kwargs=kwargs)
            target_style = (style or payload.get("style") or "").strip()
            allowed_styles = {
                "static_1", "static_2", "static_3", "static_4",
                "animated_1", "animated_2", "animated_3", "animated_4",
                "static_custom", "custom_static",
            }
            if target_style not in allowed_styles:
                return {"code": 1, "msg": f"不支持的风格: {target_style}"}
            if target_style == "custom_static":
                target_style = "static_custom"
            self._cover_style = target_style
            base, variant = self.__resolve_cover_style_ui(target_style)
            self._cover_style_base = base
            self._cover_style_variant = variant
            if target_style.startswith("animated_"):
                self.__apply_animated_settings_for_style(target_style)
            self.__update_config()
            logger.info(f"【YahahaCoverStudio】已保存封面风格: {target_style}")
            return {"code": 0, "msg": f"已保存风格: {target_style}"}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】保存封面风格失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"保存风格失败: {e}"}

    def api_set_animated_settings(self, data: Optional[Any] = Body(None), kwargs: Optional[Any] = None):
        try:
            payload = self.__extract_request_payload(data=data, kwargs=kwargs)
            style_key = self.__get_animated_style_key(
                payload.get("style")
                or payload.get("cover_style")
                or payload.get("base_style")
                or self._cover_style
            )
            current_settings = self.__get_animated_settings_for_style(style_key)
            next_settings = self.__normalize_animated_setting(payload, current_settings)
            self._animated_settings = self.__normalize_animated_settings_map(self._animated_settings)
            self._animated_settings[style_key] = next_settings
            if self.__get_animated_style_key(self._cover_style) == style_key:
                self.__apply_animated_settings_for_style(style_key)

            self.__update_config()
            animated_settings = self.__export_animated_settings()
            active_settings = self.__get_animated_settings_for_style(style_key)
            return {
                "code": 0,
                "msg": "已保存动态封面参数",
                "data": {
                    "animation_duration": active_settings["animation_duration"],
                    "animation_fps": active_settings["animation_fps"],
                    "animation_format": active_settings["animation_format"],
                    "animation_scroll": active_settings["animation_scroll"],
                    "animation_reduce_colors": active_settings["animation_reduce_colors"],
                    "animated_2_image_count": active_settings["animated_2_image_count"],
                    "animated_2_departure_type": active_settings["animated_2_departure_type"],
                    "main_title_font_preset": active_settings["main_title_font_preset"],
                    "subtitle_font_preset": active_settings["subtitle_font_preset"],
                    "custom_text_font_preset": active_settings["custom_text_font_preset"],
                    "main_title_font_size": active_settings["main_title_font_size"],
                    "subtitle_font_size": active_settings["subtitle_font_size"],
                    "blur_size": active_settings["blur_size"],
                    "color_ratio": active_settings["color_ratio"],
                    "title_scale": active_settings["title_scale"],
                    "animated_settings": animated_settings,
                },
            }
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】保存动态封面参数失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"保存动态封面参数失败: {e}"}

    def api_set_render_options(self, data: Optional[Any] = Body(None), kwargs: Optional[Any] = None):
        try:
            payload = self.__extract_request_payload(data=data, kwargs=kwargs)
            poster_source = str(payload.get("poster_source") or "").strip()
            if poster_source:
                if poster_source not in ["backdrop", "poster"]:
                    return {"code": 1, "msg": f"不支持的海报来源: {poster_source}"}
                self._use_primary = poster_source == "poster"
            elif "use_primary" in payload:
                self._use_primary = bool(payload.get("use_primary"))

            sort_by = str(payload.get("sort_by") or self._sort_by or "Random").strip()
            if self._lock_latest_sort:
                sort_by = "DateCreated"
            if sort_by not in ["Random", "DateCreated", "PremiereDate"]:
                sort_by = "Random"
            self._sort_by = sort_by

            image_count_mode = str(payload.get("image_count_mode") or self._image_count_mode or "auto").strip()
            self._image_count_mode = "fixed" if image_count_mode == "fixed" else "auto"
            self._image_count = self.__clamp_value(
                payload.get("image_count", self._image_count),
                1,
                60,
                9,
                "image_count[api]",
                int,
            )

            resolution = str(payload.get("resolution") or self._resolution or "480p").strip()
            if resolution not in ["1080p", "720p", "480p"]:
                resolution = "480p"
            if resolution != self._resolution:
                self._resolution_config = None
            self._resolution = resolution

            self.__update_config()
            logger.info(
                "【YahahaCoverStudio】素材参数已保存: poster_source=%s, sort_by=%s, image_count_mode=%s, image_count=%s, resolution=%s",
                "poster" if self._use_primary else "backdrop",
                self._sort_by or "Random",
                self._image_count_mode,
                self._image_count,
                self._resolution,
            )
            return {
                "code": 0,
                "msg": "已保存素材参数",
                "data": {
                    "poster_source": "poster" if self._use_primary else "backdrop",
                    "use_primary": bool(self._use_primary),
                    "sort_by": self._sort_by or "Random",
                    "image_count_mode": self._image_count_mode,
                    "image_count": self._image_count,
                    "auto_image_count": self.__get_auto_required_items(),
                    "resolution": self._resolution,
                },
            }
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】保存素材参数失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"保存素材参数失败: {e}"}

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
        logger.info(f"【YahahaCoverStudio】已保存封面风格: {target_style}")

    def api_toggle_style_variant(self):
        try:
            variant, index = self.__get_cover_style_parts()
            new_variant = "animated" if variant == "static" else "static"
            self.__set_cover_style_parts(new_variant, index)
            return {"code": 0, "msg": f"已切换为{new_variant}风格{index}"}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】切换静态/动态失败: {e}", exc_info=True)
            return {"code": 1, "msg": f"切换失败: {e}"}

    def __api_select_style(self, index: int):
        try:
            variant, _ = self.__get_cover_style_parts()
            self.__set_cover_style_parts(variant, index)
            return {"code": 0, "msg": f"已选择{variant}风格{index}"}
        except Exception as e:
            logger.error(f"【YahahaCoverStudio】选择风格失败: {e}", exc_info=True)
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
        self._page_tab = tab if tab in ["generate-tab", "custom-tab", "history-tab", "clean-tab"] else "generate-tab"
        logger.info(f"【YahahaCoverStudio】已切换页面Tab: {self._page_tab}")

    def api_set_page_tab_generate(self):
        self.__set_page_tab("generate-tab")
        return {"code": 0, "msg": "已切换到封面生成"}

    def api_set_page_tab_custom(self):
        self.__set_page_tab("custom-tab")
        return {"code": 0, "msg": "已切换到自定义风格"}

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
            stat = target_file.stat()
            return FileResponse(path=str(target_file), media_type=mime_type, headers={"Cache-Control": "private, max-age=86400", "ETag": f'\"{stat.st_mtime_ns}-{stat.st_size}\"'})
        except Exception:
            try:
                from starlette.responses import FileResponse
                return FileResponse(path=str(target_file), media_type=mime_type)
            except Exception as e:
                logger.error(f"【YahahaCoverStudio】返回图片失败: {e}")
                return {"code": 1, "msg": "返回图片失败"}

    def api_plugin_asset(self, file: str = ""):
        safe_name = Path(str(file or "")).name
        if safe_name not in {"yahaha-cover-studio.png", "yahaha-preview-avatar.png"}:
            return {"code": 1, "msg": "资源不存在"}
        target_file = Path(__file__).parent / "assets" / safe_name
        if not target_file.exists() or not target_file.is_file():
            return {"code": 1, "msg": "资源不存在"}
        mime_type, _ = mimetypes.guess_type(str(target_file))
        if not mime_type:
            mime_type = "image/png"
        try:
            from fastapi.responses import FileResponse
            return FileResponse(path=str(target_file), media_type=mime_type)
        except Exception:
            try:
                from starlette.responses import FileResponse
                return FileResponse(path=str(target_file), media_type=mime_type)
            except Exception as e:
                logger.error(f"【YahahaCoverStudio】返回插件资源失败: {e}")
                return {"code": 1, "msg": "返回插件资源失败"}

    def get_service(self) -> List[Dict[str, Any]]:
        """
        注册插件公共服务
        """
        services = []
        if self._enabled and self._cron:
            services.append({
                "id": "YahahaCoverStudio",
                "name": "媒体库封面更新服务",
                "trigger": CronTrigger.from_crontab(self._cron),
                "func": self.__update_all_libraries,
                "kwargs": {}
            })
        if self._enabled and self._backup_enabled and self._backup_cron:
            try:
                services.append({
                    "id": "YahahaCoverStudioConfigBackup",
                    "name": "媒体库封面完整配置备份服务",
                    "trigger": CronTrigger.from_crontab(self._backup_cron),
                    "func": self.__backup_full_config,
                    "kwargs": {}
                })
            except Exception as e:
                logger.warning(f"配置备份 cron 表达式无效，已跳过定时备份: {self._backup_cron}, {e}")
        
        # 总是显示停止按钮，以便中断长时间运行的任务
        services.append({
            "id": "StopYahahaCoverStudio",
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
        if self._enabled:
            self.__refresh_media_server_context(force=True)
        
        main_title_font_items, subtitle_font_items, _, _ = self.__get_font_presets()
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
                                    'label': '主副标题配置',
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
                                    'text': '字体设置为可选项。上传或导入的字体会保存到字体库，并可在所有字体下拉列表中选择。'
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
                                    'model': 'main_title_font_preset',
                                    'label': '主标题字体预设',
                                    'prependInnerIcon': 'mdi-ideogram-cjk',
                                    'items': main_title_font_items
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
                                    'model': 'subtitle_font_preset',
                                    'label': '副标题字体预设',
                                    'prependInnerIcon': 'mdi-format-font',
                                    'items': subtitle_font_items
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
                                    'model': 'main_title_font_size',
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
                                    'model': 'subtitle_font_size',
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
                                    'model': 'main_title_font_offset',
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
                                    'model': 'subtitle_line_spacing',
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
                                                            'label': '动画时长 (秒)',
                                                            'type': 'number',
                                                            'min': 1,
                                                            'max': 60,
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
                                                            'min': 1,
                                                            'max': 60,
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
                                                            'label': '样式1/2/4 图片数量 (3~60)',
                                                            'type': 'number',
                                                            'min': 3,
                                                            'max': 60,
                                                            'hint': '仅样式1/2/4有效',
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
                                                        'component': 'VSelect',
                                                        'props': {
                                                            'model': 'monitor_source',
                                                            'label': '监控来源',
                                                            'items': [
                                                                {"title": "MP 整理完成（方便）", "value": "transfer"},
                                                                {"title": "Emby 新媒体已添加（精准）", "value": "emby"}
                                                            ],
                                                            'hint': 'MP 事件更方便，Emby Webhook 在媒体库扫描后触发更精准',
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
            "auto_save_config": False,
            "update_now": False,
            "transfer_monitor": True,
            "monitor_source": "transfer",
            "lock_latest_sort": False,
            "cron": "",
            "delay": 60,
            "selected_servers": self._selected_servers,
            "include_libraries": self._include_libraries,
            "all_libraries": self._all_libraries,
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
            "title_config_strict": False,
            "distinguish_same_name_libraries": False,
            "tab": "style-tab",
            "cover_style": "static_1",
            "cover_style_base": "static_1",
            "cover_style_variant": "static",
            "multi_1_blur": True,
            "main_title_font_preset": "chaohei",
            "subtitle_font_preset": "EmblemaOne",
            "custom_text_font_preset": "EmblemaOne",
            "main_title_font_custom": "",
            "subtitle_font_custom": "",
            "custom_text_font_custom": "",
            "main_title_font_size": None,
            "subtitle_font_size": None,
            "blur_size": 50,
            "color_ratio": 0.8,
            "title_scale": 1.0,
            "use_primary": False,
            "main_title_font_offset": None,
            "subtitle_line_spacing": None,
            "resolution": "480p",
            "custom_width": 1920,
            "custom_height": 1080,
            "image_count_mode": "auto",
            "image_count": 9,
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
            "animated_settings": "",
            "clean_images": False,
            "clean_fonts": False,
            "backup_enabled": False,
            "backup_cron": "",
            "backup_path": "",
            "save_recent_covers": True,
            "covers_history_limit_per_library": 10,
            "covers_page_history_limit": 50,
            "history_retention_batches": 30,
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
                    delete_api = f"plugin/YahahaCoverStudio/delete_saved_cover?file={quote(item['path'])}"
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
                                "events": {"click": {"api": "plugin/YahahaCoverStudio/set_page_tab_generate", "method": "post"}},
                            },
                            {
                                "component": "VTab",
                                "props": {"value": "history-tab"},
                                "text": "历史封面",
                                "events": {"click": {"api": "plugin/YahahaCoverStudio/set_page_tab_history", "method": "post"}},
                            },
                            {
                                "component": "VTab",
                                "props": {"value": "clean-tab"},
                                "text": "清理缓存",
                                "events": {"click": {"api": "plugin/YahahaCoverStudio/set_page_tab_clean", "method": "post"}},
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
                                                    "events": {"click": {"api": "plugin/YahahaCoverStudio/toggle_style_variant", "method": "post"}},
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
                                                    "events": {"click": {"api": "plugin/YahahaCoverStudio/generate_now", "method": "post"}},
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
                                                    "events": {"click": {"api": "plugin/YahahaCoverStudio/toggle_style_variant", "method": "post"}},
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
                                                    "events": {"click": {"api": "plugin/YahahaCoverStudio/generate_now", "method": "post"}},
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
                                    "events": {"click": {"api": "plugin/YahahaCoverStudio/clean_images", "method": "post"}},
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
                                    "events": {"click": {"api": "plugin/YahahaCoverStudio/clean_fonts", "method": "post"}},
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
                                    "api": f"plugin/YahahaCoverStudio/select_style_{style['index']}",
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

    def __parse_saved_cover_metadata(self, file_path: Path, mtime_ts: float) -> Dict[str, Any]:
        stem = file_path.stem
        fallback_date = datetime.datetime.fromtimestamp(mtime_ts)
        fallback = {
            "server": "Unknown",
            "library": stem,
            "date": fallback_date.strftime("%Y-%m-%d"),
            "date_label": fallback_date.strftime("%Y-%m-%d %H:%M"),
        }

        match = re.match(r"^(?P<prefix>.+)_(?P<date>\d{8})_(?P<time>\d{6})$", stem)
        if not match:
            return fallback

        prefix = match.group("prefix")
        raw_date = match.group("date")
        raw_time = match.group("time")
        try:
            parsed_date = datetime.datetime.strptime(f"{raw_date}{raw_time}", "%Y%m%d%H%M%S")
            date_value = parsed_date.strftime("%Y-%m-%d")
            date_label = parsed_date.strftime("%Y-%m-%d %H:%M")
        except Exception:
            date_value = fallback["date"]
            date_label = fallback["date_label"]

        server = ""
        library = ""
        server_candidates = []
        try:
            server_candidates.extend([str(item) for item in (self._selected_servers or []) if item])
            server_candidates.extend([str(item) for item in (self._servers or {}).keys() if item])
        except Exception:
            pass
        server_candidates = sorted(set(server_candidates), key=len, reverse=True)
        for candidate in server_candidates:
            safe_candidate = self.__sanitize_filename(candidate)
            if safe_candidate and prefix.startswith(f"{safe_candidate}_"):
                server = safe_candidate
                library = prefix[len(safe_candidate) + 1:]
                break

        if not server:
            parts = prefix.split("_", 1)
            server = parts[0] if parts else "Unknown"
            library = parts[1] if len(parts) > 1 else prefix

        return {
            "server": server or "Unknown",
            "library": library or prefix,
            "date": date_value,
            "date_label": date_label,
        }

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
                            if thumb.mode != 'RGB':
                                thumb = thumb.convert('RGB')
                            buf = BytesIO()
                            thumb.save(buf, format="JPEG", quality=75)
                            image_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                            image_src = f"data:image/jpeg;base64,{image_b64}"
                            
                    except Exception as img_err:
                        logger.debug(f"生成缩略图失败 {file_path}: {img_err}")
                        continue

                    metadata = self.__parse_saved_cover_metadata(file_path, float(stat.st_mtime))

                    items.append(
                        {
                            "name": file_path.name,
                            "path": str(file_path),
                            "mtime_ts": float(stat.st_mtime),
                            "mtime": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                            "size": self.__format_size(stat.st_size),
                            "src": image_src,
                            **metadata,
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
        if self._covers_input:
            result.append(Path(self._covers_input))
        if self._covers_path:
            result.append(Path(self._covers_path))
        data_path = self.get_data_path()
        result.append(data_path / "covers")
        default_output = data_path / "output"
        result.append(default_output)
        result.append(data_path / "history" / "batches")
        result.append(data_path / "stickers")
        if self._font_path:
            result.append(Path(self._font_path))
        result.append(Path(__file__).resolve().parent / "fonts")
        try:
            result.append(Path(__file__).resolve().parents[2] / "fonts")
        except Exception:
            pass
        result.extend(self.__font_search_dirs())
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
        if self._monitor_source != "transfer":
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
        # 安全地获取字体和翻译
        try:
            self.__get_fonts()
        except Exception as e:
            logger.error(f"初始化字体或翻译时出错: {e}")
            # 继续执行，但可能会影响封面生成质量
        self._monitor_sort = 'DateCreated'
        self._current_updating_items.add(update_key)
        try:
            updated = self.__update_library(service, library)
        finally:
            self._monitor_sort = ''
            self._current_updating_items.discard(update_key)
        if updated is CoverUpdateOutcome.UPDATED:
            logger.info(f"媒体库 {server}：{library['Name']} 封面更新成功")
        elif updated is CoverUpdateOutcome.SKIPPED:
            logger.info(f"媒体库 {server}：{library['Name']} 最新入库素材未变化，跳过生成")
        else:
            logger.warning(f"媒体库 {server}：{library['Name']} 封面更新失败")

    @eventmanager.register(EventType.WebhookMessage)
    def update_library_cover_by_webhook(self, event: Event):
        """
        媒体服务器 Webhook 新入库后，更新所在库封面。
        """
        if not self._enabled:
            return
        if not self._transfer_monitor:
            return
        if self._monitor_source != "emby":
            return

        event_info = getattr(event, "event_data", None)
        if not event_info:
            return

        self.__log_webhook_debug(event_info)

        event_type = str(getattr(event_info, "event", "") or "").strip()
        if event_type not in {"library.new", "ItemAdded"}:
            return

        channel = str(getattr(event_info, "channel", "") or "").strip().lower()
        if channel and channel not in {"emby", "jellyfin"}:
            return

        item_id = str(getattr(event_info, "item_id", "") or "").strip()
        item_name = str(getattr(event_info, "item_name", "") or item_id or "新入库媒体").strip()
        if not item_id:
            logger.debug("Webhook 新入库事件缺少 item_id，跳过媒体库封面更新")
            return

        # 开始前清理可能遗留的停止信号，防止阻塞监控
        self._event.clear()

        if self._delay:
            logger.info(f"收到 {channel or '媒体服务器'} 新入库事件，延迟 {self._delay} 秒后开始更新封面")
            time.sleep(int(self._delay))

        resolved = self.__resolve_webhook_library(event_info)
        if not resolved:
            logger.warning(f"找不到 Webhook 媒体 {item_name} 所在媒体库，跳过封面更新")
            return

        server, service, library = resolved
        library_id = library.get("Id") if service.type == "emby" else library.get("ItemId")
        if self._include_libraries and f"{server}-{library_id}" not in self._include_libraries:
            logger.info(f"{server}：{library.get('Name')} 不在列表中，跳过 Webhook 封面更新")
            return

        update_key = (server, item_id)
        if update_key in self._current_updating_items:
            logger.info(f"媒体库 {server}：{library.get('Name')} 的项目 {item_name} 正在更新中，跳过此次 Webhook 更新")
            return

        try:
            self.__get_fonts()
        except Exception as e:
            logger.error(f"初始化字体或翻译时出错: {e}")

        self._monitor_sort = "DateCreated"
        self._current_updating_items.add(update_key)
        try:
            updated = self.__update_library(service, library)
            if updated is CoverUpdateOutcome.UPDATED:
                logger.info(f"媒体库 {server}：{library.get('Name')} Webhook 封面更新成功")
            elif updated is CoverUpdateOutcome.SKIPPED:
                logger.info(f"媒体库 {server}：{library.get('Name')} 最新入库素材未变化，跳过生成")
            else:
                logger.warning(f"媒体库 {server}：{library.get('Name')} Webhook 封面更新失败")
        finally:
            self._monitor_sort = ""
            self._current_updating_items.discard(update_key)

    def __log_webhook_debug(self, event_info):
        """
        临时输出媒体服务器 Webhook 原始内容，便于按真实事件结构调整匹配逻辑。
        """
        try:
            import json

            json_object = getattr(event_info, "json_object", None) or {}
            raw_item = json_object.get("Item") if isinstance(json_object, dict) else {}
            raw_server = json_object.get("Server") if isinstance(json_object, dict) else {}
            summary = {
                "event": getattr(event_info, "event", None),
                "channel": getattr(event_info, "channel", None),
                "server_name": getattr(event_info, "server_name", None) or (raw_server or {}).get("Name"),
                "item_type": getattr(event_info, "item_type", None),
                "media_type": getattr(event_info, "media_type", None),
                "item_name": getattr(event_info, "item_name", None),
                "item_id": getattr(event_info, "item_id", None),
                "item_path": getattr(event_info, "item_path", None) or (raw_item or {}).get("Path"),
                "raw_item_id": (raw_item or {}).get("Id"),
                "raw_parent_id": (raw_item or {}).get("ParentId"),
                "raw_series_id": (raw_item or {}).get("SeriesId"),
                "raw_season_id": (raw_item or {}).get("SeasonId"),
                "raw_type": (raw_item or {}).get("Type"),
            }
            logger.info(
                "【YahahaCoverStudio】Webhook调试摘要："
                + json.dumps(summary, ensure_ascii=False, default=str)
            )
            payload = json.dumps(json_object, ensure_ascii=False, default=str)
            if not payload or payload == "{}":
                logger.info("【YahahaCoverStudio】Webhook调试原始JSON：{}")
                return
            chunk_size = 3500
            for index in range(0, len(payload), chunk_size):
                chunk = payload[index:index + chunk_size]
                part = index // chunk_size + 1
                total = (len(payload) + chunk_size - 1) // chunk_size
                logger.info(f"【YahahaCoverStudio】Webhook调试原始JSON {part}/{total}：{chunk}")
        except Exception as e:
            logger.warning(f"输出 Webhook 调试日志失败: {e}")

    def __resolve_webhook_library(self, event_info) -> Optional[Tuple[str, Any, Dict[str, Any]]]:
        """
        根据 Webhook item 路径定位媒体服务器与媒体库。
        """
        if not self._servers:
            return None

        json_object = getattr(event_info, "json_object", None) or {}
        raw_item = json_object.get("Item") if isinstance(json_object, dict) else {}
        raw_server = json_object.get("Server") if isinstance(json_object, dict) else {}
        item_path = (
            str(getattr(event_info, "item_path", "") or "")
            or str((raw_item or {}).get("Path") or "")
        ).strip()
        server_name = (
            str(getattr(event_info, "server_name", "") or "")
            or str((raw_server or {}).get("Name") or "")
        ).strip()
        channel = str(getattr(event_info, "channel", "") or "").strip().lower()

        candidates: List[Tuple[str, Any]] = []
        for server, service in self._servers.items():
            if channel and getattr(service, "type", "") != channel:
                continue
            if server_name and server_name not in {str(server), str(getattr(service, "name", ""))}:
                continue
            candidates.append((server, service))

        if not candidates:
            for server, service in self._servers.items():
                if channel and getattr(service, "type", "") != channel:
                    continue
                candidates.append((server, service))

        item_id = str(getattr(event_info, "item_id", "") or "").strip()
        for server, service in candidates:
            resolved = self.__find_library_by_item_path(service, item_path)
            if resolved:
                return server, service, resolved

            if item_id:
                try:
                    iteminfo = self.mschain.iteminfo(server=server, item_id=item_id)
                    iteminfo_path = str(getattr(iteminfo, "path", "") or "").strip() if iteminfo else ""
                    resolved = self.__find_library_by_item_path(service, iteminfo_path)
                    if resolved:
                        return server, service, resolved
                except Exception as e:
                    logger.debug(f"通过 item_id 定位 Webhook 媒体库失败: {server}/{item_id}, {e}")

        return None

    def __find_library_by_item_path(self, service, item_path: str) -> Optional[Dict[str, Any]]:
        """
        根据媒体路径匹配媒体库。
        """
        if not item_path:
            return None

        def normalize_path(value: str) -> str:
            return str(value or "").replace("\\", "/").rstrip("/").lower()

        normalized_item_path = normalize_path(item_path)
        if not normalized_item_path:
            return None

        libraries = self.__get_server_libraries(service)
        for library in libraries or []:
            locations = library.get("Locations") or []
            for location in locations:
                normalized_location = normalize_path(str(location or ""))
                if normalized_location and normalized_item_path.startswith(normalized_location):
                    return library
        return None

    
    def __update_all_libraries(self, source: str = "system"):
        """
        更新所有媒体库封面
        """
        if not self._enabled:
            return
        # 所有媒体服务器
        if not self._servers:
            return
        if not self._generation_run_lock.acquire(blocking=False):
            logger.info("【YahahaCoverStudio】已有封面生成任务在执行，跳过重复启动")
            return "封面生成任务正在执行中"
        success_count = 0
        fail_count = 0
        stopped = False
        logger.info("开始检查字体 ...")
        self.__set_generation_state(True, source=source, style=self._cover_style)
        try:
            self.__get_fonts()
        except Exception as e:
            logger.error(f"初始化过程中出错: {e}")
            logger.warning("将尝试继续执行，但可能影响封面生成质量")
        try:
            logger.info("开始更新媒体库封面 ...")
            # 开始前确保停止信号已清除
            self._event.clear()
            update_targets: List[Tuple[str, Any, Dict[str, Any]]] = []
            for server, service in self._servers.items():
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
                libraries = self.__get_server_libraries(service)
                if not libraries:
                    logger.warning(f"服务器 {server} 的媒体库列表获取失败")
                    continue
                for library in libraries:
                    if service.type == 'emby':
                        library_id = library.get("Id")
                    else:
                        library_id = library.get("ItemId")
                    if self._include_libraries and f"{server}-{library_id}" not in self._include_libraries:
                        logger.info(f"{server}：{library['Name']} 不在列表中，跳过更新封面")
                        continue
                    update_targets.append((server, service, library))

            total_count = len(update_targets)
            self.__set_generation_progress(0, total_count, "准备生成")

            for index, (server, service, library) in enumerate(update_targets, start=1):
                if index == 1 or not any(target[0] == server for target in update_targets[:index - 1]):
                    logger.info(f"当前服务器 {server}")
                if self._event.is_set():
                    logger.info("媒体库封面更新服务停止")
                    self._event.clear()
                    stopped = True
                    break
                self.__set_generation_progress(
                    index,
                    total_count,
                    f"{server}：{library.get('Name', '')}",
                )
                outcome = self.__update_library(service, library)
                if outcome is CoverUpdateOutcome.UPDATED:
                    logger.info(f"媒体库 {server}：{library['Name']} 封面更新成功")
                    success_count += 1
                elif outcome is CoverUpdateOutcome.SKIPPED:
                    logger.info(f"媒体库 {server}：{library['Name']} 素材未变化，跳过生成")
                    success_count += 1
                else:
                    logger.warning(f"媒体库 {server}：{library['Name']} 封面更新失败")
                    fail_count += 1

            tips = (
                f"媒体库封面更新任务已停止，成功 {success_count} 个，失败 {fail_count} 个"
                if stopped
                else f"媒体库封面更新任务结束，成功 {success_count} 个，失败 {fail_count} 个"
            )
            logger.info(tips)
            return tips
        finally:
            self.__set_generation_state(False)
            if self._generation_run_lock.locked():
                self._generation_run_lock.release()
                 

    def __update_library(self, service, library):
        library_name = library['Name']
        logger.info(f"媒体库 {service.name}：{library_name} 开始准备更新封面")
        # 自定义图像路径
        image_path = self.__check_custom_image(library_name)
        # 从配置获取标题和背景颜色
        title_result = self.__get_title_from_config(library_name, service.name)
        if len(title_result) == 3:
            title = (title_result[0], title_result[1])
            config_bg_color = title_result[2]
        else:
            title = title_result
            config_bg_color = None
        if image_path:
            logger.info(f"媒体库 {service.name}：{library_name} 从自定义路径获取封面")
            custom_image_input = image_path
            if self._cover_style == "static_custom" and isinstance(image_path, list):
                required_items = self.__get_required_items()
                custom_image_input = image_path[:required_items] if required_items > 1 else image_path[0]
            image_data = self.__generate_image_from_path(service.name, library_name, title, custom_image_input, config_bg_color)
        else:
            image_data = self.__generate_from_server(service, library, title)

        # `True` is the legacy signal from __generate_from_server for a monitor
        # de-duplication skip. It is intentionally not image/Base64 data.
        if image_data is True:
            return CoverUpdateOutcome.SKIPPED
        if isinstance(image_data, str) and image_data:
            return CoverUpdateOutcome.UPDATED if self.__set_library_image(service, library, image_data) else CoverUpdateOutcome.FAILED
        return CoverUpdateOutcome.FAILED

    def __check_custom_image(self, library_name):
        images = self.__collect_library_images_from_root(self._covers_input, library_name)
        return images if images else None

    @memory_efficient_operation
    def __build_preview_local_image_input(self, image_paths: Optional[List[str]]):
        valid_paths = [str(path) for path in (image_paths or []) if path]
        if not valid_paths:
            return None
        if self._cover_style == "static_custom":
            required_items = self.__get_required_items()
            return valid_paths[:required_items] if required_items > 1 else valid_paths[0]
        return valid_paths[0]

    @memory_efficient_operation
    def __generate_image_from_path(self, server, library_name, title, image_path=None, config_bg_color=None, source_root=None):
        logger.info(f"媒体库 {server}：{library_name} 正在生成封面图 ...")

        if isinstance(image_path, (list, tuple)):
            image_paths = [str(path) for path in image_path if path]
            primary_image_path = image_paths[0] if image_paths else None
        elif image_path:
            primary_image_path = str(image_path)
            image_paths = [primary_image_path]
        else:
            primary_image_path = None
            image_paths = []

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
        animated_runtime_settings = self.__get_animated_settings_for_style(self._cover_style) if self._cover_style.startswith("animated") else {}
        try:
            base_main_title_font_size = float(
                animated_runtime_settings.get("main_title_font_size")
                if animated_runtime_settings
                else self._main_title_font_size
            ) if (animated_runtime_settings.get("main_title_font_size") if animated_runtime_settings else self._main_title_font_size) else 170
        except ValueError:
            base_main_title_font_size = 170

        try:
            base_subtitle_font_size = float(
                animated_runtime_settings.get("subtitle_font_size")
                if animated_runtime_settings
                else self._subtitle_font_size
            ) if (animated_runtime_settings.get("subtitle_font_size") if animated_runtime_settings else self._subtitle_font_size) else 75
        except ValueError:
            base_subtitle_font_size = 75

        try:
            title_scale_value = animated_runtime_settings.get("title_scale") if animated_runtime_settings else self._title_scale
            title_scale = float(title_scale_value) if title_scale_value else 1.0
        except (ValueError, TypeError):
            title_scale = 1.0
        if title_scale <= 0:
            title_scale = 1.0
        if self._cover_style.startswith("animated"):
            main_title_font_size = float(base_main_title_font_size) * title_scale
            subtitle_font_size = float(base_subtitle_font_size) * title_scale
        else:
            # 静态风格按当前分辨率缩放
            main_title_font_size = self._resolution_config.get_font_size(base_main_title_font_size) * title_scale
            subtitle_font_size = self._resolution_config.get_font_size(base_subtitle_font_size) * title_scale

        blur_size = animated_runtime_settings.get("blur_size", self._blur_size) if animated_runtime_settings else (self._blur_size or 50)
        color_ratio = animated_runtime_settings.get("color_ratio", self._color_ratio) if animated_runtime_settings else (self._color_ratio or 0.8)

        # 检查字体路径是否有效
        if not self._main_title_font_path or not self._subtitle_font_path:
            logger.error("字体路径未设置或无效，无法生成封面")
            return False

        if self._cover_style == 'static_custom' and not self._custom_text_font_path:
            logger.error("自定义文本字体路径未设置或无效，无法生成自定义封面")
            return False

        # 验证字体文件是否存在
        if not validate_font_file(Path(self._main_title_font_path)):
            logger.error(f"主标题字体文件无效: {self._main_title_font_path}")
            return False

        if not validate_font_file(Path(self._subtitle_font_path)):
            logger.error(f"副标题字体文件无效: {self._subtitle_font_path}")
            return False

        if self._cover_style == 'static_custom' and not validate_font_file(Path(self._custom_text_font_path)):
            logger.error(f"自定义文本字体文件无效: {self._custom_text_font_path}")
            return False

        main_title_font_family = animated_runtime_settings.get("main_title_font_preset", "main_title") if animated_runtime_settings else "main_title"
        subtitle_font_family = animated_runtime_settings.get("subtitle_font_preset", "subtitle") if animated_runtime_settings else "subtitle"
        custom_text_font_family = animated_runtime_settings.get("custom_text_font_preset", "custom_text") if animated_runtime_settings else "custom_text"
        main_title_render_font_path = self.__resolve_template_font_path(main_title_font_family, title[0] if len(title) > 0 else "") or self.__resolve_template_font_path("main_title", title[0] if len(title) > 0 else "")
        subtitle_render_font_path = self.__resolve_template_font_path(subtitle_font_family, title[1] if len(title) > 1 else "") or self.__resolve_template_font_path("subtitle", title[1] if len(title) > 1 else "")
        custom_text_render_font_path = self.__resolve_template_font_path(custom_text_font_family, "")
        preset_font_path = (
            str(main_title_render_font_path or self._main_title_font_path),
            str(subtitle_render_font_path or self._subtitle_font_path),
        )
        custom_font_path = (
            str(main_title_render_font_path or self._main_title_font_path),
            str(subtitle_render_font_path or self._subtitle_font_path),
            str(custom_text_render_font_path or self._custom_text_font_path or self._subtitle_font_path),
        )
        custom_texts = self.__get_custom_texts_from_config(library_name, server)
        static_preset_layout = self.__get_static_preset_layout_config(self._cover_style)
        if static_preset_layout:
            static_preset_layout = self.__layout_with_resolved_custom_texts(static_preset_layout, custom_texts)
        resolved_custom_static_layout = self.__layout_with_resolved_custom_texts(self._custom_static_layout or {}, custom_texts)
        static_template_font_paths = self.__build_template_font_paths(static_preset_layout or {}, title) if static_preset_layout else {}
        custom_template_font_paths = self.__build_template_font_paths(resolved_custom_static_layout or {}, title)
        font_size = (float(main_title_font_size), float(subtitle_font_size))

        main_title_font_offset = float(self._main_title_font_offset or 0)
        title_spacing = float(self._title_spacing or 40) * title_scale
        subtitle_line_spacing = float(self._subtitle_line_spacing or 40) * title_scale
        font_offset = (float(main_title_font_offset), float(title_spacing), float(subtitle_line_spacing))
        # 记录分辨率配置信息
        logger.info(f"当前分辨率配置: {self._resolution_config}")

        # 准备背景颜色配置
        bg_color_config = {
            'mode': self._bg_color_mode,
            'custom_color': self._custom_bg_color,
            'config_color': config_bg_color
        }
        preset_image_input = image_paths if len(image_paths) > 1 else primary_image_path

        # 传递分辨率配置给图像生成函数
        if self._cover_style == 'static_1':
            image_data = create_style_static_1(preset_image_input, title, static_template_font_paths or preset_font_path,
                                                font_size=font_size,
                                                font_offset=font_offset,
                                                blur_size=blur_size,
                                                color_ratio=color_ratio,
                                                resolution_config=self._resolution_config,
                                                bg_color_config=bg_color_config,
                                                layout_config=static_preset_layout)
        elif self._cover_style == 'static_2':
            image_data = create_style_static_2(preset_image_input, title, static_template_font_paths or preset_font_path,
                                                font_size=font_size,
                                                font_offset=font_offset,
                                                blur_size=blur_size,
                                                color_ratio=color_ratio,
                                                resolution_config=self._resolution_config,
                                                bg_color_config=bg_color_config,
                                                layout_config=static_preset_layout)
        elif self._cover_style == 'static_4':
            image_data = create_style_static_4(preset_image_input, title, static_template_font_paths or preset_font_path,
                                                font_size=font_size,
                                                font_offset=font_offset,
                                                blur_size=blur_size,
                                                color_ratio=color_ratio,
                                                resolution_config=self._resolution_config,
                                                bg_color_config=bg_color_config,
                                                layout_config=static_preset_layout)
        elif self._cover_style == 'static_3':
            if image_paths:
                required_items = self.__get_required_items()
                static_3_input = image_paths[:max(1, required_items)]
                logger.info("static_3: 使用已准备素材直接渲染，数量 %s", len(static_3_input))
                image_data = create_style_static_3(static_3_input, title, static_template_font_paths or preset_font_path,
                                                    font_size=font_size,
                                                    font_offset=font_offset,
                                                    is_blur=self._multi_1_blur,
                                                    blur_size=blur_size,
                                                    color_ratio=color_ratio,
                                                    resolution_config=self._resolution_config,
                                                    bg_color_config=bg_color_config,
                                                    layout_config=static_preset_layout)
            else:
                # 使用安全的文件名
                safe_library_name = self.__sanitize_filename(library_name)
                if source_root:
                    library_dir = Path(source_root) / safe_library_name
                elif primary_image_path:
                    library_dir = Path(self._covers_input) / safe_library_name
                else:
                    library_dir = Path(self._covers_path) / safe_library_name
                logger.info(f"static_3: 准备图片目录 {library_dir}")
                if self.prepare_library_images(library_dir, required_items=9):
                    logger.info("static_3: 图片目录准备完成，开始生成封面")
                    image_data = create_style_static_3(library_dir, title, static_template_font_paths or preset_font_path,
                                                        font_size=font_size,
                                                        font_offset=font_offset,
                                                        is_blur=self._multi_1_blur,
                                                        blur_size=blur_size,
                                                        color_ratio=color_ratio,
                                                        resolution_config=self._resolution_config,
                                                        bg_color_config=bg_color_config,
                                                        layout_config=static_preset_layout)
                else:
                    logger.warning(f"static_3: 图片目录准备失败 {library_dir}")
        elif self._cover_style == 'static_custom':
            image_slots = {
                index: path for index, path in enumerate(image_paths, start=1) if path
            }
            if not image_slots and primary_image_path:
                image_slots[1] = primary_image_path

            if not image_slots and self.__get_custom_static_required_items() > 0:
                logger.warning("static_custom: 未找到素材图片，将按布局背景与非素材图层继续生成")

            image_data = create_style_static_custom(
                image_slots=image_slots,
                title=title,
                font_path=custom_template_font_paths or custom_font_path,
                layout_config=resolved_custom_static_layout or {},
                blur_size=blur_size,
                color_ratio=color_ratio,
                resolution_config=self._resolution_config,
                bg_color_config=bg_color_config,
            )
        elif self._cover_style == 'animated_3':
            # 动态封面强制使用 320x180 分辨率以保证性能
            anim_res = '320x180'
            logger.info(f"强制动图生成分辨率为: {anim_res}")
            
            # 动态封面逻辑，类似于 multi_1
            safe_library_name = self.__sanitize_filename(library_name)
            if source_root:
                library_dir = Path(source_root) / safe_library_name
            elif image_path:
                library_dir = Path(self._covers_input) / safe_library_name
            else:
                library_dir = Path(self._covers_path) / safe_library_name
            
            logger.info(f"正在准备库图片目录: {library_dir}")
            if self.prepare_library_images(library_dir, required_items=9):
                logger.info("库图片准备完成，开始调用 create_style_animated_3")
                image_data = create_style_animated_3(library_dir, title, preset_font_path,
                                                    font_size=font_size,
                                                    font_offset=font_offset,
                                                    is_blur=self._multi_1_blur,
                                                    blur_size=blur_size,
                                                    color_ratio=color_ratio,
                                                    resolution_config=self._resolution_config,
                                                    bg_color_config=bg_color_config,
                                                    animation_duration=animated_runtime_settings["animation_duration"],
                                                    animation_scroll=animated_runtime_settings["animation_scroll"],
                                                    animation_fps=animated_runtime_settings["animation_fps"],
                                                    animation_format=animated_runtime_settings["animation_format"],
                                                    animation_resolution=anim_res,
                                                    animation_reduce_colors=animated_runtime_settings["animation_reduce_colors"],
                                                    stop_event=self._event)
        elif self._cover_style == 'animated_1':
            # 动态封面强制使用 320x180 分辨率以保证性能
            anim_res = '320x180'
            logger.info(f"强制动图生成分辨率为: {anim_res}")

            animated_2_image_count = int(animated_runtime_settings["animated_2_image_count"])

            # 动态封面逻辑，类似于 multi_1
            safe_library_name = self.__sanitize_filename(library_name)
            if source_root:
                library_dir = Path(source_root) / safe_library_name
            elif image_path:
                library_dir = Path(self._covers_input) / safe_library_name
            else:
                library_dir = Path(self._covers_path) / safe_library_name

            logger.info(f"正在准备库图片目录: {library_dir}")
            if self.prepare_library_images(library_dir, required_items=animated_2_image_count):
                logger.info("库图片准备完成，开始调用 create_style_animated_1")
                image_data = create_style_animated_1(library_dir, title, preset_font_path,
                                                    font_size=font_size,
                                                    font_offset=font_offset,
                                                    is_blur=self._multi_1_blur,
                                                    blur_size=blur_size,
                                                    color_ratio=color_ratio,
                                                    resolution_config=self._resolution_config,
                                                    bg_color_config=bg_color_config,
                                                    animation_duration=animated_runtime_settings["animation_duration"],
                                                    animation_fps=animated_runtime_settings["animation_fps"],
                                                    animation_format=animated_runtime_settings["animation_format"],
                                                    animation_resolution=anim_res,
                                                    animation_reduce_colors=animated_runtime_settings["animation_reduce_colors"],
                                                    image_count=animated_2_image_count,
                                                    departure_type=animated_runtime_settings["animated_2_departure_type"],
                                                    stop_event=self._event)
        elif self._cover_style == 'animated_2':
            # 动态封面强制使用 320x180 分辨率以保证性能
            anim_res = '320x180'
            logger.info(f"强制动图生成分辨率为: {anim_res}")

            safe_library_name = self.__sanitize_filename(library_name)
            if source_root:
                library_dir = Path(source_root) / safe_library_name
            elif image_path:
                library_dir = Path(self._covers_input) / safe_library_name
            else:
                library_dir = Path(self._covers_path) / safe_library_name

            logger.info(f"正在准备库图片目录: {library_dir}")
            if self.prepare_library_images(library_dir, required_items=9):
                logger.info("库图片准备完成，开始调用 create_style_animated_2")
                image_data = create_style_animated_2(library_dir, title, preset_font_path,
                                                    font_size=font_size,
                                                    font_offset=font_offset,
                                                    is_blur=self._multi_1_blur,
                                                    blur_size=blur_size,
                                                    color_ratio=color_ratio,
                                                    resolution_config=self._resolution_config,
                                                    bg_color_config=bg_color_config,
                                                    animation_duration=animated_runtime_settings["animation_duration"],
                                                    animation_fps=animated_runtime_settings["animation_fps"],
                                                    animation_format=animated_runtime_settings["animation_format"],
                                                    animation_resolution=anim_res,
                                                    animation_reduce_colors=animated_runtime_settings["animation_reduce_colors"],
                                                    image_count=int(animated_runtime_settings["animated_2_image_count"]),
                                                    stop_event=self._event)
        elif self._cover_style == 'animated_4':
            anim_res = '320x180'
            logger.info(f"强制动图生成分辨率为: {anim_res}")

            animated_2_image_count = int(animated_runtime_settings["animated_2_image_count"])

            safe_library_name = self.__sanitize_filename(library_name)
            if source_root:
                library_dir = Path(source_root) / safe_library_name
            elif image_path:
                library_dir = Path(self._covers_input) / safe_library_name
            else:
                library_dir = Path(self._covers_path) / safe_library_name

            logger.info(f"正在准备库图片目录: {library_dir}")
            if self.prepare_library_images(library_dir, required_items=animated_2_image_count):
                logger.info("库图片准备完成，开始调用 create_style_animated_4")
                image_data = create_style_animated_4(library_dir, title, preset_font_path,
                                                    font_size=font_size,
                                                    font_offset=font_offset,
                                                    is_blur=self._multi_1_blur,
                                                    blur_size=blur_size,
                                                    color_ratio=color_ratio,
                                                    resolution_config=self._resolution_config,
                                                    bg_color_config=bg_color_config,
                                                    animation_duration=animated_runtime_settings["animation_duration"],
                                                    animation_fps=animated_runtime_settings["animation_fps"],
                                                    animation_format=animated_runtime_settings["animation_format"],
                                                    animation_resolution=anim_res,
                                                    animation_reduce_colors=animated_runtime_settings["animation_reduce_colors"],
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
            if self.__should_skip_unchanged_latest_item(service, library, items[0]):
                return True
            if self.__is_single_image_style():
                return self.__update_single_image(service, library, title, items[0])
            else:
                return self.__update_grid_image(service, library, title, items[:required_items])
        else:
            logger.warning(f"媒体库 {service.name}：{library['Name']} 无法找到有效的图片项目 (筛选类型: {include_types})")
            return False

    def __should_skip_unchanged_latest_item(self, service, library, first_item: Optional[Dict[str, Any]]) -> bool:
        """
        最新入库排序时，如果首张素材与上次生成时记录的首张素材一致，则跳过生成。
        """
        if not first_item:
            return False
        # Manual and scheduled runs always follow their configured sort and must
        # remain reproducible. Only monitor-triggered work is latest-item deduped.
        if not self._monitor_sort:
            return False

        if service.type == "emby":
            library_id = library.get("Id")
        else:
            library_id = library.get("ItemId")
        if not library_id:
            return False

        first_item_id = str(self.__get_item_id(first_item) or "").strip()
        if not first_item_id:
            return False

        latest_item = self.__get_latest_cover_history_item(service.name, library_id)
        latest_item_id = str((latest_item or {}).get("item_id") or "").strip()
        if latest_item_id and latest_item_id == first_item_id:
            logger.info(
                "媒体库 %s：%s 最新入库首张素材未变化（item_id=%s），跳过封面生成",
                service.name,
                library.get("Name"),
                first_item_id,
            )
            return True
        return False

    def __get_latest_cover_history_item(self, server: str, library_id: Any) -> Optional[Dict[str, Any]]:
        """
        返回指定媒体库最近一次用于生成封面的首张素材记录。
        """
        history = self.get_data('cover_history') or []
        library_id = str(library_id)
        candidates = [
            item for item in history
            if item.get("server") == server and str(item.get("library_id")) == library_id
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda item: float(item.get("timestamp") or 0))
        
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
        title_result = self.__get_title_from_config(library['Name'], service.name)
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
        """更新多图封面"""
        logger.info(f"媒体库 {service.name}：{library['Name']} 从媒体项获取图片")

        image_paths = []

        updated_item_ids = []
        download_jobs = []
        for i, item in enumerate(items):
            image_url = self.__get_image_url(item)
            if image_url:
                download_jobs.append((i, item, image_url))

        download_start = time.time()
        if download_jobs:
            max_workers = max(1, min(6, len(download_jobs)))
            results: List[Tuple[int, Optional[str], str]] = []
            logger.info(
                "媒体库 %s：%s 开始并发准备 %s 张素材（workers=%s）",
                service.name,
                library["Name"],
                len(download_jobs),
                max_workers,
            )
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_map = {
                    executor.submit(self.__download_image, service, image_url, library["Name"], index + 1): (index, item)
                    for index, item, image_url in download_jobs
                }
                for future in as_completed(future_map):
                    if self._event.is_set():
                        logger.info("检测到停止信号，中断图片下载 ...")
                        return False
                    index, item = future_map[future]
                    try:
                        image_path = future.result()
                    except Exception as err:
                        logger.warning("媒体库 %s：%s 第 %s 张素材下载异常: %s", service.name, library["Name"], index + 1, err)
                        image_path = None
                    results.append((index, image_path, self.__get_item_id(item)))
            for _, image_path, item_id in sorted(results, key=lambda value: value[0]):
                if image_path:
                    image_paths.append(image_path)
                    updated_item_ids.append(item_id)
        logger.info(
            "媒体库 %s：%s 素材准备完成，成功 %s/%s，耗时 %.2fs",
            service.name,
            library["Name"],
            len(image_paths),
            len(download_jobs),
            time.time() - download_start,
        )

        if len(image_paths) < 1:
            return False

        # 生成多图封面
        # 从配置获取背景颜色
        title_result = self.__get_title_from_config(library['Name'], service.name)
        config_bg_color = title_result[2] if len(title_result) == 3 else None
        image_input = image_paths if (
            self._cover_style == 'static_custom'
            or self._cover_style == 'static_3'
            or (self._cover_style in ['static_1', 'static_2', 'static_4'] and self.__get_required_items() > 1)
        ) else None
        render_start = time.time()
        image_data = self.__generate_image_from_path(service.name, library['Name'], title, image_input, config_bg_color)
        logger.info("媒体库 %s：%s 静态封面渲染完成，耗时 %.2fs", service.name, library["Name"], time.time() - render_start)
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
    
    def __parse_title_config(self, yaml_str: str, strict: Optional[bool] = None) -> Tuple[Dict[str, Any], List[str], str]:
        errors: List[str] = []
        strict_mode = self._title_config_strict if strict is None else bool(strict)
        raw_yaml = str(yaml_str or "")
        if not raw_yaml.strip():
            return {}, [], ""

        try:
            known_entry_keys = {
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

            if strict_mode:
                processed_yaml = raw_yaml
                if "：" in raw_yaml:
                    errors.append("严格模式不允许中文冒号，请使用英文冒号 ':'。")
                if "\t" in raw_yaml:
                    errors.append("严格模式不允许制表符缩进，请使用空格。")
            else:
                yaml_str = raw_yaml.replace("：", ":")
                yaml_str = yaml_str.replace("\t", "  ")
                lines = yaml_str.split('\n')
                processed_lines = []
                current_library_open = False
                current_texts_open = False
                for line in lines:
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#'):
                        processed_lines.append(line)
                        continue
                    if ':' not in line:
                        if current_library_open and not line[:1].isspace() and stripped.startswith("-"):
                            processed_lines.append(f"  {line}")
                        else:
                            processed_lines.append(line)
                        continue

                    match = re.match(r'^(\s*)(-\s*)?([^:]+?):(.*)$', line)
                    if not match:
                        processed_lines.append(line)
                        continue

                    indent, list_marker, key_part, value_part = match.groups()
                    key_part = key_part.strip()
                    list_marker = list_marker or ""
                    key_lookup = key_part.strip('"\'').strip()

                    # 容错：用户常把子字段写成顶格。当前面已经有媒体库键时，
                    # 将 title/subtitle/texts 以及 texts 下的自定义键自动缩进。
                    if not indent and current_library_open:
                        if list_marker:
                            indent = "  "
                        elif key_lookup in known_entry_keys:
                            indent = "  "
                        elif current_texts_open and str(value_part or "").strip():
                            indent = "    "

                    # 如果键不是以引号开头，且包含数字或特殊字符，则添加引号。
                    # 注意保留原缩进和列表标记，避免把 "- texts:" 误处理成键名。
                    if key_part and not (key_part.startswith('"') or key_part.startswith("'")):
                        if (
                            key_part[0].isdigit()
                            or any(char in key_part for char in [' ', '.', '(', ')', '[', ']'])
                        ):
                            key_part = f'"{key_part}"'

                    if value_part and not value_part.startswith((" ", "\t", "\n")):
                        value_part = f" {value_part.lstrip()}"

                    processed_lines.append(f"{indent}{list_marker}{key_part}:{value_part}")

                    effective_indent_len = len(indent)
                    if not list_marker and effective_indent_len == 0 and key_lookup not in known_entry_keys:
                        current_library_open = True
                        current_texts_open = False
                    elif current_library_open:
                        if key_lookup == "texts":
                            current_texts_open = True
                        elif effective_indent_len <= 2 and key_lookup in known_entry_keys:
                            current_texts_open = False

                processed_yaml = '\n'.join(processed_lines)

            preview_limit = 800
            flat_yaml = " ".join(part.strip() for part in processed_yaml.splitlines() if part.strip())
            if len(flat_yaml) > preview_limit:
                logger.debug(f"处理后的YAML(扁平, 前{preview_limit}字): {flat_yaml[:preview_limit]}... (已截断)")
            else:
                logger.debug(f"处理后的YAML(扁平): {flat_yaml}")

            title_config = yaml.safe_load(processed_yaml) or {}
            if not isinstance(title_config, dict):
                return {}, ["标题配置根节点必须是 YAML 对象。"], processed_yaml
            filtered = {}

            def normalize_texts(raw_texts: Any) -> Dict[str, str]:
                if not isinstance(raw_texts, dict):
                    return {}
                return {
                    str(text_key).strip(): str(text_val)
                    for text_key, text_val in raw_texts.items()
                    if str(text_key).strip() and text_val is not None
                }

            def collect_extra_texts(raw_map: Dict[str, Any]) -> Dict[str, str]:
                texts = normalize_texts(raw_map.get("texts"))
                for text_key, text_val in raw_map.items():
                    normalized_text_key = str(text_key).strip()
                    if normalized_text_key in known_entry_keys:
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
                    entry = [value[0], value[1]]
                    bg_color = None
                    texts: Dict[str, str] = {}
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
                # 忽略格式不正确的项
                errors.append(
                    f"标题配置项格式不正确: {normalized_key}。请使用列表格式 [- 主标题, - 副标题] 或字典格式 title/subtitle。"
                )
                continue

            logger.debug(f"解析后的配置: {filtered}")
            if raw_yaml.strip() and not filtered:
                errors.append("没有解析到任何有效媒体库配置。")
            return filtered, errors, processed_yaml
        except Exception as e:
            return {}, [f"YAML 解析失败: {e}"], raw_yaml

    def __load_title_config(self, yaml_str: str, strict: Optional[bool] = None) -> dict:
        parsed, errors, _ = self.__parse_title_config(yaml_str, strict=strict)
        for error in errors:
            logger.warning(f"标题配置错误: {error}")
        return parsed

    def __find_title_config_values(self, library_name: Any, server_name: Any = "") -> Optional[List[Any]]:
        raw_library_name = str(library_name or "").strip()
        title_config = self._current_config or (self.__load_title_config(self._title_config) if self._title_config else {})
        if not raw_library_name or not isinstance(title_config, dict):
            return None

        def compact(value: Any) -> str:
            return re.sub(r"[^\w\u4e00-\u9fff]+", "", str(value or ""), flags=re.UNICODE).casefold()

        if self._distinguish_same_name_libraries and str(server_name or "").strip():
            server_key = compact(server_name)
            library_key = compact(raw_library_name)
            for config_key, config_values in title_config.items():
                candidate = compact(config_key)
                if server_key and library_key and server_key in candidate and library_key in candidate:
                    return config_values if isinstance(config_values, list) else None

        library_key = compact(raw_library_name)
        for config_key, config_values in title_config.items():
            if compact(config_key) == library_key:
                return config_values if isinstance(config_values, list) else None
        return None

    def __get_title_from_config(self, library_name, server_name: Any = ""):
        """
        从 yaml 配置中获取媒体库的主副标题和背景颜色
        """
        raw_library_name = str(library_name or "")
        normalized_library_name = raw_library_name.strip()
        zh_title = normalized_library_name
        en_title = ''
        bg_color = None
        title_config = {}
        if self._current_config:
            title_config = self._current_config
        elif self._title_config:
            title_config = self.__load_title_config(self._title_config)

        # 添加调试信息
        logger.debug(f"查找媒体库名称: '{normalized_library_name}' (原始值: {library_name}, 类型: {type(library_name)})")
        logger.debug(f"可用的配置键: {list(title_config.keys())}")

        if not normalized_library_name:
            logger.debug("媒体库名称为空，使用空标题")
            return (zh_title, en_title, bg_color)

        config_values = self.__find_title_config_values(normalized_library_name, server_name)
        if isinstance(config_values, list):
            zh_title = config_values[0] if config_values else normalized_library_name
            en_title = config_values[1] if len(config_values) > 1 else ''
            bg_color = config_values[2] if len(config_values) > 2 and isinstance(config_values[2], str) else None
        else:
            logger.debug(f"未找到媒体库 '{normalized_library_name}' 的配置，回退为媒体库名")

        return (zh_title, en_title, bg_color)

    def __get_custom_texts_from_config(self, library_name, server_name: Any = "") -> Dict[str, str]:
        raw_library_name = str(library_name or "")
        normalized_library_name = raw_library_name.strip()
        title_config = {}
        if self._current_config:
            title_config = self._current_config
        elif self._title_config:
            title_config = self.__load_title_config(self._title_config)

        matched_values = self.__find_title_config_values(normalized_library_name, server_name)
        if not isinstance(matched_values, list):
            return {}

        for item in matched_values[2:]:
            if not isinstance(item, dict):
                continue
            raw_texts = item.get("texts")
            if isinstance(raw_texts, dict):
                return {
                    str(key).strip(): str(value)
                    for key, value in raw_texts.items()
                    if str(key).strip()
                }
        return {}
    
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
                        "value": f"{server}-{library_id}",
                        "server": str(server),
                        "server_id": str(server),
                        "library_id": str(library_id),
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
            image_key = self.__build_image_key(imageurl) or str(imageurl or "")
            cache_key = hashlib.sha256(image_key.encode("utf-8")).hexdigest()
            cache_meta_path = f"{filepath}.urlhash"

            # 如果同一张服务端图片已经下载过，直接复用本地素材，避免静态封面每次重复拉取。
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0 and os.path.exists(cache_meta_path):
                try:
                    if Path(cache_meta_path).read_text(encoding="utf-8").strip() == cache_key:
                        logger.debug("复用已缓存图片: %s", filepath)
                        return filepath
                except Exception as cache_err:
                    logger.debug("读取图片缓存标记失败，将重新下载: %s", cache_err)

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
                    try:
                        Path(cache_meta_path).write_text(cache_key, encoding="utf-8")
                    except Exception as cache_err:
                        logger.debug("写入图片缓存标记失败: %s", cache_err)
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

            image_bytes = None
            if self._save_recent_covers:
                try:
                    image_bytes = base64.b64decode(image_base64)
                except Exception as save_err:
                    logger.error(f"保存发送前图片失败: {str(save_err)}")
            
            res = service.instance.post_data(
                url=url,
                data=image_base64,
                headers={
                    "Content-Type": content_type
                }
            )
            
            uploaded = bool(res and res.status_code in [200, 204])
            if image_bytes:
                self.__save_image_to_local(image_bytes, service.name, library['Name'], extension)
                if self._history_batch:
                    try:
                        library_id = library.get("Id") if service.type == "emby" else library.get("ItemId")
                        HistoryStore(self.get_data_path()).add_bytes(self._history_batch, image_bytes, service.name, service.name, str(library_id or library["Name"]), library["Name"], self._cover_style, extension, uploaded)
                    except Exception as history_err:
                        logger.error(f"【YahahaCoverStudio】记录历史批次失败: {history_err}", exc_info=True)
            if uploaded:
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

        _, _, main_title_font_preset_paths, subtitle_font_preset_paths = self.__get_font_presets()

        if not self._main_title_font_preset:
            self._main_title_font_preset = "chaohei"

        default_font_url = self.__builtin_font_urls()
        default_main_title_font_url = default_font_url.get(self._main_title_font_preset, "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/chaohei.ttf")

        if not self._subtitle_font_preset:
            self._subtitle_font_preset = "EmblemaOne"

        if not self._custom_text_font_preset:
            self._custom_text_font_preset = self._subtitle_font_preset or "EmblemaOne"

        default_subtitle_font_url = default_font_url.get(self._subtitle_font_preset, "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/EmblemaOne.woff2")
        default_custom_text_font_url = default_font_url.get(self._custom_text_font_preset, default_subtitle_font_url)
        
        log_prefix = "默认"
        main_title_font_custom_type = detect_string_type(self._main_title_font_custom)
        subtitle_font_custom_type = detect_string_type(self._subtitle_font_custom)
        custom_text_font_custom_type = detect_string_type(self._custom_text_font_custom)
        current_main_title_font_url = self._main_title_font_custom if main_title_font_custom_type == 'url' else default_main_title_font_url
        current_subtitle_font_url = self._subtitle_font_custom if subtitle_font_custom_type == 'url' else default_subtitle_font_url
        current_custom_text_font_url = self._custom_text_font_custom if custom_text_font_custom_type == 'url' else default_custom_text_font_url
        main_title_font_local_path_config = self._main_title_font_custom if main_title_font_custom_type == 'path' else main_title_font_preset_paths.get(self._main_title_font_preset)
        subtitle_font_local_path_config = self._subtitle_font_custom if subtitle_font_custom_type == 'path' else subtitle_font_preset_paths.get(self._subtitle_font_preset)
        custom_text_font_local_path_config = self._custom_text_font_custom if custom_text_font_custom_type == 'path' else subtitle_font_preset_paths.get(self._custom_text_font_preset)
        main_title_custom_preset_path = self.__resolve_custom_font_path(self._main_title_font_preset)
        subtitle_custom_preset_path = self.__resolve_custom_font_path(self._subtitle_font_preset)
        custom_text_custom_preset_path = self.__resolve_custom_font_path(self._custom_text_font_preset)
        if main_title_custom_preset_path:
            main_title_font_local_path_config = str(main_title_custom_preset_path)
        if subtitle_custom_preset_path:
            subtitle_font_local_path_config = str(subtitle_custom_preset_path)
        if custom_text_custom_preset_path:
            custom_text_font_local_path_config = str(custom_text_custom_preset_path)

        downloaded_main_title_font_base = f"{self._main_title_font_preset}_custom" if main_title_font_custom_type == 'url' else self._main_title_font_preset
        downloaded_subtitle_font_base = f"{self._subtitle_font_preset}_custom" if subtitle_font_custom_type == 'url' else self._subtitle_font_preset
        downloaded_custom_text_font_base = f"{self._custom_text_font_preset}_custom" if custom_text_font_custom_type == 'url' else self._custom_text_font_preset
        main_title_font_hash_file_name = f"{downloaded_main_title_font_base}_url.hash"
        subtitle_font_hash_file_name = f"{downloaded_subtitle_font_base}_url.hash"
        custom_text_font_hash_file_name = f"{downloaded_custom_text_font_base}_url.hash"
        final_main_title_font_path_attr = "_main_title_font_path"
        final_subtitle_font_path_attr = "_subtitle_font_path"
        final_custom_text_font_path_attr = "_custom_text_font_path"

        logger.info(f"当前主标题字体URL: {current_main_title_font_url} (本地路径: {main_title_font_local_path_config})")

        active_fonts_to_process = [
            {
                "lang": "主标题",
                "url": current_main_title_font_url,
                "local_path_config": main_title_font_local_path_config,
                "download_base_name": downloaded_main_title_font_base,
                "hash_file_name": main_title_font_hash_file_name,
                "final_attr_name": final_main_title_font_path_attr,
                "fallback_ext": ".ttf"
            },
            {
                "lang": "副标题",
                "url": current_subtitle_font_url,
                "local_path_config": subtitle_font_local_path_config,
                "download_base_name": downloaded_subtitle_font_base,
                "hash_file_name": subtitle_font_hash_file_name,
                "final_attr_name": final_subtitle_font_path_attr,
                "fallback_ext": ".ttf"
            },
            {
                "lang": "自定义文本",
                "url": current_custom_text_font_url,
                "local_path_config": custom_text_font_local_path_config,
                "download_base_name": downloaded_custom_text_font_base,
                "hash_file_name": custom_text_font_hash_file_name,
                "final_attr_name": final_custom_text_font_path_attr,
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

            if not current_font_path:
                fallback_font_path = self.__find_system_font_fallback(lang)
                if fallback_font_path:
                    current_font_path = Path(fallback_font_path)
                    using_local_font = True
            
            # 安全设置字体路径
            if current_font_path and current_font_path.exists():
                setattr(self, final_attr, current_font_path)
                if using_local_font and str(current_font_path).startswith("/usr/share/fonts"):
                    status_log = '(系统回退)'
                else:
                    status_log = '(本地路径)' if using_local_font else '(已下载/缓存)'
                logger.info(f"{log_prefix}{lang}字体最终路径: {getattr(self,final_attr)} {status_log}")
            else:
                # 字体获取失败，设置为None并记录错误
                setattr(self, final_attr, None)
                logger.error(f"{log_prefix}{lang}字体获取失败，这可能导致封面生成失败")

        # 检查是否所有必要的字体都已获取
        if not self._main_title_font_path or not self._subtitle_font_path or not self._custom_text_font_path:
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

            if not self.__ensure_fonts_ready(force_refresh=False):
                logger.warning("字体检查未通过，自动恢复失败")
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
