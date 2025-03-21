import datetime
import re
import xml.dom.minidom
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


class DoubanRankRate(_PluginBase):
    # 插件名称
    plugin_name = "豆瓣榜单订阅（豆瓣评分）"
    # 插件描述
    plugin_desc = "监控豆瓣热门榜单，自动添加订阅。基于原版，改用豆瓣评分筛选，不同分类使用不同分数。"
    # 插件图标
    plugin_icon = "movie.jpg"
    # 插件版本
    plugin_version = "0.2.2"
    # 插件作者
    plugin_author = "jxxghp,justzerock"
    # 作者主页
    author_url = "https://github.com/justzerock/MoviePilot-Plugins"
    # 插件配置项ID前缀
    plugin_config_prefix = "doubanrankrate_"
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
    _douban_address = {
        'movie-ustop': 'https://rsshub.app/douban/movie/ustop',
        'movie-weekly': 'https://rsshub.app/douban/movie/weekly',
        'movie-real-time': 'https://rsshub.app/douban/movie/weekly/movie_real_time_hotest',
        'show-domestic': 'https://rsshub.app/douban/movie/weekly/show_domestic',
        'movie-hot-gaia': 'https://rsshub.app/douban/movie/weekly/movie_hot_gaia',
        'tv-hot': 'https://rsshub.app/douban/movie/weekly/tv_hot',
        'movie-top250': 'https://rsshub.app/douban/movie/weekly/movie_top250',
        'movie-top250-full': 'https://rsshub.app/douban/list/movie_top250',
    }
    _enabled = False
    _cron = ""
    _onlyonce = False
    _rss_addrs = []
    _ranks = []
    _stmrate = 0
    _chmrate = 0
    _jpmrate = 0
    _mrate = 0
    _chtvrate = 0
    _jptvrate = 0
    _tvrate = 0
    _srate = 0
    _drate = 0
    _year = 2000
    _homo = False
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
            self._stmrate = float(config.get("stmrate")) if config.get("stmrate") else 0
            self._chmrate = float(config.get("chmrate")) if config.get("chmrate") else 0
            self._jpmrate = float(config.get("jpmrate")) if config.get("jpmrate") else 0
            self._mrate = float(config.get("mrate")) if config.get("mrate") else 0
            self._chtvrate = float(config.get("chtvrate")) if config.get("chtvrate") else 0
            self._jptvrate = float(config.get("jptvrate")) if config.get("jptvrate") else 0
            self._tvrate = float(config.get("tvrate")) if config.get("tvrate") else 0
            self._srate = float(config.get("srate")) if config.get("srate") else 0
            self._drate = float(config.get("drate")) if config.get("drate") else 0
            self._year = int(config.get("year")) if config.get("year") else 2000
            self._homo = config.get("homo") or False
            rss_addrs = config.get("rss_addrs")
            if rss_addrs:
                if isinstance(rss_addrs, str):
                    self._rss_addrs = rss_addrs.split('\n')
                else:
                    self._rss_addrs = rss_addrs
            else:
                self._rss_addrs = []
            self._ranks = config.get("ranks") or []
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
                    "id": "DoubanRankRate",
                    "name": "豆瓣榜单订阅服务",
                    "trigger": CronTrigger.from_crontab(self._cron),
                    "func": self.__refresh_rss,
                    "kwargs": {}
                }
            ]
        elif self._enabled:
            return [
                {
                    "id": "DoubanRankRate",
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
                                    'cols': 3,
                                    'md': 2
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
                                    'cols': 3,
                                    'md': 2
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'chtvrate',
                                            'label': '国产剧集评分',
                                            'placeholder': '评分大于等于该值才订阅'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 4,
                                    'md': 2
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'jptvrate',
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
                                    'md': 2
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'tvrate',
                                            'label': '其他剧集评分',
                                            'placeholder': '评分大于等于该值才订阅'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 4,
                                    'md': 2
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'srate',
                                            'label': '综艺评分',
                                            'placeholder': '评分大于等于该值才订阅'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 4,
                                    'md': 2
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'homo',
                                            'label': '同性',
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
                                    'cols': 3,
                                    'md': 2
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
                                    'md': 2
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'chmrate',
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
                                    'md': 2
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'jpmrate',
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
                                    'md': 2
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'mrate',
                                            'label': '其他电影评分',
                                            'placeholder': '评分大于等于该值才订阅'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 4,
                                    'md': 2
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'drate',
                                            'label': '纪录片评分',
                                            'placeholder': '评分大于等于该值才订阅'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 3,
                                    'md': 2
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'stmrate',
                                            'label': '科幻惊悚等评分',
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
                                'content': [
                                    {
                                        'component': 'VSelect',
                                        'props': {
                                            'chips': True,
                                            'multiple': True,
                                            'model': 'ranks',
                                            'label': '热门榜单',
                                            'items': [
                                                {'title': '电影北美票房榜', 'value': 'movie-ustop'},
                                                {'title': '一周口碑电影榜', 'value': 'movie-weekly'},
                                                {'title': '实时热门电影', 'value': 'movie-real-time'},
                                                {'title': '热门综艺', 'value': 'show-domestic'},
                                                {'title': '热门电影', 'value': 'movie-hot-gaia'},
                                                {'title': '热门电视剧', 'value': 'tv-hot'},
                                                {'title': '电影TOP10', 'value': 'movie-top250'},
                                                {'title': '电影TOP250', 'value': 'movie-top250-full'},
                                            ]
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
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'rss_addrs',
                                            'label': '自定义榜单地址',
                                            'placeholder': '''每行一个地址，支持单独添加评分筛选，精确到整数，如：
                                            https://rsshub.app/douban/list/movie_weekly_best/score=7
                                            https://rsshub.app/douban/list/tv_global_best_weekly/score=8
                                            '''
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
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 6,
                                    'md': 3,
                                    'style': 'display: flex; align-items: center;'
                                },
                                'content': [
                                    {
                                        'component': 'a',
                                        'props': {
                                            'href': 'https://docs.rsshub.app/zh/routes/social-media#%E8%B1%86%E7%93%A3%E6%A6%9C%E5%8D%95%E4%B8%8E%E9%9B%86%E5%90%88',
                                            'target': '_blank'
                                        },
                                        'text': "RSSHub - 豆瓣榜单与集合"
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
            "stmrate": "0",
            "chmrate": "0",
            "jpmrate": "0",
            "mrate": "0",
            "chtvrate": "0",
            "jptvrate": "0",
            "tvrate": "0",
            "srate": "0",
            "drate": "0",
            "year": "2000",
            "ranks": [],
            "rss_addrs": "",
            "homo": False,
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
                                    'api': 'plugin/DoubanRankRate/delete_history',
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
                                            'text': f'类型：{rtype} - {rate}分'
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
            "stmrate": self._stmrate,
            "chmrate": self._chmrate,
            "jpmrate": self._jpmrate,
            "mrate": self._mrate,
            "chtvrate": self._chtvrate,
            "jptvrate": self._jptvrate,
            "tvrate": self._tvrate,
            "srate": self._srate,
            "drate": self._drate,
            "year": self._year,
            "ranks": self._ranks,
            "rss_addrs": '\n'.join(map(str, self._rss_addrs)),
            "homo": self._homo,
            "clear": self._clear
        })

    def __refresh_rss(self):
        """
        刷新RSS
        """
        logger.info(f"开始刷新豆瓣榜单 ...")
        addr_list = self._rss_addrs + [self._douban_address.get(rank) for rank in self._ranks]
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
                    mtype = None
                    title = rss_info.get('title')
                    douban_id = rss_info.get('doubanid')
                    year = rss_info.get('year')
                    rate = rss_info.get('rate')
                    preset = rss_info.get('preset')
                    is_docu = rss_info.get('is_docu')
                    is_st = rss_info.get('is_st')
                    country = rss_info.get('country')
                    is_homo = rss_info.get('is_homo')
                    rtype = '电影'

                    if not self._homo and is_homo:
                        logger.info(f"跳过：{title} ，类型：{rtype} ，为同性题材")
                        continue

                    if int(year) < self._year:
                        logger.info(f"跳过：{title} ，年份：{year} ，低于设定年份：{self._year}")
                        continue

                    score_match = re.search(r"score=(\d+(?:\.\d+)?)", addr)
                    if country == '日本':
                        rate_limit = self._jpmrate
                    elif country == '中国大陆':
                        rate_limit = self._chmrate
                    else:
                        rate_limit = self._mrate
                    if is_docu:
                        rate_limit = self._drate
                        rtype = '纪录片'
                    elif 'movie_' in addr and is_st:
                        rate_limit = self._stmrate
                        rtype = '科幻惊悚等'
                    elif score_match:
                        rate_limit = float(score_match.group(1))
                        if 'movie_' in addr:
                            rtype = '电影'
                            if country == '日本':
                                rate_limit = self._jpmrate
                            elif country == '中国大陆':
                                rate_limit = self._chmrate
                            else:
                                rate_limit = self._mrate
    
                        elif 'tv_' in addr:
                            rtype = '电视剧'
                            if country == '日本':
                                rate_limit = self._jptvrate
                            elif country == '中国大陆':
                                rate_limit = self._chtvrate
                            else:
                                rate_limit = self._tvrate
                        elif 'show_' in addr:
                            rtype = '综艺'
                    elif 'movie_top250' in addr:
                        rate_limit = 0  # 不做评分限制
                        rtype = '电影'
                    elif 'tv_' in addr:
                        rate_limit = self._tvrate  # 电视剧评分限制
                        rtype = '电视剧'
                        if country == '日本':
                            rate_limit = self._jptvrate
                        elif country == '中国大陆':
                            rate_limit = self._chtvrate
                    elif 'show_' in addr:
                        rate_limit = self._srate  # 综艺评分限制
                        rtype = '综艺'
                    # 判断评分是否符合要求
                    if rate < rate_limit:
                        logger.info(f'{title} 评分{rate}低于 {rate_limit}，不符合要求')
                        continue

                    if 'tv_' in addr or 'show_' in addr:
                        mtype = MediaType.TV
                    else:
                        mtype = MediaType.MOVIE
                    unique_flag = f"doubanrank: {title} (DB:{douban_id})"
                    # 检查是否已处理过
                    if unique_flag in [h.get("unique") for h in history]:
                        continue
                    # 元数据
                    meta = MetaInfo(title)
                    meta.year = year
                    if mtype:
                        meta.type = mtype
                    # 识别媒体信息
                    if douban_id:
                        # 识别豆瓣信息
                        if settings.RECOGNIZE_SOURCE == "themoviedb":
                            tmdbinfo = self.mediachain.get_tmdbinfo_by_doubanid(doubanid=douban_id, mtype=meta.type)
                            if not tmdbinfo:
                                logger.warn(f'未能通过豆瓣ID {douban_id} 获取到TMDB信息，标题：{title}，豆瓣ID：{douban_id}')
                                continue
                            mediainfo = self.chain.recognize_media(meta=meta, tmdbid=tmdbinfo.get("id"))
                            if not mediainfo:
                                logger.warn(f'TMDBID {tmdbinfo.get("id")} 未识别到媒体信息')
                                continue
                        else:
                            mediainfo = self.chain.recognize_media(meta=meta, doubanid=douban_id)
                            if not mediainfo:
                                logger.warn(f'豆瓣ID {douban_id} 未识别到媒体信息')
                                continue
                    else:
                        # 匹配媒体信息
                        mediainfo: MediaInfo = self.chain.recognize_media(meta=meta)
                        if not mediainfo:
                            logger.warn(f'未识别到媒体信息，标题：{title}，豆瓣ID：{douban_id}')
                            continue
                    # 判断评分是否符合要求
                    # if self._rate and rate < self._rate:
                    #     logger.info(f'{mediainfo.title_year} 评分不符合要求')
                    #     continue
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
                        "type": rtype,
                        "year": mediainfo.year,
                        "poster": mediainfo.get_poster_image(),
                        "overview": mediainfo.overview,
                        "tmdbid": mediainfo.tmdb_id,
                        "doubanid": douban_id,
                        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "unique": unique_flag
                    })
            except Exception as e:
                logger.error(str(e))

        # 保存历史记录
        self.save_data('history', history)
        # 缓存只清理一次
        self._clearflag = False
        logger.info(f"所有榜单RSS刷新完成")

    def __get_rss_info(self, addr) -> List[dict]:
        """
        获取RSS
        """
        try:
            if self._proxy:
                ret = RequestUtils(proxies=settings.PROXY).get_res(addr)
            else:
                ret = RequestUtils().get_res(addr)
            if not ret:
                return []
            ret_xml = ret.text
            ret_array = []
            # 解析XML
            dom_tree = xml.dom.minidom.parseString(ret_xml)
            rootNode = dom_tree.documentElement
            items = rootNode.getElementsByTagName("item")
            for item in items:
                try:
                    rss_info = {}

                    # 标题
                    title = DomUtils.tag_value(item, "title", default="")
                    # 链接
                    link = DomUtils.tag_value(item, "link", default="")
                    # 年份
                    description = DomUtils.tag_value(item, "description", default="")

                    if not title and not link:
                        logger.warn(f"条目标题和链接均为空，无法处理")
                        continue
                    rss_info['title'] = title
                    rss_info['link'] = link

                    doubanid = re.findall(r"/(\d+)/", link)
                    if doubanid:
                        doubanid = doubanid[0]
                    if doubanid and not str(doubanid).isdigit():
                        logger.warn(f"解析的豆瓣ID格式不正确：{doubanid}")
                        continue
                    rss_info['doubanid'] = doubanid

                    # 匹配4位独立数字1900-2099年
                    year = re.findall(r"\b(19\d{2}|20\d{2})\b", description)
                    if year:
                        rss_info['year'] = year[0]

                    if "中国大陆" in description:
                        rss_info['country'] = "中国大陆"
                    elif "日本" in description:
                        rss_info['country'] = "日本"
                    else:
                        rss_info['country'] = "其他" 
                    # 是否同性
                    if "同性" in description:
                        rss_info['is_homo'] = True
                    else:
                        rss_info['is_homo'] = False

                    # 是否科幻惊悚恐怖犯罪
                    if "科幻" in description or "惊悚" in description or "恐怖" in description or "犯罪" in description:
                        rss_info['is_st'] = True
                    else:
                        rss_info['is_st'] = False

                    # 提取评分
                    if '评分' in description:
                        # rss_info['preset'] = 'preset'
                        rate_match = re.search(r"评分：(\d+\.?\d*|\无)", description)
                        if rate_match:
                            if rate_match.group(1) == "无":
                                rss_info['rate'] = 0
                            else:
                                rss_info['rate'] = float(rate_match.group(1))
                    else:
                        # rss_info['preset'] = 'custom'
                        rate_match = re.search(r"<p>(\d+(?:\.\d+)?)</p>", description)
                        if rate_match:
                            rss_info['rate'] = float(rate_match.group(1))

                    # 是否纪录片
                    if "纪录片" in description:
                        rss_info['is_docu'] = True
                    else:
                        rss_info['is_docu'] = False

                    # 返回对象
                    ret_array.append(rss_info)
                except Exception as e1:
                    logger.error("解析RSS条目失败：" + str(e1))
                    continue
            return ret_array
        except Exception as e:
            logger.error("获取RSS失败：" + str(e))
            return []
