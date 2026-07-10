"""
集中管理颜色相关工具函数，避免在多个 style 文件中重复定义。
"""
import colorsys
import random
from collections import Counter

import numpy as np
from PIL import Image


def is_not_black_white_gray_near(color, threshold=20):
    """判断颜色既不是黑、白、灰，也不是接近黑、白。"""
    r, g, b = color
    if (r < threshold and g < threshold and b < threshold) or \
       (r > 255 - threshold and g > 255 - threshold and b > 255 - threshold):
        return False
    gray_diff_threshold = 10
    if abs(r - g) < gray_diff_threshold and abs(g - b) < gray_diff_threshold and abs(r - b) < gray_diff_threshold:
        return False
    return True


def rgb_to_hsv(color):
    """将 RGB 颜色转换为 HSV 颜色。"""
    r, g, b = [x / 255.0 for x in color]
    return colorsys.rgb_to_hsv(r, g, b)


def hsv_to_rgb(h, s, v):
    """将 HSV 颜色转换为 RGB 颜色。"""
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def adjust_to_macaron(h, s, v, target_saturation_range=(0.2, 0.7), target_value_range=(0.55, 0.85)):
    """将颜色的饱和度和亮度调整到接近马卡龙色系的范围，同时避免颜色过亮。"""
    adjusted_s = min(max(s, target_saturation_range[0]), target_saturation_range[1])
    adjusted_v = min(max(v, target_value_range[0]), target_value_range[1])
    return adjusted_s, adjusted_v


def find_dominant_vibrant_colors(image, num_colors=5):
    """
    从图像中提取出现次数较多的前 N 种非黑非白非灰的颜色，
    并将其调整到接近马卡龙色系。
    """
    img = image.copy()
    img.thumbnail((100, 100))
    img = img.convert('RGB')
    pixels = list(img.getdata())
    filtered_pixels = [p for p in pixels if is_not_black_white_gray_near(p)]
    if not filtered_pixels:
        return []
    color_counter = Counter(filtered_pixels)
    dominant_colors = color_counter.most_common(num_colors * 3)

    macaron_colors = []
    seen_hues = set()

    for color, count in dominant_colors:
        h, s, v = rgb_to_hsv(color)
        adjusted_s, adjusted_v = adjust_to_macaron(h, s, v)
        adjusted_rgb = hsv_to_rgb(h, adjusted_s, adjusted_v)

        hue_degree = int(h * 360)
        is_similar_hue = any(abs(hue_degree - seen) < 15 for seen in seen_hues)

        if not is_similar_hue and adjusted_rgb not in macaron_colors:
            macaron_colors.append(adjusted_rgb)
            seen_hues.add(hue_degree)
            if len(macaron_colors) >= num_colors:
                break

    return macaron_colors


def darken_color(color, factor=0.7):
    """将颜色加深。"""
    r, g, b = color
    return (int(r * factor), int(g * factor), int(b * factor))


def add_film_grain(image, intensity=0.05):
    """添加胶片颗粒效果"""
    img_array = np.array(image, dtype=np.float32)

    if image.mode == 'RGBA':
        channels = img_array.shape[2]
        for i in range(min(3, channels)):
            channel = img_array[:, :, i]
            noise = np.random.normal(0, 255 * intensity, channel.shape)
            img_array[:, :, i] = np.clip(channel + noise, 0, 255)
    else:
        noise = np.random.normal(0, 255 * intensity, img_array.shape)
        img_array = np.clip(img_array + noise, 0, 255)

    return Image.fromarray(img_array.astype(np.uint8), image.mode)
