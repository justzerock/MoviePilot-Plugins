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
from app.plugins.mediacovergenerator.style_single_1 import create_style_single_1
from app.plugins.mediacovergenerator.style_single_2 import create_style_single_2
from app.plugins.mediacovergenerator.style_multi_1 import create_style_multi_1


class MediaCoverGenerator(_PluginBase):
    # 插件名称
    plugin_name = "媒体库封面生成"
    # 插件描述
    plugin_desc = "自动生成媒体库封面，支持 Emby，Jellyfin"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/icons/emby.png"
    # 插件版本
    plugin_version = "0.8.1"
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
    _delay = 0
    _mediaservers = []
    _sort_by = 'Random'
    _covers_output = ''
    _covers_input = ''
    _zh_font_url = ''
    _en_font_url = ''
    _zh_font_path = ''
    _en_font_path = ''
    _zh_font_url_multi_1 = ''
    _en_font_url_multi_1 = ''
    _zh_font_path_multi_1 = ''
    _en_font_path_multi_1 = ''
    _multi_1_use_main_font = False
    _title_config = ''
    _cover_style = 'single_1'
    _font_path = ''
    _cover_path = ''
    _collection_name = '合集'
    _music_name = '音乐'
    _tab = 'cover-tab'
    _multi_1_blur = False

    def __init__(self):
        super().__init__()
        data_path = self.get_data_path()
        self._font_path = data_path / 'fonts'
        font_path = Path(self._font_path)
        font_path.mkdir(parents=True, exist_ok=True)
        self._cover_path = data_path / 'covers'
        cover_path = Path(self._cover_path)
        cover_path.mkdir(parents=True, exist_ok=True)

    def init_plugin(self, config: dict = None):
        self.mschain = MediaServerChain()
        self.mediaserver_helper = MediaServerHelper()    
        if config:
            self._enabled = config.get("enabled")
            self._onlyonce = config.get("onlyonce")
            self._transfer_monitor = config.get("transfer_monitor")
            self._cron = config.get("cron")
            self._delay = config.get("delay") or 0
            self._mediaservers = config.get("mediaservers") or []
            self._sort_by = config.get("sort_by") or 'Random'
            self._covers_output = config.get("covers_output") or ''
            self._covers_input = config.get("covers_input") or ''
            self._title_config = config.get("title_config") or ''
            self._zh_font_url = config.get("zh_font_url") or ""
            self._en_font_url = config.get("en_font_url") or ""
            self._zh_font_path = config.get("zh_font_path")
            self._en_font_path = config.get("en_font_path")
            self._cover_style = config.get("cover_style") or "single_1"
            self._tab = config.get("tab") or 'cover-tab'
            self._collection_name = config.get("collection_name") or '合集'
            self._music_name = config.get("music_name") or '音乐'
            self._multi_1_blur = config.get("multi_1_blur")
            self._zh_font_url_multi_1 = config.get("zh_font_url_multi_1")
            self._en_font_url_multi_1 = config.get("en_font_url_multi_1")
            self._zh_font_path_multi_1 = config.get("zh_font_path_multi_1")
            self._en_font_path_multi_1 = config.get("en_font_path_multi_1")
            self._multi_1_use_main_font = config.get("multi_1_use_main_font")

        # 停止现有任务
        self.stop_service()

        # 启动服务
        if self._onlyonce:
            self._scheduler = BackgroundScheduler(timezone=settings.TZ)
            self._scheduler.add_job(func=self.update_all_libraries, trigger='date',
                                    run_date=datetime.datetime.now(
                                        tz=pytz.timezone(settings.TZ)) + datetime.timedelta(seconds=3)
                                    )
            logger.info(f"媒体库背景图更新服务启动，立即运行一次")
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
            "mediaservers": self._mediaservers,
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
            "collection_name": self._collection_name,
            "music_name": self._music_name,
            "multi_1_blur": self._multi_1_blur,
            "zh_font_url_multi_1": self._zh_font_url_multi_1,
            "en_font_url_multi_1": self._en_font_url_multi_1,
            "zh_font_path_multi_1": self._zh_font_path_multi_1,
            "en_font_path_multi_1": self._en_font_path_multi_1,
            "multi_1_use_main_font": self._multi_1_use_main_font
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
                "name": "媒体库背景图更新服务",
                "trigger": CronTrigger.from_crontab(self._cron),
                "func": self.update_all_libraries,
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
        font_cover_tab = [
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
                                'component': 'VTextField',
                                'props': {
                                    'model': 'zh_font_url',
                                    'label': '中文字体链接（可选）',
                                    'placeholder': '留空使用预设字体'
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
                                    'label': '英文字体链接（可选）',
                                    'placeholder': '留空使用预设字体'
                                }
                            }
                        ]
                    }
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
                                'component': 'VTextField',
                                'props': {
                                    'model': 'covers_input',
                                    'label': '自定义背景图目录（可选）',
                                    'placeholder': '具体要求查看下方说明'
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
                                    'placeholder': '如 /mnt/covers_output，生成的封面在此另存一份'
                                }
                            }
                        ]
                    }
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
                                'component': 'VTextField',
                                'props': {
                                    'model': 'music_name',
                                    'label': '音乐库名',
                                    'placeholder': '音乐库的名字，默认「音乐」',
                                    'hint': '若不能获取到音乐库的图片，请设置此项',
                                    'persistent-hint': True
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
                                    'model': 'collection_name',
                                    'label': '合集库名',
                                    'placeholder': '合集库的名字，默认「合集」',
                                    'hint': '若不能获取到合集库的图片，请设置此项',
                                    'persistent-hint': True
                                }
                            }
                        ]
                    }
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
                                'component': 'VAlert',
                                'props': {
                                    'type': 'info',
                                    'variant': 'tonal',
                                    'text': '「自定义背景图目录」，请将图片存于与媒体库同名的文件夹下，单图模式对文件名无要求'
                                }
                            }
                        ]
                    },
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
                                    'text': '多图模式: 文件名须为 1.jpg, 2.jpg, ...9.jpg，不满足的会被重命名，不够的会随机复制填满9张'
                                }
                            }
                        ]
                    }
                ]
            }
        ]

        covers = [
            {
                "title": "单图 1",
                "value": "single_1",
                "src": "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/images/single_1.jpg"
            },
            {
                "title": "单图 2",
                "value": "single_2",
                "src": "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/images/single_2.jpg"
            },
            {
                "title": "多图 1",
                "value": "multi_1",
                "src": "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/images/multi_1.jpg"
            }
        ]

        cover_content = []

        for cover in covers:
            cover_content.append(
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
                                        "src": cover.get("src"),
                                        "aspect-ratio": "16/9",
                                        "cover": True,
                                    }
                                },  
                                {
                                    "component": "VCardTitle",
                                    # "text": cover.get("title"),
                                    "props": {
                                        "class": "text-secondary text-h6 text-center bg-surface-light"
                                    },
                                    "content": [
                                        {
                                            "component": "VRadio",
                                            "props": {
                                                "color": "primary",
                                                "value": cover.get("value"),
                                                "label": cover.get("title"),
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
        cover_tab = [
            {
                'component': 'VRadioGroup',
                'props': {
                    'model': 'cover_style',
                    'inline': True,
                },
                'content': cover_content
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
                            'md': 6
                        },
                        'content': [
                            {
                                'component': 'VTextField',
                                'props': {
                                    'model': 'zh_font_url_multi_1',
                                    'label': '中文字体链接（可选）',
                                    'placeholder': '留空使用预设字体'
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
                                    'label': '英文字体链接（可选）',
                                    'placeholder': '留空使用预设字体'
                                }
                            }
                        ]
                    }
                ]
            },
            {
                'component': 'VRow',
                'content': [
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
                                    'model': 'multi_1_blur',
                                    'label': '启用模糊背景',
                                    'hint': '不启用则使用原效果',
                                    "persistent-hint": True,
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
                                    'model': 'multi_1_use_main_font',
                                    'label': '使用主字体',
                                    'hint': '不启用则单独使用字体',
                                    "persistent-hint": True,
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
                                'component': 'VAlert',
                                'props': {
                                    'type': 'info',
                                    'variant': 'tonal',
                                    'text': '这里的设置只影响多图风格1'
                                }
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
                                                    'md': 4
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
                                                    'md': 4
                                                },
                                                'content': [
                                                    {
                                                        'component': 'VSwitch',
                                                        'props': {
                                                            'model': 'onlyonce',
                                                            'label': '立即运行一次',
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
                                                            'model': 'transfer_monitor',
                                                            'label': '入库监控',
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
                                                        'component': 'VSelect',
                                                        'props': {
                                                            'multiple': True,
                                                            'chips': True,
                                                            'clearable': True,
                                                            'model': 'mediaservers',
                                                            'label': '媒体服务器',
                                                            'items': [{"title": config.name, "value": config.name}
                                                                    for config in self.mediaserver_helper.get_configs().values()]
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
                                                            'placeholder': '如：30，等待入库再更新'
                                                        }
                                                    }
                                                ]
                                            },
                                        ]
                                    },
                                    
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
                                "props": {"value": "cover-tab"},
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
                                    {"component": "span", "text": "封面标题 *"},
                                ],
                            },
                            {
                                "component": "VTab",
                                "props": {"value": "font-cover-tab"},
                                "content": [
                                    {
                                        "component": "VIcon",
                                        "props": {
                                            "icon": "mdi-format-size",
                                            "start": True,
                                            "color": "#4CAF50",
                                        },
                                    },
                                    {"component": "span", "text": "字体与图像"},
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
                                "props": {"value": "font-cover-tab"},
                                "content": [
                                    {"component": "VCardText", "content": font_cover_tab}
                                ],
                            },
                            {
                                "component": "VWindowItem",
                                "props": {"value": "cover-tab"},
                                "content": [
                                    {"component": "VCardText", "content": cover_tab}
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
            "delay": 30,
            "mediaservers": [],
            "sort_by": "Random",
            "title_config": '''# 配置封面标题（按媒体库名称对应）
# 格式如下：
#
# 媒体库名称:
#   - 中文标题
#   - 英文标题
#

华语剧集:
  - 华语剧集
  - Chinese Series
 
华语电影:
  - 华语电影
  - Chinese Films
''',
            "tab": "cover-tab",
            "cover_style": "single_1",
            "multi_1_blur": False
        }

    def get_page(self) -> List[dict]:
        pass

    def service_infos(self, type_filter: Optional[str] = None) -> Optional[Dict[str, ServiceInfo]]:
        """
        获取媒体服务器信息
        """
        if not self._mediaservers:
            logger.warning("尚未配置媒体服务器，请检查配置")
            return None
        services = self.mediaserver_helper.get_services(type_filter=type_filter, name_filters=self._mediaservers)
        if not services:
            logger.warning("获取媒体服务器实例失败，请检查配置")
            return None

        active_services = {}
        for service_name, service_info in services.items():
            if service_info.instance.is_inactive():
                logger.warning(f"媒体服务器 {service_name} 未连接，请检查配置")
            else:
                active_services[service_name] = service_info

        if not active_services:
            logger.warning("没有已连接的媒体服务器，请检查配置")
            return None

        return active_services

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
            time.sleep(int(self._delay))
            
        # Query the item in media server
        existsinfo = self.mschain.media_exists(mediainfo=mediainfo)
        if not existsinfo or not existsinfo.itemid:
            logger.warning(f"{mediainfo.title_year} 不存在媒体库中，可能服务器还未扫描完成，建议设置延迟")
            return
        
        # Get item details including backdrop
        iteminfo = self.mschain.iteminfo(server=existsinfo.server, item_id=existsinfo.itemid)
        # logger.info(f"获取到媒体项 {mediainfo.title_year} 详情：{iteminfo}")
        if not iteminfo:
            logger.warning(f"获取 {mediainfo.title_year} 详情失败")
            return
            
        # Try to get library ID
        library_id = None
        media_service = self.service_infos(existsinfo.server_type).get(existsinfo.server)
        if existsinfo.server_type == "emby":
            libraries = media_service.instance.get_emby_virtual_folders()
        elif existsinfo.server_type == "jellyfin":
            libraries = media_service.instance.get_jellyfin_virtual_folders()
        if libraries and not library_id:
            library_info = next(
                ((library.get('Id', ''), library.get('Name', '')) for library in libraries if library.get('Path', '') and any(iteminfo.path.startswith(path) for path in library.get('Path', ''))),
                None
            )
            library_id, library_name = library_info
        
        if not library_id:
            logger.warning(f"找不到 {mediainfo.title_year} 所在媒体库")
            return
        # logger.info(f"服务器：{existsinfo.server} 服务器类型：{existsinfo.server_type} 库ID：{library_id} 库名称：{library_name} 媒体ID：{existsinfo.itemid}")
        # self.clean_cover_history(save=True)
        old_history = self.get_data('cover_history') or []
        # 新增去重判断逻辑
        latest_item = max(
            (item for item in old_history if str(item.get("library_id")) == str(library_id)),
            key=lambda x: x["timestamp"],
            default=None
        )
        if latest_item and str(latest_item.get("item_id")) == str(existsinfo.itemid):
            logger.info(f"媒体 {mediainfo.title_year} 在库中是最新记录，跳过此次更新")
            return
        new_history = self.update_cover_history(
            server=existsinfo.server, 
            server_type=existsinfo.server_type,
            library_id=library_id, 
            library_name=library_name,
            item_id=existsinfo.itemid
        )
        # logger.info(f"最新数据： {new_history}")
        count = sum(1 for item in new_history if str(item.get("library_id")) == str(library_id))
        if self._cover_style.startswith('single'):
            self.__update_library_backdrop(
                server=existsinfo.server, 
                server_type=existsinfo.server_type,
                library_id=library_id, 
                library_name=library_name,
                item_id=existsinfo.itemid
            )
        elif self._cover_style.startswith('multi') and count >= 9:
            items = sorted(new_history, key=lambda x: x["timestamp"], reverse=True)
            item_ids = [item["item_id"] for item in items]
            self.__update_library_backdrop(
                server=existsinfo.server, 
                server_type=existsinfo.server_type,
                library_id=library_id, 
                library_name=library_name,
                item_ids=item_ids
            )
        else:
            self.update_all_libraries()
    
    def clean_cover_history(self, save=True):
        history = self.get_data('cover_history') or []
        cleaned = []

        for item in history:
            try:
                cleaned_item = {
                    "server": item["server"],
                    "server_type": item["server_type"],
                    "library_id": str(item["library_id"]),
                    "library_name": item["library_name"],
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


    def update_cover_history(self, server, server_type, library_id, library_name, item_id):
        now = time.time()
        item_id = str(item_id)
        library_id = str(library_id)

        history_item = {
            "server": server,
            "server_type": server_type,
            "library_id": library_id,
            "library_name": library_name,
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
        
    def download_font_safely(self, font_url: str, font_path: Path, retries: int = 3, delay: int = 2):
        """
        从链接下载字体文件到指定目录

        """
        logger.info(f"准备下载字体: {font_url} -> {font_path}")
        attempt = 0
        while attempt < retries:
            attempt += 1
            try:
                font_path.parent.mkdir(parents=True, exist_ok=True)

                logger.debug(f"下载尝试 {attempt}/{retries} for {font_url}")

                font_content = RequestUtils().get_res(url=font_url).content

                with open(font_path, "wb") as f:
                    f.write(font_content)

                logger.info(f"字体下载成功: {font_path}")
                return True

            except Exception as e:
                logger.warning(f"下载尝试 {attempt}/{retries} 失败 for {font_url}. 错误: {e}")
                if attempt < retries:
                    logger.info(f"将在 {delay} 秒后重试...")
                    time.sleep(delay)
                else:
                    logger.error(f"下载字体失败 (已达最大重试次数): {font_url}")
                    if font_path.exists():
                        try:
                            font_path.unlink()
                            logger.info(f"已删除部分下载的文件: {font_path}")
                        except OSError as unlink_error:
                            logger.error(f"无法删除部分下载的文件 {font_path}: {unlink_error}")
                    return False

        return False


    def __get_fonts(self):
        data_path = self.get_data_path()
        path = Path(data_path / "fonts")
        path.mkdir(parents=True, exist_ok=True)

        # 默认字体链接
        default_zh_url = "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/wendao.ttf"
        default_en_url = "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/lilitaone.woff2"
        
        # 默认多图1字体链接
        default_zh_url_multi_1 = "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/multi_1_zh.ttf"
        default_en_url_multi_1 = "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/multi_1_en.otf"

        zh_font_url = self._zh_font_url or default_zh_url
        en_font_url = self._en_font_url or default_en_url

        if not self._multi_1_use_main_font:
            zh_font_url_multi_1 = self._zh_font_url_multi_1 or default_zh_url_multi_1
            en_font_url_multi_1 = self._en_font_url_multi_1 or default_en_url_multi_1
        else:
            zh_font_url_multi_1 = zh_font_url
            en_font_url_multi_1 = en_font_url

        zh_extension = self.get_file_extension_from_url(zh_font_url, fallback_ext=".ttf")
        en_extension = self.get_file_extension_from_url(en_font_url, fallback_ext=".ttf")
        zh_extension_multi_1 = self.get_file_extension_from_url(zh_font_url_multi_1, fallback_ext=".ttf")
        en_extension_multi_1 = self.get_file_extension_from_url(en_font_url_multi_1, fallback_ext=".ttf")

        self._zh_font_path = path / f"zh{zh_extension}"
        self._en_font_path = path / f"en{en_extension}"
        self._zh_font_path_multi_1 = path / f"zh_multi_1{zh_extension_multi_1}"
        self._en_font_path_multi_1 = path / f"en_multi_1{en_extension_multi_1}"

        # 记录上次使用的 URL 哈希
        zh_hash_path = path / "zh_url.hash"
        en_hash_path = path / "en_url.hash"
        zh_hash_path_multi_1 = path / "zh_url_multi_1.hash"
        en_hash_path_multi_1 = path / "en_url_multi_1.hash"

        def url_changed(url, hash_path):
            url_hash = hashlib.md5(url.encode()).hexdigest()
            if not hash_path.exists() or hash_path.read_text() != url_hash:
                hash_path.write_text(url_hash)
                return True
            return False

        # 检查是否需要下载
        zh_changed = url_changed(zh_font_url, zh_hash_path)
        en_changed = url_changed(en_font_url, en_hash_path)
        zh_changed_multi_1 = url_changed(zh_font_url_multi_1, zh_hash_path_multi_1)
        en_changed_multi_1 = url_changed(en_font_url_multi_1, en_hash_path_multi_1)

        if zh_changed or not self._zh_font_path.exists():
            download_successful = self.download_font_safely(zh_font_url, self._zh_font_path)
            if not download_successful:
                logger.critical(f"无法获取必要的中文支持字体: {zh_font_url}")


        if en_changed or not self._en_font_path.exists():
            download_successful = self.download_font_safely(en_font_url, self._en_font_path)
            if not download_successful:
                logger.critical(f"无法获取必要的英文支持字体: {en_font_url}")

        if zh_changed_multi_1 or not self._zh_font_path_multi_1.exists():
            download_successful = self.download_font_safely(zh_font_url_multi_1, self._zh_font_path_multi_1)
            if not download_successful:
                logger.critical(f"无法获取必要的多图风格1中文支持字体: {zh_font_url_multi_1}")


        if en_changed_multi_1 or not self._en_font_path_multi_1.exists():
            download_successful = self.download_font_safely(en_font_url_multi_1, self._en_font_path_multi_1)
            if not download_successful:
                logger.critical(f"无法获取必要的多图风格1英文支持字体: {en_font_url_multi_1}")

    def prepare_library_images(self, library_dir: str):
        os.makedirs(library_dir, exist_ok=True)

        # --- 新增检查 ---
        # 检查 1.jpg 到 9.jpg 是否都已存在
        all_target_files_exist = True
        for i in range(1, 10):
            target_file_path = os.path.join(library_dir, f"{i}.jpg")
            if not os.path.exists(target_file_path):
                all_target_files_exist = False
                break # 只要有一个不存在，就无需继续检查

        if all_target_files_exist:
            # if logger:
            logger.info(f"信息: {library_dir} 中已存在 1-9.jpg，跳过生成和重命名步骤。")
            return True # 表示操作成功或无需操作
        # --- 检查结束 ---

        # 如果程序执行到这里，说明 1-9.jpg 并非全部存在，需要进行处理

        # 1. 获取所有原始图片，排除已经是 1.jpg ~ 9.jpg 的文件 (以防万一，虽然上面的检查会处理全部存在的情况)
        #    这些是我们选择的基础
        source_image_filenames = []
        for f in os.listdir(library_dir):
            if not re.match(r"^[1-9]\.jpg$", f, re.IGNORECASE): # 排除已是 1-9.jpg 的文件作为源
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    source_image_filenames.append(f)

        if not source_image_filenames:
            logger.info(f"警告: {library_dir} 中没有可用的原始图片（已排除 1-9.jpg）来生成新的 1-9.jpg。")
            return False

        source_image_paths = [os.path.join(library_dir, f) for f in sorted(source_image_filenames)]

        # 2. 从原始图片中选择或补足 9 张
        selected_final_sources = []
        if len(source_image_paths) >= 9:
            selected_final_sources = source_image_paths[:9]
        else:
            selected_final_sources = source_image_paths.copy()
            if source_image_paths:
                needed = 9 - len(selected_final_sources)
                selected_final_sources.extend(random.choices(source_image_paths, k=needed))
            else:
                logger.info(f"警告: {library_dir} 没有原始图片可用于复制填充。")
                return False

        if len(selected_final_sources) < 9:
            logger.info(f"错误: {library_dir} 无法准备足够的图片凑成9张，实际只有 {len(selected_final_sources)} 张。")
            return False

        # 3. 删除原有的 1.jpg ~ 9.jpg (如果存在部分)
        #    这一步是为了确保我们是从一个干净的状态开始创建新的 1-9.jpg
        for i in range(1, 10):
            fpath = os.path.join(library_dir, f"{i}.jpg")
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except OSError as e:
                    logger.info(f"错误: 无法删除文件 {fpath}: {e}")
                    return False

        # 4. 将选定的源图片复制并重命名为 1.jpg ~ 9.jpg
        for idx, original_img_path in enumerate(selected_final_sources, 1):
            target_path = os.path.join(library_dir, f"{idx}.jpg")
            try:
                if not os.path.exists(original_img_path):
                    logger.info(f"错误: 源文件 {original_img_path} 在尝试复制前找不到了！")
                    return False
                shutil.copy(original_img_path, target_path)
            except FileNotFoundError:
                logger.info(f"错误: 复制文件失败: 源文件 {original_img_path} 未找到。")
                return False
            except Exception as e:
                logger.info(f"错误: 复制文件 {original_img_path} 到 {target_path} 时发生错误: {e}")
                return False

        logger.info(f"信息: {library_dir} 已准备好 1~9.jpg")
        return True
    
    def update_all_libraries(self):
        """
        定时更新所有媒体库的背景图
        """
        if not self._enabled:
            return
        # 所有媒体服务器
        service_infos = self.service_infos()
        if not service_infos:
            return
        
        self.__get_fonts()  
        for server, service in service_infos.items():
            # 扫描所有媒体库
            logger.info(f"开始更新服务器 {server} 的媒体库背景...")
            logger.info(f"当前选择的风格: {self._cover_style}")
            # 获取媒体库列表
            libraries = self.mschain.librarys(server)
            if not libraries:
                logger.warning(f"获取服务器 {server} 的媒体库列表失败")
                continue
            for library in libraries:
                if self._event.is_set():
                    logger.info("媒体库背景图更新服务停止")
                    return
                    
                logger.info(f"开始更新媒体库 {library.name} 的背景图...")
                matched = False
                # 优先使用自定义背景图
                library_dir = os.path.join(self._covers_input, library.name)
                if os.path.isdir(library_dir):
                    images = sorted([
                        os.path.join(library_dir, f)
                        for f in os.listdir(library_dir)
                        if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"))
                    ])
                    if images:
                        if self._cover_style.startswith("single"):
                            image_path = images[0]
                            logger.info(f"找到自定义单图背景图: {image_path}")
                            self.__update_library_backdrop(
                                server=server, 
                                server_type=service.type,
                                library_id=library.id, 
                                library_name=library.name,
                                image_path=image_path
                            )
                            logger.info(f"媒体库 {library.name} 背景图已更新")
                            matched = True
                        elif self._cover_style.startswith("multi"):
                            if self.prepare_library_images(library_dir):
                                self.__update_library_backdrop(
                                    server=server, 
                                    server_type=service.type,
                                    library_id=library.id, 
                                    library_name=library.name,
                                    cover_path=self._covers_input
                                )
                                logger.info(f"媒体库 {library.name} 背景图已更新")
                                matched = True
                            else:
                                logger.info(f"从自定义目录：{library_dir} 生成封面失败:")
                                # 继续尝试下一个匹配方式
                
                # 如果自定义背景图没有匹配成功，尝试使用最新项目的背景图
                if not matched:
                    def has_valid_image(item):
                        return (
                            (item.get('BackdropImageTags') and len(item['BackdropImageTags']) > 0) or
                            (item.get('ImageTags') and item['ImageTags'].get('Primary')) or
                            (item.get('ParentBackdropImageTags') and len(item['ParentBackdropImageTags']) > 0)
                        )
                    # 获取最新项目
                    latest_items = self.__get_latest_items(server, service.type, library.id, library.name)
                    items = [
                        item
                        for item in latest_items.get('Items', [])
                        if has_valid_image(item)
                    ]
                    if not items:
                        logger.info(f"媒体库 {library.name} 中没有项目")
                        continue
                    
                    if self._cover_style.startswith('single'):
                        item = items[0]
                        item_id = item.get('SeriesId') or item.get('Id')

                        self.update_cover_history(
                            server=server, 
                            server_type=service.type,
                            library_id=library.id, 
                            library_name=library.name,
                            item_id=item_id
                        )

                        # 使用第一个项目的背景图
                        if self.__update_library_backdrop(
                            server=server, 
                            server_type=service.type,
                            library_id=library.id, 
                            library_name=library.name,
                            item_id=item_id
                        ):
                            logger.info(f"媒体库 {library.name} 背景图已更新")
                    
                    elif self._cover_style.startswith('multi'):
                        if len(items) < 9:
                            items += random.choices(items, k=9 - len(items))
                        item_ids = [item.get('Id') for item in items]
                        for item_id in item_ids:
                            self.update_cover_history(
                                server=server, 
                                server_type=service.type,
                                library_id=library.id, 
                                library_name=library.name,
                                item_id=item_id
                            )
                        # 使用多个项目的背景图
                        if self.__update_library_backdrop(
                            server=server, 
                            server_type=service.type,
                            library_id=library.id, 
                            library_name=library.name,
                            item_ids=item_ids
                        ):
                            logger.info(f"媒体库 {library.name} 背景图已更新")
                    
            logger.info(f"服务器 {server} 的媒体库背景更新完成")
    
    def __update_library_backdrop(self, server, server_type, library_id, library_name, item_id=None, item_ids=None, image_path=None, cover_path=None):
        """
        将媒体项的背景图设置为媒体库的背景图
        """
        try:
            
            if image_path:
                image_path = image_path
            elif cover_path:
                image_path = cover_path
            elif item_id:
                # 获取媒体项详情
                iteminfo = self.get_iteminfo(server, server_type, item_id)
                # logger.info(f"媒体详情：{iteminfo}")
                if not iteminfo:
                    logger.warning(f"获取媒体项 {item_id} 详情失败")
                    return False
                # 获取背景图URL
                backdrop_url = self.__get_backdrop_url(library_name, iteminfo)
                if not backdrop_url:
                    logger.warning(f"媒体项 {iteminfo.get('Name', item_id)} 没有背景图")
                    return False
                
                # 记录背景图URL
                # logger.info(f"为媒体库 {library_id} 获取到背景图 URL: {backdrop_url}")
                
                # 下载并处理背景图
                image_path = self.__download_image(backdrop_url, library_name, count=1)
                if not image_path:
                    logger.warning(f"下载背景图失败: {backdrop_url}")
                    return False
            elif item_ids:
                count = 0
                for item_id in item_ids:
                    iteminfo = self.get_iteminfo(server, server_type, item_id)
                    if not iteminfo:
                        logger.warning(f"获取媒体项 {item_id} 详情失败")
                        continue
                    backdrop_url = self.__get_backdrop_url(library_name, iteminfo)
                    if not backdrop_url:
                        logger.warning(f"媒体项 {iteminfo.get('Name', item_id)} 没有背景图")
                        continue
                    image_path = self.__download_image(backdrop_url, library_name, count=count+1)
                    if not image_path:
                        logger.warning(f"下载背景图失败: {backdrop_url}")
                        continue
                    count += 1
                    if count == 9:
                        image_path = self._cover_path
                        break
                
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
            
            if self._title_config:
                title_config = load_and_validate_titles(self._title_config)
                zh_title = en_title = None  # 初始化为空，避免未匹配时报错

                for lib_name, (zh, en) in title_config.items():
                    if lib_name == library_name:
                        zh_title = zh
                        en_title = en
                        break

                # 这里应该是您已有的图像处理代码
                if self._cover_style == 'single_1':
                    image_data = create_style_single_1(image_path, library_name, zh_title, en_title, self._zh_font_path, self._en_font_path)
                elif self._cover_style == 'single_2':
                    image_data = create_style_single_2(image_path, library_name, zh_title, en_title, self._zh_font_path, self._en_font_path)
                elif self._cover_style == 'multi_1':
                    image_data = create_style_multi_1(image_path, library_name, zh_title, en_title, self._zh_font_path_multi_1, self._en_font_path_multi_1, is_blur=self._multi_1_blur)
                    # 这里是还没写的新方法，需要多张图片
                # 更新媒体库背景图
                result = self.__set_library_image(server, server_type, library_id, library_name, image_data)
                if result:
                    return True
                else:
                    return False
                    
        except Exception as err:
            logger.error(f"更新媒体库背景图失败: {str(err)}")
            return False
        
    def __get_latest_items(self, server, server_type, library_id, library_name):
        """
        Get latest items in the media library
        """
        try:
            service = self.service_infos(server_type).get(server)
            if not service:
                logger.warning(f"未找到媒体服务器 {server} 的实例")
                return {}
            
            try:
                if not self._sort_by:
                    self._sort_by = 'Random'

                date_created = 'Movie,Episode' if self._cover_style.startswith('single') else 'Movie,Series'
                limit = '3' if self._cover_style.startswith('single') else '18'
                
                include_item_types = {
                    "PremiereDate": "Movie,Series",
                    "DateCreated": date_created,
                    "Random": "Movie,Series"
                }[self._sort_by]

                if library_name == self._music_name:
                    include_item_types = 'MusicAlbum'
                elif library_name == self._collection_name:
                    include_item_types = 'BoxSet'

                url = f'[HOST]emby/Items/?api_key=[APIKEY]' \
                      f'&ParentId={library_id}&SortBy={self._sort_by}&Limit={limit}' \
                      f'&Recursive=True&IncludeItemTypes={include_item_types}&SortOrder=Descending'

                res = service.instance.get_data(url=url)
                if res:
                    return res.json()
            except Exception as err:
                logger.error(f"获取Emby媒体项详情失败：{str(err)}")
            return {}
                
        except Exception as err:
            logger.error(f"Failed to get latest items: {str(err)}")
            return None
        
    def __get_backdrop_url(self, library_name, iteminfo):
        """
        从媒体项信息中获取背景图URL
        """
        # Emby/Jellyfin
        if library_name == self._music_name:
            if iteminfo.get("ImageTags") and iteminfo.get("ImageTags").get("Primary"):
                item_id = iteminfo.get("Id")
                tag = iteminfo.get("ImageTags").get("Primary")
                return f'[HOST]emby/Items/{item_id}/Images/Primary?tag={tag}&api_key=[APIKEY]'
            elif iteminfo.get("ParentBackdropImageTags") and len(iteminfo["ParentBackdropImageTags"]) > 0:
                item_id = iteminfo.get("ParentBackdropItemId")
                tag = iteminfo["ParentBackdropImageTags"][0]
                return f'[HOST]emby/Items/{item_id}/Images/Backdrop/0?tag={tag}&api_key=[APIKEY]'

        elif self._cover_style.startswith('multi'):
            if iteminfo.get("ImageTags") and iteminfo.get("ImageTags").get("Primary"):
                item_id = iteminfo.get("Id")
                tag = iteminfo.get("ImageTags").get("Primary")
                return f'[HOST]emby/Items/{item_id}/Images/Primary?tag={tag}&api_key=[APIKEY]'

        elif self._cover_style.startswith('single'):
            if iteminfo.get("BackdropImageTags") and len(iteminfo["BackdropImageTags"]) > 0:
                item_id = iteminfo.get("Id")
                tag = iteminfo["BackdropImageTags"][0]
                return f'[HOST]emby/Items/{item_id}/Images/Backdrop/0?tag={tag}&api_key=[APIKEY]'

    def __download_image(self, imageurl, library_name, count=None, retries=3, delay=1):
        """
        下载图片，保存到本地目录 self._cover_path/library_name/ 下，文件名为 1-9.jpg
        若已存在则跳过下载，直接返回图片路径。
        下载失败时重试若干次。
        """
        try:
            # 创建目标子目录
            subdir = os.path.join(self._cover_path, library_name)
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
                    service_infos = self.service_infos()
                    if not service_infos:
                        return None

                    for service_name, service_info in service_infos.items():
                        r = service_info.instance.get_data(url=imageurl)
                        if r and r.status_code == 200:
                            image_content = r.content
                            break
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

    def get_iteminfo(self, server, server_type, itemid) -> dict:
        """
        获取媒体项详情
        """
        service = self.service_infos(server_type).get(server)
        if not service:
            logger.warning(f"未找到媒体服务器 {server} 的实例")
            return {}

        try:
            image_tag = 'BackdropImageTags' if self._cover_style.startswith('single') else 'ImageTags'
            url = f'[HOST]emby/Users/[USER]/Items/{itemid}?Fields={image_tag}&api_key=[APIKEY]'
            res = service.instance.get_data(url=url)
            if res:
                return res.json()
        except Exception as err:
            logger.error(f"获取 {itemid} 详情失败：{str(err)}")
        return {}
        

    def __set_library_image(self, server, server_type, library_id, library_name, image_base64):
        """
        设置媒体库背景图
        """
        service = self.service_infos(server_type).get(server)
        if not service:
            logger.warning(f"未找到媒体服务器 {server} 的实例")
            return False

        """设置Emby媒体库背景图"""
        try:
            url = f'[HOST]emby/Items/{library_id}/Images/Primary?api_key=[APIKEY]'
            
            # 在发送前保存一份图片到本地
            if self._covers_output:
                try:
                    image_bytes = base64.b64decode(image_base64)
                    self.__save_image_to_local(image_bytes, f"{library_name}.jpg")
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
                logger.error(f"设置「{library_name}」背景图失败，错误码：{res.status_code if res else 'No response'}")
                return False
        except Exception as err:
            logger.error(f"设置「{library_name}」背景图失败：{str(err)}")
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