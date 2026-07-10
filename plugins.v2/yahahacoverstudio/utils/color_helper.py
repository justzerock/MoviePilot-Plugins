"""
通用颜色处理工具类
提供从图像中提取颜色、颜色转换、颜色验证等功能
"""

import re
import colorsys
import random
from collections import Counter
from typing import List, Tuple, Optional, Union
from PIL import Image
import numpy as np

from app.log import logger


class ColorHelper:
    """通用颜色处理工具类"""
    
    # 预定义的马卡龙风格备选颜色
    MACARON_FALLBACK_COLORS = [
        (237, 159, 77),    # 杏色
        (186, 225, 255),   # 淡蓝色
        (255, 223, 186),   # 浅橘色
        (202, 231, 200),   # 淡绿色
        (255, 182, 193),   # 浅粉色
        (221, 160, 221),   # 梅花色
        (176, 196, 222),   # 浅钢蓝
        (255, 218, 185),   # 桃色
    ]
    
    # 常见颜色名称到RGB的映射
    COLOR_NAMES = {
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
        'yellow': (255, 255, 0),
        'orange': (255, 165, 0),
        'purple': (128, 0, 128),
        'pink': (255, 192, 203),
        'cyan': (0, 255, 255),
        'magenta': (255, 0, 255),
        'lime': (0, 255, 0),
        'navy': (0, 0, 128),
        'teal': (0, 128, 128),
        'silver': (192, 192, 192),
        'gray': (128, 128, 128),
        'grey': (128, 128, 128),
        'maroon': (128, 0, 0),
        'olive': (128, 128, 0),
        'aqua': (0, 255, 255),
        'fuchsia': (255, 0, 255),
        'white': (255, 255, 255),
        'black': (0, 0, 0),
    }

    @staticmethod
    def rgb_to_hsv(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
        """RGB转HSV"""
        r, g, b = [x / 255.0 for x in rgb]
        return colorsys.rgb_to_hsv(r, g, b)

    @staticmethod
    def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
        """HSV转RGB"""
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return (int(r * 255), int(g * 255), int(b * 255))

    @staticmethod
    def is_not_black_white_gray_near(color: Tuple[int, int, int], threshold: int = 30) -> bool:
        """检查颜色是否不是黑白灰"""
        r, g, b = color
        # 检查是否接近黑色
        if max(r, g, b) < threshold:
            return False
        # 检查是否接近白色
        if min(r, g, b) > 255 - threshold:
            return False
        # 检查是否接近灰色（RGB值相近）
        if abs(r - g) < threshold and abs(g - b) < threshold and abs(r - b) < threshold:
            return False
        return True

    @staticmethod
    def color_distance(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """计算两个颜色在HSV空间中的距离"""
        h1, s1, v1 = ColorHelper.rgb_to_hsv(color1)
        h2, s2, v2 = ColorHelper.rgb_to_hsv(color2)
        
        # 色调是环形的，需要特殊处理
        h_dist = min(abs(h1 - h2), 1 - abs(h1 - h2))
        
        # 综合距离，给予色调更高的权重
        return h_dist * 5 + abs(s1 - s2) + abs(v1 - v2)

    @staticmethod
    def adjust_color_macaron(color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """调整颜色为马卡龙风格"""
        h, s, v = ColorHelper.rgb_to_hsv(color)
        
        # 调整饱和度和亮度以获得马卡龙风格
        s = min(0.6, max(0.3, s))  # 饱和度控制在30%-60%
        v = min(0.9, max(0.6, v))  # 亮度控制在60%-90%
        
        return ColorHelper.hsv_to_rgb(h, s, v)

    @staticmethod
    def darken_color(color: Tuple[int, int, int], factor: float = 0.7) -> Tuple[int, int, int]:
        """将颜色加深"""
        r, g, b = color
        return (int(r * factor), int(g * factor), int(b * factor))

    @staticmethod
    def lighten_color(color: Tuple[int, int, int], factor: float = 1.3) -> Tuple[int, int, int]:
        """将颜色变亮"""
        r, g, b = color
        return (min(255, int(r * factor)), min(255, int(g * factor)), min(255, int(b * factor)))

    @staticmethod
    def parse_color_string(color_str: str) -> Optional[Tuple[int, int, int]]:
        """
        解析颜色字符串，支持多种格式：
        - 十六进制: #FF0000, #f00
        - RGB: rgb(255, 0, 0)
        - 颜色名称: red, blue, etc.
        """
        if not color_str:
            return None
            
        color_str = color_str.strip().lower()
        
        # 十六进制颜色（支持 #RGB / #RGBA / #RRGGBB / #RRGGBBAA）
        if color_str.startswith('#'):
            hex_color = color_str[1:]
            try:
                if len(hex_color) == 3:
                    # 短格式 #f00 -> #ff0000
                    hex_color = ''.join([c*2 for c in hex_color])
                elif len(hex_color) == 4:
                    # 短格式带透明度 #f00f -> #ff0000ff（忽略 alpha）
                    hex_color = ''.join([c*2 for c in hex_color])
                if len(hex_color) == 6:
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    return (r, g, b)
                if len(hex_color) == 8:
                    # hexa: #RRGGBBAA（忽略 alpha）
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    return (r, g, b)
            except ValueError:
                logger.warning(f"无效的十六进制颜色: {color_str}")
                return None
        
        # RGB格式
        rgb_match = re.match(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color_str)
        if rgb_match:
            try:
                r, g, b = map(int, rgb_match.groups())
                if all(0 <= c <= 255 for c in (r, g, b)):
                    return (r, g, b)
            except ValueError:
                logger.warning(f"无效的RGB颜色: {color_str}")
                return None

        # RGBA格式（忽略 alpha）：rgba(35, 226, 218, 0.73)
        rgba_match = re.match(
            r'rgba\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([01]?(?:\.\d+)?)\s*\)',
            color_str,
        )
        if rgba_match:
            try:
                r = int(rgba_match.group(1))
                g = int(rgba_match.group(2))
                b = int(rgba_match.group(3))
                if all(0 <= c <= 255 for c in (r, g, b)):
                    return (r, g, b)
            except ValueError:
                logger.warning(f"无效的RGBA颜色: {color_str}")
                return None
        
        # 颜色名称
        if color_str in ColorHelper.COLOR_NAMES:
            return ColorHelper.COLOR_NAMES[color_str]
        
        logger.warning(f"无法解析的颜色格式: {color_str}")
        return None

    @staticmethod
    def extract_dominant_colors(image: Image.Image, num_colors: int = 5, 
                              style: str = "auto") -> List[Tuple[int, int, int]]:
        """
        从图像中提取主要颜色
        
        Args:
            image: PIL图像对象
            num_colors: 要提取的颜色数量
            style: 颜色风格 ("auto", "macaron", "vibrant", "muted")
        
        Returns:
            颜色列表 [(r, g, b), ...]
        """
        # 缩小图片以提高效率
        img = image.copy()
        img.thumbnail((150, 150))
        img = img.convert('RGB')
        pixels = list(img.getdata())
        
        # 过滤掉黑白灰颜色
        filtered_pixels = [p for p in pixels if ColorHelper.is_not_black_white_gray_near(p)]
        if not filtered_pixels:
            logger.warning("图像中没有找到有效的颜色，使用默认颜色")
            return ColorHelper.MACARON_FALLBACK_COLORS[:num_colors]
        
        # 统计颜色出现频率
        color_counter = Counter(filtered_pixels)
        candidate_colors = color_counter.most_common(num_colors * 5)  # 提取更多候选颜色
        
        extracted_colors = []
        min_color_distance = 0.15  # 颜色差异阈值
        
        for color, _ in candidate_colors:
            # 根据风格调整颜色
            if style == "macaron":
                adjusted_color = ColorHelper.adjust_color_macaron(color)
            elif style == "vibrant":
                # 增强饱和度
                h, s, v = ColorHelper.rgb_to_hsv(color)
                s = min(1.0, s * 1.3)
                adjusted_color = ColorHelper.hsv_to_rgb(h, s, v)
            elif style == "muted":
                # 降低饱和度
                h, s, v = ColorHelper.rgb_to_hsv(color)
                s = s * 0.7
                adjusted_color = ColorHelper.hsv_to_rgb(h, s, v)
            else:  # auto
                adjusted_color = color
            
            # 检查与已选颜色的差异
            if not any(ColorHelper.color_distance(adjusted_color, existing) < min_color_distance 
                      for existing in extracted_colors):
                extracted_colors.append(adjusted_color)
                if len(extracted_colors) >= num_colors:
                    break
        
        # 如果提取的颜色不够，用备选颜色补充
        while len(extracted_colors) < num_colors:
            fallback_color = random.choice(ColorHelper.MACARON_FALLBACK_COLORS)
            if not any(ColorHelper.color_distance(fallback_color, existing) < min_color_distance 
                      for existing in extracted_colors):
                extracted_colors.append(fallback_color)
            else:
                # 如果所有备选颜色都太相似，直接添加
                extracted_colors.append(fallback_color)
                break
        
        return extracted_colors[:num_colors]

    @staticmethod
    def get_background_color(image: Image.Image, color_mode: str = "auto", 
                           custom_color: Optional[str] = None,
                           config_color: Optional[str] = None) -> Tuple[int, int, int]:
        """
        根据模式获取背景颜色
        
        Args:
            image: PIL图像对象
            color_mode: 颜色模式 ("auto", "custom", "config")
            custom_color: 自定义颜色字符串
            config_color: 配置中的颜色字符串
        
        Returns:
            RGB颜色元组
        """
        if color_mode == "custom" and custom_color:
            parsed_color = ColorHelper.parse_color_string(custom_color)
            if parsed_color:
                return parsed_color
            logger.warning(f"无法解析自定义颜色 {custom_color}，回退到自动模式")
        
        if color_mode == "config" and config_color:
            parsed_color = ColorHelper.parse_color_string(config_color)
            if parsed_color:
                return parsed_color
            logger.warning(f"无法解析配置颜色 {config_color}，回退到自动模式")
        
        # 自动模式：从图像中提取
        colors = ColorHelper.extract_dominant_colors(image, num_colors=1, style="macaron")
        return ColorHelper.darken_color(colors[0], 0.85) if colors else (100, 100, 100)
