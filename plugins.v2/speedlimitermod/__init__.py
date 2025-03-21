import ipaddress
from typing import List, Tuple, Dict, Any, Optional

from app.core.event import eventmanager, Event
from app.helper.downloader import DownloaderHelper
from app.helper.mediaserver import MediaServerHelper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import NotificationType, WebhookEventInfo, ServiceInfo
from app.schemas.types import EventType
from app.utils.ip import IpUtils


class SpeedLimiterMod(_PluginBase):
    # 插件名称
    plugin_name = "播放限速"
    # 插件描述
    plugin_desc = "外网播放媒体库视频时，自动对下载器进行限速。"
    # 插件图标
    plugin_icon = "Librespeed_A.png"
    # 插件版本
    plugin_version = "3.1.7"
    # 插件作者
    plugin_author = "Shurelol, justzerock"
    # 作者主页
    author_url = "https://github.com/justzerock/MoviePilot-Plugins"
    # 插件配置项ID前缀
    plugin_config_prefix = "speedlimitmod_"
    # 加载顺序
    plugin_order = 11
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    downloader_helper = None
    mediaserver_helper = None
    _scheduler = None
    _enabled: bool = False
    _notify: bool = False
    _interval: int = 60
    _downloader: list = []
    _play_up_speed: float = 0
    _play_down_speed: float = 0
    _noplay_up_speed: float = 0
    _noplay_down_speed: float = 0
    _bandwidth_up: float = 0
    _bandwidth_down: float = 0
    _allocation_ratio_up: str = ""
    _allocation_ratio_down: str = ""
    _auto_limit: bool = False
    _limit_enabled: bool = False
    # 不限速地址
    _unlimited_ips = {}
    # 当前限速状态
    _current_state = ""
    _include_path_up = ""
    _include_path_down = ""

    def init_plugin(self, config: dict = None):
        self.downloader_helper = DownloaderHelper()
        self.mediaserver_helper = MediaServerHelper()
        # 读取配置
        if config:
            self._enabled = config.get("enabled")
            self._notify = config.get("notify")
            self._play_up_speed = float(config.get("play_up_speed")) if config.get("play_up_speed") else 0
            self._play_down_speed = float(config.get("play_down_speed")) if config.get("play_down_speed") else 0
            self._noplay_up_speed = float(config.get("noplay_up_speed")) if config.get("noplay_up_speed") else 0
            self._noplay_down_speed = float(config.get("noplay_down_speed")) if config.get("noplay_down_speed") else 0
            self._current_state = f"U:{self._noplay_up_speed},D:{self._noplay_down_speed}"
            self._include_path_up = config.get("include_path_up")
            self._include_path_down = config.get("include_path_down")

            try:
                # 总带宽
                self._bandwidth_up = int(float(config.get("bandwidth_up") or 0)) * 1024*1024
                self._bandwidth_down = int(float(config.get("bandwidth_down") or 0)) * 1024*1024
                # 自动限速开关
                if self._bandwidth_up > 0 or self._bandwidth_down > 0:
                    self._auto_limit = True
                else:
                    self._auto_limit = False
            except Exception as e:
                logger.error(f"智能限速上行带宽设置错误：{str(e)}")
                self._bandwidth_up = 0
                self._bandwidth_down = 0

            # 限速服务开关
            self._limit_enabled = True if (self._play_up_speed
                                           or self._play_down_speed
                                           or self._auto_limit) else False
            self._allocation_ratio_up = config.get("allocation_ratio_up") or ""
            self._allocation_ratio_down = config.get("allocation_ratio_down") or ""
            # 不限速地址
            self._unlimited_ips["ipv4"] = config.get("ipv4") or ""
            self._unlimited_ips["ipv6"] = config.get("ipv6") or ""

            self._downloader = config.get("downloader") or []

            self.check_playing_sessions()

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass

    def get_service(self) -> List[Dict[str, Any]]:
        """
        注册插件公共服务
        [{
            "id": "服务ID",
            "name": "服务名称",
            "trigger": "触发器：cron/interval/date/CronTrigger.from_crontab()",
            "func": self.xxx,
            "kwargs": {} # 定时器参数
        }]
        """
        if self._enabled and self._limit_enabled and self._interval:
            return [
                {
                    "id": "AdvancedSpeedLimiter",
                    "name": "播放限速检查服务",
                    "trigger": "interval",
                    "func": self.check_playing_sessions,
                    "kwargs": {"seconds": self._interval}
                }
            ]
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
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
                            },
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
                                            'model': 'notify',
                                            'label': '发送通知',
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
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VSelect',
                                        'props': {
                                            'multiple': True,
                                            'chips': True,
                                            'clearable': True,
                                            'model': 'downloader',
                                            'label': '下载器',
                                            'items': [{"title": config.name, "value": config.name}
                                                      for config in self.downloader_helper.get_configs().values()]
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
                                            'model': 'play_up_speed',
                                            'label': '播放限速（上传）',
                                            'placeholder': 'KB/s'
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
                                            'model': 'play_down_speed',
                                            'label': '播放限速（下载）',
                                            'placeholder': 'KB/s'
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
                                            'model': 'noplay_up_speed',
                                            'label': '未播放限速（上传）',
                                            'placeholder': 'KB/s'
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
                                            'model': 'noplay_down_speed',
                                            'label': '未播放限速（下载）',
                                            'placeholder': 'KB/s'
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
                                            'model': 'bandwidth_up',
                                            'label': '智能限速上行带宽',
                                            'placeholder': 'Mbps'
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
                                            'model': 'allocation_ratio_up',
                                            'label': '智能限速分配比例',
                                            'placeholder': '3:2:1'
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
                                            'model': 'bandwidth_down',
                                            'label': '智能限速下行带宽',
                                            'placeholder': 'Mbps'
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
                                            'model': 'allocation_ratio_down',
                                            'label': '智能限速分配比例',
                                            'placeholder': '0:0:1'
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
                                            'model': 'ipv4',
                                            'label': '不限速地址范围（ipv4）',
                                            'placeholder': '留空默认不限速内网ipv4'
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
                                            'model': 'ipv6',
                                            'label': '不限速地址范围（ipv6）',
                                            'placeholder': '留空默认不限速内网ipv6'
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
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'include_path_up',
                                            'label': '外网上传限速路径',
                                            'placeholder': '包含该路径的媒体限速,多个请换行'
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
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'include_path_down',
                                            'label': '内网下载限速路径',
                                            'placeholder': '包含该路径的媒体限速,多个请换行'
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
            "notify": True,
            "downloader": [],
            "play_up_speed": None,
            "play_down_speed": None,
            "noplay_up_speed": None,
            "noplay_down_speed": None,
            "bandwidth_up": None,
            "bandwidth_down": None,
            "allocation_ratio_up": "",
            "allocation_ratio_down": "",
            "ipv4": "",
            "ipv6": "",
            "include_path_up": "",
            "include_path_down": ""
        }

    def get_page(self) -> List[dict]:
        pass

    @property
    def service_infos(self) -> Optional[Dict[str, ServiceInfo]]:
        """
        服务信息
        """
        if not self._downloader:
            logger.warning("尚未配置下载器，请检查配置")
            return None

        services = self.downloader_helper.get_services(name_filters=self._downloader)
        if not services:
            logger.warning("获取下载器实例失败，请检查配置")
            return None

        active_services = {}
        for service_name, service_info in services.items():
            if service_info.instance.is_inactive():
                logger.warning(f"下载器 {service_name} 未连接，请检查配置")
            else:
                active_services[service_name] = service_info

        if not active_services:
            logger.warning("没有已连接的下载器，请检查配置")
            return None

        return active_services

    @eventmanager.register(EventType.WebhookMessage)
    def check_playing_sessions(self, event: Event = None):
        """
        检查播放会话
        """
        media_info = {}
        if not self.service_infos:
            return
        if not self._enabled:
            return
        if event:
            event_data: WebhookEventInfo = event.event_data
            media_info['event'] = self.__get_play_event(event_data.event)
            media_info['title'] = event_data.item_name
            media_info['user'] = event_data.user_name
            media_info['is_up'] = self.__path_included(event_data.item_path, is_up=True)
            media_info['is_down'] = self.__path_included(event_data.item_path, is_up=False)
            service = self.service_infos().get(event_data.server_name)
            if service:
                media_info['link'] = service.instance.get_play_url(event_data.item_id)
            else:
                media_info['link'] = ''
            if event_data.event not in [
                "playback.start",
                "PlaybackStart",
                "media.play",
                "media.stop",
                "PlaybackStop",
                "playback.stop"
            ]:
                return
        # 当前播放的总比特率
        total_bit_rate_up = 0
        total_bit_rate_down = 0
        media_now = []
        media_servers = self.mediaserver_helper.get_services()
        if not media_servers:
            return
        # 查询所有媒体服务器状态
        for server, service in media_servers.items():
            # 查询播放中会话
            playing_sessions_up = []
            playing_sessions_down = []
            if service.type == "emby":
                req_url = "[HOST]emby/Sessions?api_key=[APIKEY]"
                try:
                    res = service.instance.get_data(req_url)
                    if res and res.status_code == 200:
                        sessions = res.json()
                        for session in sessions:
                            # logger.info(session)
                            if session.get("NowPlayingItem") and not session.get("PlayState", {}).get("IsPaused"):
                                media_now.append(self.__get_media_info(session))
                                if self.__path_included(session.get("NowPlayingItem").get("Path"), is_up=True):
                                    playing_sessions_up.append(session)
                                elif self.__path_included(session.get("NowPlayingItem").get("Path"), is_up=False):
                                    playing_sessions_down.append(session)

                except Exception as e:
                    logger.error(f"获取Emby播放会话失败：{str(e)}")
                    continue
                # 计算有效比特率
                for session in playing_sessions_up:
                    # 设置了不限速范围则判断session ip是否在不限速范围内
                    if self._unlimited_ips["ipv4"] or self._unlimited_ips["ipv6"]:
                        if not self.__allow_access(self._unlimited_ips, session.get("RemoteEndPoint")) \
                                and session.get("NowPlayingItem", {}).get("MediaType") == "Video":
                            total_bit_rate_up += int(session.get("NowPlayingItem", {}).get("Bitrate") or 0)
                    # 未设置不限速范围，则默认不限速内网ip
                    elif not IpUtils.is_private_ip(session.get("RemoteEndPoint")) \
                            and session.get("NowPlayingItem", {}).get("MediaType") == "Video":
                        total_bit_rate_up += int(session.get("NowPlayingItem", {}).get("Bitrate") or 0)
                for session in playing_sessions_down:
                    # 设置了不限速范围则判断session ip是否在不限速范围内
                    if self._unlimited_ips["ipv4"] or self._unlimited_ips["ipv6"]:
                        if not self.__allow_access(self._unlimited_ips, session.get("RemoteEndPoint")) \
                                and session.get("NowPlayingItem", {}).get("MediaType") == "Video":
                            total_bit_rate_down += int(session.get("NowPlayingItem", {}).get("Bitrate") or 0)
                    # 未设置不限速范围，则默认限速内网ip
                    elif IpUtils.is_private_ip(session.get("RemoteEndPoint")) \
                            and session.get("NowPlayingItem", {}).get("MediaType") == "Video":
                        total_bit_rate_down += int(session.get("NowPlayingItem", {}).get("Bitrate") or 0)
            elif service.type == "jellyfin":
                req_url = "[HOST]Sessions?api_key=[APIKEY]"
                try:
                    res = service.instance.get_data(req_url)
                    if res and res.status_code == 200:
                        sessions = res.json()
                        for session in sessions:
                            if session.get("NowPlayingItem") and not session.get("PlayState", {}).get("IsPaused"):
                                if self.__path_included(session.get("NowPlayingItem").get("Path"), is_up=True):
                                    playing_sessions_up.append(session)
                                elif self.__path_included(session.get("NowPlayingItem").get("Path"), is_up=False):
                                    playing_sessions_down.append(session)
                except Exception as e:
                    logger.error(f"获取Jellyfin播放会话失败：{str(e)}")
                    continue
                # 计算有效比特率
                for session in playing_sessions_up:
                    # 设置了不限速范围则判断session ip是否在不限速范围内
                    if self._unlimited_ips["ipv4"] or self._unlimited_ips["ipv6"]:
                        if not self.__allow_access(self._unlimited_ips, session.get("RemoteEndPoint")) \
                                and session.get("NowPlayingItem", {}).get("MediaType") == "Video":
                            media_streams = session.get("NowPlayingItem", {}).get("MediaStreams") or []
                            for media_stream in media_streams:
                                total_bit_rate_up += int(media_stream.get("BitRate") or 0)
                    # 未设置不限速范围，则默认不限速内网ip
                    elif not IpUtils.is_private_ip(session.get("RemoteEndPoint")) \
                            and session.get("NowPlayingItem", {}).get("MediaType") == "Video":
                        media_streams = session.get("NowPlayingItem", {}).get("MediaStreams") or []
                        for media_stream in media_streams:
                            total_bit_rate_up += int(media_stream.get("BitRate") or 0)
                for session in playing_sessions_down:
                    # 设置了不限速范围则判断session ip是否在不限速范围内
                    if self._unlimited_ips["ipv4"] or self._unlimited_ips["ipv6"]:
                        if not self.__allow_access(self._unlimited_ips, session.get("RemoteEndPoint")) \
                                and session.get("NowPlayingItem", {}).get("MediaType") == "Video":
                            media_streams = session.get("NowPlayingItem", {}).get("MediaStreams") or []
                            for media_stream in media_streams:
                                total_bit_rate_down += int(media_stream.get("BitRate") or 0)
                    # 未设置不限速范围，则默认限速内网ip
                    elif IpUtils.is_private_ip(session.get("RemoteEndPoint")) \
                            and session.get("NowPlayingItem", {}).get("MediaType") == "Video":
                        media_streams = session.get("NowPlayingItem", {}).get("MediaStreams") or []
                        for media_stream in media_streams:
                            total_bit_rate_down += int(media_stream.get("BitRate") or 0)
            elif service.type == "plex":
                _plex = service.instance.get_plex()
                if _plex:
                    sessions = _plex.sessions()
                    for session in sessions:
                        bitrate = sum([m.bitrate or 0 for m in session.media])
                        playing_sessions_up.append({
                            "type": session.TAG,
                            "bitrate": bitrate,
                            "address": session.player.address
                        })
                    # 计算有效比特率
                    for session in playing_sessions_up:
                        # 设置了不限速范围则判断session ip是否在不限速范围内
                        if self._unlimited_ips["ipv4"] or self._unlimited_ips["ipv6"]:
                            if not self.__allow_access(self._unlimited_ips, session.get("address")) \
                                    and session.get("type") == "Video":
                                total_bit_rate_up += int(session.get("bitrate") or 0)
                        # 未设置不限速范围，则默认不限速内网ip
                        elif not IpUtils.is_private_ip(session.get("address")) \
                                and session.get("type") == "Video":
                            total_bit_rate_up += int(session.get("bitrate") or 0)
        media_info['playing'] = media_now
        media_info['bitrate_up'] = total_bit_rate_up
        media_info['bitrate_down'] = total_bit_rate_down
        if total_bit_rate_up or total_bit_rate_down:
            # 开启智能限速计算上传限速
            if self._auto_limit:
                play_up_speed = self.__calc_limit(total_bit_rate_up, is_up=True)
                play_down_speed = self.__calc_limit(total_bit_rate_down, is_up=False)
            else:
                play_up_speed = self._play_up_speed
                play_down_speed = self._play_down_speed

            # 当前正在播放，开始限速
            self.__set_limiter(limit_type="播放", 
                               upload_limit=play_up_speed,
                               download_limit=play_down_speed,
                               media_info=media_info)
        else:
            if self._auto_limit:
                noplay_up_speed = int(self._bandwidth_up / 8 / 1024)
                noplay_down_speed = int(self._bandwidth_down / 8 / 1024)
            else:
                # 当前没有播放，取消限速
                noplay_up_speed = self._noplay_up_speed
                noplay_down_speed = self._noplay_down_speed

            self.__set_limiter(limit_type="未播放", 
                               upload_limit=noplay_up_speed,
                                download_limit=noplay_down_speed,
                                media_info=media_info)

    def __get_media_info(self, session: dict) -> dict:
        """
        获取媒体信息
        """
        user = session.get("UserName", "")
        item = session.get("NowPlayingItem", {})
        series_name = item.get('SeriesName', '')
        if series_name:
            title = f"{series_name} S{item.get('ParentIndexNumber')}E{item.get('IndexNumber')} {item.get('Name')}"
        else:
            title = f"{item.get('Name')} ({item.get('ProductionYear')})"
        # path = item.get("Path", "")
        bitrate = round(int(item.get("Bitrate", 0))/1024/1024, 1)
        media_info = {
            "user": user,
            "title": title,
            'bitrate': f"{bitrate} mbps",
        }
        return media_info

    def __path_included(self, path: str, is_up: bool) -> bool:
        """
        判断是否在限速路径内
        """
        if is_up:
            if self._include_path_up:
                include_paths = self._include_path_up.split("\n")
                for include_path_up in include_paths:
                    if include_path_up in path:
                        # logger.info(f"{path} 在限速路径：{include_path_up} 内，限速")
                        return True
            return False
        else:
            if self._include_path_down:
                include_paths = self._include_path_down.split("\n")
                for include_path_down in include_paths:
                    if include_path_down in path:
                        # logger.info(f"{path} 在限速路径：{include_path_down} 内，限速")
                        return True
            return False
        
    def __get_play_event(self, event: str) -> str:
        """
        获取播放事件
        """
        if event in [
                "playback.start",
                "PlaybackStart",
                "media.play",
            ]:
            return "start"
        else:
            return "stop"
    
    def __calc_limit(self, total_bit_rate: float, is_up: bool) -> float:
        """
        计算智能上传限速
        """
        if is_up:
            if not self._bandwidth_up:
                return 10
            return round((self._bandwidth_up - total_bit_rate) / 8 / 1024, 2)
        else:
            if not self._bandwidth_down:
                return 10
            return round((self._bandwidth_down - total_bit_rate) / 8 / 1024, 2)

    def __set_limiter(self, limit_type: str, upload_limit: float, download_limit: float, media_info: dict):
        """
        设置限速
        """
        if not self.service_infos:
            return
        state = f"U:{upload_limit},D:{download_limit}"
        if self._current_state == state:
            # 限速状态没有改变
            return
        else:
            self._current_state = state
            
        try:
            cnt = 0
            upload_limit_final = None
            download_limit_final = None
            notify_text_speed = "═══ 限速状态 ═══\n"
            for download in self._downloader:
                service = self.service_infos.get(download)
                # if self._auto_limit and limit_type == "播放":
                if self._auto_limit:
                    # 开启了播放智能限速
                    if len(self._downloader) == 1:
                        # 只有一个下载器
                        upload_limit_final = int(upload_limit)
                        download_limit_final = int(download_limit)
                    else:
                        # 多个下载器
                        if not self._allocation_ratio_up or not self._allocation_ratio_down:
                            # 平均
                            upload_limit_final = int(upload_limit / len(self._downloader))
                            download_limit_final = int(download_limit / len(self._downloader))
                        else:
                            # 按比例
                            allocation_count_up = sum([int(i) for i in self._allocation_ratio_up.split(":")])
                            weight_up = int(self._allocation_ratio_up.split(":")[cnt])
                            if weight_up == 0:
                                upload_limit_final = 0
                            else:
                                upload_limit_final = int(upload_limit * weight_up / allocation_count_up)
                            allocation_count_down = sum([int(i) for i in self._allocation_ratio_down.split(":")])
                            weight_down = int(self._allocation_ratio_down.split(":")[cnt])
                            if weight_down == 0:
                                download_limit_final = 0
                            else:
                                download_limit_final = int(download_limit * weight_down / allocation_count_down)
                            cnt += 1
                if upload_limit_final:
                    text = f"⇡ {round(upload_limit_final/1024,1)}"
                else:
                    text = f"⇡ ∞"
                if download_limit_final:
                    text = f"{text} ⇣ {round(download_limit_final/1024,1)} MB/s"
                else:
                    text = f"{text} ⇣ ∞ MB/s"
                notify_text_speed = f"{notify_text_speed} {download} {text}\n"
                if service.type == 'qbittorrent':
                    service.instance.set_speed_limit(download_limit=download_limit_final, upload_limit=upload_limit_final)
                else:
                    upload_limit_final = upload_limit_final if upload_limit_final > 0 else -1
                    download_limit_final = download_limit_final if download_limit_final > 0 else -1
                    service.instance.set_speed_limit(download_limit=download_limit_final, upload_limit=upload_limit_final)

            notify_title = ''
            if media_info['title']:
                text_up = ' ⇡' if media_info['is_up'] else ''
                text_down = ' ⇣' if media_info['is_down'] else ''
                if media_info['event'] == "start":
                    notify_title = f"[+] {media_info['title']}{text_up}{text_down}\n"
                elif media_info['event'] == "stop":
                    notify_title = f"[-] {media_info['title']}\n"
            else:
                notify_title = ''
            link = media_info['link']
            index = 1
            playing_text = ''
            if media_info['playing']:
                playing_text = '\n═══ 正在播放 ═══\n'
                bitrate_up = ''
                bitrate_down = ''
                if media_info['bitrate_up']:
                    bitrate_up = f"⇡ {round(int(media_info['bitrate_up'])/1024/1024,1)} mbps "
                if media_info['bitrate_down']:
                    bitrate_down = f"⇣ {round(int(media_info['bitrate_down'])/1024/1024,1)} mbps "
                playing_text += f"总码率：{bitrate_up} {bitrate_down} \n\n"
                playing_items = media_info['playing']
                for item in playing_items:
                    playing_text += f"{index}. {item.get('title')}\n"
                    playing_text += f"    用户：{item.get('user')} | 码率：{item.get('bitrate')}\n\n"
                    index += 1
            if self._notify:
                if link:
                    self.post_message(
                        mtype = NotificationType.MediaServer,
                        title = notify_title,
                        text = notify_text_speed + playing_text,
                        link = link
                    )
                else:
                    self.post_message(
                        mtype = NotificationType.MediaServer,
                        title = notify_title,
                        text = notify_text_speed + playing_text
                    )
        except Exception as e:
            logger.error(f"设置限速失败：{str(e)}")

    @staticmethod
    def __allow_access(allow_ips: dict, ip: str) -> bool:
        """
        判断IP是否合法
        :param allow_ips: 充许的IP范围 {"ipv4":, "ipv6":}
        :param ip: 需要检查的ip
        """
        if not allow_ips:
            return True
        try:
            ipaddr = ipaddress.ip_address(ip)
            if ipaddr.version == 4:
                if not allow_ips.get('ipv4'):
                    return True
                allow_ipv4s = allow_ips.get('ipv4').split(",")
                for allow_ipv4 in allow_ipv4s:
                    if ipaddr in ipaddress.ip_network(allow_ipv4, strict=False):
                        return True
            elif ipaddr.ipv4_mapped:
                if not allow_ips.get('ipv4'):
                    return True
                allow_ipv4s = allow_ips.get('ipv4').split(",")
                for allow_ipv4 in allow_ipv4s:
                    if ipaddr.ipv4_mapped in ipaddress.ip_network(allow_ipv4, strict=False):
                        return True
            else:
                if not allow_ips.get('ipv6'):
                    return True
                allow_ipv6s = allow_ips.get('ipv6').split(",")
                for allow_ipv6 in allow_ipv6s:
                    if ipaddr in ipaddress.ip_network(allow_ipv6, strict=False):
                        return True
        except Exception as err:
            print(str(err))
            return False
        return False

    def stop_service(self):
        pass
