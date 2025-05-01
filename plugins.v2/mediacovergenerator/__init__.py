import base64
import datetime
import hashlib
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytz
import yaml

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

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
from app.plugins.mediacovergenerator.image_processor import create_emby_cover


class MediaCoverGenerator(_PluginBase):
    # 插件名称
    plugin_name = "媒体库封面生成"
    # 插件描述
    plugin_desc = "自动生成媒体库封面，支持 Emby，Jellyfin"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/icons/emby.png"
    # 插件版本
    plugin_version = "0.7"
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
    _transfer_update = True
    _cron = None
    _delay = 0
    _mediaservers = []
    _sort_by = 'Random'
    _covers_output = ''
    _covers_input = ''
    _image_process_enabled = True
    _zh_font_url = ''
    _en_font_url = ''
    _zh_font_path = None
    _en_font_path = None
    _title_config = ''

    def init_plugin(self, config: dict = None):
        self.mschain = MediaServerChain()
        self.mediaserver_helper = MediaServerHelper()    
        if config:
            self._enabled = config.get("enabled")
            self._onlyonce = config.get("onlyonce")
            self._transfer_update = config.get("transfer_update")
            self._cron = config.get("cron")
            self._delay = config.get("delay") or 0
            self._mediaservers = config.get("mediaservers") or []
            self._sort_by = config.get("sort_by") or 'Random'
            self._covers_output = config.get("covers_output") or ''
            self._covers_input = config.get("covers_input") or ''
            self._image_process_enabled = config.get("image_process_enabled", True)
            self._title_config = config.get("title_config") or ''
            self._zh_font_url = config.get("zh_font_url") or ""
            self._en_font_url = config.get("en_font_url") or ""

        # 停止现有任务
        self.stop_service()

        self.__get_fonts()  
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
            "transfer_update": self._transfer_update,
            "cron": self._cron,
            "delay": self._delay,
            "mediaservers": self._mediaservers,
            "sort_by": self._sort_by,
            "covers_output": self._covers_output,
            "covers_input": self._covers_input,
            "image_process_enabled": self._image_process_enabled,
            "title_config": self._title_config,
            "zh_font_url": self._zh_font_url,
            "en_font_url": self._en_font_url
        })

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
                                            'model': 'image_process_enabled',
                                            'label': '封面处理',
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
                                            'model': 'transfer_update',
                                            'label': '入库监控',
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
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'delay',
                                            'label': '入库延迟时间（秒）',
                                            'placeholder': '如：30，等待入库再更新'
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
                                            'model': 'zh_font_url',
                                            'label': '中文字体链接（可选）',
                                            'placeholder': '留空使用预设字体，尽量用 .ttf 格式'
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
                                            'placeholder': '留空使用预设字体，尽量用 .ttf 格式'
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
                                            'placeholder': '如 /mnt/covers_input，图片须与媒体库名称一致'
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
                                            'text': '某些库无法获取图片，可以将图片保存在「自定义背景图目录」，' \
                                                    '此目录中的图片优先级高于媒体库中获取的图片，图片须与媒体库名称一致'
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
            "onlyonce": False,
            "transfer_update": True,
            "cron": "",
            "delay": 30,
            "mediaservers": [],
            "sort_by": "Random",
            "covers_output": "",
            "covers_input": "",
            "image_process_enabled": True,
            "title_config": '''# 配置封面标题（按媒体库名称对应）
# 格式如下：
#
# 媒体库名称:
#   - 中文标题
#   - 英文标题
#

动画剧集:
  - 动画剧集
  - Animated Series
  
华语剧集:
  - 华语剧集
  - Chinese Series
  
外语剧集:
  - 外语剧集
  - Foreign Series
  
动画电影:
  - 动画电影
  - Animated Films
 
华语电影:
  - 华语电影
  - Chinese Films

外语电影:
  - 外语电影
  - Foreign Films

其他:
  - 其他
  - Others

音乐:
  - 音乐
  - Musics
  
合集:
  - 合集
  - collection
''',
            "zh_font_url": '',
            "en_font_url": ''
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
        if not self._transfer_update:
            return
        
        # Event data
        mediainfo: MediaInfo = event.event_data.get("mediainfo")
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
            
        # Set library backdrop
        self.__update_library_backdrop(
            server=existsinfo.server, 
            server_type=existsinfo.server_type,
            library_id=library_id, 
            library_name=library_name,
            item_id=existsinfo.itemid
        )


    def __get_fonts(self):
        data_path = self.get_data_path()
        path = Path(data_path)
        path.mkdir(parents=True, exist_ok=True)

        self._zh_font_path = path / "zh.ttf"
        self._en_font_path = path / "en.ttf"

        # 默认字体链接
        default_zh_url = "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/zh.ttf"
        default_en_url = "https://raw.githubusercontent.com/justzerock/MoviePilot-Plugins/main/fonts/en.ttf"

        zh_font_url = self._zh_font_url or default_zh_url
        en_font_url = self._en_font_url or default_en_url

        # 记录上次使用的 URL 哈希
        zh_hash_path = path / "zh_url.hash"
        en_hash_path = path / "en_url.hash"

        def url_changed(url, hash_path):
            url_hash = hashlib.md5(url.encode()).hexdigest()
            if not hash_path.exists() or hash_path.read_text() != url_hash:
                hash_path.write_text(url_hash)
                return True
            return False

        # 检查是否需要下载
        zh_changed = url_changed(zh_font_url, zh_hash_path)
        en_changed = url_changed(en_font_url, en_hash_path)

        if zh_changed or not self._zh_font_path.exists():
            logger.info(f"下载中文字体: {zh_font_url}")
            zh_font = RequestUtils().get_res(url=zh_font_url).content
            with open(self._zh_font_path, "wb") as f:
                f.write(zh_font)

        if en_changed or not self._en_font_path.exists():
            logger.info(f"下载英文字体: {en_font_url}")
            en_font = RequestUtils().get_res(url=en_font_url).content
            with open(self._en_font_path, "wb") as f:
                f.write(en_font)

    
    def update_all_libraries(self):
        """
        定时更新所有媒体库的背景图
        """
        # 所有媒体服务器
        service_infos = self.service_infos()
        if not service_infos:
            return
            
        for server, service in service_infos.items():
            # 扫描所有媒体库
            logger.info(f"开始更新服务器 {server} 的媒体库背景...")
            
            image_paths = []
            if self._covers_input:
                image_paths = sorted([os.path.join(self._covers_input, f) for f in os.listdir(self._covers_input)
                        if f.lower().endswith((".jpg", ".png", ".jpeg", ".webp"))])
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
                if image_paths:
                    for image_path in image_paths:
                        if library.name in image_path:
                            logger.info(f"找到自定义背景图: {image_path}")
                            self.__update_library_backdrop(server=server, 
                                                            server_type=service.type,
                                                            library_id=library.id, 
                                                            library_name=library.name,
                                                            image_path=image_path)
                            logger.info(f"媒体库 {library.name} 背景图已更新")
                            matched = True
                            break  # 找到就不再继续循环 image_paths
                if not matched:
                    # 获取最新项目
                    latest_items = self.__get_latest_items(server, service.type, library.id)
                    if not latest_items:
                        logger.info(f"媒体库 {library.name} 中没有项目")
                        continue
                    if len(latest_items.get('Items', [])) > 0:
                        latest_item = latest_items.get('Items', [])[0]
                        type = latest_item.get('Type', '')
                        if type == 'Episode':
                            item_id = latest_item.get('SeriesId', '')
                        else:
                            item_id = latest_item.get('Id', '')
                        # 使用第一个项目的背景图
                        if self.__update_library_backdrop(server=server, 
                                                        server_type=service.type,
                                                        library_id=library.id, 
                                                        library_name=library.name,
                                                        item_id=item_id):
                            logger.info(f"媒体库 {library.name} 背景图已更新")
                    
            logger.info(f"服务器 {server} 的媒体库背景更新完成")

    def __get_latest_items(self, server, server_type, library_id):
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
                include_item_types = {
                    "PremiereDate": "Movie,Series",
                    "DateCreated": "Movie,Episode",
                    "Random": "Movie,Series"
                }[self._sort_by]

                url = f'[HOST]emby/Items/?api_key=[APIKEY]' \
                      f'&ParentId={library_id}&SortBy={self._sort_by}&Limit=1' \
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

    def preprocess_yaml_text(self, yaml_str: str) -> str:
        # 替换中文全角冒号为英文半角
        yaml_str = yaml_str.replace("：", ":")
        # 替换制表符为两个空格，统一缩进
        yaml_str = yaml_str.replace("\t", "  ")
        return yaml_str
    
    def load_yaml_safe(self, yaml_str: str) -> dict:
        try:
            yaml_str = self.preprocess_yaml_text(yaml_str)
            data = yaml.safe_load(yaml_str)
            if not isinstance(data, dict):
                raise ValueError("YAML 顶层结构必须是一个字典")
            return data
        except yaml.YAMLError as e:
            raise ValueError(f"YAML 解析错误：{str(e)}")
        
    def validate_title_config(self, data: dict) -> dict:
        for key, value in data.items():
            if not isinstance(value, list) or len(value) < 2:
                raise ValueError(f"条目“{key}”格式错误，必须是包含中英文标题的列表")
        return data


    def load_and_validate_titles(self, yaml_str: str) -> dict:
        data = self.load_yaml_safe(yaml_str)
        return self.validate_title_config(data)
    
    def __update_library_backdrop(self, server, server_type, library_id, library_name, item_id=None, image_path=None):
        """
        将媒体项的背景图设置为媒体库的背景图
        """
        try:
            
            if image_path:
                with open(image_path, "rb") as f:
                    image_content = f.read()
                image_data = base64.b64encode(image_content).decode()
            else:
                # 获取媒体项详情
                iteminfo = self.get_iteminfo(server, server_type, item_id)
                # logger.info(f"媒体详情：{iteminfo}")
                if not iteminfo:
                    logger.warning(f"获取媒体项 {item_id} 详情失败")
                    return False
                # 获取背景图URL
                backdrop_url = self.__get_backdrop_url(server, server_type, iteminfo)
                if not backdrop_url:
                    logger.warning(f"媒体项 {iteminfo.get('Name', item_id)} 没有背景图")
                    return False
                
                # 记录背景图URL
                # logger.info(f"为媒体库 {library_id} 获取到背景图 URL: {backdrop_url}")
                
                # 下载并处理背景图
                image_data = self.__download_image(backdrop_url, library_id)
                if not image_data:
                    logger.warning(f"下载背景图失败: {backdrop_url}")
                    return False
            
            if self._title_config:
                title_config = self.load_and_validate_titles(self._title_config)
                zh_title = en_title = None  # 初始化为空，避免未匹配时报错

                for lib_name, (zh, en) in title_config.items():
                    if lib_name == library_name:
                        zh_title = zh
                        en_title = en
                        break

                # 处理图像（如需要）
                if self._image_process_enabled:
                    # 这里应该是您已有的图像处理代码
                    image_data = create_emby_cover(image_data, zh_title, en_title, self._zh_font_path, self._en_font_path)
                
                # 更新媒体库背景图
                result = self.__set_library_image(server, server_type, library_id, library_name, image_data)
                if result:
                    return True
                else:
                    return False
                    
        except Exception as err:
            logger.error(f"更新媒体库背景图失败: {str(err)}")
            return False

    def __get_backdrop_url(self, server, server_type, iteminfo):
        """
        从媒体项信息中获取背景图URL
        """
        # Emby/Jellyfin
        if iteminfo.get("BackdropImageTags") and len(iteminfo["BackdropImageTags"]) > 0:
            item_id = iteminfo.get("Id")
            tag = iteminfo["BackdropImageTags"][0]
            return f'[HOST]emby/Items/{item_id}/Images/Backdrop/0?tag={tag}&api_key=[APIKEY]'

    def __download_image(self, imageurl, library_id):
        """
        下载图片，返回base64编码，并保存到本地
        """
        try:
            # 从Emby/Jellyfin API获取图片
            image_content = None
            if '[HOST]' in imageurl:
                service_infos = self.service_infos()
                if not service_infos:
                    return None
                    
                for service_name, service_info in service_infos.items():
                    # 直接使用当前服务的实例和内置的请求方法
                    url = imageurl
                    
                    # 使用service_info.instance的内置get_data方法
                    r = service_info.instance.get_data(url=url)
                    if r and r.status_code == 200:
                        image_content = r.content
                        return base64.b64encode(image_content).decode()
            # 从外部URL获取图片
            else:
                r = RequestUtils().get_res(url=imageurl)
                if r and r.status_code == 200:
                    image_content = r.content
                    return base64.b64encode(image_content).decode()
                    
            logger.warning(f"{imageurl} 图片下载失败，请检查网络连通性")
        except Exception as err:
            logger.error(f"下载图片失败：{str(err)}")
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
            url = f'[HOST]emby/Users/[USER]/Items/{itemid}?Fields=BackdropImageTags&api_key=[APIKEY]'
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