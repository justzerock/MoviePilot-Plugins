import base64
import colorsys
from io import BytesIO
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from app.log import logger
from app.plugins.mediacovergenerator.utils.color_utils import (
    is_not_black_white_gray_near, rgb_to_hsv, hsv_to_rgb, darken_color, add_film_grain
)
from app.plugins.mediacovergenerator.utils.image_manager import (
    ResolutionConfig, ImageResourceManager, managed_image, managed_images
)
from app.plugins.mediacovergenerator.utils.performance_helper import (
    OptimizedImageProcessor, PerformanceMonitor, memory_efficient_operation
)
from app.plugins.mediacovergenerator.utils.color_helper import ColorHelper


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

def add_shadow_and_rotate(canvas, img, angle, offset=(10, 10), radius=10, opacity=0.5, center_pos=None):
    """
    先创建阴影并旋转放置，然后旋转图像并放置
    
    Args:
        canvas: 目标画布
        img: 需要处理的图像
        angle: 旋转角度
        offset: 阴影偏移
        radius: 阴影模糊半径
        opacity: 阴影透明度
        center_pos: 放置中心位置 (x, y)
        
    Returns:
        更新后的画布
    """
    # 获取原图尺寸
    width, height = img.size
    
    # 如果没有指定中心位置，默认使用画布中心
    if center_pos is None:
        center_pos = (canvas.width // 2, canvas.height // 2)
    
    # 1. 创建阴影
    # 创建一个更大的阴影画布，给阴影留足空间，避免截断
    padding = max(radius * 4, 100)  # 为阴影提供足够的空间
    shadow_size = (width + padding * 2, height + padding * 2)
    shadow = Image.new("RGBA", shadow_size, (0, 0, 0, 0))
    
    # 准备阴影蒙版
    mask_size = (width, height)
    shadow_mask = Image.new("L", mask_size, 255)  # 白色蒙版
    
    # 如果原图是RGBA模式，使用其透明通道作为蒙版
    if img.mode == "RGBA":
        shadow_mask = img.split()[3]  # 获取Alpha通道作为蒙版
    
    # 在阴影中心位置创建阴影形状
    shadow_center = (padding, padding)
    shadow.paste((0, 0, 0, int(255 * opacity)), 
                (shadow_center[0], shadow_center[1], 
                 shadow_center[0] + width, shadow_center[1] + height), 
                shadow_mask)
    
    # 模糊阴影，使用较大的半径确保柔和效果
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius))
    
    # 2. 旋转阴影和图像
    # 旋转阴影
    rotated_shadow = rotate_image(shadow, angle)
    shadow_width, shadow_height = rotated_shadow.size
    
    # 计算旋转后的阴影位置（考虑偏移）
    shadow_x = center_pos[0] - shadow_width // 2 + offset[0]
    shadow_y = center_pos[1] - shadow_height // 2 + offset[1]
    
    # 将阴影粘贴到画布上
    canvas.paste(rotated_shadow, (shadow_x, shadow_y), rotated_shadow)
    
    # 旋转原图
    rotated_img = rotate_image(img, angle)
    img_width, img_height = rotated_img.size
    
    # 计算旋转后的图片位置
    img_x = center_pos[0] - img_width // 2
    img_y = center_pos[1] - img_height // 2
    
    # 将图片粘贴到画布上
    canvas.paste(rotated_img, (img_x, img_y), rotated_img)
    
    return canvas


def rotate_image(img, angle, bg_color=(0, 0, 0, 0)):
    """旋转图片并确保不会截断图片内容"""
    # expand=True 确保旋转后的图片不会被截断
    return img.rotate(angle, Image.BICUBIC, expand=True, fillcolor=bg_color)


@memory_efficient_operation
def create_style_static_1(image_path, title, font_path, font_size=(170,75), font_offset=(0,40,40), blur_size=50, color_ratio=0.8, resolution_config=None, bg_color_config=None):
    try:
        logger.info("开始创建单图封面...")

        # 初始化分辨率配置
        if resolution_config is None:
            resolution_config = ResolutionConfig("1080p")

        canvas_size = resolution_config.size
        logger.info(f"图像生成使用的画布尺寸: {canvas_size} (分辨率配置: {resolution_config})")

        zh_font_path, en_font_path = font_path
        title_zh, title_en = title
        zh_font_size = float(font_size[0])
        en_font_size = float(font_size[1])
        zh_font_offset, title_spacing, en_line_spacing = font_offset

        if int(blur_size) < 0:
            blur_size = 50

        if float(color_ratio) < 0 or float(color_ratio) > 1:
            color_ratio = 0.8

        if not float(zh_font_size) > 0:
            zh_font_size = resolution_config.get_font_size(170)
        if not float(en_font_size) > 0:
            en_font_size = resolution_config.get_font_size(75)


        num_colors = 6

        # 使用资源管理器加载原始图片
        with managed_image(image_path, "RGB") as original_img:

            # 获取背景颜色
            if bg_color_config:
                bg_color = ColorHelper.get_background_color(
                    original_img,
                    color_mode=bg_color_config.get('mode', 'auto'),
                    custom_color=bg_color_config.get('custom_color'),
                    config_color=bg_color_config.get('config_color')
                )
                logger.info(f"使用背景颜色: {bg_color} (模式: {bg_color_config.get('mode', 'auto')})")
            else:
                # 从图片提取马卡龙风格的颜色（使用优化的颜色分析）
                candidate_colors = OptimizedImageProcessor.optimized_color_analysis(original_img, num_colors)
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

            # 获取卡片颜色（始终从图片提取）
            card_colors_extracted = ColorHelper.extract_dominant_colors(original_img, num_colors=3, style="macaron")
            card_colors = [card_colors_extracted[1] if len(card_colors_extracted) > 1 else (186, 225, 255),
                          card_colors_extracted[2] if len(card_colors_extracted) > 2 else (255, 223, 186)]

            # 2. 背景处理
            bg_img = original_img.copy()
            bg_img = ImageOps.fit(bg_img, canvas_size, method=Image.LANCZOS)
            # 使用优化的高斯模糊
            bg_img = OptimizedImageProcessor.optimized_gaussian_blur(bg_img, int(blur_size))
        
            # 将背景图片与背景色混合
            bg_img_array = np.array(bg_img, dtype=float)
            bg_color_array = np.array([[bg_color]], dtype=float)

            # 混合背景图和颜色 (15% 背景图 + 85% 颜色)
            blended_bg = bg_img_array * (1 - float(color_ratio)) + bg_color_array * float(color_ratio)
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

            # 计算卡片尺寸 (画布高度的70%)
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

            # 4. 分别添加阴影和旋转
            # 计算卡片放置中心位置 (画布右侧)
            center_x = int(canvas_size[0] - canvas_size[1] * 0.5)  # 稍微左移，给旋转后的卡片留出空间
            center_y = int(canvas_size[1] * 0.5)
            center_pos = (center_x, center_y)
        
            # 按照需求指定旋转角度
            rotation_angles = [36, 18, 0]  # 底层、中间层、顶层的旋转角度

            # 阴影配置
            shadow_configs = [
                {'offset': (10, 16), 'radius': 12, 'opacity': 0.4},  # 底层卡片阴影配置
                {'offset': (15, 22), 'radius': 15, 'opacity': 0.5},  # 中间层卡片阴影配置
                {'offset': (20, 26), 'radius': 18, 'opacity': 0.6},  # 顶层卡片阴影配置
            ]

            # 创建一个临时画布，用于叠加卡片和阴影效果
            cards_canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))

            # 从底层到顶层依次添加阴影和卡片
            cards = [aux_card2, aux_card1, main_card]

            for i, (card, angle, shadow_config) in enumerate(zip(cards, rotation_angles, shadow_configs)):
                # 使用优化后的函数添加阴影和旋转图片
                cards_canvas = add_shadow_and_rotate(
                    cards_canvas,
                    card,
                    angle,
                    offset=shadow_config['offset'],
                    radius=shadow_config['radius'],
                    opacity=shadow_config['opacity'],
                    center_pos=center_pos
                )

            # 将裁剪后的卡片画布与背景合并
            canvas = Image.alpha_composite(canvas.convert("RGBA"), cards_canvas)

            # 5. 文字处理
            text_layer = Image.new('RGBA', canvas_size, (255, 255, 255, 0))
            shadow_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))

            shadow_draw = ImageDraw.Draw(shadow_layer)
            draw = ImageDraw.Draw(text_layer)

            # 计算左侧区域的中心 X 位置 (画布宽度的四分之一处)
            left_area_center_x = int(canvas_size[0] * 0.25)
            left_area_center_y = canvas_size[1] // 2

            # 使用动态字体大小
            zh_font = ImageFont.truetype(zh_font_path, int(zh_font_size))
            en_font = ImageFont.truetype(en_font_path, int(en_font_size))

            # 文字颜色和阴影颜色
            text_color = (255, 255, 255, 229)  # 85% 不透明度
            shadow_color = darken_color(bg_color, 0.8) + (75,)  # 阴影颜色加透明度
            shadow_offset = 12
            shadow_alpha = 75
        
        # 计算中文标题的位置
        zh_bbox = draw.textbbox((0, 0), title_zh, font=zh_font)
        zh_text_w = zh_bbox[2] - zh_bbox[0]
        zh_text_h = zh_bbox[3] - zh_bbox[1]
        
        # 定义英文行间距
        en_line_spacing = int(en_font_size * 0.3)  # 英文行间距为字体大小的30%
        
        # 处理英文标题（如果有）
        en_lines = []
        en_text_w = 0
        en_text_h = 0
        total_en_height = 0
        
        if title_en:
            # 检查英文标题是否需要分行
            en_bbox = draw.textbbox((0, 0), title_en, font=en_font)
            en_full_width = en_bbox[2] - en_bbox[0]
            
            # 如果英文标题比中文标题宽，且包含多个单词，则分行处理
            if en_full_width > zh_text_w and " " in title_en:
                words = title_en.split(" ")
                current_line = words[0]
                
                for word in words[1:]:
                    test_line = current_line + " " + word
                    test_bbox = draw.textbbox((0, 0), test_line, font=en_font)
                    test_width = test_bbox[2] - test_bbox[0]
                    
                    # 如果添加新单词后超过中文宽度，则换行
                    if test_width > zh_text_w:
                        en_lines.append(current_line)
                        current_line = word
                    else:
                        current_line = test_line
                
                # 添加最后一行
                if current_line:
                    en_lines.append(current_line)
                
                # 计算所有英文行的最大宽度和总高度
                for line in en_lines:
                    line_bbox = draw.textbbox((0, 0), line, font=en_font)
                    line_width = line_bbox[2] - line_bbox[0]
                    line_height = line_bbox[3] - line_bbox[1]
                    en_text_w = max(en_text_w, line_width)
                    total_en_height += line_height + en_line_spacing
                
                # 减去最后一个多余的行间距
                if en_lines:
                    total_en_height -= en_line_spacing
                    
                en_text_h = total_en_height
            else:
                # 英文标题不需要分行
                en_lines = [title_en]
                en_text_w = en_full_width
                en_text_h = en_bbox[3] - en_bbox[1]
                total_en_height = en_text_h
        
        # 定义中英文标题间距
        title_spacing = float(title_spacing) if title_en else 0

        # 计算整体文本高度：中文标题高度 + 英文标题高度（如果有）+ 间距（如果有英文标题）
        total_text_height = zh_text_h + total_en_height + title_spacing

        # 计算整体的垂直居中起始位置
        total_text_y = left_area_center_y - total_text_height // 2

        # 中文标题位置
        zh_x = left_area_center_x - zh_text_w // 2
        zh_y = total_text_y + float(zh_font_offset)

        # 中文标题阴影效果
        for offset in range(3, shadow_offset + 1, 2):
            current_shadow_color = shadow_color[:3] + (shadow_alpha,)
            shadow_draw.text((zh_x + offset, zh_y + offset), title_zh, font=zh_font, fill=current_shadow_color)
        
            # 中文标题
            draw.text((zh_x, zh_y), title_zh, font=zh_font, fill=text_color)

            if en_lines:
                # 英文标题起始位置
                en_y = zh_y + zh_text_h + title_spacing

                # 处理多行英文
                for i, line in enumerate(en_lines):
                    # 计算每行的水平居中位置
                    line_bbox = draw.textbbox((0, 0), line, font=en_font)
                    line_width = line_bbox[2] - line_bbox[0]
                    line_height = line_bbox[3] - line_bbox[1]

                    en_x = left_area_center_x - line_width // 2
                    current_y = en_y + i * (line_height + en_line_spacing)

                    # 英文标题阴影效果
                    for offset in range(2, shadow_offset // 2 + 1):
                        current_shadow_color = shadow_color[:3] + (shadow_alpha,)
                        shadow_draw.text((en_x + offset, current_y + offset), line, font=en_font, fill=current_shadow_color)

                    # 英文标题
                    draw.text((en_x, current_y), line, font=en_font, fill=text_color)

            blurred_shadow = shadow_layer.filter(ImageFilter.GaussianBlur(radius=shadow_offset))
            combined = Image.alpha_composite(canvas, blurred_shadow)
            # 合并所有图层
            combined = Image.alpha_composite(combined, text_layer)

            # 转为 RGB
            # rgb_image = combined.convert("RGB")

            def image_to_base64(image, format="auto", quality=85):
                buffer = BytesIO()
                if format.lower() == "auto":
                    if image.mode == "RGBA" or (image.info.get('transparency') is not None):
                        format = "PNG"
                    else:
                        try:
                            image.save(buffer, format="WEBP", quality=quality, optimize=True)
                            base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
                            return base64_str
                        except Exception:
                            format = "JPEG" # Fallback to JPEG if WebP fails
                if format.lower() == "png":
                    image.save(buffer, format="PNG", optimize=True)
                    base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    return base64_str
                elif format.lower() == "jpeg":
                    image = image.convert("RGB") # Ensure RGB for JPEG
                    image.save(buffer, format="JPEG", quality=quality, optimize=True, progressive=True)
                    base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    return base64_str
                else:
                    raise ValueError(f"Unsupported format: {format}")

            return image_to_base64(combined)
        
    except Exception as e:
        logger.error(f"创建单图封面时出错: {e}")
        return False


def create_style_single_1(*args, **kwargs):
    """兼容旧命名"""
    return create_style_static_1(*args, **kwargs)
