import base64
import hashlib
import math
import os
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from app.log import logger
from app.plugins.mediacovergenerator.utils.animation_utils import (
    _clamp, _ease_in_out_sine, _ease_out_back, _lerp, _blend_rgba, _image_signature
)
from app.plugins.mediacovergenerator.style.style_static_2 import (
    add_film_grain,
    align_image_right,
    darken_color,
    find_dominant_vibrant_colors,
)
from app.plugins.mediacovergenerator.utils.color_helper import ColorHelper


def _create_dynamic_diagonal_mask(size, top_x, bottom_x):
    w, h = size
    mask = Image.new("L", size, 255)
    draw = ImageDraw.Draw(mask)
    draw.polygon(
        [
            (top_x, 0),
            (w, 0),
            (w, h),
            (bottom_x, h),
        ],
        fill=0,
    )
    return mask


def _create_dynamic_shadow_mask(size, top_x, bottom_x, feather_size=12):
    w, h = size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    edge_w = max(2, feather_size // 2)
    draw.polygon(
        [
            (top_x - 2, 0),
            (top_x - 2 + edge_w, 0),
            (bottom_x - 2 + edge_w, h),
            (bottom_x - 2, h),
        ],
        fill=255,
    )
    return mask.filter(ImageFilter.GaussianBlur(radius=max(2, feather_size // 2)))


def _animate_zoom(base_img, phase, duration_seconds, amp=0.018):
    duration_seconds = max(1.0, float(duration_seconds))
    duration_scale = _clamp(duration_seconds / 8.0, 0.5, 1.0)
    effective_amp = _clamp(amp * duration_scale, 0.006, 0.03)

    theta = 2.0 * math.pi * _clamp(phase, 0.0, 1.0)
    z = 0.5 - 0.5 * math.cos(theta)  # 0 -> 1 -> 0
    zoom = 1.0 + effective_amp * z

    w, h = base_img.size
    sw = max(w + 2, int(round(w * zoom)))
    sh = max(h + 2, int(round(h * zoom)))
    scaled = base_img.resize((sw, sh), Image.Resampling.BICUBIC)
    left = (sw - w) // 2
    top = (sh - h) // 2
    return scaled.crop((left, top, left + w, top + h))


def _build_text_layer(canvas_size, title, font_path, font_size, font_offset, bg_color):
    width, height = canvas_size
    title_zh, title_en = title
    zh_font_path, en_font_path = font_path
    zh_font_size, en_font_size = float(font_size[0]), float(font_size[1])
    zh_font_offset, title_spacing, _ = font_offset

    # 小分辨率动图按比例放大字体，避免文字过小
    scale = height / 1080.0
    zh_font = ImageFont.truetype(zh_font_path, max(1, int(zh_font_size * scale)))
    en_font = ImageFont.truetype(en_font_path, max(1, int(en_font_size * scale)))

    text_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    shadow_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    sdraw = ImageDraw.Draw(shadow_layer)

    left_center_x = int(width * 0.25)
    left_center_y = int(height * 0.5)

    text_color = (255, 255, 255, 232)
    shadow_color = darken_color(bg_color, 0.8) + (78,)

    zh_bbox = draw.textbbox((0, 0), title_zh, font=zh_font)
    zh_w = zh_bbox[2] - zh_bbox[0]
    zh_h = zh_bbox[3] - zh_bbox[1]

    en_lines = []
    en_line_spacing = max(1, int(en_font.size * 0.12))
    en_height = 0
    if title_en:
        en_bbox = draw.textbbox((0, 0), title_en, font=en_font)
        en_full_w = en_bbox[2] - en_bbox[0]
        if en_full_w > zh_w and " " in title_en:
            words = title_en.split(" ")
            current_line = words[0]
            for word in words[1:]:
                test_line = current_line + " " + word
                test_bbox = draw.textbbox((0, 0), test_line, font=en_font)
                test_w = test_bbox[2] - test_bbox[0]
                if test_w > zh_w:
                    en_lines.append(current_line)
                    current_line = word
                else:
                    current_line = test_line
            if current_line:
                en_lines.append(current_line)
        else:
            en_lines = [title_en]

        for i, line in enumerate(en_lines):
            line_bbox = draw.textbbox((0, 0), line, font=en_font)
            line_h = line_bbox[3] - line_bbox[1]
            en_height += line_h
            if i < len(en_lines) - 1:
                en_height += en_line_spacing

    total_h = zh_h + (float(title_spacing) * scale if en_lines else 0) + en_height
    y0 = left_center_y - int(total_h // 2)

    zh_x = left_center_x - zh_w // 2
    zh_y = y0 + int(float(zh_font_offset) * scale)

    for off in range(3, 11, 2):
        sdraw.text((zh_x + off, zh_y + off), title_zh, font=zh_font, fill=shadow_color)
    draw.text((zh_x, zh_y), title_zh, font=zh_font, fill=text_color)

    if en_lines:
        ey = zh_y + zh_h + int(float(title_spacing) * scale)
        for line in en_lines:
            eb = draw.textbbox((0, 0), line, font=en_font)
            ew = eb[2] - eb[0]
            eh = eb[3] - eb[1]
            ex = left_center_x - ew // 2
            for off in range(2, 8, 2):
                sdraw.text((ex + off, ey + off), line, font=en_font, fill=shadow_color)
            draw.text((ex, ey), line, font=en_font, fill=text_color)
            ey += eh + en_line_spacing

    return Image.alpha_composite(shadow_layer.filter(ImageFilter.GaussianBlur(radius=8)), text_layer)


def create_style_animated_2(
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
    animation_duration=10,
    animation_fps=15,
    animation_format="apng",
    animation_resolution="320x180",
    animation_reduce_colors="strong",
    image_count=9,
    stop_event=None,
):
    try:
        try:
            target_w, target_h = map(int, animation_resolution.split("x"))
        except Exception:
            target_w, target_h = 320, 180

        split_top = 0.55
        split_bottom = 0.40
        split_top_start = int(target_w * split_top)
        split_bottom_start = int(target_w * split_bottom)
        split_full_cover = int(target_w * 1.22)
        static_mask = _create_dynamic_diagonal_mask((target_w, target_h), split_top_start, split_bottom_start)
        static_shadow_mask = _create_dynamic_shadow_mask(
            (target_w, target_h),
            split_top_start,
            split_bottom_start,
            feather_size=max(8, int(target_h * 0.08)),
        )

        folder = Path(library_dir)
        formats = (".jpg", ".jpeg", ".png", ".webp", ".bmp")
        all_posters = sorted(
            [str(folder / f) for f in os.listdir(folder) if f.lower().endswith(formats)],
            key=lambda p: os.path.getmtime(p),
            reverse=True,
        )
        if not all_posters:
            logger.warning("style_animated_3 未找到素材图片")
            return False

        unique = []
        seen = set()
        for p in all_posters:
            sig = _image_signature(p)
            if sig in seen:
                continue
            seen.add(sig)
            unique.append(p)

        poster_paths = unique if unique else all_posters
        image_count = int(_clamp(int(image_count), 2, 12))
        if len(poster_paths) > image_count:
            poster_paths = poster_paths[:image_count]
        if len(poster_paths) < 2:
            poster_paths = all_posters[:2] if len(all_posters) >= 2 else all_posters * 2

        prepared_right = []
        prepared_left_bg = []
        prepared_text = []

        for p in poster_paths:
            src = Image.open(p).convert("RGB")
            right_img = align_image_right(src, (target_w, target_h)).convert("RGBA")
            prepared_right.append(right_img)

            if bg_color_config:
                bg_color = ColorHelper.get_background_color(
                    src,
                    color_mode=bg_color_config.get('mode', 'auto'),
                    custom_color=bg_color_config.get('custom_color'),
                    config_color=bg_color_config.get('config_color')
                )
            else:
                colors = find_dominant_vibrant_colors(src, num_colors=5)
                bg_color = colors[0] if colors else (120, 120, 120)
            bg_img = ImageOps.fit(src, (target_w, target_h), method=Image.Resampling.BICUBIC)
            bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=max(1, int(blur_size * target_h / 1080.0))))
            bg_mix = Image.blend(bg_img, Image.new("RGB", (target_w, target_h), darken_color(bg_color, 0.85)), float(_clamp(float(color_ratio), 0.0, 1.0)))
            bg_mix = add_film_grain(bg_mix, intensity=0.03)
            prepared_left_bg.append(bg_mix.convert("RGBA"))

            prepared_text.append(_build_text_layer((target_w, target_h), title, font_path, font_size, font_offset, bg_color))


        safe_fps = max(1, int(animation_fps))
        safe_duration = max(1, int(animation_duration))
        total_frames = max(1, int(round(safe_fps * safe_duration)))

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            n_imgs = len(prepared_right)
            logger.info(f"开始生成帧，共 {total_frames} 帧，素材数 {n_imgs}")
            for f in range(total_frames):
                if stop_event and stop_event.is_set():
                    return False
                if f % 10 == 0:
                    logger.info(f"正在生成第 {f}/{total_frames} 帧...")

                phase = f / float(total_frames)
                cycle_pos = phase * n_imgs
                idx = int(cycle_pos) % n_imgs
                nxt = (idx + 1) % n_imgs
                local = cycle_pos - int(cycle_pos)
                # 取消帷幕动画（不再根据 bg_motion_mode 切换）
                # 保留固定斜切布局，仅做新旧画面渐变切换
                panel_mix_t = _ease_in_out_sine(local)
                right_mix_t = panel_mix_t
                dynamic_mask = static_mask
                dynamic_shadow_mask = static_shadow_mask

                right_old = prepared_right[idx]
                right_new = prepared_right[nxt]
                right_anim = _blend_rgba(right_old, right_new, right_mix_t)

                # 背景固定，不做左右位移/缩放动画
                left_old = prepared_left_bg[idx]
                left_new = prepared_left_bg[nxt]
                left_bg_anim = _blend_rgba(left_old, left_new, panel_mix_t)

                # 背景始终用斜切边界在左右层之间做过渡，不会在左侧留下空白
                frame = Image.composite(left_bg_anim, right_anim, dynamic_mask)

                # 动态边缘阴影
                edge_shadow = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
                edge_shadow_layer = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 120))
                edge_shadow.paste(edge_shadow_layer, (0, 0), dynamic_shadow_mask)
                frame = Image.alpha_composite(frame, edge_shadow)

                # 标题固定，不做左右位移动画
                text_mix = _blend_rgba(prepared_text[idx], prepared_text[nxt], panel_mix_t)
                moving_text = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
                moving_text.paste(text_mix, (0, 0), text_mix)
                frame = Image.alpha_composite(frame, moving_text)

                frame_file = tmp_path / f"frame_{f:04d}.bmp"
                frame.convert("RGB").save(frame_file, format="BMP")

            output_ext = ".gif" if animation_format == "gif" else ".png"
            output_file = tmp_path / f"output{output_ext}"

            ffmpeg_common = [
                "ffmpeg", "-hide_banner", "-y",
                "-framerate", str(safe_fps),
                "-i", str(tmp_path / "frame_%04d.bmp"),
                "-threads", "0",
            ]

            reduce_mode = animation_reduce_colors
            if isinstance(reduce_mode, bool):
                reduce_mode = "strong" if reduce_mode else "off"
            if reduce_mode not in ["off", "medium", "strong"]:
                reduce_mode = "strong"

            if animation_format == "gif":
                p_colors = "64" if reduce_mode == "strong" else ("128" if reduce_mode == "medium" else "256")
                p_dither = "none" if reduce_mode == "strong" else ("bayer:bayer_scale=3" if reduce_mode == "medium" else "floyd_steinberg")
                ffmpeg_cmd = ffmpeg_common + [
                    "-filter_complex", f"[0:v] split [a][b]; [a] palettegen=max_colors={p_colors} [p]; [b][p] paletteuse=dither={p_dither}",
                    "-loop", "0", "-f", "gif", str(output_file),
                ]
            else:
                if reduce_mode == "off":
                    ffmpeg_cmd = ffmpeg_common + [
                        "-vcodec", "apng", "-pix_fmt", "rgba", "-plays", "0", "-f", "apng", str(output_file),
                    ]
                else:
                    p_colors = "64" if reduce_mode == "strong" else "128"
                    p_dither = "none" if reduce_mode == "strong" else "bayer:bayer_scale=3"
                    ffmpeg_cmd = ffmpeg_common + [
                        "-filter_complex", f"[0:v] split [a][b]; [a] palettegen=max_colors={p_colors}:reserve_transparent=on [p]; [b][p] paletteuse=dither={p_dither}",
                        "-vcodec", "apng", "-pix_fmt", "rgba", "-plays", "0", "-f", "apng", str(output_file),
                    ]

            proc = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=False)
            while True:
                ret = proc.poll()
                if ret is not None:
                    if ret != 0:
                        err_data = proc.stderr.read() if proc.stderr else b""
                        raise subprocess.CalledProcessError(ret, ffmpeg_cmd, stderr=err_data)
                    break
                if stop_event and stop_event.is_set():
                    proc.terminate()
                    try:
                        proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=2)
                    return False
                time.sleep(0.05)

            with open(output_file, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")

    except Exception as e:
        logger.error(f"创建 style_animated_2 失败: {e}")
        return False
