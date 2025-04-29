import base64
import datetime
import threading
import time
import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from app.plugins.librarybackdrop.image_processor import create_emby_cover

import pytz
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


class MediaCoverGenerator(_PluginBase):
    # 插件名称
    plugin_name = "媒体库封面生成"
    # 插件描述
    plugin_desc = "获取媒体库的最新媒体，生成封面"
    # 插件图标
    plugin_icon = "Emby_A.png"
    # 插件版本
    plugin_version = "0.1"
    # 插件作者
    plugin_author = "justzerock"
    # 作者主页
    author_url = "https://github.com/justzerock/MoviePilot-Plugins"
    # 插件配置项ID前缀
    plugin_config_prefix = "mediacovergenerator_"
    # 加载顺序
    plugin_order = 25
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
    _sort_by = []
    _image_process_enabled = True
    _zh_font_url = 'https://fastly.jsdelivr.net/gh/justzerock/assets@master/zh.ttf'
    _en_font_url = 'https://fastly.jsdelivr.net/gh/justzerock/assets@master/en.ttf'
    _zh_path = None
    _en_path = None
    _title_config = ""

    def init_plugin(self, config: dict = None):
        self.mschain = MediaServerChain()
        self.mediaserver_helper = MediaServerHelper()    
        self.__get_fonts()  
        if config:
            self._enabled = config.get("enabled")
            self._onlyonce = config.get("onlyonce")
            self._transfer_update = config.get("transfer_update")
            self._cron = config.get("cron")
            self._delay = config.get("delay") or 0
            self._mediaservers = config.get("mediaservers") or []
            self._sort_by = config.get("sort_by") or []
            self._image_process_enabled = config.get("image_process_enabled") or True
            self._title_config = config.get("title_config") or ""
            self._zh_font_url = config.get("zh_font_url") or ""
            self._en_font_url = config.get("en_font_url") or ""

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
            "transfer_update": self._transfer_update,
            "cron": self._cron,
            "delay": self._delay,
            "mediaservers": self._mediaservers,
            "sort_by": self._sort_by,
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
                                            'model': 'transfer_update',
                                            'label': '监控入库更新封面',
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
                                        'component': 'VCronField',
                                        'props': {
                                            'model': 'cron',
                                            'label': '媒体库背景图更新周期',
                                            'placeholder': '5位cron表达式'
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
                                            'model': 'delay',
                                            'label': '入库延迟时间（秒）',
                                            'placeholder': '30'
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
                                        'component': 'VSelect',
                                        'props': {
                                            'chips': True,
                                            'multiple': False,
                                            'model': 'sort_by',
                                            'label': '背景图来源排序',
                                            'items': [
                                                {"title": "最新加入", "value": "DateCreated"},
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
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'zh_font_url',
                                            'label': '中文字体链接',
                                            'placeholder': self._zh_font_url
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
                                            'model': 'en_font_url',
                                            'label': '英文字体链接',
                                            'placeholder': self._en_font_url
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
                                            'theme': 'textmate',
                                            'style': 'height: 30rem',
                                            'label': '中英标题配置',
                                            'placeholder': '''库名:
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
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'image_process_enabled',
                                            'label': '启用图像处理',
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
            "sort_by": [],
            "image_process_enabled": True,
            "title_config": "",
            "zh_font_url": "",
            "en_font_url": ""
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
            logger.warning(f"{mediainfo.title_year} does not exist in media library")
            return
            
        # Log the existsinfo for debugging
        logger.info(f"Existsinfo: {existsinfo}")
        
        # Get item details including backdrop
        logger.info(f"Getting backdrop for {mediainfo.title_year}...")
        iteminfo = self.mschain.iteminfo(server=existsinfo.server, item_id=existsinfo.itemid)
        logger.info(f"Iteminfo: {iteminfo.path}")
        if not iteminfo:
            logger.warning(f"Failed to get item details for {mediainfo.title_year}")
            return
            
        # Try to get library ID
        library_id = None
        media_service = self.service_infos(existsinfo.server_type).get(existsinfo.server)
        if existsinfo.server_type == "emby":
            libraries = media_service.instance.get_emby_virtual_folders()
        elif existsinfo.server_type == "jellyfin":
            libraries = media_service.instance.get_jellyfin_virtual_folders()
        elif existsinfo.server_type == "plex":
            # For Plex
            plex = media_service.instance.get_plex()
            item = plex.fetchItem(existsinfo.itemid)
            if item:
                library_id = item.librarySectionID
            libraries = plex.get_librarys()
            library_name = next((library.get('name', '') for library in libraries if library.get('Id', '') == library_id), None)

        if libraries and not library_id:
            library_info = next(
                ((library.get('Id', ''), library.get('Name', '')) for library in libraries if library.get('Path', '') and any(iteminfo.path.startswith(path) for path in library.get('Path', ''))),
                None
            )
            library_id, library_name = library_info

        logger.info(f"媒体库ID: {library_id}")
        
        if library_id:
            logger.info(f"Found library by API method: {library_id}")
        
        if not library_id:
            logger.warning(f"Could not find library for {mediainfo.title_year}")
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
        logger.info(f"Data path: {data_path}")
        path = Path(data_path)
        if not path.exists():
            os.mkdir(path)
        self._zh_path = path / "zh.ttf"
        self._en_path = path / "en.ttf"
        if not Path(self._zh_path).exists() or not Path(self._en_path).exists():
            logger.info("字体文件不存在，开始下载...")
            zh_font = RequestUtils().get_res(url=self._zh_font_url).content
            en_font = RequestUtils().get_res(url=self._en_font_url).content
            with open(self._zh_path, "wb") as f:
                f.write(zh_font)
            with open(self._zh_path, "wb") as f:
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
                # 获取最新项目
                latest_items = self.__get_latest_items(server, service.type, library.id)
                if not latest_items:
                    logger.info(f"媒体库 {library.name} 中没有项目")
                    continue
                
                if service.type == "plex":
                    item_id = latest_items[0].item_id
                else:
                    latest_item = latest_items.get('Items', {})[0]
                    type = latest_item.get('Type', '')
                    if type == 'Series':
                        item_id = latest_item.get('Id', '')
                    else:
                        item_id = latest_item.get('PrimaryImageItemId', '')
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
            if self._sort_by:
                sort_by = self._sort_by[0].get('value', 'DateCreated')
            else:
                sort_by = 'DateCreated'

            def __get_emby_iteminfo() -> dict:
                """获取Emby媒体项详情"""
                try:
                    url = f'[HOST]emby/Items/?ParentId={library_id}&SortBy={sort_by}' \
                          f'&Limit=1&SortOrder=Descending&api_key=[APIKEY]'
                    res = service.instance.get_data(url=url)
                    if res:
                        return res.json()
                except Exception as err:
                    logger.error(f"获取Emby媒体项详情失败：{str(err)}")
                return {}

            def __get_jellyfin_iteminfo() -> dict:
                """获取Jellyfin媒体项详情"""
                try:
                    url = f'[HOST]Items/?ParentId={library_id}&SortBy={sort_by}' \
                          f'&Limit=1&SortOrder=Descending&api_key=[APIKEY]'
                    res = service.instance.get_data(url=url)
                    if res:
                        return res.json()
                except Exception as err:
                    logger.error(f"获取Jellyfin媒体项详情失败：{str(err)}")
                return {}

            def __get_plex_iteminfo() -> dict:
                """获取Plex媒体项详情"""
                all_items = self.mschain.items(server, library_id)
                if not all_items:
                    return None
                
                # 按添加时间排序
                sorted_items = sorted(all_items, key=lambda x: x.added, reverse=True)
                
                # 返回指定数量的最新项目
                return sorted_items[:1]

            if server_type == "emby":
                return __get_emby_iteminfo()
            elif server_type == "jellyfin":
                return __get_jellyfin_iteminfo()
            else:
                return __get_plex_iteminfo()
                
        except Exception as err:
            logger.error(f"Failed to get latest items: {str(err)}")
            return None

    def __update_library_backdrop(self, server, server_type, library_id, library_name, item_id):
        """
        将媒体项的背景图设置为媒体库的背景图
        """
        try:
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
            logger.info(f"为媒体库 {library_id} 获取到背景图 URL: {backdrop_url}")
            
            # 下载并处理背景图
            image_data = self.__download_image(backdrop_url, library_id)
            logger.info("下载的图片")
            if not image_data:
                logger.warning(f"下载背景图失败: {backdrop_url}")
                return False
            
            logger.info(f"背景图下载成功，base64数据长度: {len(image_data)}")
            
            title_config = yaml.safe_load(self._title_config)
            zh_title = en_title = None  # 初始化为空，避免未匹配时报错

            for lib_name, (zh, en) in title_config.items():
                if lib_name == library_name:
                    zh_title = zh
                    en_title = en
                    break

            # 处理图像（如需要）
            if self._image_process_enabled:
                # 这里应该是您已有的图像处理代码
                image_data = create_emby_cover(image_data, zh_title, en_title, self._zh_path, self._en_path)
            
            # 更新媒体库背景图
            result = self.__set_library_image(server, server_type, library_id, image_data)
            if result:
                logger.info(f"媒体库 {library_id} 背景图已更新")
                return True
            else:
                logger.warning(f"媒体库 {library_id} 背景图更新失败")
                return False
                    
        except Exception as err:
            logger.error(f"更新媒体库背景图失败: {str(err)}")
            return False

    def __get_backdrop_url(self, server, server_type, iteminfo):
        """
        从媒体项信息中获取背景图URL
        """
        # Emby/Jellyfin
        if server_type in ["emby", "jellyfin"]:
            if iteminfo.get("BackdropImageTags") and len(iteminfo["BackdropImageTags"]) > 0:
                item_id = iteminfo.get("Id")
                tag = iteminfo["BackdropImageTags"][0]
                if server_type == "emby":
                    return f'[HOST]emby/Items/{item_id}/Images/Backdrop/0?tag={tag}&api_key=[APIKEY]'
                else:  # jellyfin
                    return f'[HOST]Items/{item_id}/Images/Backdrop/0?tag={tag}&api_key=[APIKEY]'
        # Plex
        elif server_type == "plex":
            if iteminfo.get("art"):
                return iteminfo["art"]
        
        return None

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
                        # 保存到本地临时文件
                        self.__save_image_to_local(image_content, f"backdrop_{library_id}_{int(time.time())}.jpg")
                        return base64.b64encode(image_content).decode()
            # 从外部URL获取图片
            else:
                r = RequestUtils().get_res(url=imageurl)
                if r and r.status_code == 200:
                    image_content = r.content
                    # 保存到本地临时文件
                    self.__save_image_to_local(image_content, f"external_backdrop_{int(time.time())}.jpg")
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
            local_path = "/mnt/Local/temp"
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

        def __get_emby_iteminfo() -> dict:
            """获取Emby媒体项详情"""
            try:
                url = f'[HOST]emby/Users/[USER]/Items/{itemid}?Fields=BackdropImageTags&api_key=[APIKEY]'
                res = service.instance.get_data(url=url)
                if res:
                    return res.json()
            except Exception as err:
                logger.error(f"获取Emby媒体项详情失败：{str(err)}")
            return {}

        def __get_jellyfin_iteminfo() -> dict:
            """获取Jellyfin媒体项详情"""
            try:
                url = f'[HOST]Users/[USER]/Items/{itemid}?Fields=BackdropImageTags&api_key=[APIKEY]'
                res = service.instance.get_data(url=url)
                if res:
                    return res.json()
            except Exception as err:
                logger.error(f"获取Jellyfin媒体项详情失败：{str(err)}")
            return {}

        def __get_plex_iteminfo() -> dict:
            """获取Plex媒体项详情"""
            iteminfo = {}
            try:
                plexitem = service.instance.get_plex().library.fetchItem(ekey=itemid)
                iteminfo['Name'] = plexitem.title
                iteminfo['Id'] = plexitem.key
                iteminfo['Path'] = plexitem.locations[0] if plexitem.locations else ""
                if hasattr(plexitem, 'art'):
                    iteminfo['art'] = plexitem.art
                return iteminfo
            except Exception as err:
                logger.error(f"获取Plex媒体项详情失败：{str(err)}")
            return {}

        if server_type == "emby":
            return __get_emby_iteminfo()
        elif server_type == "jellyfin":
            return __get_jellyfin_iteminfo()
        else:
            return __get_plex_iteminfo()

    def __set_library_image(self, server, server_type, library_id, image_base64):
        """
        设置媒体库背景图
        """
        service = self.service_infos(server_type).get(server)
        if not service:
            logger.warning(f"未找到媒体服务器 {server} 的实例")
            return False

        def __set_emby_library_image():
            """设置Emby媒体库背景图"""
            try:
                url = f'[HOST]emby/Items/{library_id}/Images/Primary?api_key=[APIKEY]'
                logger.info(f"设置背景图 URL: {url}")
                
                # 在发送前保存一份图片到本地
                try:
                    image_bytes = base64.b64decode(image_base64)
                    self.__save_image_to_local(image_bytes, f"sending_to_emby_{library_id}_{int(time.time())}.jpg")
                except Exception as save_err:
                    logger.error(f"保存发送前图片失败: {str(save_err)}")
                
                # 直接使用服务实例的post_data方法，它会处理[HOST]和[APIKEY]占位符
                res = service.instance.post_data(
                    url=url,
                    data=image_base64,
                    headers={
                        "Content-Type": "image/png"
                    }
                )
                
                if res:
                    logger.info(f"媒体库背景图更新响应状态码: {res.status_code}")
                    if res.text:
                        logger.info(f"媒体库背景图更新响应内容: {res.text[:200]}")
                
                if res and res.status_code in [200, 204]:
                    return True
                else:
                    logger.error(f"设置Emby媒体库背景图失败，错误码：{res.status_code if res else 'No response'}")
                    return False
            except Exception as err:
                logger.error(f"设置Emby媒体库背景图失败：{str(err)}")
            return False

        def __set_jellyfin_library_image():
            """设置Jellyfin媒体库背景图"""
            try:
                url = f'[HOST]Items/{library_id}/Images/Primary?api_key=[APIKEY]'
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
                    logger.error(f"设置Jellyfin媒体库背景图失败，错误码：{res.status_code}")
                    return False
            except Exception as err:
                logger.error(f"设置Jellyfin媒体库背景图失败：{str(err)}")
            return False

        def __set_plex_library_image():
            """设置Plex媒体库背景图"""
            try:
                # Plex需要先将base64保存为临时文件
                import tempfile
                import os
                import base64
                
                # 创建临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                    temp_file.write(base64.b64decode(image_base64))
                    temp_path = temp_file.name
                
                # 更新媒体库背景
                section = service.instance.get_plex().library.sectionByID(library_id)
                section.uploadArt(filepath=temp_path)
                
                # 删除临时文件
                os.unlink(temp_path)
                return True
            except Exception as err:
                logger.error(f"设置Plex媒体库背景图失败：{str(err)}")
            return False

        if server_type == "emby":
            return __set_emby_library_image()
        elif server_type == "jellyfin":
            return __set_jellyfin_library_image()
        else:
            return __set_plex_library_image()

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