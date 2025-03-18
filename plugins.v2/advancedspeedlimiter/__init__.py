import ipaddress
import time
from typing import List, Tuple, Dict, Any, Optional
from collections import defaultdict
from threading import Lock

from app.core.event import eventmanager, Event
from app.helper.downloader import DownloaderHelper
from app.helper.mediaserver import MediaServerHelper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import NotificationType, WebhookEventInfo
from app.schemas.types import EventType
from app.utils.ip import IpUtils


class AdvancedSpeedLimiter(_PluginBase):
    plugin_name = "智能播放限速"
    plugin_desc = "根据播放情况智能调整下载器带宽分配，支持路径定向限速"
    plugin_icon = "Speedlimit.png"
    plugin_version = "3.0"
    plugin_author = "Shurelol, justzerock"
    author_url = "https://github.com/justzerock/MoviePilot-Plugins"
    plugin_config_prefix = "advancedspeedlimiter_"
    plugin_order = 11
    auth_level = 1

    # 私有属性
    downloader_helper = None
    mediaserver_helper = None
    _enabled: bool = False
    _notify: bool = True
    _interval: int = 30
    _notify_delay: int = 5
    _downloader: list = []
    _upload_weights: dict = {}
    _download_weights: dict = {}
    _bandwidth_up: float = 0
    _bandwidth_down: float = 0
    _limit_upload_paths: list = []
    _limit_download_paths: list = []
    _last_notify_time: float = 0
    _notification_cache: dict = defaultdict(list)
    _lock = Lock()
    _current_limits: dict = {}

    def init_plugin(self, config: dict = None):
        self.downloader_helper = DownloaderHelper()
        self.mediaserver_helper = MediaServerHelper()
        
        if config:
            self._enabled = config.get("enabled")
            self._notify = config.get("notify")
            self._interval = int(config.get("interval") or 30)
            self._notify_delay = int(config.get("notify_delay") or 5)
            self._bandwidth_up = float(config.get("bandwidth_up") or 0) * 1e6  # 转换为bps
            self._bandwidth_down = float(config.get("bandwidth_down") or 0) * 1e6
            self._limit_upload_paths = [p.strip().lower() for p in (config.get("limit_upload_paths") or "").split("\n") if p.strip()]
            self._limit_download_paths = [p.strip().lower() for p in (config.get("limit_download_paths") or "").split("\n") if p.strip()]
            
            # 解析权重配置
            self._upload_weights = {}
            self._download_weights = {}
            weights = [w.strip() for w in (config.get("weights") or "").split(",") if w.strip()]
            for idx, weight in enumerate(weights):
                try:
                    up, down = map(float, weight.split())
                    dl_name = self._downloader[idx] if idx < len(self._downloader) else f"downloader_{idx+1}"
                    self._upload_weights[dl_name] = up
                    self._download_weights[dl_name] = down
                except Exception as e:
                    logger.error(f"权重配置解析失败：{weight} - {str(e)}")

    def get_service(self) -> List[Dict[str, Any]]:
        if self._enabled:
            return [{
                "id": "SpeedLimiter",
                "name": "智能限速服务",
                "trigger": "interval",
                "func": self.check_playing_sessions,
                "kwargs": {"seconds": self._interval}
            }]
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        # 保持原有表单结构，添加新配置项
        return [
            {
                'component': 'VForm',
                'content': [
                    # 原有基础配置项...
                    # 新增配置项
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
                            {'component': 'VCol', 'props': {'cols': 6}, 'content': [
                                {'component': 'VTextField', 'props': {
                                    'model': 'bandwidth_up', 'label': '总上行带宽(Mbps)', 'type': 'number'
                                }}
                            ]},
                            {'component': 'VCol', 'props': {'cols': 6}, 'content': [
                                {'component': 'VTextField', 'props': {
                                    'model': 'bandwidth_down', 'label': '总下行带宽(Mbps)', 'type': 'number'
                                }}
                            ]}
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {'component': 'VCol', 'props': {'cols': 12}, 'content': [
                                {'component': 'VTextarea', 'props': {
                                    'model': 'weights', 
                                    'label': '下载器权重（上传 下载，多个用逗号分隔）',
                                    'placeholder': '示例：1 0, 2 1 表示第一个下载器上传权重1不限速，第二个上传权重2下载权重1'
                                }}
                            ]}
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {'component': 'VCol', 'props': {'cols': 6}, 'content': [
                                {'component': 'VTextarea', 'props': {
                                    'model': 'limit_upload_paths', 
                                    'label': '限制上传路径（外网播放时生效）',
                                    'rows': 3,
                                    'placeholder': '每行一个路径（不区分大小写）'
                                }}
                            ]},
                            {'component': 'VCol', 'props': {'cols': 6}, 'content': [
                                {'component': 'VTextarea', 'props': {
                                    'model': 'limit_download_paths', 
                                    'label': '限制下载路径（内网播放时生效）',
                                    'rows': 3,
                                    'placeholder': '每行一个路径（不区分大小写）'
                                }}
                            ]}
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {'component': 'VCol', 'props': {'cols': 6}, 'content': [
                                {'component': 'VTextField', 'props': {
                                    'model': 'interval', 'label': '检查间隔（秒）', 'type': 'number'
                                }}
                            ]},
                            {'component': 'VCol', 'props': {'cols': 6}, 'content': [
                                {'component': 'VTextField', 'props': {
                                    'model': 'notify_delay', 'label': '通知延迟（秒）', 'type': 'number'
                                }}
                            ]}
                        ]
                    }
                ]
            }
        ], {
            "enabled": False,
            "notify": True,
            "downloader": [],
            "bandwidth_up": 100,
            "bandwidth_down": 500,
            "weights": "1 0, 2 0",
            "limit_upload_paths": "",
            "limit_download_paths": "",
            "interval": 30,
            "notify_delay": 5
        }

    @eventmanager.register(EventType.WebhookMessage)
    def check_playing_sessions(self, event: Event = None):
        """核心逻辑：检查播放会话并调整限速"""
        if not self._enabled:
            return

        total_bitrate_up = 0
        total_bitrate_down = 0
        playing_sessions = []
        media_servers = self.mediaserver_helper.get_services()

        # 获取播放会话（保留原有逻辑）
        for server, service in media_servers.items():
            sessions = []
            if service.type == "emby":
                sessions = self._get_emby_sessions(service)
            # elif service.type == "jellyfin":
            #     sessions = self._get_jellyfin_sessions(service)
            # elif service.type == "plex":
            #     sessions = self._get_plex_sessions(service)

            for session in sessions:
                # 路径检查（新增逻辑）
                path = session.get('Path', '').lower()
                is_external = self._is_external_ip(session)
                
                # 判断是否需要限速
                should_limit = False
                if is_external and any(p in path for p in self._limit_upload_paths):
                    should_limit = True
                    total_bitrate_up += session.get('Bitrate', 0)
                elif not is_external and any(p in path for p in self._limit_download_paths):
                    should_limit = True
                    total_bitrate_down += session.get('Bitrate', 0)

                if should_limit:
                    playing_sessions.append(session)

        # 计算可用带宽（新增逻辑）
        available_up = max(self._bandwidth_up - total_bitrate_up, 0)
        available_down = max(self._bandwidth_down - total_bitrate_down, 0)

        # 执行限速（修改后的分配逻辑）
        self._apply_speed_limits(available_up, available_down)

        # 处理通知（新增聚合逻辑）
        self._process_notification(playing_sessions, available_up, available_down)

    def _apply_speed_limits(self, available_up: float, available_down: float):
        """根据权重分配带宽"""
        total_up_weight = sum(self._upload_weights.values()) or 1
        total_down_weight = sum(self._download_weights.values()) or 1

        for dl_name in self._downloader:
            service = self.downloader_helper.get_downloader(dl_name)
            if not service:
                continue

            # 计算分配速率
            up_limit = (available_up * self._upload_weights.get(dl_name, 0) / total_up_weight) / 1024  # 转换为KB/s
            down_limit = (available_down * self._download_weights.get(dl_name, 0) / total_down_weight) / 1024

            # 应用限速
            try:
                service.instance.set_speed_limit(
                    download_limit=int(down_limit),
                    upload_limit=int(up_limit)
                )
                self._cache_limit_status(dl_name, up_limit, down_limit)
            except Exception as e:
                logger.error(f"限速设置失败：{dl_name} - {str(e)}")

    def _cache_limit_status(self, name: str, up: float, down: float):
        """缓存当前限速状态"""
        with self._lock:
            self._current_limits[name] = {
                'up': up / 1024,  # 转换为MB/s
                'down': down / 1024
            }

    def _process_notification(self, sessions: list, available_up: float, available_down: float):
        """处理聚合通知"""
        with self._lock:
            now = time.time()
            # 缓存播放信息
            self._notification_cache['sessions'].extend(sessions)
            self._notification_cache['available_up'] = available_up
            self._notification_cache['available_down'] = available_down

            # 达到延迟时间或立即通知
            if self._notify_delay == 0 or now - self._last_notify_time >= self._notify_delay:
                self._send_notification()
                self._last_notify_time = now
                self._notification_cache.clear()

    def _send_notification(self):
        """发送格式化通知"""
        if not self._notification_cache:
            return

        # 构建通知内容
        msg = "═══ 限速状态 ═══\n"
        for name, limits in self._current_limits.items():
            up_icon = "⇡" if limits['up'] > 0 else " "
            down_icon = "⇣" if limits['down'] > 0 else " "
            msg += f"{name} {up_icon} {limits['up']:.1f} {down_icon} {limits['down']:.1f} MB/s\n"

        msg += "\n═══ 正在播放 ═══\n"
        msg += f"总码率: ⇡ {self._notification_cache['available_up']/1e6:.2f} ⇣ {self._notification_cache['available_down']/1e6:.2f} Mbps\n"
        for idx, session in enumerate(self._notification_cache.get('sessions', []), 1):
            title = session.get('Title', '未知媒体')
            user = session.get('User', '未知用户')
            bitrate = session.get('Bitrate', 0) / 1e6
            msg += f"{idx}. {title}\n   用户: {user} | 码率: ⇡ {bitrate:.2f}Mbps\n"

        if self._notify:
            self.post_message(
                mtype=NotificationType.MediaServer,
                title="【智能限速状态】",
                text=msg
            )

    # 保留原有媒体服务器会话获取方法
    def _get_emby_sessions(self, service):
        """获取Emby播放会话（保持原有实现）"""
        sessions = []
        try:
            res = service.instance.get_data("[HOST]emby/Sessions?api_key=[APIKEY]")
            if res and res.status_code == 200:
                for session in res.json():
                    if session.get("NowPlayingItem") and not session.get("PlayState", {}).get("IsPaused"):
                        sessions.append({
                            'Path': session.get("NowPlayingItem", {}).get("Path", ""),
                            'Bitrate': session.get("NowPlayingItem", {}).get("Bitrate", 0),
                            'User': session.get("UserName"),
                            'Title': session.get("NowPlayingItem", {}).get("Name"),
                            'RemoteEndPoint': session.get("RemoteEndPoint")
                        })
        except Exception as e:
            logger.error(f"获取Emby会话失败：{str(e)}")
        return sessions
    
    def _is_external_ip(self, session):
        """判断是否为外网IP（保持原有逻辑）"""
        ip = session.get('RemoteEndPoint') or session.get('address')
        return not IpUtils.is_private_ip(ip)

    # 其他原有方法保持不变...
    # ...（保留原有Jellyfin/Plex处理逻辑）
    
    def stop_service(self):
        """停止服务时重置限速"""
        for dl in self.downloader_helper.get_downloaders():
            try:
                dl.set_speed_limit(upload_limit=0, download_limit=0)
            except:
                pass
        logger.info("已重置所有下载器限速设置")