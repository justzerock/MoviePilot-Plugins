import base64
import datetime
import hashlib
import os
import re
import threading
import time
import shutil
import random
from pathlib import Path
from urllib.parse import urlparse
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
from app.helper.mediaserver import MediaServerHelper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import MediaInfo
from app.schemas.types import EventType
from app.schemas import ServiceInfo
from app.utils.http import RequestUtils
from app.utils.url import UrlUtils
from app.plugins.mediacovergenerator.style_single_1 import create_style_single_1
from app.plugins.mediacovergenerator.style_single_2 import create_style_single_2
from app.plugins.mediacovergenerator.style_multi_1  import create_style_multi_1
from app.plugins.mediacovergenerator.static.single_1 import single_1
from app.plugins.mediacovergenerator.static.single_2 import single_2
from app.plugins.mediacovergenerator.static.multi_1  import multi_1


class MediaCoverGenerator(_PluginBase):
    # 插件名称
    plugin_name = "媒体库封面生成"
    # 插件描述
    plugin_desc = "自动生成媒体库封面，支持 Emby，Jellyfin"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/icons/emby.png"
    # 插件版本
    plugin_version = "0.8.3"
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
    _onlyonce = False
    _transfer_monitor = True
    _cron = None
    _delay = 60
    _servers = None
    _selected_servers = []
    _all_libraries = []
    _exclude_libraries = []
    _sort_by = 'Random'
    _monitor_sort = ''
    _covers_output = ''
    _covers_input = ''
    _zh_font_url = ''
    _en_font_url = ''
    _zh_font_path = ''
    _en_font_path = ''
    _zh_font_path_local = ''
    _en_font_path_local = ''
    _zh_font_path_multi_1_local = ''
    _en_font_path_multi_1_local = ''
    _zh_font_url_multi_1 = ''
    _en_font_url_multi_1 = ''
    _zh_font_path_multi_1 = ''
    _en_font_path_multi_1 = ''
    _multi_1_use_main_font = False
    _title_config = ''
    _cover_style = 'single_1'
    _font_path = ''
    _covers_path = ''
    _tab = 'style-tab'
    _multi_1_blur = False
    _zh_font_size = 1
    _en_font_size = 1
    _zh_font_size_multi_1 = 1
    _en_font_size_multi_1 = 1
    _blur_size = 50
    _blur_size_multi_1 = 50
    _color_ratio = 0.8
    _color_ratio_multi_1 = 0.8

    def __init__(self):
        super().__init__()

    def init_plugin(self, config: dict = None):
        self.mschain = MediaServerChain()
        self.mediaserver_helper = MediaServerHelper()   
        data_path = self.get_data_path()
        (data_path / 'fonts').mkdir(parents=True, exist_ok=True)
        (data_path / 'covers').mkdir(parents=True, exist_ok=True)
        if config:
            self._enabled = config.get("enabled")
            self._onlyonce = config.get("onlyonce")
            self._transfer_monitor = config.get("transfer_monitor")
            self._cron = config.get("cron")
            self._delay = config.get("delay") or 60
            self._selected_servers = config.get("selected_servers") or []
            self._exclude_libraries = config.get("exclude_libraries") or []
            # self._all_libraries = config.get("all_libraries") or []
            self._sort_by = config.get("sort_by") or 'Random'
            self._covers_output = config.get("covers_output") or ''
            self._covers_input = config.get("covers_input") or ''
            self._title_config = config.get("title_config") or ''
            self._zh_font_url = config.get("zh_font_url") or ""
            self._en_font_url = config.get("en_font_url") or ""
            self._zh_font_path = config.get("zh_font_path")
            self._en_font_path = config.get("en_font_path")
            self._cover_style = config.get("cover_style") or "single_1"
            self._tab = config.get("tab") or 'style-tab'
            self._multi_1_blur = config.get("multi_1_blur")
            self._zh_font_url_multi_1 = config.get("zh_font_url_multi_1")
            self._en_font_url_multi_1 = config.get("en_font_url_multi_1")
            self._zh_font_path_multi_1 = config.get("zh_font_path_multi_1")
            self._en_font_path_multi_1 = config.get("en_font_path_multi_1")
            self._multi_1_use_main_font = config.get("multi_1_use_main_font")
            self._zh_font_path_local = config.get("zh_font_path_local")
            self._en_font_path_local = config.get("en_font_path_local")
            self._zh_font_path_multi_1_local = config.get("zh_font_path_multi_1_local")
            self._en_font_path_multi_1_local = config.get("en_font_path_multi_1_local")
            self._font_path = config.get("font_path") or data_path / 'fonts'
            self._covers_path = config.get("covers_path") or data_path / 'covers'
            self._zh_font_size = config.get("zh_font_size") or 1
            self._en_font_size = config.get("en_font_size") or 1
            self._zh_font_size_multi_1 = config.get("zh_font_size_multi_1") or 1
            self._en_font_size_multi_1 = config.get("en_font_size_multi_1") or 1
            self._blur_size = config.get("blur_size") or 50
            self._blur_size_multi_1 = config.get("blur_size_multi_1") or 50
            self._color_ratio = config.get("color_ratio") or 0.8
            self._color_ratio_multi_1 = config.get("color_ratio_multi_1") or 0.8

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

        # 启动服务
        if self._onlyonce:
            self._scheduler = BackgroundScheduler(timezone=settings.TZ)
            self._scheduler.add_job(func=self.__update_all_libraries, trigger='date',
                                    run_date=datetime.datetime.now(
                                        tz=pytz.timezone(settings.TZ)) + datetime.timedelta(seconds=3)
                                    )
            logger.info(f"媒体库封面更新服务启动，立即运行一次")
            # 关闭一次性开关
            self._onlyonce = False
            # 保存配置
            self.__update_config()
            # 启动服务
            if self._scheduler.get_jobs():
                self._scheduler.print_jobs()
                self._scheduler.start()

    def __update_config(self):
        """
        更新配置
        """
        self.update_config({
            "enabled": self._enabled,
            "onlyonce": self._onlyonce,
            "transfer_monitor": self._transfer_monitor,
            "cron": self._cron,
            "delay": self._delay,
            "selected_servers": self._selected_servers,
            "exclude_libraries": self._exclude_libraries,
            "all_libraries": self._all_libraries,
            "sort_by": self._sort_by,
            "covers_output": self._covers_output,
            "covers_input": self._covers_input,
            "title_config": self._title_config,
            "zh_font_url": self._zh_font_url,
            "en_font_url": self._en_font_url,
            "zh_font_path": self._zh_font_path,
            "en_font_path": self._en_font_path,
            "cover_style": self._cover_style,
            "tab": self._tab,
            "multi_1_blur": self._multi_1_blur,
            "zh_font_url_multi_1": self._zh_font_url_multi_1,
            "en_font_url_multi_1": self._en_font_url_multi_1,
            "zh_font_path_multi_1": self._zh_font_path_multi_1,
            "en_font_path_multi_1": self._en_font_path_multi_1,
            "multi_1_use_main_font": self._multi_1_use_main_font,
            "zh_font_path_local": self._zh_font_path_local,
            "en_font_path_local": self._en_font_path_local,
            "zh_font_path_multi_1_local": self._zh_font_path_multi_1_local,
            "en_font_path_multi_1_local": self._en_font_path_multi_1_local,
            "font_path": self._font_path,
            "covers_path": self._covers_path,
            "zh_font_size": self._zh_font_size,
            "en_font_size": self._en_font_size,
            "zh_font_size_multi_1": self._zh_font_size_multi_1,
            "en_font_size_multi_1": self._en_font_size_multi_1,
            "blur_size": self._blur_size,
            "blur_size_multi_1": self._blur_size_multi_1,
            "color_ratio": self._color_ratio,
            "color_ratio_multi_1": self._color_ratio_multi_1
        })

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

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
        pass

    def get_service(self) -> List[Dict[str, Any]]:
        """
        注册插件公共服务
        """
        if self._enabled and self._cron:
            return [{
                "id": "MediaCoverGenerator",
                "name": "媒体库封面更新服务",
                "trigger": CronTrigger.from_crontab(self._cron),
                "func": self.__update_all_libraries,
                "kwargs": {}
            }]

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面
        """
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
                                'component': 'VAlert',
                                'props': {
                                    'type': 'info',
                                    'variant': 'tonal',
                                    'text': '未配置的媒体库将默认使用媒体库名称作为封面中文标题，无副标题'
                                }
                            }
                        ]
                    },
                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12
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
- 中文标题
- 英文标题'''
                                }
                            }
                        ]
                    }
                ]
            },
        ]

        # 字体与封面目录标签
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
                            'md': 6
                        },
                        'content': [
                            {
                                'component': 'VTextField',
                                'props': {
                                    'model': 'covers_input',
                                    'label': '自定义图片目录（可选）',
                                    'prependInnerIcon': 'mdi-file-image',
                                    'hint': '使用目录内图片生成封面',
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
                                    'model': 'covers_output',
                                    'label': '封面另存目录（可选）',
                                    'prependInnerIcon': 'mdi-file-image',
                                    'hint': '生成的封面在此另存一份',
                                    'persistentHint': True
                                }
                            }
                        ]
                    }
                ]
            },
            
        ]
        # 字体与封面目录标签
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
                                    'text': '若字体无法下载，建议设置：系统 -> 高级设置 -> 网络 -> GitHub加速代理，或者手动下载，填写本地路径'
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
                                    'model': 'zh_font_path_local',
                                    'label': '中文字体（本地路径）',
                                    'prependInnerIcon': 'mdi-ideogram-cjk',
                                    'placeholder': '留空使用预设字体',
                                    'hint': '字体本地路径，优先使用',
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
                                    'model': 'en_font_path_local',
                                    'label': '英文字体（本地路径）',
                                    'prependInnerIcon': 'mdi-format-font',
                                    'placeholder': '留空使用预设字体',
                                    'hint': '字体本地路径，优先使用',
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
                                    'model': 'zh_font_url',
                                    'label': '中文字体（下载链接）',
                                    'prependInnerIcon': 'mdi-link',
                                    'placeholder': '留空使用预设字体',
                                    'hint': '下载链接，优先级低于本地路径',
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
                                    'model': 'en_font_url',
                                    'label': '英文字体（下载链接）',
                                    'prependInnerIcon': 'mdi-link',
                                    'placeholder': '留空使用预设字体',
                                    'hint': '下载链接，优先级低于本地路径',
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
                                    'label': '中文字体大小比例',
                                    'prependInnerIcon': 'mdi-format-size',
                                    'placeholder': '留空使用预设尺寸',
                                    'hint': '根据自己喜好设置，值为相对原本尺寸的比例，1为原本大小',
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
                                    'label': '英文字体大小比例',
                                    'prependInnerIcon': 'mdi-format-size',
                                    'placeholder': '留空使用预设尺寸',
                                    'hint': '根据自己喜好设置，值为相对原本尺寸的比例，1为原本大小',
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
                    
                ]
            },
            
        ]

        styles = [
            {
                "title": "单图 1",
                "value": "single_1",
                "src": single_1
            },
            {
                "title": "单图 2",
                "value": "single_2",
                "src": single_2
            },
            {
                "title": "多图 1",
                "value": "multi_1",
                "src": multi_1
            }
        ]

        style_content = []

        for style in styles:
            style_content.append(
                {
                    'component': 'VCol',
                    'props': {
                        'cols': 12,
                        'md': 3,
                    },
                    'content': [
                        {
                            "component": "VCard",
                            "props": {
                            },
                            "content": [
                                {
                                    "component": "VImg",
                                    "props": {
                                        "src": style.get("src"),
                                        "aspect-ratio": "16/9",
                                        "cover": True,
                                    }
                                },  
                                {
                                    "component": "VCardTitle",
                                    # "text": style.get("title"),
                                    "props": {
                                        "class": "text-secondary text-h6 text-center bg-surface-light"
                                    },
                                    "content": [
                                        {
                                            "component": "VRadio",
                                            "props": {
                                                "color": "primary",
                                                "value": style.get("value"),
                                                "label": style.get("title"),
                                            },
                                        },
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
                'component': 'VRadioGroup',
                'props': {
                    'model': 'cover_style',
                    'inline': True,
                },
                'content': style_content
            }
        ]

        # 多图风格设置
        multi_1_tab = [
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
                                    'text': '若字体无法下载，建议设置：系统 -> 高级设置 -> 网络 -> GitHub加速代理，或者手动下载，填写本地路径'
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
                                    'model': 'zh_font_path_multi_1_local',
                                    'label': '中文字体（本地路径）',
                                    'prependInnerIcon': 'mdi-ideogram-cjk',
                                    'placeholder': '留空使用预设字体',
                                    'hint': '字体本地路径，优先使用，多图风格专用',
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
                                    'model': 'en_font_path_multi_1_local',
                                    'label': '英文字体（本地路径）',
                                    'prependInnerIcon': 'mdi-format-font',
                                    'placeholder': '留空使用预设字体',
                                    'hint': '字体本地路径，优先使用，多图风格专用',
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
                                    'model': 'zh_font_url_multi_1',
                                    'label': '中文字体（下载链接）',
                                    'prependInnerIcon': 'mdi-link',
                                    'placeholder': '留空使用预设字体',
                                    'hint': '下载链接，优先级低于本地路径，多图风格专用',
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
                                    'model': 'en_font_url_multi_1',
                                    'label': '英文字体（下载链接）',
                                    'prependInnerIcon': 'mdi-link',
                                    'placeholder': '留空使用预设字体',
                                    'hint': '下载链接，优先级低于本地路径，多图风格专用',
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
                                    'model': 'zh_font_size_multi_1',
                                    'label': '中文字体大小比例',
                                    'prependInnerIcon': 'mdi-format-size',
                                    'placeholder': '留空使用预设尺寸',
                                    'hint': '根据自己喜好设置，值为相对原本尺寸的比例，1为原本大小',
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
                                    'model': 'en_font_size_multi_1',
                                    'label': '英文字体大小比例',
                                    'prependInnerIcon': 'mdi-format-size',
                                    'placeholder': '留空使用预设尺寸',
                                    'hint': '根据自己喜好设置，值为相对原本尺寸的比例，1为原本大小',
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
                                    'model': 'blur_size_multi_1',
                                    'label': '背景模糊尺寸',
                                    'prependInnerIcon': 'mdi-blur',
                                    'placeholder': '留空使用预设尺寸',
                                    'hint': '不启用模糊背景请忽略，数字越大越模糊，默认 50',
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
                                    'model': 'color_ratio_multi_1',
                                    'label': '背景颜色混合占比',
                                    'prependInnerIcon': 'mdi-format-color-fill',
                                    'placeholder': '留空使用预设占比',
                                    'hint': '不启用模糊背景请忽略，颜色所占的比例，0-1，默认 0.8',
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
                            'md': 3
                        },
                        'content': [
                            {
                                'component': 'VSwitch',
                                'props': {
                                    'model': 'multi_1_blur',
                                    'label': '启用模糊背景',
                                    'hint': '不启用则使用纯色渐变背景',
                                    "persistent-hint": True,
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
                                    'model': 'multi_1_use_main_font',
                                    'label': '使用单图风格字体',
                                    'hint': '勾选则忽略本页字体设置，字体大小除外',
                                    "persistent-hint": True,
                                }
                            }
                        ]
                    },
                ]
            },
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
                                                            'model': 'onlyonce',
                                                            'label': '立即运行一次',
                                                            'hint': '更新全部媒体库封面',
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
                                                            'chips': True,
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
                                                            'model': 'exclude_libraries',
                                                            'label': '忽略媒体库，默认更新全部',
                                                            'items': [
                                                                {"title": config['name'], "value": config['value']}
                                                                    for config in self._all_libraries
                                                            ],
                                                            'hint': '勾选媒体服务器，保存后获取列表',
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
                                "props": {"value": "single-tab"},
                                "content": [
                                    {
                                        "component": "VIcon",
                                        "props": {
                                            "icon": "mdi-palette-swatch-variant",
                                            "start": True,
                                            "color": "#f3afe4",
                                        },
                                    },
                                    {"component": "span", "text": "单图风格设置"},
                                ],
                            },
                            {
                                "component": "VTab",
                                "props": {"value": "multi-1-tab"},
                                "content": [
                                    {
                                        "component": "VIcon",
                                        "props": {
                                            "icon": "mdi-palette-swatch-variant",
                                            "start": True,
                                            "color": "#609585",
                                        },
                                    },
                                    {"component": "span", "text": "多图风格1设置"},
                                ],
                            },
                            {
                                "component": "VTab",
                                "props": {"value": "others-tab"},
                                "content": [
                                    {
                                        "component": "VIcon",
                                        "props": {
                                            "icon": "mdi-cogs",
                                            "start": True,
                                            "color": "#8958f4",
                                        },
                                    },
                                    {"component": "span", "text": "其他设置"},
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
                                "props": {"value": "others-tab"},
                                "content": [
                                    {"component": "VCardText", "content": others_tab}
                                ],
                            },
                            {
                                "component": "VWindowItem",
                                "props": {"value": "style-tab"},
                                "content": [
                                    {"component": "VCardText", "content": style_tab}
                                ],
                            },
                            {
                                "component": "VWindowItem",
                                "props": {"value": "single-tab"},
                                "content": [
                                    {"component": "VCardText", "content": single_tab}
                                ],
                            },
                            {
                                "component": "VWindowItem",
                                "props": {"value": "multi-1-tab"},
                                "content": [
                                    {"component": "VCardText", "content": multi_1_tab}
                                ],
                            },
                        ],
                    },
                ],
            }
        ], {
            "enabled": False,
            "onlyonce": False,
            "transfer_monitor": True,
            "cron": "",
            "delay": 60,
            "selected_servers": [],
            "exclude_libraries": [],
            "sort_by": "Random",
            "title_config": '''# 配置封面标题（按媒体库名称对应）
# 格式如下：
#
# 媒体库名称:
#   - 中文标题
#   - 英文标题
#
''',
            "tab": "style-tab",
            "cover_style": "single_1",
            "multi_1_blur": False
        }

    def get_page(self) -> List[dict]:
        pass

    @eventmanager.register(EventType.TransferComplete)
    def update_library_backdrop_rt(self, event: Event):
        """
        When media is added to library, update the library backdrop
        """
        if not self._enabled:
            return
        if not self._transfer_monitor:
            return
        self.__get_fonts()     # Event data
        # Event data
        mediainfo: MediaInfo = event.event_data.get("mediainfo")
        # logger.info(f"监控到的媒体信息：{mediainfo}")
        if not mediainfo:
            return
            
        # Delay
        if self._delay:
            logger.info(f"延迟 {self._delay} 秒后开始更新封面")
            time.sleep(int(self._delay))
            
        # Query the item in media server
        existsinfo = self.mschain.media_exists(mediainfo=mediainfo)
        if not existsinfo or not existsinfo.itemid:
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
        service = self._servers.get(existsinfo.server)
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
        if f"{existsinfo.server}-{library_id}" in self._exclude_libraries:
            logger.info(f"服务器 {existsinfo.server} 的媒体库 {library['Name']} 已忽略，跳过更新封面")
            return
        # self.clean_cover_history(save=True)
        old_history = self.get_data('cover_history') or []
        # 新增去重判断逻辑
        latest_item = max(
            (item for item in old_history if str(item.get("library_id")) == str(library_id)),
            key=lambda x: x["timestamp"],
            default=None
        )
        if latest_item and str(latest_item.get("item_id")) == str(existsinfo.itemid):
            logger.info(f"媒体 {mediainfo.title_year} 在库中是最新记录，不更新封面图")
            return
        new_history = self.update_cover_history(
            server=existsinfo.server, 
            library_id=library_id, 
            item_id=existsinfo.itemid
        )
        # logger.info(f"最新数据： {new_history}")
        self._monitor_sort = 'DateCreated'
        if self._cover_style.startswith('single'):
            if self.__update_library(service, library):
                self._monitor_sort = ''
                logger.info(f"服务器 {existsinfo.server} 的媒体库 {library['Name']} 封面更新成功")
        elif self._cover_style.startswith('multi'):
            if self.__update_library(service, library):
                self._monitor_sort = ''
                logger.info(f"服务器 {existsinfo.server} 的媒体库 {library['Name']} 封面更新成功")
    
    def __update_all_libraries(self):
        """
        更新所有媒体库封面
        """
        if not self._enabled:
            return
        # 所有媒体服务器
        if not self._servers:
            return
        
        self.__get_fonts()  
        for server, service in self._servers.items():
            # 扫描所有媒体库
            logger.info(f"准备更新服务器 {server} 的媒体库封面...")
            cover_style = {
                "single_1": "单图 1",
                "single_2": "单图 2",
                "multi_1": "多图 1"
            }[self._cover_style]
            logger.info(f"当前选择的风格: {cover_style}")
            # 获取媒体库列表
            libraries = self.__get_server_libraries(service)
            if not libraries:
                logger.warning(f"服务器 {server} 的媒体库列表获取失败")
                continue
            for library in libraries:
                if self._event.is_set():
                    logger.info("媒体库封面更新服务停止")
                    return
                if service.type == 'emby':
                    library_id = library.get("Id")
                else:
                    library_id = library.get("ItemId")
                if f"{server}-{library_id}" in self._exclude_libraries:
                    logger.info(f"服务器 {server} 的媒体库 {library['Name']} 已忽略，跳过更新封面")
                    continue
                if self.__update_library(service, library):
                    logger.info(f"服务器 {server} 的媒体库 {library['Name']} 封面更新成功")
                else:
                    logger.warning(f"服务器 {server} 的媒体库 {library['Name']} 封面更新失败")
        logger.info("所有媒体库封面更新完成")
                 

    def __update_library(self, service, library):
        library_name = library['Name']
        logger.info(f"开始更新服务器 {service.name} 的媒体库 {library_name} 的封面")
        # 自定义图像路径
        image_path = self.__check_custom_image(library_name)
        # 从配置获取标题
        title = self.__get_library_title_from_yaml(library_name)
        if image_path:
            image_data = self.__generate_image_from_path(library_name, title, image_path[0])
        else:
            image_data = self.__generate_from_server(service, library, title)

        if image_data:
            return self.__set_library_image(service, library, image_data)

    def __check_custom_image(self, library_name):
        if not self._covers_input:
            return None

        library_dir = os.path.join(self._covers_input, library_name)
        if not os.path.isdir(library_dir):
            return None

        images = sorted([
            os.path.join(library_dir, f)
            for f in os.listdir(library_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"))
        ])
        
        return images if images else None  # 或改为 return images if images else False

    def __generate_image_from_path(self, library_name, title, image_path=None):
        logger.info(f"请耐心等待，正在生成封面图...")
        font_path = (str(self._zh_font_path), str(self._en_font_path))
        font_size = (float(self._zh_font_size), float(self._en_font_size))
        if self._cover_style == 'single_1':
            image_data = create_style_single_1(image_path, title, font_path, font_size, 
                                               self._blur_size, self._color_ratio)
        elif self._cover_style == 'single_2':
            image_data = create_style_single_2(image_path, title, font_path, font_size, 
                                               self._blur_size, self._color_ratio)
        elif self._cover_style == 'multi_1':
            zh_font_path = self._zh_font_path if self._multi_1_use_main_font else self._zh_font_path_multi_1
            en_font_path = self._en_font_path if self._multi_1_use_main_font else self._en_font_path_multi_1
            font_path = (zh_font_path, en_font_path)
            font_size = (float(self._zh_font_size_multi_1), float(self._en_font_size_multi_1))
            if image_path:
                library_dir = Path(self._covers_input) / library_name
            else:
                library_dir = Path(self._covers_path) / library_name
            if self.prepare_library_images(library_dir):
                image_data = create_style_multi_1(library_dir, title, font_path, font_size, 
                                                  self._multi_1_blur, self._blur_size_multi_1, 
                                                  self._color_ratio_multi_1)
        return image_data
    
    def __generate_from_server(self, service, library, title):

        logger.info(f"开始从服务器 {service.name} 的媒体库 {library['Name']} 获取图片")
        required_items = 1 if self._cover_style.startswith('single') else 9
        
        # 获取项目集合
        items = []
        offset = 0
        batch_size = 20  # 每次获取的项目数量
        max_attempts = 5  # 最大尝试次数，防止无限循环
        
        library_type = library.get('CollectionType')
        if service.type == 'emby':
            library_id = library.get("Id")
        else:
            library_id = library.get("ItemId")
        parent_id = library_id
        
        # 处理合集类型的特殊情况
        if library_type == "boxsets":
            return self.__handle_boxset_library(service, library, title)
        elif library_type == "music":
            include_types = 'MusicAlbum,Audio'
        else:
            date_created = 'Movie,Episode' if self._cover_style.startswith('single') else 'Movie,Series'
            include_types = {
                "PremiereDate": "Movie,Series",
                "DateCreated": date_created,
                "Random": "Movie,Series"
            }[self._sort_by]
        for attempt in range(max_attempts):
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
            if self._cover_style.startswith('single'):
                return self.__update_single_image(service, library, title, items[0])
            else:
                return self.__update_grid_image(service, library, title, items[:9])
        else:
            print(f"警告: 无法为媒体库 {library['Name']} 找到有效的图片项目")
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
        
        required_items = 1 if self._cover_style.startswith('single') else 9
        valid_items = []
        
        # 首先检查BoxSet本身是否有合适的图片
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
            logger.info(f"已获取足够的图片")
            if self._cover_style.startswith('single'):
                return self.__update_single_image(service, library, title, valid_items[0])
            else:
                return self.__update_grid_image(service, library, title, valid_items[:9])
        else:
            print(f"警告: 无法为合集媒体库 {library['Name']} 找到有效的图片项目")
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
                logger.error(f"获取Emby媒体项详情失败：{str(err)}")
            return []
                
        except Exception as err:
            logger.error(f"Failed to get latest items: {str(err)}")
            return []
        
    def __filter_valid_items(self, items):
        """筛选有效的项目（包含所需图片的项目）"""
        valid_items = []
        
        for item in items:
            if item['Type'] in 'MusicAlbum,Audio' :
                if (item.get("ParentBackdropImageTags") and len(item["ParentBackdropImageTags"]) > 0) \
                    or item.get("AlbumPrimaryImageTag") \
                    or item.get("PrimaryImageTag"):
                    valid_items.append(item)
            elif self._cover_style.startswith('single'):
                # 单图模式需要背景图
                if (item.get("BackdropImageTags") and len(item["BackdropImageTags"]) > 0) \
                    or (item.get("ParentBackdropImageTags") and len(item.get("ParentBackdropImageTags")) > 0):
                    valid_items.append(item)
            else:
                # 多图模式需要主图
                if item.get("ImageTags") and item.get("ImageTags").get("Primary"):
                    valid_items.append(item)
        
        return valid_items
    
    def __update_single_image(self, service, library, title, item):
        """更新单图封面"""
        logger.info(f"开始为服务器 {service.name} 的媒体库 {library['Name']} 更新单图封面")
        updated_item_id = ''
        image_url = self.__get_image_url(item)
        if not image_url:
            return False
            
        image_path = self.__download_image(service, image_url, library['Name'], count=1)
        if not image_path:
            return False
        updated_item_id = self.__get_item_id(item)
        image_data = self.__generate_image_from_path(library['Name'], title, image_path)
            
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
        logger.info(f"开始为服务器 {service.name} 的媒体库 {library['Name']} 更新多图封面")

        image_paths = []
        
        updated_item_ids = []
        for i, item in enumerate(items[:9]):
            image_url = self.__get_image_url(item)
            if image_url:
                image_path = self.__download_image(service, image_url, library['Name'], count=i+1)
                if image_path:
                    image_paths.append(image_path)
                    updated_item_ids.append(self.__get_item_id(item))
        
        if len(image_paths) < 1:
            return False
            
        # 生成九宫格图片
        image_data = self.__generate_image_from_path(library['Name'], title)
        if not image_data:
            return False
        if service.type == 'emby':
            library_id = library.get("Id")
        else:
            library_id = library.get("ItemId")
        # 更新ids
        for item_id in updated_item_ids:
            self.update_cover_history(
                server=service.name, 
                library_id=library_id, 
                item_id=item_id
            )
            
        return image_data
    
    def __get_library_title_from_yaml(self, library_name):
        """ 
        从 yaml 配置中获取媒体库的中英文标题
        """
        def preprocess_yaml_text(yaml_str: str) -> str:
            # 替换中文全角冒号为英文半角
            yaml_str = yaml_str.replace("：", ":")
            # 替换制表符为两个空格，统一缩进
            yaml_str = yaml_str.replace("\t", "  ")
            return yaml_str
        
        def load_yaml_safe(yaml_str: str) -> dict:
            try:
                yaml_str = preprocess_yaml_text(yaml_str)
                data = yaml.safe_load(yaml_str)
                if not isinstance(data, dict):
                    raise ValueError("YAML 顶层结构必须是一个字典")
                return data
            except yaml.YAMLError as e:
                raise ValueError(f"YAML 解析错误：{str(e)}")
            
        def validate_title_config(data: dict) -> dict:
            for key, value in data.items():
                if not isinstance(value, list) or len(value) < 2:
                    raise ValueError(f"条目“{key}”格式错误，必须是包含中英文标题的列表")
            return data

        def load_and_validate_titles(yaml_str: str) -> dict:
            data = load_yaml_safe(yaml_str)
            return validate_title_config(data)
        
        zh_title = library_name
        en_title = ''
        if self._title_config:
            try:
                title_config = load_and_validate_titles(self._title_config)
                for lib_name, (zh, en) in title_config.items():
                    if lib_name == library_name:
                        zh_title = zh
                        en_title = en
                        break
            except ValueError as e:
                # 如果YAML解析出错，记录错误并继续
                logger.info(f"标题配置解析错误，将使用库名: {e}")
        return (zh_title, en_title)
    
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
                logger.error(f"获取Emby媒体库列表失败：{str(err)}")
            return []
        except Exception as err:
            logger.error(f"获取Emby媒体库列表失败：{str(err)}")
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

        elif self._cover_style.startswith('multi'):
            if item.get("ImageTags") and item.get("ImageTags").get("Primary"):
                item_id = item.get("Id")
                tag = item.get("ImageTags").get("Primary")
                return f'[HOST]emby/Items/{item_id}/Images/Primary?tag={tag}&api_key=[APIKEY]'

        elif self._cover_style.startswith('single'):
            if item.get("ParentBackdropImageTags") and len(item["ParentBackdropImageTags"]) > 0:
                item_id = item.get("ParentBackdropItemId")
                tag = item["ParentBackdropImageTags"][0]
            elif item.get("BackdropImageTags") and len(item["BackdropImageTags"]) > 0:
                item_id = item.get("Id")
                tag = item["BackdropImageTags"][0]
            return f'[HOST]emby/Items/{item_id}/Images/Backdrop/0?tag={tag}&api_key=[APIKEY]'
        
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

        elif self._cover_style.startswith('multi'):
            if item.get("ImageTags") and item.get("ImageTags").get("Primary"):
                item_id = item.get("Id")

        elif self._cover_style.startswith('single'):
            if item.get("ParentBackdropImageTags") and len(item["ParentBackdropImageTags"]) > 0:
                item_id = item.get("ParentBackdropItemId")
            elif item.get("BackdropImageTags") and len(item["BackdropImageTags"]) > 0:
                item_id = item.get("Id")

        return item_id

    def __download_image(self, service, imageurl, library_name, count=None, retries=3, delay=1):
        """
        下载图片，保存到本地目录 self._covers_path/library_name/ 下，文件名为 1-9.jpg
        若已存在则跳过下载，直接返回图片路径。
        下载失败时重试若干次。
        """
        try:
            # 创建目标子目录
            subdir = os.path.join(self._covers_path, library_name)
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


    def __save_image_to_local(self, image_content, filename):
        """
        保存图片到本地路径
        """
        try:
            # 确保目录存在
            local_path = self._covers_output
            import os
            os.makedirs(local_path, exist_ok=True)
            
            # 保存文件
            file_path = os.path.join(local_path, filename)
            with open(file_path, "wb") as f:
                f.write(image_content)
            logger.info(f"图片已保存到本地: {file_path}")
        except Exception as err:
            logger.error(f"保存图片到本地失败: {str(err)}")
        

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
            
            # 在发送前保存一份图片到本地
            if self._covers_output:
                try:
                    image_bytes = base64.b64decode(image_base64)
                    self.__save_image_to_local(image_bytes, f"{library['Name']}.jpg")
                except Exception as save_err:
                    logger.error(f"保存发送前图片失败: {str(save_err)}")
            
            res = service.instance.post_data(
                url=url,
                data=image_base64,
                headers={
                    "Content-Type": "image/png"
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

    def prepare_library_images(self, library_dir: str):
        """
        准备目录下的1-9.jpg图片文件:
        1. 检查已有的1-9.jpg文件
        2. 保留已有的文件，只补足缺失的编号
        3. 补充文件时尽量避免连续使用相同的源图片
        """
        os.makedirs(library_dir, exist_ok=True)

        # 检查哪些编号的文件已存在，哪些缺失
        existing_numbers = []
        missing_numbers = []
        for i in range(1, 10):
            target_file_path = os.path.join(library_dir, f"{i}.jpg")
            if os.path.exists(target_file_path):
                existing_numbers.append(i)
            else:
                missing_numbers.append(i)

        # 如果已经存在所有文件，直接返回
        if not missing_numbers:
            # logger.info(f"信息: {library_dir} 中已存在所有 1-9.jpg，无需任何操作。")
            return True

        logger.info(f"信息: {library_dir} 中缺少以下编号的图片: {missing_numbers}，将进行补充。")

        # 获取所有可用作源的图片（排除已有的1-9.jpg）
        source_image_filenames = []
        for f in os.listdir(library_dir):
            # 排除1-9.jpg作为源
            if not re.match(r"^[1-9]\.jpg$", f, re.IGNORECASE):
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    source_image_filenames.append(f)

        # 如果没有源图片可用
        if not source_image_filenames:
            # 如果已经有部分1-9.jpg，可以从这些现有文件中选择
            if existing_numbers:
                logger.info(f"信息: {library_dir} 中没有其他图片可用，将从现有的 1-9.jpg 中随机选择进行复制。")
                existing_file_paths = [os.path.join(library_dir, f"{i}.jpg") for i in existing_numbers]
                source_image_paths = existing_file_paths
            else:
                logger.info(f"警告: {library_dir} 中没有任何可用的图片来生成 1-9.jpg。")
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

        logger.info(f"信息: {library_dir} 已成功补充所有缺失的图片，现在包含完整的 1-9.jpg")
        return True

    def __get_fonts(self):
        font_dir_path = self._font_path

        default_zh_url = "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/wendao.ttf"
        default_en_url = "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/EmblemaOne.woff2"
        
        default_zh_url_multi_1 = "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/multi_1_zh.ttf"
        default_en_url_multi_1 = "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/multi_1_en.otf"

        is_multi_1_style = self._cover_style == "multi_1"

        if is_multi_1_style and not self._multi_1_use_main_font:
            log_prefix = "多图风格1"
            current_zh_font_url = self._zh_font_url_multi_1 or default_zh_url_multi_1
            current_en_font_url = self._en_font_url_multi_1 or default_en_url_multi_1
            zh_local_path_config = self._zh_font_path_multi_1_local
            en_local_path_config = self._en_font_path_multi_1_local
            
            downloaded_zh_font_base = "zh_multi_1"
            downloaded_en_font_base = "en_multi_1"
            hash_zh_file_name = "zh_url_multi_1.hash"
            hash_en_file_name = "en_url_multi_1.hash"
            final_zh_font_path_attr = "_zh_font_path_multi_1"
            final_en_font_path_attr = "_en_font_path_multi_1"
        else:
            log_prefix = "默认"
            current_zh_font_url = self._zh_font_url or default_zh_url
            current_en_font_url = self._en_font_url or default_en_url
            zh_local_path_config = self._zh_font_path_local
            en_local_path_config = self._en_font_path_local
            
            downloaded_zh_font_base = "zh"
            downloaded_en_font_base = "en"
            hash_zh_file_name = "zh_url.hash"
            hash_en_file_name = "en_url.hash"
            final_zh_font_path_attr = "_zh_font_path"
            final_en_font_path_attr = "_en_font_path"

        active_fonts_to_process = [
            {
                "lang": "中文",
                "url": current_zh_font_url,
                "local_path_config": zh_local_path_config,
                "download_base_name": downloaded_zh_font_base,
                "hash_file_name": hash_zh_file_name,
                "final_attr_name": final_zh_font_path_attr,
                "fallback_ext": ".ttf"
            },
            {
                "lang": "英文",
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
                if self._validate_font_file(local_font_p):
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
                
                font_file_is_valid = self._validate_font_file(downloaded_font_file_path)

                if url_has_changed or not font_file_is_valid:
                    if url_has_changed:
                        logger.info(f"{log_prefix}{lang}字体URL已更改或首次下载。")
                    if not font_file_is_valid and downloaded_font_file_path.exists():
                         logger.info(f"{log_prefix}{lang}字体文件 {downloaded_font_file_path} 无效或损坏，将重新下载。")
                    elif not downloaded_font_file_path.exists():
                         logger.info(f"{log_prefix}{lang}字体文件 {downloaded_font_file_path} 不存在，将下载。")

                    if self.download_font_safely(url, downloaded_font_file_path):
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
            
            setattr(self, final_attr, current_font_path)
            status_log = '(本地路径)' if using_local_font else '(已下载/缓存)' if current_font_path and current_font_path.exists() else '(获取失败)'
            logger.info(f"{log_prefix}{lang}字体最终路径: {getattr(self,final_attr)} {status_log}")

    def download_font_safely(self, font_url: str, font_path: Path, retries: int = 3, delay: int = 2):
        """
        从链接下载字体文件到指定目录，支持多种下载策略（GitHub镜像、代理、直连）
        :param font_url: 字体文件URL
        :param font_path: 保存路径
        :param retries: 每种策略的最大重试次数
        :param delay: 重试间隔（秒）
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
        
        # 准备下载策略
        strategies = []
        
        # 判断是否为GitHub链接
        is_github_url = "github.com" in font_url or "raw.githubusercontent.com" in font_url
        
        # 对于GitHub链接，优先使用GitHub镜像站
        if is_github_url and settings.GITHUB_PROXY:
            github_proxy_url = f"{UrlUtils.standardize_base_url(settings.GITHUB_PROXY)}{font_url}"
            strategies.append(("GitHub镜像站", github_proxy_url))
        
        # 其次尝试使用代理
        if settings.PROXY_HOST:
            strategies.append(("代理", font_url, {"proxies": settings.PROXY}))
        
        # 最后尝试直连
        strategies.append(("直连", font_url, {}))
        
        # 遍历所有策略
        for strategy_name, target_url, *request_params in strategies:
            request_kwargs = request_params[0] if request_params else {}
            logger.info(f"尝试使用策略：{strategy_name} 下载字体: {target_url}")
            
            attempt = 0
            while attempt < retries:
                attempt += 1
                try:
                    logger.debug(f"使用策略 {strategy_name}，下载尝试 {attempt}/{retries} for {target_url}")
                    
                    # 创建目标目录
                    font_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 使用对应策略下载内容
                    font_content = RequestUtils(**request_kwargs).get_res(url=target_url).content
                    
                    # 创建临时文件用于验证下载内容
                    temp_path = font_path.with_suffix('.temp')
                    with open(temp_path, "wb") as f:
                        f.write(font_content)
                    
                    # 验证下载的字体文件
                    if self._validate_font_file(temp_path):
                        # 验证通过后，将临时文件移动到正确位置
                        temp_path.replace(font_path)
                        logger.info(f"字体下载成功: 使用策略 {strategy_name}")
                        return True
                    else:
                        logger.warning(f"下载的字体文件验证失败，可能已损坏")
                        if temp_path.exists():
                            temp_path.unlink()
                    
                except Exception as e:
                    logger.warning(f"策略 {strategy_name} 下载尝试 {attempt}/{retries} 失败: {e}")
                    # 清理可能的临时文件
                    temp_path = font_path.with_suffix('.temp')
                    if temp_path.exists():
                        try:
                            temp_path.unlink()
                        except OSError:
                            pass
                    
                    if attempt < retries:
                        logger.info(f"将在 {delay} 秒后重试...")
                        time.sleep(delay)
                    else:
                        logger.error(f"使用策略 {strategy_name} 下载字体失败 (已达最大重试次数): {target_url}")
                        # 转到下一个策略，不返回False
                        break
        
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