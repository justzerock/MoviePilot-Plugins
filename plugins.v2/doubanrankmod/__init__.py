import re
import json
import datetime
from threading import Event
from typing import Tuple, List, Dict, Any

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app import schemas
from app.chain.download import DownloadChain
from app.chain.media import MediaChain
from app.chain.subscribe import SubscribeChain
from app.core.config import settings
from app.core.context import MediaInfo
from app.core.metainfo import MetaInfo
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import MediaType
from app.utils.dom import DomUtils
from app.utils.http import RequestUtils


class DoubanRankMod(_PluginBase):
    # 插件名称
    plugin_name = "豆瓣榜单订阅·自用修改"
    # 插件描述
    plugin_desc = "获取豆瓣榜单信息，筛选添加订阅"
    # 插件图标
    plugin_icon = "douban.png"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "justzerock"
    # 作者主页
    author_url = "https://github.com/justzerock/MoviePilot-Plugins"
    # 插件配置项ID前缀
    plugin_config_prefix = "doubanrankmod_"
    # 加载顺序
    plugin_order = 2
    # 可使用的用户级别
    auth_level = 2

    # 退出事件
    _event = Event()
    # 私有属性
    downloadchain: DownloadChain = None
    subscribechain: SubscribeChain = None
    mediachain: MediaChain = None
    _scheduler = None
    _douban_list = [
        {
            'title':'实时热门书影音', 
            'value':'subject_real_time_hotest',
            'referer':'https://m.douban.com/subject_collection/subject_real_time_hotest', 
            'address':'https://m.douban.com/rexxar/api/v2/subject_collection/subject_real_time_hotest/items?type=subject&start=0&count=20&updated_at&items_only=1&for_mobile=1'
        },
        {
            'title':'一周口碑电影榜', 
            'value':'movie_weekly_best',
            'referer':'https://m.douban.com/subject_collection/movie_weekly_best', 
            'address':'https://m.douban.com/rexxar/api/v2/subject_collection/movie_weekly_best/items?start=0&count=10&updated_at&items_only=1&for_mobile=1'
        },
        {
            'title':'华语口碑剧集榜', 
            'value':'tv_chinese_best_weekly',
            'referer':'https://m.douban.com/subject_collection/tv_chinese_best_weekly', 
            'address':'https://m.douban.com/rexxar/api/v2/subject_collection/tv_chinese_best_weekly/items?start=0&count=10&updated_at&items_only=1&for_mobile=1'
        },
        {
            'title':'全球口碑剧集榜', 
            'value':'tv_global_best_weekly',
            'referer':'https://m.douban.com/subject_collection/tv_global_best_weekly', 
            'address':'https://m.douban.com/rexxar/api/v2/subject_collection/tv_global_best_weekly/items?start=0&count=10&updated_at&items_only=1&for_mobile=1'
        },
        {
            'title':'近期热门动画', 
            'value':'tv_animation',
            'referer':'https://m.douban.com/subject_collection/tv_animation', 
            'address':'https://m.douban.com/rexxar/api/v2/subject_collection/tv_animation/items?start=0&count=10&updated_at&items_only=1&for_mobile=1'
        },
        {
            'title':'影院热映', 
            'value':'movie_showing',
            'referer':'https://m.douban.com/app_topic/movie_showing', 
            'address':'https://m.douban.com/rexxar/api/v2/subject_collection/movie_showing/items?start=0&count=18&updated_at&items_only=1&for_mobile=1'
        }
    ]
    _enabled = False
    _cron = ""
    _onlyonce = False
    _douban_ranks = []
    _count = 5000
    _genre_rate = []
    _blacklist = []
    _cn_movie = 0
    _jp_movie = 0
    _etc_movie = 0
    _cn_tv = 0
    _jp_tv = 0
    _etc_tv = 0
    _year = 2000
    _clear = False
    _clearflag = False
    _proxy = False

    def init_plugin(self, config: dict = None):
        self.downloadchain = DownloadChain()
        self.subscribechain = SubscribeChain()
        self.mediachain = MediaChain()

        if config:
            self._enabled = config.get("enabled")
            self._cron = config.get("cron")
            self._proxy = config.get("proxy")
            self._onlyonce = config.get("onlyonce")
            self._cn_movie = float(config.get("cn_movie")) if config.get("cn_movie") else 0
            self._jp_movie = float(config.get("jp_movie")) if config.get("jp_movie") else 0
            self._etc_movie = float(config.get("etc_movie")) if config.get("etc_movie") else 0
            self._cn_tv = float(config.get("cn_tv")) if config.get("cn_tv") else 0
            self._jp_tv = float(config.get("jp_tv")) if config.get("jp_tv") else 0
            self._etc_tv = float(config.get("etc_tv")) if config.get("etc_tv") else 0
            self._year = int(config.get("year")) if config.get("year") else 2000
            self._count = int(config.get("count")) if config.get("count") else 5000
            genre_rate = config.get("genre_rate")
            if genre_rate:
                if isinstance(genre_rate, str):
                    self._genre_rate = genre_rate.split('\n')
                else:
                    self._genre_rate = genre_rate
            else:
                self._genre_rate = []
            self._douban_ranks = config.get("douban_ranks") or []
            self._blacklist = config.get("blacklist") or []
            self._clear = config.get("clear")

        # 停止现有任务
        self.stop_service()

        # 启动服务
        if self._enabled or self._onlyonce:
            if self._onlyonce:
                self._scheduler = BackgroundScheduler(timezone=settings.TZ)
                logger.info("豆瓣榜单订阅服务启动，立即运行一次")
                self._scheduler.add_job(func=self.__refresh_rss, trigger='date',
                                        run_date=datetime.datetime.now(
                                            tz=pytz.timezone(settings.TZ)) + datetime.timedelta(seconds=3)
                                        )

                if self._scheduler.get_jobs():
                    # 启动服务
                    self._scheduler.print_jobs()
                    self._scheduler.start()

            if self._onlyonce or self._clear:
                # 关闭一次性开关
                self._onlyonce = False
                # 记录缓存清理标志
                self._clearflag = self._clear
                # 关闭清理缓存
                self._clear = False
                # 保存配置
                self.__update_config()

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
        return [
            {
                "path": "/delete_history",
                "endpoint": self.delete_history,
                "methods": ["GET"],
                "summary": "删除豆瓣榜单订阅历史记录"
            }
        ]

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
        if self._enabled and self._cron:
            return [
                {
                    "id": "DoubanRankMod",
                    "name": "豆瓣榜单订阅服务",
                    "trigger": CronTrigger.from_crontab(self._cron),
                    "func": self.__refresh_rss,
                    "kwargs": {}
                }
            ]
        elif self._enabled:
            return [
                {
                    "id": "DoubanRankMod",
                    "name": "豆瓣榜单订阅服务",
                    "trigger": CronTrigger.from_crontab("0 8 * * *"),
                    "func": self.__refresh_rss,
                    "kwargs": {}
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
                                            'model': 'proxy',
                                            'label': '使用代理服务器',
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
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 4,
                                    'md': 3
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'cron',
                                            'label': '执行周期',
                                            'placeholder': '5位cron表达式，留空自动'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 4,
                                    'md': 3
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'cn_tv',
                                            'label': '中国大陆剧集评分',
                                            'placeholder': '评分大于等于该值才订阅'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 4,
                                    'md': 3
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'jp_tv',
                                            'label': '日本剧集评分',
                                            'placeholder': '评分大于等于该值才订阅'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 4,
                                    'md': 3
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'etc_tv',
                                            'label': '其他剧集评分',
                                            'placeholder': '评分大于等于该值才订阅'
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
                                    'cols': 4,
                                    'md': 3
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'year',
                                            'label': '年份筛选',
                                            'placeholder': '年份大于等于该值才订阅'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 4,
                                    'md': 3
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'cn_movie',
                                            'label': '中国大陆电影评分',
                                            'placeholder': '评分大于等于该值才订阅'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 4,
                                    'md': 3
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'jp_movie',
                                            'label': '日本电影评分',
                                            'placeholder': '评分大于等于该值才订阅'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 4,
                                    'md': 3
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'etc_movie',
                                            'label': '其他电影评分',
                                            'placeholder': '评分大于等于该值才订阅'
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
                                        'component': 'VSelect',
                                        'props': {
                                            'chips': True,
                                            'multiple': True,
                                            'model': 'douban_ranks',
                                            'label': '豆瓣榜单',
                                            'items': [{"title": item.get("title"), "value": item.get("value")}
                                                      for item in self._douban_list]
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
                                            'model': 'count',
                                            'label': '最低评分人数',
                                            'placeholder': '默认 5000'
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
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'genre_rate',
                                            'label': '类型评分',
                                            'placeholder': '类型评分，数据包含设定的全部类型时生效，如：科幻,恐怖:7.0'
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
                                        'component': 'VCombobox',
                                        'props': {
                                            'multiple': True,
                                            'chips': True,
                                            'clearable': True,
                                            'model': 'blacklist',
                                            'label': '不订阅的类型（可自定义）',
                                            'items': ["真人秀", "脱口秀", "纪录片", "歌舞", "同性"]
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
                                    'cols': 6,
                                    'md': 3
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'clear',
                                            'label': '清理历史记录',
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
            "cron": "",
            "proxy": False,
            "onlyonce": False,
            "cn_movie": "",
            "jp_movie": "",
            "etc_movie": "",
            "cn_tv": "",
            "jp_tv": "",
            "etc_tv": "",
            "year": "",
            "douban_ranks": [],
            "count": "",
            "genre_rate": "",
            "clear": False
        }

    def get_page(self) -> List[dict]:
        """
        拼装插件详情页面，需要返回页面配置，同时附带数据
        """
        # 查询历史记录
        historys = self.get_data('history')
        if not historys:
            return [
                {
                    'component': 'div',
                    'text': '暂无数据',
                    'props': {
                        'class': 'text-center',
                    }
                }
            ]
        # 数据按时间降序排序
        historys = sorted(historys, key=lambda x: x.get('time'), reverse=True)
        # 拼装页面
        contents = []
        for history in historys:
            title = history.get("title")
            rate = history.get("rate")
            count = history.get("count")
            genres = history.get("genres")
            year = history.get("year")
            poster = history.get("poster")
            rtype = history.get("type")
            time_str = history.get("time")
            doubanid = history.get("doubanid")
            contents.append(
                {
                    'component': 'VCard',
                    'content': [
                        {
                            "component": "VDialogCloseBtn",
                            "props": {
                                'innerClass': 'absolute top-0 right-0',
                            },
                            'events': { 
                                'click': {
                                    'api': 'plugin/DoubanRankMod/delete_history',
                                    'method': 'get',
                                    'params': {
                                        'key': f"doubanrank: {title} (DB:{doubanid})",
                                        'apikey': settings.API_TOKEN
                                    }
                                }
                            },
                        },
                        {
                            'component': 'div',
                            'props': {
                                'class': 'd-flex justify-space-start flex-nowrap flex-row',
                            },
                            'content': [
                                {
                                    'component': 'div',
                                    'content': [
                                        {
                                            'component': 'VImg',
                                            'props': {
                                                'src': poster,
                                                'height': 120,
                                                'width': 80,
                                                'aspect-ratio': '2/3',
                                                'class': 'object-cover shadow ring-gray-500',
                                                'cover': True
                                            }
                                        }
                                    ]
                                },
                                {
                                    'component': 'div',
                                    'content': [
                                        {
                                            'component': 'VCardTitle',
                                            'props': {
                                                'class': 'ps-1 pe-5 break-words whitespace-break-spaces',
                                                'style': 'font-size: 14px;'
                                            },
                                            'content': [
                                                {
                                                    'component': 'a',
                                                    'props': {
                                                        'href': f"https://movie.douban.com/subject/{doubanid}",
                                                        'target': '_blank'
                                                    },
                                                    'text': f"{title} ({year})"
                                                }
                                            ]
                                        },
                                        {
                                            'component': 'VCardText',
                                            'props': {
                                                'class': 'pa-0 px-2'
                                            },
                                            'text': f'评分：{rate} ({count})'
                                        },
                                        {
                                            'component': 'VCardText',
                                            'props': {
                                                'class': 'pa-0 px-2'
                                            },
                                            'text': f'类型：{rtype}/{genres}'
                                        },
                                        {
                                            'component': 'VCardText',
                                            'props': {
                                                'class': 'pa-0 px-2'
                                            },
                                            'text': f'时间：{time_str}'
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            )

        return [
            {
                'component': 'div',
                'props': {
                    'class': 'grid gap-3 grid-info-card',
                },
                'content': contents
            }
        ]

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
            print(str(e))

    def delete_history(self, key: str, apikey: str):
        """
        删除同步历史记录
        """
        if apikey != settings.API_TOKEN:
            return schemas.Response(success=False, message="API密钥错误")
        # 历史记录
        historys = self.get_data('history')
        if not historys:
            return schemas.Response(success=False, message="未找到历史记录")
        # 删除指定记录
        historys = [h for h in historys if h.get("unique") != key]
        self.save_data('history', historys)
        return schemas.Response(success=True, message="删除成功")
    
    def __update_config(self):
        """
        列新配置
        """
        self.update_config({    
            "enabled": self._enabled,
            "cron": self._cron,
            "onlyonce": self._onlyonce,
            "cn_movie": self._cn_movie,
            "jp_movie": self._jp_movie,
            "etc_movie": self._etc_movie,
            "cn_tv": self._cn_tv,
            "jp_tv": self._jp_tv,
            "etc_tv": self._etc_tv,
            "year": self._year,
            "count": self._count,
            "douban_ranks": self._douban_ranks,
            "blacklist": self._blacklist,
            "genre_rate": '\n'.join(map(str, self._genre_rate)),
            "clear": self._clear
        })

    def __refresh_rss(self):
        """
        刷新RSS
        """
        logger.info(f"开始刷新豆瓣榜单 ...")
        addr_list = []
        for douban_item in self._douban_list:
            for rank in self._douban_ranks:
                if rank == douban_item.get("value"):
                    addr_list.append(douban_item)
        if not addr_list:
            logger.info(f"未设置榜单RSS地址")
            return
        else:
            logger.info(f"共 {len(addr_list)} 个榜单RSS地址需要刷新")

        # 读取历史记录
        if self._clearflag:
            history = []
        else:
            history: List[dict] = self.get_data('history') or []

        for addr in addr_list:
            if not addr:
                continue
            try:
                logger.info(f"获取RSS：{addr} ...")
                rss_infos = self.__get_rss_info(addr)
                if not rss_infos:
                    logger.error(f"RSS地址：{addr} ，未查询到数据")
                    continue
                else:
                    logger.info(f"RSS地址：{addr} ，共 {len(rss_infos)} 条数据")
                for rss_info in rss_infos:
                    if self._event.is_set():
                        logger.info(f"订阅服务停止")
                        return
                    title = rss_info.get('title')
                    type = rss_info.get('type')
                    doubanid = rss_info.get('doubanid')
                    year = rss_info.get('year')
                    rate = rss_info.get('rate')
                    count = rss_info.get('count')
                    genres = rss_info.get('genres')

                    rtype = '电影' if type == 'movie' else '电视剧'

                    mtype = MediaType.TV if type == 'tv' else MediaType.MOVIE

                    logger.info(f"片名：{title}，类型：{genres}，评分：{rate}，链接：https://movie.douban.com/subject/{doubanid}")
  
                    unique_flag = f"doubanrank: {title} (DB:{doubanid})"
                    # 检查是否已处理过
                    if unique_flag in [h.get("unique") for h in history]:
                        continue
                    # 元数据
                    meta = MetaInfo(title)
                    meta.year = year
                    if mtype:
                        meta.type = mtype
                    # 识别媒体信息
                    if doubanid:
                        # 识别豆瓣信息
                        if settings.RECOGNIZE_SOURCE == "themoviedb":
                            tmdbinfo = self.mediachain.get_tmdbinfo_by_doubanid(doubanid=doubanid, mtype=meta.type)
                            if not tmdbinfo:
                                logger.warn(f'未能通过豆瓣ID {doubanid} 获取到TMDB信息，标题：{title}，豆瓣ID：{doubanid}')
                                continue
                            mediainfo = self.chain.recognize_media(meta=meta, tmdbid=tmdbinfo.get("id"))
                            if not mediainfo:
                                logger.warn(f'TMDBID {tmdbinfo.get("id")} 未识别到媒体信息')
                                continue
                        else:
                            mediainfo = self.chain.recognize_media(meta=meta, doubanid=doubanid)
                            if not mediainfo:
                                logger.warn(f'豆瓣ID {doubanid} 未识别到媒体信息')
                                continue
                    else:
                        # 匹配媒体信息
                        mediainfo: MediaInfo = self.chain.recognize_media(meta=meta)
                        if not mediainfo:
                            logger.warn(f'未识别到媒体信息，标题：{title}，豆瓣ID：{doubanid}')
                            continue
                    # 查询缺失的媒体信息
                    exist_flag, _ = self.downloadchain.get_no_exists_info(meta=meta, mediainfo=mediainfo)
                    if exist_flag:
                        logger.info(f'{mediainfo.title_year} 媒体库中已存在')
                        continue
                    # 判断用户是否已经添加订阅
                    if self.subscribechain.exists(mediainfo=mediainfo, meta=meta):
                        logger.info(f'{mediainfo.title_year} 订阅已存在')
                        continue
                    # 添加订阅
                    self.subscribechain.add(title=mediainfo.title,
                                            year=mediainfo.year,
                                            mtype=mediainfo.type,
                                            tmdbid=mediainfo.tmdb_id,
                                            season=meta.begin_season,
                                            exist_ok=True,
                                            username="豆瓣榜单")
                    # 存储历史记录
                    history.append({
                        "title": title,
                        "rate": rate,
                        "count": count,
                        "type": rtype,
                        "genres": genres,
                        "year": mediainfo.year,
                        "poster": mediainfo.get_poster_image(),
                        "overview": mediainfo.overview,
                        "tmdbid": mediainfo.tmdb_id,
                        "doubanid": doubanid,
                        "time": datetime.datetime.now().strftime("%m-%d %H:%M"),
                        "unique": unique_flag
                    })
            except Exception as e:
                logger.error(str(e))

        # 保存历史记录
        self.save_data('history', history)
        # 缓存只清理一次
        self._clearflag = False
        logger.info(f"所有榜单RSS刷新完成")
    
    def check_genre_rate(self, all_genres, rate, _genre_rate):
        for genre_rate in _genre_rate:
            # 分割genre和rate
            genre, threshold_rate = genre_rate.split(':')
            
            # 将genre转换为列表
            genre_list = genre.split(',')
            
            # 检查genre_list中的所有类型是否都在all_genres中
            if all(g in all_genres for g in genre_list):
                # 如果所有类型都存在，则需要满足评分要求
                if float(rate) >= float(threshold_rate):
                    return True
            else:
                # 如果有类型不存在，则不做评分判断
                continue
        return False
            
    def check_country_rate(self, card_subtitle, rate, type):
        if '中国大陆' in card_subtitle:
            threshold = self._cn_tv if type == 'tv' else self._cn_movie
        elif '日本' in card_subtitle:
            threshold = self._jp_tv if type == 'tv' else self._jp_movie
        else:
            threshold = self._etc_tv if type == 'tv' else self._etc_movie
        
        return float(rate) >= threshold
    
    def filter_item(self, year, count, all_genres, card_subtitle, rate, type):
        # 基本条件：年份和评分人数
        if int(year) < self._year or int(count) < self._count:
            return False
        
        # 黑名单类型
        if any(genre in self._blacklist for genre in all_genres):
            return False
        
        # 国家和评分筛选
        country_rate_pass = self.check_country_rate(card_subtitle, rate, type)
        # 自定义类型和评分筛选
        genre_rate_pass = self.check_genre_rate(all_genres, rate, self._genre_rate)
        
        # 只要地区评分或分类评分有一个通过即可
        return country_rate_pass or genre_rate_pass

    def __get_rss_info(self, addr) -> List[dict]:
        """
        获取RSS
        """
        try:
            if self._proxy:
                ret = RequestUtils(proxies=settings.PROXY, referer=addr.get("referer")).get_res(addr.get("address"))
            else:
                ret = RequestUtils(referer=addr.get("referer")).get_res(addr.get("address"))
            if not ret:
                return []
            douban_items = json.loads(ret.text).get('subject_collection_items')
            douban_array = []
            for item in douban_items:
                try:
                    rss_info = {}
                    card_subtitle = item.get("card_subtitle")
                    # 标题
                    title = item.get("title")
                    # 豆瓣ID
                    doubanid = item.get("id")
                    # 类型
                    type = item.get("type")
                    # 年份
                    year = card_subtitle.split()[0]
                    # 评分
                    rating = item.get("rating", {})
                    if rating:
                        rate = rating.get("value")
                        count = rating.get("count")
                    else:
                        rate = 0
                        count = 0
                    # 人数
                    all_genres = []
                    genres_text = ''
                    if re.search(r'\d{4}\s*/\s*[^/]+/\s*[^/]+/\s*', card_subtitle):
                        # 提取类型部分（在第二个和第三个斜杠之间）
                        match = re.search(r'\d{4}\s*/\s*[^/]+/\s*([^/]+)/\s*', card_subtitle)
                        if match:
                            genres_text = match.group(1).strip()
                            # 分割类型（假设类型之间有空格）
                            genres = [genre.strip() for genre in genres_text.split()]
                            all_genres.extend(genres)
                    
                    if not self.filter_item(year, count, all_genres, card_subtitle, rate, type):
                        continue

                    rss_info['title'] = title
                    rss_info['doubanid'] = doubanid
                    rss_info['type'] = type
                    rss_info['year'] = year
                    rss_info['rate'] = rate
                    rss_info['count'] = count
                    rss_info['genres'] = genres_text
                    douban_array.append(rss_info)
                except Exception as e1:
                    logger.error("解析RSS条目失败：" + str(e1) + "，条目：" + str(item))
                    continue
            return douban_array
        except Exception as e:
            logger.error("获取RSS失败：" + str(e))
            return []
