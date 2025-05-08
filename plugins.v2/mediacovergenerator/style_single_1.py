import base64
import random
import colorsys
from collections import Counter
from io import BytesIO
from pathlib import Path
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


# ========== 配置 ==========
canvas_size = (1920, 1080)

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

def adjust_color_macaron(color):
    """
    调整颜色使其更接近马卡龙风格：
    - 如果颜色太暗，增加亮度
    - 如果颜色太亮，降低亮度
    - 调整饱和度到适当范围
    """
    h, s, v = rgb_to_hsv(color)
    
    # 马卡龙风格的理想范围
    target_saturation_range = (0.3, 0.7)  # 饱和度范围
    target_value_range = (0.6, 0.85)      # 亮度范围
    
    # 调整饱和度
    if s < target_saturation_range[0]:
        s = target_saturation_range[0]
    elif s > target_saturation_range[1]:
        s = target_saturation_range[1]
    
    # 调整亮度
    if v < target_value_range[0]:
        v = target_value_range[0]  # 太暗，加亮
    elif v > target_value_range[1]:
        v = target_value_range[1]  # 太亮，加暗
    
    return hsv_to_rgb(h, s, v)

def color_distance(color1, color2):
    """计算两个颜色在HSV空间中的距离"""
    h1, s1, v1 = rgb_to_hsv(color1)
    h2, s2, v2 = rgb_to_hsv(color2)
    
    # 色调在环形空间中，需要特殊处理
    h_dist = min(abs(h1 - h2), 1 - abs(h1 - h2))
    
    # 综合距离，给予色调更高的权重
    return h_dist * 5 + abs(s1 - s2) + abs(v1 - v2)

def find_dominant_macaron_colors(image, num_colors=5):
    """
    从图像中提取主要颜色并调整为马卡龙风格：
    1. 过滤掉黑白灰颜色
    2. 从剩余颜色中找到出现频率最高的几种
    3. 调整这些颜色使其接近马卡龙风格
    4. 确保提取的颜色之间有足够的差异
    """
    # 缩小图片以提高效率
    img = image.copy()
    img.thumbnail((150, 150))
    img = img.convert('RGB')
    pixels = list(img.getdata())
    
    # 过滤掉黑白灰颜色
    filtered_pixels = [p for p in pixels if is_not_black_white_gray_near(p)]
    if not filtered_pixels:
        return []
    
    # 统计颜色出现频率
    color_counter = Counter(filtered_pixels)
    candidate_colors = color_counter.most_common(num_colors * 5)  # 提取更多候选颜色
    
    macaron_colors = []
    min_color_distance = 0.15  # 颜色差异阈值
    
    for color, _ in candidate_colors:
        # 调整为马卡龙风格
        adjusted_color = adjust_color_macaron(color)
        
        # 检查与已选颜色的差异
        if not any(color_distance(adjusted_color, existing) < min_color_distance for existing in macaron_colors):
            macaron_colors.append(adjusted_color)
            if len(macaron_colors) >= num_colors:
                break
    
    return macaron_colors

def adjust_background_color(color, darken_factor=0.85):
    """
    调整背景色，使其适合作为背景：
    - 降低亮度以减少对比度
    - 略微降低饱和度
    """
    h, s, v = rgb_to_hsv(color)
    # 降低亮度
    v = v * darken_factor
    # 略微降低饱和度
    s = s * 0.9
    return hsv_to_rgb(h, s, v)

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

def crop_to_square(img):
    """将图片裁剪为正方形"""
    width, height = img.size
    size = min(width, height)
    
    left = (width - size) // 2
    top = (height - size) // 2
    right = left + size
    bottom = top + size
    
    return img.crop((left, top, right, bottom))
    
def add_rounded_corners(img, radius=30):
    """
    给图片添加圆角，通过超采样技术消除锯齿
    
    Args:
        img: PIL.Image对象
        radius: 圆角半径
        
    Returns:
        带圆角的图片(RGBA模式)
    """
    # 超采样倍数
    factor = 2
    
    # 获取原始尺寸
    width, height = img.size
    
    # 创建更大尺寸的空白图像（用于超采样）
    enlarged_img = img.resize((width * factor, height * factor), Image.Resampling.LANCZOS)
    enlarged_img = enlarged_img.convert("RGBA")
    
    # 创建透明蒙版，尺寸为放大后的尺寸
    mask = Image.new('L', (width * factor, height * factor), 0)
    draw = ImageDraw.Draw(mask)
    
    draw.rounded_rectangle([(0, 0), (width * factor, height * factor)], 
                            radius=radius * factor, fill=255)
    
    # 创建超采样尺寸的透明背景
    background = Image.new("RGBA", (width * factor, height * factor), (255, 255, 255, 0))
    
    # 使用蒙版合成图像（在高分辨率下）
    high_res_result = Image.composite(enlarged_img, background, mask)
    
    # 将结果缩小回原来的尺寸，应用抗锯齿
    result = high_res_result.resize((width, height), Image.Resampling.LANCZOS)
    
    return result



def add_card_shadow(img, offset=(10, 10), radius=10, opacity=0.5):
    """给卡片添加更真实的阴影效果"""
    # 获取原图尺寸
    width, height = img.size
    
    # 创建一个更大的画布以容纳阴影和旋转后的图像
    # 提供足够的边距，确保旋转后阴影不会被截断
    padding = max(width, height) // 2
    shadow = Image.new("RGBA", (width + padding * 2, height + padding * 2), (0, 0, 0, 0))
    
    # 在原图轮廓绘制黑色阴影，放置在中心偏移的位置
    orig_mask = Image.new("L", (width, height), 255)
    rounded_mask = add_rounded_corners(orig_mask, radius).convert("L")
    
    # 阴影位置计算，从中心位置开始偏移
    shadow_x = padding + offset[0]
    shadow_y = padding + offset[1]
    shadow.paste((0, 0, 0, int(255 * opacity)), 
                (shadow_x, shadow_y, width + shadow_x, height + shadow_y), 
                rounded_mask)
    
    # 模糊阴影以获得更自然的效果
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius))
    
    # 创建结果图像
    result = Image.new("RGBA", shadow.size, (0, 0, 0, 0))
    
    # 先放置阴影
    result.paste(shadow, (0, 0), shadow)
    
    # 放置原图到中心位置
    result.paste(img, (padding, padding), img if img.mode == "RGBA" else None)
    
    return result

def rotate_image(img, angle, bg_color=(0, 0, 0, 0)):
    """旋转图片并确保不会截断图片内容"""
    # expand=True 确保旋转后的图片不会被截断
    return img.rotate(angle, Image.BICUBIC, expand=True, fillcolor=bg_color)


def create_style_single_1(image_path, library_name, title_zh, title_en, zh_font_path, en_font_path):
    try:
        
        num_colors = 6
        # 加载原始图片
        original_img = Image.open(image_path).convert("RGB")
        
        # 从图片提取马卡龙风格的颜色
        candidate_colors = find_dominant_macaron_colors(original_img, num_colors=num_colors)
        
        random.shuffle(candidate_colors)
        extracted_colors = candidate_colors[:num_colors]
            
        # 柔和的马卡龙备选颜色
        soft_macaron_colors = [
            (237, 159, 77),    # 杏色
            (186, 225, 255),   # 淡蓝色
            (255, 223, 186),   # 浅橘色
            (202, 231, 200),   # 淡绿色
        ]
        
        # 确保有足够的颜色
        while len(extracted_colors) < num_colors:
            # 从备选颜色中选择一个与已有颜色差异最大的
            if not extracted_colors:
                extracted_colors.append(random.choice(soft_macaron_colors))
            else:
                max_diff = 0
                best_color = None
                for color in soft_macaron_colors:
                    min_dist = min(color_distance(color, existing) for existing in extracted_colors)
                    if min_dist > max_diff:
                        max_diff = min_dist
                        best_color = color
                extracted_colors.append(best_color or random.choice(soft_macaron_colors))
        
        # 处理颜色
        bg_color = darken_color(extracted_colors[0], 0.85)  # 背景色
        card_colors = [extracted_colors[1], extracted_colors[2]]  # 卡片颜色
        
        # 2. 背景处理
        bg_img = original_img.copy()
        bg_img = ImageOps.fit(bg_img, canvas_size, method=Image.LANCZOS)
        bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=50))  # 强烈模糊化
        
        # 将背景图片与背景色混合
        bg_img_array = np.array(bg_img, dtype=float)
        bg_color_array = np.array([[bg_color]], dtype=float)
        
        # 混合背景图和颜色 (15% 背景图 + 85% 颜色)
        blended_bg = bg_img_array * 0.2 + bg_color_array * 0.8
        blended_bg = np.clip(blended_bg, 0, 255).astype(np.uint8)
        blended_bg_img = Image.fromarray(blended_bg)
        
        # 添加胶片颗粒效果增强纹理感
        blended_bg_img = add_film_grain(blended_bg_img, intensity=0.03)
        
        # 创建最终画布
        canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        canvas.paste(blended_bg_img)
        
        # 3. 处理卡片效果
        # 裁剪为正方形
        square_img = crop_to_square(original_img)
        
        # 计算卡片尺寸 (画布高度的60%)
        card_size = int(canvas_size[1] * 0.7)
        square_img = square_img.resize((card_size, card_size), Image.LANCZOS)
        
        # 准备三张卡片图像
        cards = []
        
        # 主卡片 - 原始图
        main_card = add_rounded_corners(square_img, radius=card_size//8)
        main_card = main_card.convert("RGBA")
        
        # 辅助卡片1 (中间层) - 与第二种颜色混合，加深颜色
        aux_card1 = square_img.copy().filter(ImageFilter.GaussianBlur(radius=8))
        aux_card1_array = np.array(aux_card1, dtype=float)
        card_color1_array = np.array([[card_colors[0]]], dtype=float)
        # 降低原图比例，增加颜色混合比例
        blended_card1 = aux_card1_array * 0.5 + card_color1_array * 0.5
        blended_card1 = np.clip(blended_card1, 0, 255).astype(np.uint8)
        aux_card1 = Image.fromarray(blended_card1)
        aux_card1 = add_rounded_corners(aux_card1, radius=card_size//8)
        aux_card1 = aux_card1.convert("RGBA")
        
        # 辅助卡片2 (底层) - 与第三种颜色混合，加深颜色
        aux_card2 = square_img.copy().filter(ImageFilter.GaussianBlur(radius=16))
        aux_card2_array = np.array(aux_card2, dtype=float)
        card_color2_array = np.array([[card_colors[1]]], dtype=float)
        # 降低原图比例，增加颜色混合比例
        blended_card2 = aux_card2_array * 0.4 + card_color2_array * 0.6
        blended_card2 = np.clip(blended_card2, 0, 255).astype(np.uint8)
        aux_card2 = Image.fromarray(blended_card2)
        aux_card2 = add_rounded_corners(aux_card2, radius=card_size//8)
        aux_card2 = aux_card2.convert("RGBA")
        
        # 添加更明显的阴影效果
        cards = [
            add_card_shadow(aux_card2, offset=(10, 16), radius=18, opacity=0.7),  # 底层卡片阴影更大更明显
            add_card_shadow(aux_card1, offset=(12, 18), radius=20, opacity=0.8), # 中间层卡片
            add_card_shadow(main_card, offset=(15, 20), radius=25, opacity=0.9)   # 顶层卡片
        ]
        
        # 4. 旋转和摆放卡片
        # 计算卡片放置位置 (画布右侧)
        center_x = int(canvas_size[0] - canvas_size[1] * 0.5)  # 稍微左移，给旋转后的卡片留出空间
        center_y = int(canvas_size[1] * 0.5)
        
        # 按照需求指定旋转角度
        # 底层逆时针25度，中间层逆时针10度，顶层顺时针5度
        rotation_angles = [36, 18, 0]
        
        # 创建一个临时画布来保存卡片堆叠效果，提供足够的尺寸避免裁剪
        # 创建一个更大的画布以容纳旋转后的卡片
        stack_size = (canvas_size[0] * 2, canvas_size[1] * 2)
        stack_canvas = Image.new("RGBA", stack_size, (0, 0, 0, 0))
        stack_center_x = stack_size[0] // 2
        stack_center_y = stack_size[1] // 2
        
        # 计算左下角位置作为旋转中心点
        base_card = cards[0]  # 使用底层卡片作为参考
        base_width, base_height = base_card.size
        rotate_center_x = base_width // 2  # 旋转中心X坐标 (相对于卡片)
        rotate_center_y = base_height // 2  # 旋转中心Y坐标 (相对于卡片)
        
        # 放置三张卡片，从底层到顶层
        for i, (card, angle) in enumerate(zip(cards, rotation_angles)):
            # 旋转卡片，使用左下角为旋转中心
            # PIL中，旋转是围绕图片中心进行的，所以我们需要通过平移来模拟围绕左下角旋转
            
            # 旋转卡片
            rotated_card = rotate_image(card, angle)
            rotated_width, rotated_height = rotated_card.size
            
            # 计算放置位置，使三张卡片的左下角重合
            # 这里要考虑到旋转后图片尺寸的变化
            paste_x = stack_center_x - rotated_width // 2
            paste_y = stack_center_y - rotated_height // 2
            
            # 放置卡片
            stack_canvas.paste(rotated_card, (paste_x, paste_y), rotated_card)
        
        # 调整堆叠画布的大小以适合原始画布，并正确定位
        # 裁剪出需要的部分
        crop_left = stack_size[0] // 2 - center_x
        crop_top = stack_size[1] // 2 - center_y
        crop_right = crop_left + canvas_size[0]
        crop_bottom = crop_top + canvas_size[1]
        cropped_stack = stack_canvas.crop((crop_left, crop_top, crop_right, crop_bottom))
        
        # 将裁剪后的卡片画布与背景合并
        canvas = Image.alpha_composite(canvas.convert("RGBA"), cropped_stack)
        
        # 5. 文字处理
        text_layer = Image.new('RGBA', canvas_size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(text_layer)
        
        # 计算左侧区域的中心 X 位置 (画布宽度的四分之一处)
        left_area_center_x = int(canvas_size[0] * 0.25)
        left_area_center_y = canvas_size[1] // 2
        
        zh_font_size = int(canvas_size[1] * 0.17)
        en_font_size = int(canvas_size[1] * 0.07)
        
        zh_font = ImageFont.truetype(zh_font_path, zh_font_size)
        en_font = ImageFont.truetype(en_font_path, en_font_size)
        
        # 文字颜色和阴影颜色
        text_color = (255, 255, 255, 216)  # 85% 不透明度
        shadow_color = darken_color(bg_color, 0.7) + (210,)  # 阴影颜色加透明度
        shadow_offset = 12
        shadow_alpha = 210
        
        # 计算中文标题的位置
        if not title_zh:
            title_zh = library_name
        zh_bbox = draw.textbbox((0, 0), title_zh, font=zh_font)
        zh_text_w = zh_bbox[2] - zh_bbox[0]
        zh_text_h = zh_bbox[3] - zh_bbox[1]
        zh_x = left_area_center_x - zh_text_w // 2
        zh_y = left_area_center_y - zh_text_h - en_font_size // 2 - 5
        
        # 中文标题阴影效果
        for offset in range(3, shadow_offset + 1, 2):
            current_shadow_color = shadow_color[:3] + (shadow_alpha,)
            draw.text((zh_x + offset, zh_y + offset), title_zh, font=zh_font, fill=current_shadow_color)
        
        # 中文标题
        draw.text((zh_x, zh_y), title_zh, font=zh_font, fill=text_color)
        
        if title_en:
            # 计算英文标题的位置
            en_bbox = draw.textbbox((0, 0), title_en, font=en_font)
            en_text_w = en_bbox[2] - en_bbox[0]
            en_text_h = en_bbox[3] - en_bbox[1]
            en_x = left_area_center_x - en_text_w // 2
            en_y = zh_y + zh_text_h + en_font_size  # 调整英文标题位置，与中文标题有一定间距
            
            # 英文标题阴影效果
            for offset in range(2, shadow_offset // 2 + 1):
                current_shadow_color = shadow_color[:3] + (shadow_alpha,)
                draw.text((en_x + offset, en_y + offset), title_en, font=en_font, fill=current_shadow_color)
            
            # 英文标题
            draw.text((en_x, en_y), title_en, font=en_font, fill=text_color)
        
        # 合并所有图层
        combined = Image.alpha_composite(canvas, text_layer)
        
        # 转为 RGB
        rgb_image = combined.convert("RGB")
        
        # 保存到 BytesIO 而不是文件
        buffer = BytesIO()
        rgb_image.save(buffer, format="JPEG", quality=95)
        
        # 获取 base64 字符串
        base64_str = base64.b64encode(buffer.getvalue()).decode()
        return base64_str
        
    except Exception as e:
        print(f"Error creating stack style: {e}")
        return None