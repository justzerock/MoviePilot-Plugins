import time
import json
import requests
from pathlib import Path
from typing import Any, List, Dict, Tuple, Optional

from app.core.context import MediaInfo
from app.core.event import eventmanager, Event
from app.helper.mediaserver import MediaServerHelper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import TransferInfo, RefreshMediaItem, ServiceInfo
from app.schemas.types import EventType


class MediaServerRefreshMod(_PluginBase):
    # 插件名称
    plugin_name = "Emby媒体库刷新"
    # 插件描述
    plugin_desc = "入库后自动刷新Emby服务器海报墙。"
    # 插件图标
    plugin_icon = "refresh2.png"
    # 插件版本
    plugin_version = "0.0.2"
    # 插件作者
    plugin_author = "jxxghp, justzerock"
    # 作者主页
    author_url = "https://github.com/justzerock/MoviePilot-Plugins"
    # 插件配置项ID前缀
    plugin_config_prefix = "mediaserverrefreshmod_"
    # 加载顺序
    plugin_order = 14
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    mediaserver_helper = None
    _enabled = False
    _delay = 0
    _emby_api_url = None
    _emby_api_key = None

    def init_plugin(self, config: dict = None):
        self.mediaserver_helper = MediaServerHelper()
        if config:
            self._enabled = config.get("enabled")
            self._delay = config.get("delay") or 0
            self._emby_api_url = config.get("emby_api_url")
            self._emby_api_key = config.get("emby_api_key")

    def notify_emby_scan(self, file_path):
        """
        通知Emby扫描文件
        """
        if not self._emby_api_url or not self._emby_api_key:
            logger.warning("Emby API URL或API Key未配置，无法刷新媒体库")
            return False
            
        # 构建 Emby 通知的 JSON 数据
        json_data = {
            "Updates": [
                {
                    "Path": file_path,
                    "UpdateType": "Created"
                }
            ]
        }

        try:
            # 发送 Emby 通知
            response = requests.post(
                f"{self._emby_api_url}/emby/Library/Media/Updated?api_key={self._emby_api_key}",
                headers={'accept': '*/*', 'Content-Type': 'application/json'},
                data=json.dumps(json_data)
            )
            if response.status_code == 204 or response.status_code == 200:
                logger.info(f"Emby刷新请求发送成功: {file_path}")
                return True
            else:
                logger.error(f"Emby刷新请求失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Emby刷新请求异常: {str(e)}")
            return False

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
        """
        return [
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
                                    'md': 6
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
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'emby_api_url',
                                            'label': 'Emby API URL',
                                            'placeholder': 'http://emby:8096/emby/Library/Media/Updated'
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
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'emby_api_key',
                                            'label': 'Emby API Key',
                                            'placeholder': '输入您的Emby API密钥'
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
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'delay',
                                            'label': '延迟时间（秒）',
                                            'placeholder': '0'
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False,
            "delay": 0,
            "emby_api_url": "",
            "emby_api_key": ""
        }

    def get_page(self) -> List[dict]:
        pass

    @eventmanager.register(EventType.TransferComplete)
    def refresh(self, event: Event):
        """
        发送通知消息
        """
        if not self._enabled:
            return

        event_info: dict = event.event_data
        if not event_info:
            return

        # 延迟刷新
        if self._delay:
            logger.info(f"延迟 {self._delay} 秒后刷新Emby媒体库... ")
            time.sleep(float(self._delay))

        # 入库数据
        transferinfo: TransferInfo = event_info.get("transferinfo")
        if not transferinfo or not transferinfo.target_diritem or not transferinfo.target_diritem.path:
            return

        # 获取文件路径
        file_path = transferinfo.target_diritem.path
        
        # 通知Emby刷新
        self.notify_emby_scan(file_path)

    def stop_service(self):
        """
        退出插件
        """
        pass