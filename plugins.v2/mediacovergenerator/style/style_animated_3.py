import base64
from collections import Counter
import io
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageOps
import numpy as np
import os
import math
import random
from app.log import logger
import subprocess
import tempfile
import shutil
from app.plugins.mediacovergenerator.utils.color_utils import (
    darken_color, add_film_grain, find_dominant_vibrant_colors,
    is_not_black_white_gray_near, rgb_to_hsv, hsv_to_rgb, adjust_to_macaron
)
from app.plugins.mediacovergenerator.utils.color_helper import ColorHelper

""" 
代码修改自 https://github.com/HappyQuQu/jellyfin-library-poster/blob/main/gen_poster.py
"""

# 海报生成配置
POSTER_GEN_CONFIG = {
    "ROWS": 3,  # 每列图片数
    "COLS": 3,  # 总列数
    "MARGIN": 22,  # 图片垂直间距
    "CORNER_RADIUS": 46.1,  # 圆角半径
    "ROTATION_ANGLE": -15.8,  # 旋转角度
    "START_X": 835,  # 第一列的 x 坐标
    "START_Y": -362,  # 第一列的 y 坐标
    "COLUMN_SPACING": 100,  # 列间距
    "SAVE_COLUMNS": True,  # 是否保存每列图片
    "CELL_WIDTH": 410,  # 海报宽度
    "CELL_HEIGHT": 610,  # 海报高度
    "CANVAS_WIDTH": 1920,  # 画布宽度
    "CANVAS_HEIGHT": 1080,  # 画布高度
}

def add_shadow(img, offset=(5, 5), shadow_color=(0, 0, 0, 100), blur_radius=3):
    """
    给图片添加右侧和底部阴影

    参数:
        img: 原始图片（PIL.Image对象）
        offset: 阴影偏移量，(x, y)格式
        shadow_color: 阴影颜色，RGBA格式
        blur_radius: 阴影模糊半径

    返回:
        添加了阴影的新图片
    """
    # 创建一个透明背景，比原图大一些，以容纳阴影
    shadow_width = img.width + offset[0] + blur_radius * 2
    shadow_height = img.height + offset[1] + blur_radius * 2

    shadow = Image.new("RGBA", (shadow_width, shadow_height), (0, 0, 0, 0))

    # 创建阴影层
    shadow_layer = Image.new("RGBA", img.size, shadow_color)

    # 将阴影层粘贴到偏移位置
    shadow.paste(shadow_layer, (blur_radius + offset[0], blur_radius + offset[1]))

    # 模糊阴影
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))

    # 创建结果图像
    result = Image.new("RGBA", shadow.size, (0, 0, 0, 0))

    # 将原图粘贴到结果图像上
    result.paste(img, (blur_radius, blur_radius), img if img.mode == "RGBA" else None)

    # 合并阴影和原图（保持原图在上层）
    shadow_img = Image.alpha_composite(shadow, result)

    return shadow_img


# 单行文字
def draw_text_on_image(
    image, text, position, font_path, font_size, fill_color=(255, 255, 255, 255),
    shadow=False, shadow_color=None, shadow_offset=10, shadow_alpha=75
):
    """
    在图像上绘制文字，可选择添加阴影效果

    参数:
        image: PIL.Image对象
        text: 要绘制的文字
        position: 文字位置 (x, y)
        font_path: 字体文件路径
        font_size: 字体大小
        fill_color: 文字颜色，RGBA格式
        shadow: 是否添加阴影效果
        shadow_color: 阴影颜色，RGB格式，如果为None则自动生成
        shadow_offset: 阴影偏移量
        shadow_alpha: 阴影透明度(0-255)

    返回:
        添加了文字的图像
    """
    # 创建一个可绘制的图像副本
    img_copy = image.copy()
    text_layer = Image.new('RGBA', img_copy.size, (255, 255, 255, 0))
    shadow_layer = Image.new('RGBA', img_copy.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    shadow_draw = ImageDraw.Draw(shadow_layer)
    font = ImageFont.truetype(font_path, font_size)
    
    # 如果需要添加阴影
    if shadow:
        fill_color = (fill_color[0], fill_color[1], fill_color[2], 229)
        if shadow_color is None:
            if len(fill_color) >= 3:
                r = max(0, int(fill_color[0] * 0.7))
                g = max(0, int(fill_color[1] * 0.7))
                b = max(0, int(fill_color[2] * 0.7))
                shadow_color_with_alpha = (r, g, b, shadow_alpha)
            else:
                shadow_color_with_alpha = (50, 50, 50, shadow_alpha)
        else:
            # 确保 shadow_color 是 RGB 或 RGBA
            if len(shadow_color) == 3:
                shadow_color_with_alpha = shadow_color + (shadow_alpha,)
            elif len(shadow_color) == 4:
                shadow_color_with_alpha = shadow_color[:3] + (shadow_alpha,) # 修正：取前三个元素
            else:
                raise ValueError("shadow_color 格式不正确")  # 抛出异常，明确错误

        for offset in range(3, shadow_offset + 1, 2):
            shadow_draw.text(
                (position[0] + offset, position[1] + offset),
                text,
                font=font,
                fill=shadow_color_with_alpha
            )
    # 绘制主文字
    draw.text(position, text, font=font, fill=fill_color)
    blurred_shadow = shadow_layer.filter(ImageFilter.GaussianBlur(radius=shadow_offset))
    combined = Image.alpha_composite(img_copy, blurred_shadow)
    img_copy = Image.alpha_composite(combined, text_layer)

    return img_copy

# 多行文字
def draw_multiline_text_on_image(
    image,
    text,
    position,
    font_path,
    font_size,
    line_spacing=10,
    fill_color=(255, 255, 255, 255),
    shadow=False,
    shadow_color=None,
    shadow_offset=4,
    shadow_alpha=100,
    is_multiline=False,
):
    """
    在图像上绘制多行文字，根据空格自动换行，可选择添加阴影效果

    参数:
        image: PIL.Image对象
        text: 要绘制的文字
        position: 第一行文字位置 (x, y)
        font_path: 字体文件路径
        font_size: 字体大小
        line_spacing: 行间距
        fill_color: 文字颜色，RGBA格式
        shadow: 是否添加阴影效果
        shadow_color: 阴影颜色，RGB格式，如果为None则自动生成
        shadow_offset: 阴影偏移量
        shadow_alpha: 阴影透明度(0-255)

    返回:
        添加了文字的图像和行数
    """
    # 创建一个可绘制的图像副本
    img_copy = image.copy()
    text_layer = Image.new('RGBA', img_copy.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(text_layer)
    font = ImageFont.truetype(font_path, font_size)

    # 按空格分割文本
    lines = text.split(" ")

    # 如果未指定阴影颜色，则根据填充颜色生成
    if shadow:
        fill_color = (fill_color[0], fill_color[1], fill_color[2], 229)
        if shadow_color is None:
            # 使用文字颜色的暗化版本作为阴影
            if len(fill_color) >= 3:
                # 暗化颜色
                r = max(0, int(fill_color[0] * 0.7))
                g = max(0, int(fill_color[1] * 0.7))
                b = max(0, int(fill_color[2] * 0.7))
                shadow_color_with_alpha = (r, g, b, shadow_alpha)
            else:
                # 默认灰色阴影
                shadow_color_with_alpha = (50, 50, 50, shadow_alpha)
        else:
            # 确保 shadow_color 是 RGB 或 RGBA
            if len(shadow_color) == 3:
                shadow_color_with_alpha = shadow_color + (shadow_alpha,)
            elif len(shadow_color) == 4:
                shadow_color_with_alpha = shadow_color[:3] + (shadow_alpha,)
            else:
                raise ValueError("shadow_color 格式不正确")

    # 如果只有一行，直接绘制并返回
    if len(lines) <= 1 or not is_multiline:
        if shadow:
            for offset in range(3, shadow_offset + 1, 2):
                draw.text(
                    (position[0] + offset, position[1] + offset),
                    text,
                    font=font,
                    fill=shadow_color_with_alpha
                )
        draw.text(position, text, font=font, fill=fill_color)
        img_copy = Image.alpha_composite(img_copy, text_layer)
        return img_copy, 1

    # 绘制多行文本
    x, y = position
    for i, line in enumerate(lines):
        current_y = y + i * (font_size + line_spacing)

        if shadow:
            for offset in range(3, shadow_offset + 1, 2):
                draw.text(
                    (x + offset, current_y + offset),
                    line,
                    font=font,
                    fill=shadow_color_with_alpha
                )
        draw.text((x, current_y), line, font=font, fill=fill_color)
    img_copy = Image.alpha_composite(img_copy, text_layer)
    return img_copy, len(lines)


def get_random_color(image_path):
    """
    获取图片随机位置的颜色

    参数:
        image_path: 图片文件路径

    返回:
        随机点颜色，RGBA格式
    """
    try:
        img = Image.open(image_path)
        # 获取图片尺寸
        width, height = img.size

        # 在图片范围内随机选择一个点
        # 避免边缘区域，缩小范围到图片的20%-80%区域
        random_x = random.randint(int(width * 0.5), int(width * 0.8))
        random_y = random.randint(int(height * 0.5), int(height * 0.8))

        # 获取随机点的颜色
        if img.mode == "RGBA":
            r, g, b, a = img.getpixel((random_x, random_y))
            return (r, g, b, a)
        elif img.mode == "RGB":
            r, g, b = img.getpixel((random_x, random_y))
            return (r + 100, g + 50, b, 255)
        else:
            img = img.convert("RGBA")
            r, g, b, a = img.getpixel((random_x, random_y))
            return (r, g, b, a)
    except Exception as e:
        # logger.error(f"获取图片颜色时出错: {e}")
        # 返回随机颜色作为备选
        return (
            random.randint(50, 200),
            random.randint(50, 200),
            random.randint(50, 200),
            255,
        )


def draw_color_block(image, position, size, color):
    """
    在图像上绘制色块

    参数:
        image: PIL.Image对象
        position: 色块位置 (x, y)
        size: 色块大小 (width, height)
        color: 色块颜色，RGBA格式

    返回:
        添加了色块的图像
    """
    # 创建一个可绘制的图像副本
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)

    # 绘制矩形色块
    draw.rectangle(
        [position, (position[0] + size[0], position[1] + size[1])], fill=color
    )

    return img_copy


def create_gradient_background(width, height, color=None):
    """
    创建一个从左到右的渐变背景，使用遮罩技术实现渐变效果
    左侧颜色更深，右侧颜色适中，提供更明显的渐变效果
    
    参数:
        width: 背景宽度
        height: 背景高度
        color: 颜色数组或单个颜色，如果为None则随机生成
              如果是数组，会依次尝试每个颜色，跳过太黑或太淡的颜色
        
    返回:
        渐变背景图像
    """
    def _normalize_rgb(input_rgb):
        """
        将各种可能的输入格式，统一提取成 (r, g, b) 三元组。
        支持：
        - (r, g, b)
        - (r, g, b, a)
        - ((r, g, b), idx) or ((r, g, b, a), idx)
        """
        if isinstance(input_rgb, tuple):
            # 情况 3: ((r,g,b,a), idx) 或 ((r,g,b), idx)
            if len(input_rgb) == 2 and isinstance(input_rgb[0], tuple):
                return _normalize_rgb(input_rgb[0])
            # 情况 2: RGBA
            if len(input_rgb) == 4 and all(isinstance(v, (int, float)) for v in input_rgb):
                return input_rgb[:3]
            # 情况 1: RGB
            if len(input_rgb) == 3 and all(isinstance(v, (int, float)) for v in input_rgb):
                return input_rgb
        raise ValueError(f"无法识别的颜色格式: {input_rgb!r}")

    def _is_mid_bright(input_rgb, min_lum=80, max_lum=200):
        """
        基于相对亮度判断：不过暗（>=min_lum）也不过白（<=max_lum）。
        input_rgb 可为多种格式，函数内部会 normalize。
        """
        r, g, b = _normalize_rgb(input_rgb)
        lum = 0.299*r + 0.587*g + 0.114*b
        return min_lum <= lum <= max_lum
    # 定义用于判断颜色是否合适的函数
    def _is_mid_bright_hsl(input_rgb, min_l=0.3, max_l=0.7):
        """
        基于 HSL Lightness 判断。Lightness 在 [0,1]。
        """
        r, g, b = _normalize_rgb(input_rgb)
        # 归一到 [0,1]
        r1, g1, b1 = r/255.0, g/255.0, b/255.0
        h, l, s = colorsys.rgb_to_hls(r1, g1, b1)
        return min_l <= l <= max_l
    
    selected_color = None
    
    # 如果传入的是颜色数组
    if isinstance(color, list) and len(color) > 0:
        # 尝试找到合适的颜色，最多尝试5个
        for i in range(min(10, len(color))):
            if _is_mid_bright_hsl(color[i]):
                # 如果是(color_tuple, count)格式，提取颜色元组
                if isinstance(color[i], tuple) and len(color[i]) == 2 and isinstance(color[i][0], tuple):
                    selected_color = color[i][0]
                else:
                    selected_color = color[i]
                # logger.info(f" 海报主题色:[{selected_color}]适合做背景")
                break
            else:
                pass
                # logger.info(f" 海报主题色:[{color[i]}]不适合做背景,尝试做下一个颜色")
    
    # 如果没有找到合适的颜色，随机生成一个颜色
    if selected_color is None:

        def random_hsl_to_rgb(
            hue_range=(0, 360),
            sat_range=(0.5, 1.0),
            light_range=(0.5, 0.8)
        ):
            """
            hue_range: 色相范围，取值 0~360
            sat_range: 饱和度范围，取值 0~1
            light_range: 明度范围，取值 0~1
            返回值：RGB 三元组，每个通道 0~255
            """
            h = random.uniform(hue_range[0]/360.0, hue_range[1]/360.0)
            s = random.uniform(sat_range[0], sat_range[1])
            l = random.uniform(light_range[0], light_range[1])
            # colorsys.hls_to_rgb 接受 H, L, S (注意顺序) 都是 0~1
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            # 转回 0~255
            return (int(r*255), int(g*255), int(b*255))

        # 生成颜色示例
        selected_color = random_hsl_to_rgb()
        # logger.info(f"海报所有主题色不适合做背景，随机生成一个颜色[{selected_color}]。")

    # 如果是已经提供的颜色，将其加深
    # 降低各通道的亮度，使颜色更深
    r = int(selected_color[0] * 0.65)  # 降低35%
    g = int(selected_color[1] * 0.65)  # 降低35%
    b = int(selected_color[2] * 0.65)  # 降低35%
    
    # 确保RGB值不会小于0
    r = max(0, r)
    g = max(0, g)
    b = max(0, b)
    
    # 更新颜色
    selected_color = (r, g, b, selected_color[3] if len(selected_color) > 3 else 255)

    # 确保selected_color包含alpha通道
    if len(selected_color) == 3:
        selected_color = (selected_color[0], selected_color[1], selected_color[2], 255)
    
    # 基于selected_color自动生成浅色版本作为右侧颜色
    # 将selected_color的RGB值增加更合适的比例，使右侧颜色适中
    # 限制最大值为255
    r = min(255, int(selected_color[0] * 1.9))  # 从2.2降到1.9
    g = min(255, int(selected_color[1] * 1.9))  # 从2.2降到1.9
    b = min(255, int(selected_color[2] * 1.9))  # 从2.2降到1.9
    
    # 确保至少有一定的亮度增加，但比之前小
    r = max(r, selected_color[0] + 80)  # 从100降到80
    g = max(g, selected_color[1] + 80)  # 从100降到80
    b = max(b, selected_color[2] + 80)  # 从100降到80
    
    # 确保右侧颜色不会太亮
    r = min(r, 230)  # 限制最大亮度
    g = min(g, 230)  # 限制最大亮度
    b = min(b, 230)  # 限制最大亮度
    
    # 创建右侧浅色
    color2 = (r, g, b, selected_color[3])
    
    # 创建左右两个纯色图像
    left_image = Image.new("RGBA", (width, height), selected_color)
    right_image = Image.new("RGBA", (width, height), color2)
    
    # 创建渐变遮罩（从黑到白的横向线性渐变）
    mask = Image.new("L", (width, height), 0)
    mask_data = []
    
    # 生成遮罩数据，使用更加平滑的过渡
    for y in range(height):
        for x in range(width):
            # 计算从左到右的渐变值 (0-255)
            # 使用更加非线性的渐变，使左侧深色区域更大
            mask_value = int(255.0 * (x / width) ** 0.7)  # 从0.85改为0.7
            mask_data.append(mask_value)
    
    # 应用遮罩数据到遮罩图像
    mask.putdata(mask_data)
    
    # 使用遮罩合成左右两个图像
    # 遮罩中黑色部分(0)显示left_image，白色部分(255)显示right_image
    gradient = Image.composite(right_image, left_image, mask)
    
    return gradient


def get_poster_primary_color(image_path):
    """
    分析图片并提取主色调
    
    参数:
        image_path: 图片文件路径
        
    返回:
        主色调颜色，RGBA格式
    """
    try:
        from collections import Counter
        
        # 打开图片
        img = Image.open(image_path)
        
        # 缩小图片尺寸以加快处理速度
        img = img.resize((100, 150), Image.LANCZOS)
        
        # 确保图片为RGBA模式
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        # 获取图片中心部分的像素数据（避免边框和角落）
        # width, height = img.size
        # center_x1 = int(width * 0.2)
        # center_y1 = int(height * 0.2)
        # center_x2 = int(width * 0.8)
        # center_y2 = int(height * 0.8)
        
        # # 裁剪出中心区域
        # center_img = img.crop((center_x1, center_y1, center_x2, center_y2))

        # 获取所有像素
        pixels = list(img.getdata())
        
        # 过滤掉接近黑色和白色的像素，以及透明度低的像素
        filtered_pixels = []
        for pixel in pixels:
            r, g, b, a = pixel
            
            # 跳过透明度低的像素
            if a < 200:
                continue
                
            # 计算亮度
            brightness = (r + g + b) / 3
            
            # 跳过过暗或过亮的像素
            if brightness < 30 or brightness > 220:
                continue
                
            # 添加到过滤后的列表
            filtered_pixels.append((r, g, b, 255))
            
        # 如果过滤后没有像素，使用全部像素
        if not filtered_pixels:
            filtered_pixels = [(p[0], p[1], p[2], 255) for p in pixels if p[3] > 100]
            
        # 如果仍然没有像素，返回默认颜色
        if not filtered_pixels:
            return (150, 100, 50, 255)
            
        # 使用Counter找到出现最多的颜色
        color_counter = Counter(filtered_pixels)
        common_colors = color_counter.most_common(10)
        
        # 如果找到了颜色，返回最常见的颜色
        if common_colors:
            return common_colors
        
        # 如果无法找到主色调，使用平均值
        r_avg = sum(p[0] for p in filtered_pixels) // len(filtered_pixels)
        g_avg = sum(p[1] for p in filtered_pixels) // len(filtered_pixels)
        b_avg = sum(p[2] for p in filtered_pixels) // len(filtered_pixels)
        
        return [(r_avg, g_avg, b_avg, 255)]
     
        
    except Exception as e:
        # logger.error(f"获取图片主色调时出错: {e}")
        # 返回默认颜色作为备选
        return [(150, 100, 50, 255)]

def create_blur_background(image_path, template_width, template_height, background_color, blur_size, color_ratio, lighten_gradient_strength=0.6):
    """
    创建模糊背景图像，将原始图像模糊化并与指定颜色混合，添加胶片颗粒效果
    
    参数:
        image_path (str): 原始图像的路径
        template_width (int): 模板宽度
        template_height (int): 模板高度
        color (tuple or list): 背景混合颜色列表或颜色元组，包含(R,G,B,A)格式的颜色
    
    返回:
        PIL.Image: 处理后的背景图像
    """
    
    # 加载原始图像
    original_img = Image.open(image_path)
    
    # 确保原图像有正确的模式（RGB或RGBA）
    if original_img.mode != 'RGBA':
        original_img = original_img.convert('RGBA')
    
    canvas_size = (template_width, template_height)
    
    # 背景处理
    bg_img = original_img.copy()
    bg_img = ImageOps.fit(bg_img, canvas_size, method=Image.LANCZOS)
    bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=int(blur_size)))

    # 2. 与指定颜色混合
    # 假设 select_suitable_color 和 darken_color 函数存在且正常工作
    actual_color = darken_color(background_color, 0.85)
    
    # 确保 bg_color 是元组形式的RGB颜色
    if len(actual_color) >= 3:
        bg_color = (int(actual_color[0]), int(actual_color[1]), int(actual_color[2]))
    else:
        # 默认颜色，以防颜色格式不正确
        bg_color = (0, 0, 0)

    # 将背景图片与背景色混合
    bg_img_array = np.array(bg_img, dtype=float)
    height, width, channels = bg_img_array.shape
    
    # 创建和背景图片相同大小的颜色数组
    bg_color_array = np.zeros_like(bg_img_array)
    
    # 填充RGB通道
    for i in range(min(3, channels)):  
        bg_color_array[:, :, i] = float(bg_color[i])
    
    # 如果有Alpha通道，设置为完全不透明
    if channels == 4:
        bg_color_array[:, :, 3] = 255.0
    
    # 混合背景图和颜色
    blended_bg_array = bg_img_array * (1 - float(color_ratio)) + bg_color_array * float(color_ratio)
    blended_bg_array = np.clip(blended_bg_array, 0, 255).astype(np.uint8)

    # 转回PIL图像
    mode = 'RGBA' if channels == 4 else 'RGB'
    blended_bg_img = Image.fromarray(blended_bg_array, mode)

    if blended_bg_img.mode != 'RGBA':
        blended_bg_img = blended_bg_img.convert('RGBA')

    # 3. 从左到右颜色变浅的渐变处理
    if lighten_gradient_strength > 0:
        gradient_mask = Image.new("L", canvas_size, 0)  
        draw_mask = ImageDraw.Draw(gradient_mask)

        for x in range(template_width):
            max_alpha_for_gradient = int(255 * np.clip(lighten_gradient_strength, 0.0, 1.0))
            alpha_value = int((x / template_width) * max_alpha_for_gradient)
            draw_mask.line([(x, 0), (x, template_height)], fill=alpha_value)

        # 创建一个白色的叠加层
        lighten_layer = Image.new("RGBA", canvas_size, (255, 255, 255, 0))
        lighten_layer.putalpha(gradient_mask)

        blended_bg_img = Image.alpha_composite(blended_bg_img, lighten_layer)

    # 4. 添加胶片颗粒效果
    # 假设 add_film_grain 函数存在且正常工作
    final_bg_img = add_film_grain(blended_bg_img, intensity=0.03)

    return final_bg_img







def create_style_animated_3(library_dir, title, font_path, font_size=(170,75), font_offset=(0,40,40), 
                           is_blur=False, blur_size=50, color_ratio=0.8, resolution_config=None, 
                           bg_color_config=None, animation_duration=12, animation_scroll='down', 
                           animation_fps=15, animation_format='apng', animation_resolution='300x200', 
                           animation_reduce_colors='strong', stop_event=None):
    """
    生成多图滚动的动图 (GIF/WebP)，通过 ffmpeg 合成
    已优化版：在目标分辨率下直接合成，预处理旋转和文字，效率提升约 5-8 倍。
    """
    try:
        zh_font_size, en_font_size = font_size
        zh_font_offset, title_spacing, en_line_spacing = font_offset

        # 1. 动图目标分辨率 (最终合成画布)
        try:
            target_w, target_h = map(int, animation_resolution.lower().split('x'))
        except:
            target_w, target_h = 320, 180 

        # 2. 计算缩放比例 (基于 1080p 模板)
        scale = target_h / 1080.0
        
        # 内部坐标系映射 (Scale mapping)
        def s(val): return val * scale

        # 重写模板尺寸为目标尺寸
        template_width, template_height = target_w, target_h

        # 调整逻辑参数
        if int(blur_size) < 0: blur_size = 50
        if float(color_ratio) < 0 or float(color_ratio) > 1: color_ratio = 0.8
            
        # 缩放到目标分辨率
        zh_font_size_s = int(zh_font_size * scale)
        en_font_size_s = int(en_font_size * scale)

        zh_font_path, en_font_path = font_path
        title_zh, title_en = title
        poster_folder = Path(library_dir)
        first_image_path = poster_folder / "1.jpg"

        rows = POSTER_GEN_CONFIG["ROWS"]
        cols = POSTER_GEN_CONFIG["COLS"]
        margin = s(POSTER_GEN_CONFIG["MARGIN"])
        corner_radius = s(POSTER_GEN_CONFIG["CORNER_RADIUS"])
        rotation_angle = POSTER_GEN_CONFIG["ROTATION_ANGLE"]

        start_x = s(POSTER_GEN_CONFIG["START_X"])
        start_y = s(POSTER_GEN_CONFIG["START_Y"])
        column_spacing = s(POSTER_GEN_CONFIG["COLUMN_SPACING"])

        cell_width = s(POSTER_GEN_CONFIG["CELL_WIDTH"])
        cell_height = s(POSTER_GEN_CONFIG["CELL_HEIGHT"])

        # 3. 预处理：静态背景与文字层
        color_img = Image.open(first_image_path).convert("RGB")        
        vibrant_colors = find_dominant_vibrant_colors(color_img)
        selected_bg_color = None
        if bg_color_config:
            selected_bg_color = ColorHelper.get_background_color(
                color_img,
                color_mode=bg_color_config.get('mode', 'auto'),
                custom_color=bg_color_config.get('custom_color'),
                config_color=bg_color_config.get('config_color')
            )

        if selected_bg_color:
            blur_color = selected_bg_color
            gradient_color = selected_bg_color
        else:
            blur_color = vibrant_colors[0] if vibrant_colors else (237, 159, 77)
            gradient_color = get_poster_primary_color(first_image_path)

        # 直接在目标分辨率生成背景
        if is_blur:
            bg_img = create_blur_background(first_image_path, target_w, target_h, blur_color, blur_size * scale, color_ratio)
        else:
            bg_img = create_gradient_background(target_w, target_h, gradient_color)

        # 预合成文字层 (在目标分辨率)
        text_overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        text_shadow_color = darken_color(blur_color, 0.8)
        random_color = vibrant_colors[1] if len(vibrant_colors) > 1 else (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200), 255)
        
        text_overlay = draw_text_on_image(
            text_overlay, title_zh, (s(73.32), s(427.34) + zh_font_size_s * zh_font_offset), zh_font_path, zh_font_size_s,
            shadow=is_blur, shadow_color=text_shadow_color
        )
        if title_en:
            text_overlay, line_count = draw_multiline_text_on_image(
                text_overlay, title_en, (s(124.68), s(624.55) + s(title_spacing)),
                en_font_path, en_font_size_s, s(en_line_spacing),
                shadow=is_blur, shadow_color=text_shadow_color, is_multiline=True
            )
            cb_h = int(en_font_size_s + s(en_line_spacing) + (line_count - 1) * (en_font_size_s + s(en_line_spacing)))
            text_overlay = draw_color_block(text_overlay, (s(84.38), s(620.06) + s(title_spacing)), (s(21.51), cb_h), random_color)

        # 预先将文字层和背景合并，减少每帧计算
        base_frame = Image.alpha_composite(bg_img, text_overlay)

        # 4. 图片资源加载与处理
        supported_formats = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp")
        custom_order = "315426987"
        order_map = {num: index for index, num in enumerate(custom_order)}

        all_posters = sorted(
            [os.path.join(poster_folder, f) for f in os.listdir(poster_folder)
             if os.path.isfile(os.path.join(poster_folder, f)) and f.lower().endswith(supported_formats)
             and os.path.splitext(f)[0] in order_map],
            key=lambda x: order_map[os.path.splitext(os.path.basename(x))[0]]
        )
        if not all_posters: return None
        
        # 预缩放原始图片
        processed_images = []
        extended_posters = []
        while len(extended_posters) < rows * cols: extended_posters.extend(all_posters)
        extended_posters = extended_posters[:rows * cols]
        
        for p_path in extended_posters:
            try:
                img = Image.open(p_path).convert("RGBA")
                img = ImageOps.fit(img, (int(cell_width), int(cell_height)), method=Image.Resampling.BILINEAR)
                if corner_radius > 0:
                    mask = Image.new("L", (int(cell_width), int(cell_height)), 0)
                    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (int(cell_width), int(cell_height))], radius=corner_radius, fill=255)
                    img.putalpha(mask)
                # 增加投影
                img_with_shadow = add_shadow(img, offset=(int(s(15)), int(s(15))), shadow_color=(0, 0, 0, 200), blur_radius=int(s(10)))
                processed_images.append(img_with_shadow)
            except Exception as e:
                logger.error(f"图片预处理识别: {e}")
                continue
                
        if not processed_images: return None

        # 5. 准备动画列 (保持未旋转状态)
        column_posters = [processed_images[i::cols] for i in range(cols)]
        scroll_dist = rows * (cell_height + margin) 
        
        # 预计算旋转视角的高度与宽度
        cos_val = max(1e-6, math.cos(math.radians(abs(rotation_angle))))
        view_h = int(target_h / cos_val * 1.6)
        view_w = int(cell_width + s(60)) # 包含投影宽度
        
        rendered_strips = []
        for col_index, current_col_imgs in enumerate(column_posters):
            # [A, B, C, A, B, C, A] 七张无缝循环
            loop_posters = current_col_imgs * 2 + [current_col_imgs[0]]
            shadow_extra = int(s(60))
            col_strip_h = len(loop_posters) * cell_height + (len(loop_posters) - 1) * margin
            col_strip = Image.new("RGBA", (int(cell_width) + shadow_extra, int(col_strip_h) + shadow_extra), (0, 0, 0, 0))
            
            for row_index, p_img in enumerate(loop_posters):
                col_strip.paste(p_img, (0, int(row_index * (cell_height + margin))), p_img)
            
            rendered_strips.append(col_strip)

        # 6. 逐帧合成
        try: fps = max(1, int(animation_fps))
        except: fps = 15
        n_frames = int(float(animation_duration) * fps)
        # 仅交替模式使用列相位差；同向滚动严格保持 static_3 的整列同步布局
        col_phases = [0, scroll_dist // 4, scroll_dist // 2]

        # 预计算中心点对齐偏移 (1080p -> Target)
        base_centers = []
        col_x_step = cell_width - s(50)
        # 动图是按切片旋转再贴回，视觉宽度会比静态整列旋转更“吃空间”，
        # 第三列额外补一个等比偏移，避免与第二列挤在一起。
        third_col_extra_x = s(30)
        for col_index in range(cols):
            base_cx = start_x + col_index * column_spacing
            base_cy = start_y + (rows * cell_height + (rows - 1) * margin) // 2
            if col_index == 1: 
                base_cx += col_x_step
            elif col_index == 2:
                base_cy += -s(155)
                base_cx += col_x_step * 2 + third_col_extra_x
            base_centers.append((base_cx, base_cy))

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            logger.info(f"正在进行帧合成 (共 {n_frames} 帧, 目标 {target_w}x{target_h})...")
            
            # 强制转换为数值类型，防止字符串乘法导致的无限循环
            try:
                safe_fps = int(animation_fps)
                safe_duration = int(animation_duration)
            except (ValueError, TypeError):
                safe_fps = 15
                safe_duration = 12
                
            n_frames = safe_fps * safe_duration
            # 增加保护上限：动图帧数不得超过 500 帧 (约 30秒 @ 15fps)，防止意外挂起
            if n_frames > 500:
                logger.warning(f"检测到异常帧数 {n_frames}，已强制限制为 500 帧以保护系统运行")
                n_frames = 500
            
            logger.info(f"开始生成动画帧: {n_frames} 帧, 格式: {animation_format}, 分辨率: {animation_resolution}")
            
            for i in range(n_frames):
                if stop_event and stop_event.is_set():
                    logger.info("检测到停止信号，中断动图生成 ...")
                    return False
                
                if i % 10 == 0:
                    logger.info(f"正在生成第 {i}/{n_frames} 帧...")
                
                frame = base_frame.copy()
                progress = i / n_frames

                for col_index, strip in enumerate(rendered_strips):
                    total_scroll = progress * scroll_dist
                    phase_offset = col_phases[col_index % len(col_phases)]

                    if animation_scroll == 'up':
                        # 同向上滚：严格同步，不加列相位差
                        dy_float = total_scroll % scroll_dist
                    elif animation_scroll == 'down':
                        # 同向下滚：严格同步，不加列相位差
                        dy_float = (scroll_dist - total_scroll) % scroll_dist
                    elif animation_scroll == 'alternate':
                        # 现有模式：两边向下，中间向上
                        if col_index == 1:
                            dy_float = (total_scroll + phase_offset) % scroll_dist
                        else:
                            dy_float = (scroll_dist - total_scroll + phase_offset) % scroll_dist
                    elif animation_scroll == 'alternate_reverse':
                        # 新增模式：两边向上，中间向下（与 alternate 相反）
                        if col_index == 1:
                            dy_float = (scroll_dist - total_scroll + phase_offset) % scroll_dist
                        else:
                            dy_float = (total_scroll + phase_offset) % scroll_dist
                    else:
                        dy_float = (scroll_dist - total_scroll) % scroll_dist

                    # 裁剪垂直切片 (与老版一致)
                    dy_int = int(dy_float)
                    sub_strip = strip.crop((0, dy_int, view_w, dy_int + view_h))
                    
                    # 旋转切片 (关键：在目标分辨率下旋转，开销极小)
                    rotated_piece = sub_strip.rotate(rotation_angle, resample=Image.Resampling.BILINEAR, expand=True)
                    
                    bcx, bcy = base_centers[col_index]
                    pos_x = int(bcx - rotated_piece.width // 2 + cell_width // 2)
                    pos_y = int(bcy - rotated_piece.height // 2)
                    frame.paste(rotated_piece, (pos_x, pos_y), rotated_piece)

                # 最终一帧写入 (使用 BMP 消除 PNG 压缩耗时)
                frame_file = tmp_path / f"frame_{i:04d}.bmp"
                frame.convert("RGB").save(frame_file, format="BMP")

            # 7. ffmpeg 导出
            output_ext = ".gif" if animation_format == 'gif' else ".png"
            output_file = tmp_path / f"output{output_ext}"
            
            # 构建 ffmpeg 参数，限制线程数为 2，防卡死
            ffmpeg_common = ['ffmpeg', '-hide_banner', '-y', '-framerate', str(fps), '-i', str(tmp_path / 'frame_%04d.bmp'), '-threads', '2']
            
            reduce_mode = animation_reduce_colors
            if isinstance(reduce_mode, bool): reduce_mode = 'strong' if reduce_mode else 'off'
            
            if animation_format == 'gif':
                p_colors = '64' if reduce_mode == 'strong' else ('128' if reduce_mode == 'medium' else '256')
                p_dither = 'none' if reduce_mode == 'strong' else ('bayer:bayer_scale=3' if reduce_mode == 'medium' else 'floyd_steinberg')
                ffmpeg_cmd = ffmpeg_common + ['-filter_complex', f'[0:v] split [a][b]; [a] palettegen=max_colors={p_colors} [p]; [b][p] paletteuse=dither={p_dither}', '-loop', '0', '-f', 'gif', str(output_file)]
            else: # APNG
                if reduce_mode == 'off':
                    ffmpeg_cmd = ffmpeg_common + ['-vcodec', 'apng', '-pix_fmt', 'rgba', '-plays', '0', '-f', 'apng', str(output_file)]
                else:
                    p_colors = '64' if reduce_mode == 'strong' else '128'
                    p_dither = 'none' if reduce_mode == 'strong' else 'bayer:bayer_scale=3'
                    ffmpeg_cmd = ffmpeg_common + ['-filter_complex', f'[0:v] split [a][b]; [a] palettegen=max_colors={p_colors}:reserve_transparent=on [p]; [b][p] paletteuse=dither={p_dither}', '-vcodec', 'apng', '-pix_fmt', 'rgba', '-plays', '0', '-f', 'apng', str(output_file)]

            logger.debug("正在启动 ffmpeg...")
            try:
                # 显式重定向 stdout/stderr 到 PIPE 以便捕捉错误
                result = subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                if result.stderr:
                    result.stderr = b""
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.decode('utf-8', 'ignore') if e.stderr else "无详细错误信息"
                logger.error(f"[VER_FIX_PARAMS] ffmpeg 执行失败 (状态码 {e.returncode})")
                raise
            
            with open(output_file, 'rb') as f:
                final_data = f.read()
            logger.info(f"ffmpeg 导出成功! 最终大小: {len(final_data)/1024/1024:.2f} MB")
            return base64.b64encode(final_data).decode('utf-8')

    except Exception as e:
        logger.error(f"创建 style_animated_3 失败: {e}")
        return False
