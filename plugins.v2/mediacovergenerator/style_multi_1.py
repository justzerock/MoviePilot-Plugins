import base64
from collections import Counter
import io
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageOps
import numpy as np
import os
import math
import random  # 添加随机模块
import colorsys
from app.log import logger

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
    image, text, position, font_path, default_font_path, font_size, fill_color=(255, 255, 255, 255),
    shadow=False, shadow_color=None, shadow_offset=10, shadow_alpha=75
):
    """
    在图像上绘制文字，可选择添加阴影效果

    参数:
        image: PIL.Image对象
        text: 要绘制的文字
        position: 文字位置 (x, y)
        font_path: 字体文件路径
        default_font_path: 默认字体路径
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
    default_font_path,
    font_size,
    line_spacing=10,
    fill_color=(255, 255, 255, 255),
    shadow=False,
    shadow_color=None,
    shadow_offset=4,
    shadow_alpha=100
):
    """
    在图像上绘制多行文字，根据空格自动换行，可选择添加阴影效果

    参数:
        image: PIL.Image对象
        text: 要绘制的文字
        position: 第一行文字位置 (x, y)
        font_path: 字体文件路径
        default_font_path: 默认字体路径
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
    if len(lines) <= 1:
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

def add_film_grain(image, intensity=0.05):
    """
    为图像添加胶片颗粒效果
    
    参数:
        image (PIL.Image): 输入图像
        intensity (float): 颗粒强度，范围从0到1
    
    返回:
        PIL.Image: 添加颗粒效果后的图像
    """
    # 获取图像模式
    mode = image.mode
    
    # 转换为numpy数组
    img_array = np.array(image, dtype=np.float32)
    
    # 确定通道数
    if mode == 'RGBA':
        # 只对RGB通道添加噪声
        channels = img_array.shape[2]
        for i in range(min(3, channels)):  # 只处理RGB通道
            channel = img_array[:, :, i]
            noise = np.random.normal(0, 255 * intensity, channel.shape)
            img_array[:, :, i] = np.clip(channel + noise, 0, 255)
    else:
        # RGB或其他模式
        noise = np.random.normal(0, 255 * intensity, img_array.shape)
        img_array = np.clip(img_array + noise, 0, 255)
    
    # 转换回PIL图像
    grainy_image = Image.fromarray(img_array.astype(np.uint8), mode)
    
    return grainy_image

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

def create_style_multi_1(library_dir, title, font_path, font_size=(1,1), is_blur=False, blur_size=50, color_ratio=0.8):
    """
    生成海报：多张图片以旋转列的形式排列在渐变背景上。
    输入:
      image_datas_base64: base64编码的图片字符串列表。
      title_zh: 中文标题文本。
      title_en: 英文标题文本。
      zh_font_path: 首选的中文字体文件路径 (可以是None)。
      en_font_path: 首选的英文字体文件路径 (可以是None)。
    返回:
      生成的PNG海报图片的base64编码字符串，失败则返回None。
    """
    """
    将多张电影海报排列成三列，每列三张，然后将每列作为整体旋转并放在渐变背景上
    不再依赖外部模板文件，直接生成渐变背景
    """

    try:
        zh_font_size_ratio, en_font_size_ratio = font_size

        if int(blur_size) < 0:
            blur_size = 50

        if float(color_ratio) < 0 or float(color_ratio) > 1:
            color_ratio = 0.8

        if float(zh_font_size_ratio) <= 0:
            zh_font_size_ratio = 1
        if float(en_font_size_ratio) <= 0:
            en_font_size_ratio = 1
        
        zh_font_path, en_font_path = font_path
        title_zh, title_en = title
        # logger.info(f"[3/4] 正在生成海报...")
        # logger.info("-" * 40)
        poster_folder = Path(library_dir)
        first_image_path = poster_folder / "1.jpg"
        # output_path = os.path.join(cover_path, 'output', f"{library_name}.png")
        rows = POSTER_GEN_CONFIG["ROWS"]
        cols = POSTER_GEN_CONFIG["COLS"]
        margin = POSTER_GEN_CONFIG["MARGIN"]
        corner_radius = POSTER_GEN_CONFIG["CORNER_RADIUS"]
        rotation_angle = POSTER_GEN_CONFIG["ROTATION_ANGLE"]
        start_x = POSTER_GEN_CONFIG["START_X"]
        start_y = POSTER_GEN_CONFIG["START_Y"]
        column_spacing = POSTER_GEN_CONFIG["COLUMN_SPACING"]
        save_columns = POSTER_GEN_CONFIG["SAVE_COLUMNS"]

        # 定义模板尺寸（可以根据需要调整）
        template_width = POSTER_GEN_CONFIG["CANVAS_WIDTH"]
        template_height = POSTER_GEN_CONFIG["CANVAS_HEIGHT"]

        # 加载首图并处理
        color_img = Image.open(first_image_path).convert("RGB")        
        # 获取前景图中最鲜明的颜色
        vibrant_colors = find_dominant_vibrant_colors(color_img)
        
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
            blur_color = vibrant_colors[0]
        else:
            blur_color = random.choice(soft_colors) # 默认橙色

        gradient_color = get_poster_primary_color(first_image_path)

        # 创建渐变背景作为模板
        if is_blur:
          colored_bg_img = create_blur_background(first_image_path, template_width, template_height, blur_color, blur_size, color_ratio)
        else:
          colored_bg_img = create_gradient_background(template_width, template_height, gradient_color)

        # 创建保存中间文件的文件夹
        # output_dir = os.path.dirname(output_path)
        # if not os.path.exists(output_dir):
        #     os.makedirs(output_dir)
        # columns_dir = os.path.join(output_dir, "columns")
        # if save_columns and not os.path.exists(columns_dir):
        #     os.makedirs(columns_dir)

        # 支持的图片格式
        supported_formats = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp")
        # 自定义排序顺序,如果custom_order=123456789,则代表九宫格图第一列第一行(1,1)为1.jpg，第一列第二行(1,2)为2.jpg，第一列第三行(1,3)为3.jpg,(2,1)=4.jpg以此类推，(3,3)=9.jpg
        custom_order = "315426987"
        # 这个顺序是优先把最开始的两张图1.jpg和2.jpg放在最显眼的位置(1,2)和(2,2)，而最后一个9.jpg放在看不见的位置(3,1)
        order_map = {num: index for index, num in enumerate(custom_order)}

        # 获取并排序图片
        poster_files = sorted(
            [
                os.path.join(poster_folder, f)
                for f in os.listdir(poster_folder)
                if os.path.isfile(os.path.join(poster_folder, f))
                and f.lower().endswith(supported_formats)
                and os.path.splitext(f)[0]
                in order_map  # 文件名（不含扩展名）必须在自定义顺序里
            ],
            key=lambda x: order_map[os.path.splitext(os.path.basename(x))[0]],
        )

        # 确保至少有一张图片
        if not poster_files:
            # logger.error(f"错误: 在 {poster_folder} 中没有找到支持的图片文件")
            return False

        # 限制最多处理 rows*cols 张图片
        max_posters = rows * cols
        poster_files = poster_files[:max_posters]

        # 固定海报尺寸
        cell_width = POSTER_GEN_CONFIG["CELL_WIDTH"]
        cell_height = POSTER_GEN_CONFIG["CELL_HEIGHT"]

        # 将图片分成3组，每组3张
        grouped_posters = [
            poster_files[i : i + rows] for i in range(0, len(poster_files), rows)
        ]

        # 以渐变背景作为起点
        result = colored_bg_img.copy()
        # 处理每一组（每一列）图片
        for col_index, column_posters in enumerate(grouped_posters):
            if col_index >= cols:
                break

            # 计算当前列的 x 坐标
            column_x = start_x + col_index * column_spacing

            # 计算当前列所有图片组合后的高度（包括间距）
            column_height = rows * cell_height + (rows - 1) * margin

            # 创建一个透明的画布用于当前列的所有图片，增加宽度以容纳右侧阴影
            shadow_extra_width = 20 + 20 * 2  # 右侧阴影需要的额外宽度
            shadow_extra_height = 20 + 20 * 2  # 底部阴影需要的额外高度

            # 修改列画布的尺寸，确保有足够空间容纳阴影
            column_image = Image.new(
                "RGBA",
                (cell_width + shadow_extra_width, column_height + shadow_extra_height),
                (0, 0, 0, 0),
            )

            # 在列画布上放置每张图片
            for row_index, poster_path in enumerate(column_posters):
                try:
                    # 打开海报
                    poster = Image.open(poster_path)

                    # 调整海报大小为固定尺寸
                    # resized_poster = poster.resize(
                    #     (cell_width, cell_height), Image.LANCZOS
                    # )
                    resized_poster = ImageOps.fit(poster, (cell_width, cell_height), method=Image.LANCZOS)

                    # 创建圆角遮罩（如果需要）
                    if corner_radius > 0:
                        # 创建一个透明的遮罩
                        mask = Image.new("L", (cell_width, cell_height), 0)

                        # 绘制圆角
                        draw = ImageDraw.Draw(mask)
                        draw.rounded_rectangle(
                            [(0, 0), (cell_width, cell_height)],
                            radius=corner_radius,
                            fill=255,
                        )

                        # 应用遮罩
                        poster_with_corners = Image.new(
                            "RGBA", resized_poster.size, (0, 0, 0, 0)
                        )
                        poster_with_corners.paste(resized_poster, (0, 0), mask)
                        resized_poster = poster_with_corners

                    # 添加阴影效果到每张海报
                    resized_poster_with_shadow = add_shadow(
                        resized_poster,
                        offset=(20, 20),  # 较大的偏移量
                        shadow_color=(
                            0,
                            0,
                            0,
                            216,
                        ),  # 更深的黑色，但不要超过255的透明度
                        blur_radius=20,  # 保持模糊半径
                    )

                    # 计算在列画布上的位置（垂直排列）
                    y_position = row_index * (cell_height + margin)
                    x_position = 0  # 一般为0，但在有阴影时可能需要调整

                    # 粘贴到列画布上时，不要减去偏移量，确保阴影有空间
                    column_image.paste(
                        resized_poster_with_shadow,
                        (0, y_position),  # 不减去偏移量，确保阴影有空间
                        resized_poster_with_shadow,
                    )

                except Exception as e:
                    # logger.error(f"处理图片 {os.path.basename(poster_path)} 时出错: {e}")
                    continue

            # 保存原始列图像（旋转前）
            # if save_columns:
            #     column_orig_path = os.path.join(
            #         columns_dir, f"{name}_column_{col_index+1}_original.png"
            #     )
            #     column_image.save(column_orig_path)
            #     # logger.debug(
            #         f"已保存原始列图像到: {column_orig_path}"
            #     )

            # 现在我们有了完整的一列图片，准备旋转它
            # 创建一个足够大的画布来容纳旋转后的列
            rotation_canvas_size = int(
                math.sqrt(
                    (cell_width + shadow_extra_width) ** 2
                    + (column_height + shadow_extra_height) ** 2
                )
                * 1.5
            )
            rotation_canvas = Image.new(
                "RGBA", (rotation_canvas_size, rotation_canvas_size), (0, 0, 0, 0)
            )

            # 将列图片放在旋转画布的中央
            paste_x = (rotation_canvas_size - cell_width) // 2
            paste_y = (rotation_canvas_size - column_height) // 2
            rotation_canvas.paste(column_image, (paste_x, paste_y), column_image)

            # 旋转整个列
            rotated_column = rotation_canvas.rotate(
                rotation_angle, Image.BICUBIC, expand=True
            )

            # 保存旋转后的列图像
            # if save_columns:
            #     column_rotated_path = os.path.join(
            #         columns_dir, f"column_{col_index+1}_rotated.png"
            #     )
            #     rotated_column.save(column_rotated_path)
            #     # logger.debug(
            #         f"已保存旋转后的列图像到: {column_rotated_path}"
            #     )

            # 计算列在模板上的位置（不同的列有不同的y起点）
            column_center_y = start_y + column_height // 2
            column_center_x = column_x

            # 根据列索引调整位置
            if col_index == 1:  # 中间列
                column_center_x += cell_width - 50
            elif col_index == 2:  # 右侧列
                column_center_y += -155
                column_center_x += (cell_width) * 2 - 40

            # 计算最终放置位置
            final_x = column_center_x - rotated_column.width // 2 + cell_width // 2
            final_y = column_center_y - rotated_column.height // 2

            # 粘贴旋转后的列到结果图像
            result.paste(rotated_column, (final_x, final_y), rotated_column)

        # 获取第一张图片的随机点颜色
        if poster_files:
            first_image_path = poster_files[0]
            random_color = get_random_color(first_image_path)
        else:
            # 如果没有图片，生成一个随机颜色
            random_color = (
                random.randint(50, 200),
                random.randint(50, 200),
                random.randint(50, 200),
                255,
            )

        # 根据name匹配template_mapping中的配置
        library_ch_name = title_zh  # 默认使用输入的name作为中文名
        library_eng_name = title_en  # 默认英文名为空

        text_shadow_color = darken_color(blur_color, 0.8)
        result = draw_text_on_image(
            result, library_ch_name, (73.32, 427.34), zh_font_path, "ch.ttf", 163 * float(zh_font_size_ratio),
            shadow=is_blur, shadow_color=text_shadow_color
        )

        # 如果有英文名，才添加英文名文字
        if library_eng_name:
            # 动态调整字体大小，但统一使用一个字体大小
            base_font_size = 50 * float(en_font_size_ratio)  # 默认字体大小
            line_spacing = base_font_size * 0.1  # 行间距

            # 计算行数和调整字体大小
            word_count = len(library_eng_name.split())
            max_chars_per_line = max([len(word) for word in library_eng_name.split()])

            # 根据单词数量或最长单词长度调整字体大小
            if max_chars_per_line > 10 or word_count > 3:
                # 字体大小与文本长度成反比
                font_size = (
                    base_font_size
                    * (10 / max(max_chars_per_line, word_count * 3)) ** 0.8
                )
                # 设置最小字体大小限制，确保文字不会太小
                font_size = max(font_size, 30)
            else:
                font_size = base_font_size

            # 打印调试信息
            # logger.debug(f"英文名 '{library_eng_name}' 单词数量: {word_count}, 最长单词长度: {max_chars_per_line}")
            # logger.debug(f"使用字体大小: {font_size:.2f}")


            # 使用多行文本绘制
            result, line_count = draw_multiline_text_on_image(
                result,
                library_eng_name,
                (124.68, 624.55),
                en_font_path, "en.otf",
                int(font_size),
                line_spacing,
                shadow=is_blur, 
                shadow_color=text_shadow_color
            )

            # 根据行数调整色块高度
            color_block_position = (84.38, 620.06)
            # 基础高度为55，每增加一行增加(font_size + line_spacing)的高度
            color_block_height = base_font_size + line_spacing + (line_count - 1) * (int(font_size) + line_spacing)
            color_block_size = (21.51, color_block_height)

            # logger.debug(f"色块高度调整为: {color_block_height} (行数: {line_count})")

            result = draw_color_block(
                result, color_block_position, color_block_size, random_color
            )
        # 保存结果
        def image_to_base64(image, format="auto", quality=85):
            buffer = io.BytesIO()
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
            
        return image_to_base64(result)

    except Exception as e:
        logger.error(f"创建多图封面时出错: {e}")
        return False
