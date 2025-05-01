import base64
import random
import colorsys
from collections import Counter
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


# ========== 配置 ==========
canvas_size = (1280, 720)

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
    dominant_colors = color_counter.most_common(num_colors * 3) # 提取更多候选

    macaron_colors = []
    seen_hues = set() # 避免提取过于相似的颜色

    for color, count in dominant_colors:
        h, s, v = rgb_to_hsv(color)
        adjusted_s, adjusted_v = adjust_to_macaron(h, s, v)
        adjusted_rgb = hsv_to_rgb(h, adjusted_s, adjusted_v)

        # 可以加入一些色调的判断，例如避免过于接近的色调
        hue_degree = int(h * 360)
        is_similar_hue = any(abs(hue_degree - seen) < 15 for seen in seen_hues) # 15度范围内的色调认为是相似的

        if not is_similar_hue and adjusted_rgb not in macaron_colors:
            macaron_colors.append(adjusted_rgb)
            seen_hues.add(hue_degree)
            if len(macaron_colors) >= num_colors:
                break

    return macaron_colors

def darken_color(color, factor=0.7):
    """
    将颜色加深。
    """
    r, g, b = color
    return (int(r * factor), int(g * factor), int(b * factor))


def add_film_grain(image, intensity=0.05):
    """添加胶片颗粒效果"""
    img_array = np.array(image)
    
    # 创建随机噪点
    noise = np.random.normal(0, intensity * 255, img_array.shape)
    
    # 应用噪点
    img_array = img_array + noise
    img_array = np.clip(img_array, 0, 255).astype(np.uint8)
    
    return Image.fromarray(img_array)


def crop_to_16_9(img):
    """直接将图片裁剪为16:9的比例"""
    target_ratio = 16 / 9
    current_ratio = img.width / img.height
    
    if current_ratio > target_ratio:
        # 图片太宽，裁剪两侧
        new_width = int(img.height * target_ratio)
        left = (img.width - new_width) // 2
        img = img.crop((left, 0, left + new_width, img.height))
    else:
        # 图片太高，裁剪上下
        new_height = int(img.width / target_ratio)
        top = (img.height - new_height) // 2
        img = img.crop((0, top, img.width, top + new_height))
    
    return img


def center_foreground_at_three_quarters(img, canvas_size):
    """
    将前景图的高度调整为与画布相同，并将其原始水平中心平移到画布宽度的四分之三处，然后裁剪。
    """
    canvas_width, canvas_height = canvas_size
    img_width, img_height = img.size

    # 计算缩放比例以匹配画布高度
    scale_factor = canvas_height / img_height
    new_img_width = int(img_width * scale_factor)
    resized_img = img.resize((new_img_width, canvas_height), Image.LANCZOS)

    # 计算缩放后前景图的中心 X 坐标
    resized_img_center_x = new_img_width / 2
    # 目标中心 X 坐标是画布的四分之三处
    target_center_x = canvas_width * 0.75
    # 计算平移量
    translation_x = target_center_x - resized_img_center_x

    # 计算裁剪的左右边界
    crop_left = -translation_x
    crop_right = canvas_width - translation_x

    # 处理裁剪边界超出缩放后图片尺寸的情况
    if crop_left < 0:
        crop_left = 0
    if crop_right > new_img_width:
        crop_right = new_img_width

    # 进行裁剪
    cropped_img = resized_img.crop((int(crop_left), 0, int(crop_right), canvas_height))

    # 创建一个新的画布并将裁剪后的前景图粘贴到画布的右侧
    final_img = Image.new("RGB", canvas_size)
    paste_x = int(canvas_width - cropped_img.width)
    final_img.paste(cropped_img, (paste_x, 0))

    return final_img

def create_diagonal_mask(size, split_top=0.5, split_bottom=0.33):
    """
    创建斜线分割的蒙版。左侧为背景 (255)，右侧为前景 (0)。
    """
    mask = Image.new('L', size, 255)
    draw = ImageDraw.Draw(mask)
    width, height = size
    top_x = int(width * split_top)
    bottom_x = int(width * split_bottom)

    # 绘制前景区域 (右侧) - 填充为黑色
    draw.polygon(
        [
            (top_x, 0),
            (width, 0),
            (width, height),
            (bottom_x, height)
        ],
        fill=0
    )

    # 绘制背景区域 (左侧) - 填充为白色
    draw.polygon(
        [
            (0, 0),
            (top_x, 0),
            (bottom_x, height),
            (0, height)
        ],
        fill=255
    )
    return mask

def create_shadow_mask(size, split_top=0.5, split_bottom=0.33, feather_size=40):
    """
    创建一个阴影蒙版，用于左侧图片向右侧图片投射阴影
    """
    width, height = size
    top_x = int(width * split_top)
    bottom_x = int(width * split_bottom)
    
    # 创建基础蒙版 - 左侧完全透明，右侧完全不透明
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    
    # 阴影宽度再缩小一半 (原来的六分之一)
    shadow_width = feather_size // 3
    
    # 绘制阴影区域的多边形 - 向左靠拢
    draw.polygon(
        [
            (top_x - 5, 0),  # 向左偏移5像素，确保没有空隙
            (top_x - 5 + shadow_width, 0),
            (bottom_x - 5 + shadow_width, height),
            (bottom_x - 5, height)
        ],
        fill=255
    )
    
    # 模糊阴影边缘，创造渐变效果，但保持较小的模糊半径
    mask = mask.filter(ImageFilter.GaussianBlur(radius=feather_size//3))
    
    return mask

def create_emby_cover(image_data, title_zh, title_en, zh_font_path, en_font_path):
    try:
        if not title_zh or not title_en:
            title_zh = "未配置标题"
            title_en = "Not Configured"
        image_data = base64.b64decode(image_data)
        image_bytes = BytesIO(image_data)
        
        # 定义斜线分割位置
        split_top = 0.55    # 顶部分割点在画面五分之三的位置
        split_bottom = 0.4  # 底部分割点在画面二分之一的位置
        
        # 加载前景图片并处理
        fg_img_original = Image.open(image_bytes).convert("RGB")
        # 以画面四分之三处为中心处理前景图
        fg_img = center_foreground_at_three_quarters(fg_img_original, canvas_size)
        
        # 获取前景图中最鲜明的颜色
        vibrant_colors = find_dominant_vibrant_colors(fg_img)
        
        # 柔和的颜色备选（马卡龙风格）
        soft_colors = [
            (237, 159, 77),    # 原默认色
            (255, 183, 197),   # 淡粉色
            (186, 225, 255),   # 淡蓝色
            (255, 223, 186),   # 浅橘色
            (202, 231, 200),   # 淡绿色
            (245, 203, 255),   # 淡紫色
        ]
        # 如果有鲜明的颜色，则选择第一个（饱和度最高）作为背景色，否则使用默认颜色
        if vibrant_colors:
            bg_color = vibrant_colors[0]
        else:
            bg_color = random.choice(soft_colors) # 默认橙色
        shadow_color = darken_color(bg_color, 0.5)  # 加深阴影颜色到50%
        
        # 加载背景图片
        bg_img_original = Image.open(image_bytes).convert("RGB")
        bg_img = crop_to_16_9(bg_img_original)
        bg_img = bg_img.resize(canvas_size, Image.LANCZOS)
        
        # 强烈模糊化背景图
        bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=12))
        
        # 将背景图片与背景色混合
        bg_img_array = np.array(bg_img, dtype=float)
        bg_color_array = np.array([[bg_color]], dtype=float)
        
        # 混合背景图和颜色 (10% 背景图 + 90% 颜色) - 使原图几乎不可见，只保留极少纹理
        blended_bg = bg_img_array * 0.2 + bg_color_array * 0.8
        blended_bg = np.clip(blended_bg, 0, 255).astype(np.uint8)
        blended_bg_img = Image.fromarray(blended_bg)
        
        # 添加胶片颗粒效果增强纹理感
        blended_bg_img = add_film_grain(blended_bg_img, intensity=0.05)
        
        # 创建斜线分割的蒙版
        diagonal_mask = create_diagonal_mask(canvas_size, split_top, split_bottom)
        
        # 创建基础画布 - 前景图
        canvas = fg_img.copy()
        
        # 创建阴影蒙版 - 使用加深的背景色作为阴影颜色，减小阴影距离
        shadow_mask = create_shadow_mask(canvas_size, split_top, split_bottom, feather_size=30)
        
        # 创建阴影层 - 使用更加深的背景色
        shadow_layer = Image.new('RGB', canvas_size, shadow_color)
        
        # 创建临时画布用于组合
        temp_canvas = Image.new('RGB', canvas_size)
        
        # 应用阴影到前景图（先将阴影应用到前景图上）
        temp_canvas.paste(canvas)
        temp_canvas.paste(shadow_layer, mask=shadow_mask)
        
        # 使用蒙版将背景图应用到画布上（背景图会覆盖前景图的左侧部分）
        canvas = Image.composite(blended_bg_img, temp_canvas, diagonal_mask)
        
        # ===== 标题绘制 =====
        # 使用RGBA模式进行绘制，以便设置文字透明度

        canvas_rgba = canvas.convert('RGBA')
        text_layer = Image.new('RGBA', canvas_size, (255, 255, 255, 0))
        # shadow_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))

        # shadow_draw = ImageDraw.Draw(shadow_layer)
        draw = ImageDraw.Draw(text_layer)   
        
        # 计算左侧区域的中心 X 位置 (画布宽度的四分之一处)
        left_area_center_x = int(canvas_size[0] * 0.25)
        left_area_center_y = canvas_size[1] // 2
        
        zh_font_size = int(canvas_size[1] * 0.17)
        en_font_size = int(canvas_size[1] * 0.07)
        
        zh_font = ImageFont.truetype(zh_font_path, zh_font_size)
        en_font = ImageFont.truetype(en_font_path, en_font_size)
        
        # 设置80%透明度的文字颜色 (255, 255, 255, 204) - 204是80%不透明度
        text_color = (255, 255, 255, 216)
        shadow_color_rgba = shadow_color + (210,)  # 原始阴影透明度
        shadow_offset = 12
        shadow_alpha = 210
        # 计算中文标题的位置
        zh_bbox = draw.textbbox((0, 0), title_zh, font=zh_font)
        zh_text_w = zh_bbox[2] - zh_bbox[0]
        zh_text_h = zh_bbox[3] - zh_bbox[1]
        zh_x = left_area_center_x - zh_text_w // 2
        zh_y = left_area_center_y - zh_text_h - en_font_size // 2 - 5
        
        # 恢复原始的字体阴影效果 - 完全参考原代码
        for offset in range(3, shadow_offset + 1, 2):
            # shadow_alpha = int(210 * (1 - offset / shadow_offset))
            current_shadow_color = shadow_color + (shadow_alpha,)
            draw.text((zh_x + offset, zh_y + offset), title_zh, font=zh_font, fill=current_shadow_color)
        
        # 80%透明度的主文字
        draw.text((zh_x, zh_y), title_zh, font=zh_font, fill=text_color)
        
        # 计算英文标题的位置
        en_bbox = draw.textbbox((0, 0), title_en, font=en_font)
        en_text_w = en_bbox[2] - en_bbox[0]
        en_text_h = en_bbox[3] - en_bbox[1]
        en_x = left_area_center_x - en_text_w // 2
        en_y = zh_y + zh_text_h + en_font_size
        
        # 恢复原始的英文标题阴影效果
        for offset in range(2, shadow_offset // 2 + 1):
            # shadow_alpha = int(210 * (1 - offset / (shadow_offset // 2)))
            current_shadow_color = shadow_color + (shadow_alpha,)
            draw.text((en_x + offset, en_y + offset), title_en, font=en_font, fill=current_shadow_color)
        
        # 80%透明度的英文主文字
        draw.text((en_x, en_y), title_en, font=en_font, fill=text_color)
        
        # blurred_shadow = shadow_layer.filter(ImageFilter.GaussianBlur(radius=8))

        # combined = Image.alpha_composite(canvas_rgba, blurred_shadow)
        # 把 text_layer 合并到 canvas_rgba 上
        combined = Image.alpha_composite(canvas_rgba, text_layer)

        # 转为 RGB
        rgb_image = combined.convert("RGB")

        # 保存到 BytesIO 而不是文件
        buffer = BytesIO()
        rgb_image.save(buffer, format="JPEG", quality=95)

        # 获取 base64 字符串
        base64_str = base64.b64encode(buffer.getvalue()).decode()
        return base64_str
    except Exception as e:
        return None
