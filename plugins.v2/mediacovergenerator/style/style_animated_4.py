import base64
import hashlib
import math
import os
import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from app.log import logger
from app.plugins.mediacovergenerator.utils.animation_utils import (
    _clamp, _ease_in_out_sine, _blend_rgba, _image_signature, _wrap_english
)
from app.plugins.mediacovergenerator.style.style_static_2 import (
    darken_color,
    find_dominant_vibrant_colors,
)
from app.plugins.mediacovergenerator.utils.color_helper import ColorHelper


def _prepare_bg(image_path, canvas_size, blur_size, color_ratio, bg_color_config=None):
    src = Image.open(image_path).convert("RGB")
    bg = ImageOps.fit(src, canvas_size, method=Image.Resampling.LANCZOS)

    scaled_blur = int(max(8, float(blur_size) * (canvas_size[1] / 1080.0)))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=scaled_blur))

    if bg_color_config:
        tint = ColorHelper.get_background_color(
            src,
            color_mode=bg_color_config.get('mode', 'auto'),
            custom_color=bg_color_config.get('custom_color'),
            config_color=bg_color_config.get('config_color')
        )
    else:
        dominant = find_dominant_vibrant_colors(src, num_colors=5)
        tint = dominant[0] if dominant else (120, 120, 120)
    tint = darken_color(tint, 0.82)

    ratio = float(color_ratio)
    if ratio < 0 or ratio > 1:
        ratio = 0.8

    bg_np = np.array(bg, dtype=float)
    tint_np = np.array([[tint]], dtype=float)
    mixed = bg_np * (1.0 - ratio) + tint_np * ratio
    mixed = np.clip(mixed, 0, 255).astype(np.uint8)
    return Image.fromarray(mixed).convert("RGBA"), tint


def _build_text_layer(canvas_size, title, font_path, font_size, font_offset, tint):
    zh_font_path, en_font_path = font_path
    title_zh, title_en = title
    zh_font_size, en_font_size = font_size
    zh_font_offset, title_spacing, en_line_spacing = font_offset

    text_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    shadow_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    sdraw = ImageDraw.Draw(shadow_layer)

    zh_font = ImageFont.truetype(zh_font_path, int(max(1, float(zh_font_size))))
    en_font = ImageFont.truetype(en_font_path, int(max(1, float(en_font_size))))

    cx = canvas_size[0] // 2
    cy = canvas_size[1] // 2

    text_color = (255, 255, 255, 230)
    shadow_color = darken_color(tint, 0.65) + (92,)

    zh_bbox = draw.textbbox((0, 0), title_zh, font=zh_font)
    zh_w = zh_bbox[2] - zh_bbox[0]
    zh_h = zh_bbox[3] - zh_bbox[1]

    lines = _wrap_english(draw, title_en, en_font, zh_w)
    line_gap = int(max(1, float(en_line_spacing)))
    en_h = 0
    line_sizes = []
    for i, line in enumerate(lines):
        lb = draw.textbbox((0, 0), line, font=en_font)
        lw = lb[2] - lb[0]
        lh = lb[3] - lb[1]
        line_sizes.append((line, lw, lh))
        en_h += lh + (line_gap if i < len(lines) - 1 else 0)

    spacing = int(float(title_spacing)) if lines else 0
    total_h = zh_h + spacing + en_h
    y0 = cy - total_h // 2 + int(float(zh_font_offset))

    zh_x = cx - zh_w // 2
    zh_y = y0

    for off in range(3, 11, 2):
        sdraw.text((zh_x + off, zh_y + off), title_zh, font=zh_font, fill=shadow_color)
    draw.text((zh_x, zh_y), title_zh, font=zh_font, fill=text_color)

    ey = zh_y + zh_h + spacing
    for line, lw, lh in line_sizes:
        ex = cx - lw // 2
        for off in range(2, 8, 2):
            sdraw.text((ex + off, ey + off), line, font=en_font, fill=shadow_color)
        draw.text((ex, ey), line, font=en_font, fill=text_color)
        ey += lh + line_gap

    return Image.alpha_composite(
        shadow_layer.filter(ImageFilter.GaussianBlur(radius=8)),
        text_layer,
    )


def create_style_animated_4(
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
    image_count=5,
    stop_event=None,
):
    try:
        try:
            target_w, target_h = map(int, animation_resolution.split("x"))
        except Exception:
            target_w, target_h = 320, 180
        canvas_size = (max(1, target_w), max(1, target_h))

        folder = Path(library_dir)
        formats = (".jpg", ".jpeg", ".png", ".webp", ".bmp")
        all_posters = sorted(
            [str(folder / f) for f in os.listdir(folder) if f.lower().endswith(formats)],
            key=lambda p: os.path.getmtime(p),
            reverse=True,
        )
        if not all_posters:
            logger.warning("style_animated_4 未找到素材图片")
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

        zh_font_size, en_font_size = float(font_size[0]), float(font_size[1])
        anim_scale = canvas_size[1] / 1080.0
        scaled_font_size = (zh_font_size * anim_scale, en_font_size * anim_scale)
        zh_font_offset, title_spacing, en_line_spacing = font_offset
        scaled_font_offset = (
            float(zh_font_offset) * anim_scale,
            float(title_spacing) * anim_scale,
            float(en_line_spacing) * anim_scale,
        )

        prepared_bg = []
        prepared_text = []
        for p in poster_paths:
            bg, tint = _prepare_bg(p, canvas_size, blur_size, color_ratio, bg_color_config)
            prepared_bg.append(bg)
            prepared_text.append(_build_text_layer(canvas_size, title, font_path, scaled_font_size, scaled_font_offset, tint))

        safe_fps = max(1, int(animation_fps))
        safe_duration = max(1, int(animation_duration))
        total_frames = max(1, int(round(safe_fps * safe_duration)))

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            n_imgs = len(prepared_bg)

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
                mix_t = _ease_in_out_sine(local)

                frame = _blend_rgba(prepared_bg[idx], prepared_bg[nxt], mix_t)
                text_mix = _blend_rgba(prepared_text[idx], prepared_text[nxt], mix_t)
                frame = Image.alpha_composite(frame, text_mix)

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
        logger.error(f"创建 style_animated_4 失败: {e}")
        return False
