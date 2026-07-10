import base64
import hashlib
import math
import os
import subprocess
import tempfile
import time
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

from app.log import logger
from app.plugins.mediacovergenerator.utils.color_utils import darken_color, add_film_grain
from app.plugins.mediacovergenerator.utils.animation_utils import _clamp
from app.plugins.mediacovergenerator.utils.color_helper import ColorHelper


def crop_to_square(img):
    width, height = img.size
    size = min(width, height)
    left = (width - size) // 2
    top = (height - size) // 2
    return img.crop((left, top, left + size, top + size))


def add_rounded_corners(img, radius):
    if radius <= 0:
        return img
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)
    result = Image.new("RGBA", img.size, (0, 0, 0, 0))
    result.paste(img, (0, 0), mask)
    return result


def add_soft_rim(img, width=2, color=(255, 246, 236), alpha=110):
    """给圆角卡片添加微亮边，提升卡片与阴影分离度。"""
    if width <= 0:
        return img

    rgba = img.convert("RGBA")
    a = rgba.split()[3]

    ring_size = max(3, width * 2 + 1)
    if ring_size % 2 == 0:
        ring_size += 1
    expanded = a.filter(ImageFilter.MaxFilter(size=ring_size))
    ring = ImageChops.subtract(expanded, a)

    if alpha < 255:
        ring = ring.point(lambda p: int(p * (alpha / 255.0)))

    rim_layer = Image.new("RGBA", rgba.size, color + (0,))
    rim_layer.putalpha(ring)
    return Image.alpha_composite(rgba, rim_layer)


def rotate_around_pivot(
    img,
    angle,
    pivot,
    resample=Image.Resampling.BICUBIC,
    return_pivot=False,
):
    """
    img: PIL Image (RGBA)
    angle: 旋转角度（与 PIL rotate 一致，正值逆时针，负值顺时针）
    pivot: 旋转轴点坐标 (x, y)，相对于输入 img
    return_pivot: 是否返回旋转后画布中的轴点坐标
    """
    w, h = img.size
    px, py = pivot

    pad = int(math.hypot(w, h))
    canvas = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    canvas.paste(img, (pad, pad))

    pivot_on_canvas = (pad + px, pad + py)
    rotated = canvas.rotate(angle, resample=resample, center=pivot_on_canvas)

    if return_pivot:
        return rotated, pivot_on_canvas
    return rotated


def rotate_centered(img, angle, resample=Image.Resampling.BICUBIC):
    """围绕图片中心旋转并返回与原尺寸一致的结果，避免锚点跳变。"""
    w, h = img.size
    rotated = img.rotate(angle, resample=resample, expand=True)
    left = max(0, (rotated.width - w) // 2)
    top = max(0, (rotated.height - h) // 2)
    return rotated.crop((left, top, left + w, top + h))


def rotate_on_stable_canvas(img, angle, canvas_size, resample=Image.Resampling.BICUBIC):
    """
    在固定尺寸画布上围绕正中心旋转。
    要求 canvas_size 和 img 的宽高均为奇数，
    这样图像中心像素和画布中心像素完全重合，
    消除 0.5px 偏移导致的旋转抖动。
    """
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    x = (canvas_size - img.width) // 2
    y = (canvas_size - img.height) // 2
    canvas.paste(img, (x, y), img)
    # ODD // 2 得到精确中心像素索引 (e.g. 401 // 2 = 200)
    c = canvas_size // 2
    return canvas.rotate(angle, resample=resample, expand=False, center=(c, c))



def get_card_with_shadow(img, shadow_offset, shadow_radius, opacity):
    w, h = img.size
    pad = int(shadow_radius * 3)
    # 确保输出尺寸为奇数，与卡片和画布的奇数对齐
    out_w = w + pad * 2
    out_h = h + pad * 2
    if out_w % 2 == 0:
        out_w += 1
    if out_h % 2 == 0:
        out_h += 1
    # 重新计算 pad 使图像居中（左上角 pad 可能与右下角差 1px）
    pad_x = (out_w - w) // 2
    pad_y = (out_h - h) // 2

    canvas = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
    shadow_mask = img.split()[3]
    shadow_layer = Image.new("RGBA", (w, h), (0, 0, 0, int(255 * opacity)))
    canvas.paste(
        shadow_layer,
        (pad_x + int(shadow_offset[0]), pad_y + int(shadow_offset[1])),
        shadow_mask,
    )
    canvas = canvas.filter(ImageFilter.GaussianBlur(shadow_radius))
    canvas.paste(img, (pad_x, pad_y), img)
    return canvas


def _ease_out_back(t, overshoot=0.55):
    t = max(0.0, min(1.0, t))
    u = t - 1.0
    return 1.0 + (overshoot + 1.0) * (u ** 3) + overshoot * (u ** 2)


def _ease_in_out_sine(t):
    t = _clamp(t, 0.0, 1.0)
    return 0.5 * (1.0 - math.cos(math.pi * t))


def _ease_out_quad(t):
    t = _clamp(t, 0.0, 1.0)
    return 1.0 - (1.0 - t) ** 2


def _ease_in_quad(t):
    t = _clamp(t, 0.0, 1.0)
    return t ** 2


def _round_half_up(n, decimals=0):
    """
    实现确定性的“四舍五入”（远离 0 的舍入），
    解决 Python 默认 round() 在 X.5 时舍向偶数（Banker's rounding）导致的抖动。
    """
    multiplier = 10 ** decimals
    return math.floor(n * multiplier + 0.5) / multiplier


def _smoothstep01(t):
    t = _clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _alpha_scaled(img, factor):
    factor = max(0.0, min(1.0, factor))
    if factor >= 1.0:
        return img
    if factor <= 0.0:
        empty = img.copy()
        empty.putalpha(0)
        return empty
    result = img.copy()
    result.putalpha(Image.eval(result.split()[3], lambda x: int(x * factor)))
    return result


def _build_text_layer(target_w, target_h, title, font_path, font_size, font_offset, bg_color, scale):
    text_layer = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    shadow_layer = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))

    draw = ImageDraw.Draw(text_layer)
    shadow_draw = ImageDraw.Draw(shadow_layer)

    zh_font_size, en_font_size = float(font_size[0]), float(font_size[1])
    zh_font_offset, title_spacing, _ = font_offset
    zh_font_path, en_font_path = font_path
    title_zh, title_en = title

    # 参考 style_animated_1：按分辨率比例缩放字体
    zh_font = ImageFont.truetype(zh_font_path, max(1, int(zh_font_size * scale)))
    en_font = ImageFont.truetype(en_font_path, max(1, int(en_font_size * scale)))

    left_area_center_x = int(target_w * 0.25)
    left_area_center_y = int(target_h * 0.5)

    text_color = (255, 255, 255, 229)
    shadow_color = darken_color(bg_color, 0.8) + (75,)
    shadow_offset = 12
    shadow_alpha = 75

    zh_bbox = draw.textbbox((0, 0), title_zh, font=zh_font)
    zh_text_w = zh_bbox[2] - zh_bbox[0]
    zh_text_h = zh_bbox[3] - zh_bbox[1]

    en_line_spacing = max(1, int(en_font_size * 0.12 * scale))
    en_lines = []
    total_en_height = 0

    if title_en:
        en_bbox = draw.textbbox((0, 0), title_en, font=en_font)
        en_full_width = en_bbox[2] - en_bbox[0]

        if en_full_width > zh_text_w and " " in title_en:
            words = title_en.split(" ")
            current_line = words[0]
            for word in words[1:]:
                test_line = current_line + " " + word
                test_bbox = draw.textbbox((0, 0), test_line, font=en_font)
                test_width = test_bbox[2] - test_bbox[0]
                if test_width > zh_text_w:
                    en_lines.append(current_line)
                    current_line = word
                else:
                    current_line = test_line
            if current_line:
                en_lines.append(current_line)

            for line in en_lines:
                line_bbox = draw.textbbox((0, 0), line, font=en_font)
                line_height = line_bbox[3] - line_bbox[1]
                total_en_height += line_height + en_line_spacing
            if en_lines:
                total_en_height -= en_line_spacing
        else:
            en_lines = [title_en]
            total_en_height = en_bbox[3] - en_bbox[1]

    title_spacing_px = float(title_spacing) * scale if title_en else 0
    total_text_height = zh_text_h + total_en_height + title_spacing_px
    total_text_y = left_area_center_y - total_text_height // 2

    zh_x = left_area_center_x - zh_text_w // 2
    zh_y = total_text_y + float(zh_font_offset) * scale

    for offset in range(3, shadow_offset + 1, 2):
        current_shadow_color = shadow_color[:3] + (shadow_alpha,)
        shadow_draw.text((zh_x + offset, zh_y + offset), title_zh, font=zh_font, fill=current_shadow_color)

    draw.text((zh_x, zh_y), title_zh, font=zh_font, fill=text_color)

    if en_lines:
        en_y = zh_y + zh_text_h + title_spacing_px
        for i, line in enumerate(en_lines):
            line_bbox = draw.textbbox((0, 0), line, font=en_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_height = line_bbox[3] - line_bbox[1]
            en_x = left_area_center_x - line_width // 2
            current_y = en_y + i * (line_height + en_line_spacing)

            for offset in range(2, max(3, shadow_offset // 2 + 1)):
                current_shadow_color = shadow_color[:3] + (shadow_alpha,)
                shadow_draw.text((en_x + offset, current_y + offset), line, font=en_font, fill=current_shadow_color)

            draw.text((en_x, current_y), line, font=en_font, fill=text_color)

    blurred_shadow = shadow_layer.filter(ImageFilter.GaussianBlur(radius=shadow_offset))
    return Image.alpha_composite(blurred_shadow, text_layer)


def create_style_animated_1(
    library_dir,
    title,
    font_path,
    font_size=(170, 75),
    font_offset=(0, 40, 40),
    is_blur=False,
    blur_size=50,
    color_ratio=0.8,
    resolution_config=None,
    bg_color_config=None,
    animation_duration=4,
    animation_fps=15,
    animation_format="apng",
    animation_resolution="400x300",
    animation_reduce_colors="strong",
    image_count=5,
    departure_type="fly",
    stop_event=None,
):
    def _animate_background(bg_base_rgba, phase, duration_seconds):
        phase = _clamp(phase, 0.0, 1.0)
        duration_seconds = max(1.0, float(duration_seconds))

        # 缓慢背景动效：使用周期函数保证首尾无缝衔接
        base_amp = _clamp(bg_zoom_amp * 0.14 + 0.002, 0.003, 0.022)
        duration_scale = _clamp(duration_seconds / 6.0, 0.55, 1.0)
        effective_zoom_amp = base_amp * duration_scale

        theta = 2.0 * math.pi * phase
        breath = 0.5 - 0.5 * math.cos(theta)  # 0 -> 1 -> 0
        zoom = 1.0 + effective_zoom_amp * breath

        # 细微平移，增加“活性”，同样用周期函数保证循环自然
        pan_amp = _clamp(min(target_w, target_h) * 0.008 * duration_scale, 1.0, 6.0)
        pan_x = pan_amp * math.sin(theta)
        pan_y = pan_amp * 0.6 * math.sin(theta + math.pi / 3.0)

        safe_margin = max(0.025, effective_zoom_amp + 0.02 + (pan_amp / max(1.0, min(target_w, target_h))))
        overscan_w = int(round(target_w * (1.0 + safe_margin * 2.0)))
        overscan_h = int(round(target_h * (1.0 + safe_margin * 2.0)))

        overscan = ImageOps.fit(
            bg_base_rgba,
            (overscan_w, overscan_h),
            method=Image.Resampling.BICUBIC,
        )

        scaled_w = max(target_w + 2, int(round(overscan_w * zoom)))
        scaled_h = max(target_h + 2, int(round(overscan_h * zoom)))
        scaled = overscan.resize((scaled_w, scaled_h), Image.Resampling.BICUBIC)

        left = int(round((scaled_w - target_w) / 2 + pan_x))
        top = int(round((scaled_h - target_h) / 2 + pan_y))
        left = _clamp(left, 0, max(0, scaled_w - target_w))
        top = _clamp(top, 0, max(0, scaled_h - target_h))
        right = left + target_w
        bottom = top + target_h
        return scaled.crop((left, top, right, bottom))

    def _safe_clamped(value, minimum, maximum, default_value, name, cast_type):
        try:
            parsed = cast_type(value)
        except (ValueError, TypeError):
            logger.warning(f"{name} 参数非法 ({value})，回退默认值 {default_value}")
            return default_value

        if parsed < minimum or parsed > maximum:
            clamped = _clamp(parsed, minimum, maximum)
            logger.warning(f"{name} 参数超出范围 ({parsed})，已限制为 {clamped}")
            return clamped

        return parsed

    def _image_signature(image_path):
        try:
            with Image.open(image_path) as im:
                sig_img = ImageOps.fit(im.convert("L"), (24, 24), method=Image.Resampling.BILINEAR)
                return hashlib.md5(sig_img.tobytes()).hexdigest()
        except Exception:
            # 读图失败时退化到文件名签名
            return f"path:{Path(image_path).name.lower()}"

    try:
        if stop_event and stop_event.is_set():
            logger.info("检测到停止信号，跳过动图生成")
            return False

        image_count = int(_safe_clamped(image_count, 3, 9, 5, "image_count", int))
        bg_zoom_amp = 0.06
        throw_strength = 1.0

        try:
            target_w, target_h = map(int, animation_resolution.split("x"))
        except Exception:
            target_w, target_h = 400, 300

        scale = target_h / 1080.0

        logger.info("正在获取图片资源...")
        poster_folder = Path(library_dir)
        supported_formats = (".jpg", ".jpeg", ".png", ".webp")
        all_posters = sorted(
            [
                os.path.join(poster_folder, f)
                for f in os.listdir(poster_folder)
                if f.lower().endswith(supported_formats)
            ],
            key=lambda x: os.path.getmtime(x),
            reverse=True,
        )

        if not all_posters:
            logger.warning("未找到待处理图片")
            return None

        # 先按图像内容去重，避免多版本同海报扎堆
        unique_posters = []
        seen_signatures = set()
        for p in all_posters:
            sig = _image_signature(p)
            if sig in seen_signatures:
                continue
            seen_signatures.add(sig)
            unique_posters.append(p)

        if not unique_posters:
            unique_posters = all_posters[:]

        if len(unique_posters) >= image_count:
            poster_paths = unique_posters[:image_count]
        else:
            # 补齐时避免相邻重复（在可行情况下）
            poster_paths = []
            repeat_idx = 0
            while len(poster_paths) < image_count:
                candidate = unique_posters[repeat_idx % len(unique_posters)]
                if poster_paths and candidate == poster_paths[-1] and len(unique_posters) > 1:
                    repeat_idx += 1
                    candidate = unique_posters[repeat_idx % len(unique_posters)]
                poster_paths.append(candidate)
                repeat_idx += 1

        logger.info(f"选定的素材图片({len(poster_paths)}): {poster_paths}")
        images = [Image.open(p).convert("RGB") for p in poster_paths]
        n_cards = len(images)

        if stop_event and stop_event.is_set():
            logger.info("检测到停止信号，中断动图生成")
            return False

        logger.info("正在提取色彩与合成背景...")
        # 为每张卡片预生成背景，确保顶层切换时背景同步变化
        bg_bases_rgba = []
        for img in images:
            if bg_color_config:
                base_color = ColorHelper.get_background_color(
                    img,
                    color_mode=bg_color_config.get('mode', 'auto'),
                    custom_color=bg_color_config.get('custom_color'),
                    config_color=bg_color_config.get('config_color')
                )
            else:
                small_img = img.resize((50, 50))
                colors = Counter(list(small_img.getdata())).most_common(10)
                vibrant_colors = [c[0] for c in colors if 100 < sum(c[0]) < 600]
                base_color = vibrant_colors[0] if vibrant_colors else (100, 100, 100)
            bg_color = darken_color(base_color, 0.85)

            bg_img = ImageOps.fit(img, (target_w, target_h), method=Image.Resampling.BICUBIC)
            bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=int(blur_size * scale)))
            bg_img = Image.blend(
                bg_img.convert("RGB"),
                Image.new("RGB", (target_w, target_h), bg_color),
                color_ratio,
            )
            bg_img = add_film_grain(bg_img, 0.03)
            bg_bases_rgba.append(bg_img.convert("RGBA"))

        # 文本阴影主色使用第一张图的背景色系
        main_img = images[0]
        if bg_color_config:
            base_color = ColorHelper.get_background_color(
                main_img,
                color_mode=bg_color_config.get('mode', 'auto'),
                custom_color=bg_color_config.get('custom_color'),
                config_color=bg_color_config.get('config_color')
            )
        else:
            small_img = main_img.resize((50, 50))
            colors = Counter(list(small_img.getdata())).most_common(10)
            vibrant_colors = [c[0] for c in colors if 100 < sum(c[0]) < 600]
            base_color = vibrant_colors[0] if vibrant_colors else (100, 100, 100)
        bg_color = darken_color(base_color, 0.85)

        logger.info("正在合成文字层...")
        zh_font_size, en_font_size = float(font_size[0]), float(font_size[1])
        text_layer = _build_text_layer(
            target_w=target_w,
            target_h=target_h,
            title=title,
            font_path=font_path,
            font_size=(zh_font_size, en_font_size),
            font_offset=font_offset,
            bg_color=bg_color,
            scale=scale,
        )

        logger.info("正在准备卡片图块...")
        # 关键：强制卡片尺寸为奇数 (ODD)
        # 这样卡片中心像素与旋转画布中心像素完美重合，
        # 消除 0.5px 偏移导致的旋转抖动
        card_size = int(target_h * 0.7)
        if card_size % 2 == 0:
            card_size += 1

        processed_cards_main = []
        processed_cards_mid = []
        processed_cards_heavy = []
        for idx, img in enumerate(images):
            sq_raw = crop_to_square(img).resize((card_size, card_size), Image.Resampling.BICUBIC)

            # 参考 static_1：使用同样的马卡龙取色策略
            card_colors_extracted = ColorHelper.extract_dominant_colors(img, num_colors=3, style="macaron")
            c1 = card_colors_extracted[1] if len(card_colors_extracted) > 1 else (186, 225, 255)
            c2 = card_colors_extracted[2] if len(card_colors_extracted) > 2 else (255, 223, 186)

            # 顶层主卡片
            sq_main = add_rounded_corners(sq_raw, radius=card_size // 8).convert("RGBA")

            # 中层：blur=8, 50% 原图 + 50% 颜色
            aux1 = sq_raw.copy().filter(ImageFilter.GaussianBlur(radius=8))
            aux1_arr = np.array(aux1, dtype=float)
            c1_arr = np.array([[c1]], dtype=float)
            aux1_mix = np.clip(aux1_arr * 0.5 + c1_arr * 0.5, 0, 255).astype(np.uint8)
            sq_mid = add_rounded_corners(Image.fromarray(aux1_mix), radius=card_size // 8).convert("RGBA")

            # 底层：blur=16, 40% 原图 + 60% 颜色
            aux2 = sq_raw.copy().filter(ImageFilter.GaussianBlur(radius=16))
            aux2_arr = np.array(aux2, dtype=float)
            c2_arr = np.array([[c2]], dtype=float)
            aux2_mix = np.clip(aux2_arr * 0.4 + c2_arr * 0.6, 0, 255).astype(np.uint8)
            sq_heavy = add_rounded_corners(Image.fromarray(aux2_mix), radius=card_size // 8).convert("RGBA")

            # 保留微亮边，增强卡片层次
            rim_w = max(1, int(1.8 * scale))
            sq_main = add_soft_rim(sq_main, width=rim_w, color=(255, 246, 236), alpha=110)
            sq_mid = add_soft_rim(sq_mid, width=rim_w, color=(255, 246, 236), alpha=92)
            sq_heavy = add_soft_rim(sq_heavy, width=rim_w, color=(255, 246, 236), alpha=82)

            s_radius = max(1, int(15 * scale))

            card_main = get_card_with_shadow(
                sq_main,
                (int(15 * scale), int(20 * scale)),
                s_radius,
                0.5,
            )

            card_mid = get_card_with_shadow(
                sq_mid,
                (int(15 * scale), int(20 * scale)),
                s_radius,
                0.5,
            )

            card_heavy = get_card_with_shadow(
                sq_heavy,
                (int(15 * scale), int(20 * scale)),
                s_radius,
                0.5,
            )

            processed_cards_main.append(card_main)
            processed_cards_mid.append(card_mid)
            processed_cards_heavy.append(card_heavy)
            logger.info(f"卡片 {idx + 1} 准备完成: {card_main.size}")

        # 旋转画布：强制奇数 (ODD)，与卡片奇数尺寸对齐
        card_w, card_h = processed_cards_main[0].size
        stable_canvas_size = int(math.ceil(math.hypot(card_w, card_h))) + 9
        if stable_canvas_size % 2 == 0:
            stable_canvas_size += 1
        # center_offset 是纯整数 (e.g. 401 // 2 = 200)
        center_offset = stable_canvas_size // 2

        center_pos = (int(target_w * 0.75), int(target_h * 0.5))

        try:
            safe_fps = int(animation_fps)
            safe_duration = int(animation_duration)
        except (ValueError, TypeError):
            safe_fps = 15
            safe_duration = 4

        safe_fps = max(1, safe_fps)
        safe_duration = max(1, safe_duration)

        total_frames = max(1, int(round(safe_duration * safe_fps)))


        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            departure_type = (departure_type or "fly").lower()
            if departure_type not in ["fly", "fade", "crossfade"]:
                departure_type = "fly"

            if stop_event and stop_event.is_set():
                logger.info("检测到停止信号，中断动图生成")
                return False

            logger.info(f"开始生成帧，共 {total_frames} 帧，卡片数 {n_cards}")


            for f in range(total_frames):
                if stop_event and stop_event.is_set():
                    logger.info("检测到停止信号，中断动图生成")
                    return False

                if f % 10 == 0:
                    logger.info(f"正在处理第 {f}/{total_frames} 帧...")

                phase = f / float(total_frames)
                cycle_pos = phase * n_cards
                cycle_index = int(cycle_pos)
                local = cycle_pos - cycle_index  # 0.0 -> 1.0

                # 选定参与槽位的卡片
                idx_a = cycle_index % n_cards       # 顶层 -> 移到底层 (Shuffle Card)
                idx_b = (cycle_index + 1) % n_cards # 中层 -> 变顶层
                idx_c = (cycle_index + 2) % n_cards # 底层 -> 变中层
                idx_d = (cycle_index + 3) % n_cards # 未来底层 -> 出现

                # 角度 Slot (CSS 角度 -> PIL 负值)
                s1_ang = -5.0
                s2_ang = 10.0
                s3_ang = 25.0

                # 3D 堆叠位移基数
                stack_dx = int(12 * scale)
                stack_dy = int(12 * scale)
                p1 = (0.0, 0.0)
                p2 = (float(stack_dx), float(stack_dy))
                p3 = (float(stack_dx * 2), float(stack_dy * 2))

                # 全局 ease-in-out 因子
                it_stack = _ease_in_out_sine(local)

                # 1. 堆叠层同步移动 (B 和 C 同时转动)
                ang_b = s2_ang + (s1_ang - s2_ang) * it_stack
                pos_b = (p2[0] + (p1[0] - p2[0]) * it_stack, p2[1] + (p1[1] - p2[1]) * it_stack)
                
                ang_c = s3_ang + (s2_ang - s3_ang) * it_stack
                pos_c = (p3[0] + (p2[0] - p3[0]) * it_stack, p3[1] + (p2[1] - p3[1]) * it_stack)
                
                # D: 新底层卡片渐变出现
                alpha_d = _ease_in_out_sine(local)
                ang_d = s3_ang
                pos_d = p3

                # 2. 顶层卡片 A 的离开方式
                ang_a = s1_ang
                cross_t = 0.0
                if departure_type == "crossfade":
                    # 渐变：卡片不移动，仅顶层图像渐变到下一张
                    dx_a = 0.0
                    dy_a = 0.0
                    alpha_a = 1.0
                    cross_t = _ease_in_out_sine(local)
                elif departure_type == "fade":
                    # 淡出：原地不动，透明度缓慢降低
                    dx_a = 0.0
                    dy_a = 0.0
                    alpha_a = _clamp(1.0 - _ease_in_out_sine(local), 0.0, 1.0)
                else:
                    # 飞出：向右上角滑出并逐渐消失
                    fly_x = target_w * 0.75
                    fly_y = -target_h * 0.20
                    it_a = _ease_in_out_sine(local)
                    dx_a = fly_x * it_a
                    dy_a = fly_y * it_a
                    # 后半段开始淡出
                    if local > 0.4:
                        fade_t = (local - 0.4) / 0.6
                        alpha_a = _clamp(1.0 - fade_t * fade_t, 0.0, 1.0)
                    else:
                        alpha_a = 1.0

                # 绘制顺序与图层
                if departure_type == "crossfade":
                    # 顶层不透明渐变：仅顶层内容变化，不漏出下一层
                    top_blend = Image.blend(processed_cards_main[idx_a], processed_cards_main[idx_b], cross_t)
                    mid_blend = Image.blend(processed_cards_mid[idx_b], processed_cards_mid[idx_c], cross_t)
                    bottom_blend = Image.blend(processed_cards_heavy[idx_c], processed_cards_heavy[idx_d], cross_t)

                    z_order = [
                        (None, s3_ang, 1.0, p3, True, bottom_blend),
                        (None, s2_ang, 1.0, p2, True, mid_blend),
                        (None, s1_ang, 1.0, p1, False, top_blend),
                    ]
                else:
                    # 飞出/淡出：二三层在旋转补位中逐渐清晰
                    clarity_t = _ease_in_out_sine(local)
                    b_blend = Image.blend(processed_cards_mid[idx_b], processed_cards_main[idx_b], _clamp(clarity_t * 0.95, 0.0, 1.0))
                    c_blend = Image.blend(processed_cards_heavy[idx_c], processed_cards_mid[idx_c], _clamp(clarity_t * 0.90, 0.0, 1.0))

                    z_order = [
                        (idx_d, ang_d, alpha_d, pos_d, True, processed_cards_heavy[idx_d]),
                        (idx_c, ang_c, 1.0, pos_c, True, c_blend),
                        (idx_b, ang_b, 1.0, pos_b, True, b_blend),
                        (idx_a, ang_a, alpha_a, (dx_a, dy_a), False, None),
                    ]

                # 背景动效：随顶层切换做渐变，保证新顶层出现时背景同步变化
                bg_mix_t = _ease_in_out_sine(local)
                bg_base = Image.blend(bg_bases_rgba[idx_a], bg_bases_rgba[idx_b], bg_mix_t)
                frame = _animate_background(bg_base, phase, safe_duration)

                # 按照 Z-order 绘制 (center_offset 已在循环外预计算为整数)
                for idx, ang, alpha, offsets, use_soft, card_override in z_order:
                    if alpha <= 0:
                        continue

                    if card_override is not None:
                        card_src = card_override
                    else:
                        if idx is None:
                            continue
                        card_src = processed_cards_mid[idx] if use_soft else processed_cards_main[idx]

                    card_img = _alpha_scaled(card_src, alpha)

                    # 顶层渐变时给顶层加一层模糊底，避免过渡期露出下层
                    if departure_type == "crossfade" and card_override is not None and not use_soft:
                        top_blur_base = _alpha_scaled(card_override.filter(ImageFilter.GaussianBlur(radius=max(1, int(2.0 * scale)))), 0.92)
                        blur_rot = rotate_on_stable_canvas(top_blur_base, ang, stable_canvas_size)
                        blur_x = int(round(center_pos[0] + offsets[0])) - center_offset
                        blur_y = int(round(center_pos[1] + offsets[1])) - center_offset
                        frame.paste(blur_rot, (blur_x, blur_y), blur_rot)

                    rotated = rotate_on_stable_canvas(card_img, ang, stable_canvas_size)
                    
                    draw_x = int(round(center_pos[0] + offsets[0])) - center_offset
                    draw_y = int(round(center_pos[1] + offsets[1])) - center_offset
                    
                    frame.paste(rotated, (draw_x, draw_y), rotated)

                frame = Image.alpha_composite(frame, text_layer)

                frame_file = tmp_path / f"frame_{f:04d}.bmp"
                frame.convert("RGB").save(frame_file, format="BMP")

            if stop_event and stop_event.is_set():
                logger.info("检测到停止信号，跳过 ffmpeg 导出")
                return False

            output_ext = ".gif" if animation_format == "gif" else ".png"
            output_file = tmp_path / f"output{output_ext}"

            generated_frames = list(tmp_path.glob("frame_*.bmp"))
            if not generated_frames:
                logger.error("未生成任何动画帧文件，无法导出")
                return False
            logger.info(f"已生成 {len(generated_frames)} 帧素材，准备启动 ffmpeg...")

            ffmpeg_common = [
                "ffmpeg",
                "-hide_banner",
                "-y",
                "-framerate",
                str(safe_fps),
                "-i",
                str(tmp_path / "frame_%04d.bmp"),
                "-threads",
                "2",
            ]

            reduce_mode = animation_reduce_colors
            if isinstance(reduce_mode, bool):
                reduce_mode = "strong" if reduce_mode else "off"

            if animation_format == "gif":
                p_colors = "64" if reduce_mode == "strong" else ("128" if reduce_mode == "medium" else "256")
                p_dither = "none" if reduce_mode == "strong" else ("bayer:bayer_scale=3" if reduce_mode == "medium" else "floyd_steinberg")
                ffmpeg_cmd = ffmpeg_common + [
                    "-filter_complex",
                    f"[0:v] split [a][b]; [a] palettegen=max_colors={p_colors} [p]; [b][p] paletteuse=dither={p_dither}",
                    "-loop",
                    "0",
                    "-f",
                    "gif",
                    str(output_file),
                ]
            else:
                if reduce_mode == "off":
                    ffmpeg_cmd = ffmpeg_common + [
                        "-vcodec",
                        "apng",
                        "-pix_fmt",
                        "rgba",
                        "-plays",
                        "0",
                        "-f",
                        "apng",
                        str(output_file),
                    ]
                else:
                    p_colors = "64" if reduce_mode == "strong" else "128"
                    p_dither = "none" if reduce_mode == "strong" else "bayer:bayer_scale=3"
                    ffmpeg_cmd = ffmpeg_common + [
                        "-filter_complex",
                        f"[0:v] split [a][b]; [a] palettegen=max_colors={p_colors}:reserve_transparent=on [p]; [b][p] paletteuse=dither={p_dither}",
                        "-vcodec",
                        "apng",
                        "-pix_fmt",
                        "rgba",
                        "-plays",
                        "0",
                        "-f",
                        "apng",
                        str(output_file),
                    ]

            logger.debug("正在启动 ffmpeg...")

            if stop_event and stop_event.is_set():
                logger.info("检测到停止信号，取消 ffmpeg 启动")
                return False

            ffmpeg_proc = None
            try:
                ffmpeg_proc = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=False,
                )

                while True:
                    ret = ffmpeg_proc.poll()
                    if ret is not None:
                        if ret != 0:
                            err_data = ffmpeg_proc.stderr.read() if ffmpeg_proc.stderr else b""
                            error_msg = err_data.decode("utf-8", "ignore") if err_data else "无详细错误信息"
                            logger.error(f"ffmpeg 执行失败 (状态码 {ret})")
                            
                            raise subprocess.CalledProcessError(ret, ffmpeg_cmd, stderr=err_data)
                        break

                    if stop_event and stop_event.is_set():
                        logger.info("检测到停止信号，正在终止 ffmpeg...")
                        ffmpeg_proc.terminate()
                        try:
                            ffmpeg_proc.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            logger.warning("ffmpeg terminate 超时，执行 kill")
                            ffmpeg_proc.kill()
                            ffmpeg_proc.wait(timeout=2)
                        return False

                    time.sleep(0.1)

                if ffmpeg_proc.stderr:
                    ffmpeg_proc.stderr.read()

            finally:
                if ffmpeg_proc and ffmpeg_proc.poll() is None:
                    ffmpeg_proc.kill()

            with open(output_file, "rb") as f:
                final_data = f.read()

            logger.info(f"ffmpeg 导出成功! 最终大小: {len(final_data) / 1024 / 1024:.2f} MB")
            return base64.b64encode(final_data).decode("utf-8")

    except Exception as e:
        logger.error(f"创建 style_animated_1 失败: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False
