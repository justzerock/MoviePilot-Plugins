from __future__ import annotations

import base64
import colorsys
import io
import math
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps


RESOLUTIONS = {
    "1080p": (1920, 1080),
    "720p": (1280, 720),
    "480p": (854, 480),
    "360p": (640, 360),
    "4k": (3840, 2160),
}


class CoverRenderer:
    def __init__(self, fonts_dir: Path):
        self.fonts_dir = fonts_dir
        self.data_dir = fonts_dir.parent

    def render(
        self,
        image_paths: list[Path],
        title: str,
        subtitle: str = "",
        style: str = "single_1",
        style_config: dict[str, Any] | None = None,
        output_path: Path | None = None,
    ) -> Path:
        config = style_config or {}
        animated = str(style or "").startswith("animated_")
        size = self._resolution(config.get("animation_resolution" if animated else "resolution", "320x180" if animated else "1080p"))
        output_format = str(config.get("output_format") or "jpg").lower()
        if animated:
            output_format = str(config.get("animation_format") or "apng").lower()
            if output_format not in {"apng", "gif"}:
                output_format = "apng"
        output_path = output_path or Path("/app/data/output/cover.jpg")
        if animated:
            expected_suffix = ".gif" if output_format == "gif" else ".png"
            if output_path.suffix.lower() not in (".gif", ".png"):
                output_path = output_path.with_suffix(expected_suffix)
        elif output_path.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            output_path = output_path.with_suffix(".png" if output_format == "png" else ".jpg")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        images = [self._open(path) for path in image_paths if path and path.exists()]
        if not images:
            raise ValueError("No source images available")

        try:
            if animated:
                self._save_animated(images, title, subtitle, style, size, config, output_path, output_format)
            else:
                canvas = self._render_static_canvas(images, title, subtitle, style, size, config)
                save_format = "PNG" if output_path.suffix.lower() == ".png" else "JPEG"
                if save_format == "JPEG":
                    canvas = canvas.convert("RGB")
                    canvas.save(output_path, save_format, quality=92, optimize=True)
                else:
                    canvas.save(output_path, save_format, optimize=True)
        finally:
            for image in images:
                image.close()
        return output_path

    def _render_static_canvas(
        self,
        images: list[Image.Image],
        title: str,
        subtitle: str,
        style: str,
        size: tuple[int, int],
        config: dict[str, Any],
    ) -> Image.Image:
        if style == "custom_static":
            return self._custom_static(images, title, subtitle, size, config)
        if style in {"single_2", "static_2"}:
            return self._single_2(images[0], title, subtitle, size, config)
        if style in {"multi_1", "static_3"}:
            return self._multi_1(images, title, subtitle, size, config)
        if style == "static_4":
            return self._static_4(images[0], title, subtitle, size, config)
        return self._single_1(images[0], title, subtitle, size, config)

    def _animated_static_style(self, style: str) -> str:
        return {
            "animated_1": "single_1",
            "animated_2": "single_2",
            "animated_3": "multi_1",
            "animated_4": "static_4",
        }.get(style, "single_1")

    def _save_animated(
        self,
        images: list[Image.Image],
        title: str,
        subtitle: str,
        style: str,
        size: tuple[int, int],
        config: dict[str, Any],
        output_path: Path,
        output_format: str,
    ) -> None:
        fps = max(1, min(60, int(float(config.get("animation_fps") or 12))))
        duration_s = max(1, min(60, int(float(config.get("animation_duration") or 8))))
        total_frames = max(2, min(3600, fps * duration_s))
        frame_duration_ms = max(20, int(round(duration_s * 1000 / total_frames)))
        frames = [
            self._animated_frame(images, title, subtitle, style, size, config, index, total_frames)
            for index in range(total_frames)
        ]
        if output_format == "gif":
            palette_frames = [frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=192) for frame in frames]
            palette_frames[0].save(
                output_path,
                "GIF",
                save_all=True,
                append_images=palette_frames[1:],
                duration=frame_duration_ms,
                loop=0,
                optimize=True,
                disposal=2,
            )
            return
        frames[0].save(
            output_path,
            "PNG",
            save_all=True,
            append_images=frames[1:],
            duration=frame_duration_ms,
            loop=0,
            optimize=True,
        )

    def _animated_frame(
        self,
        images: list[Image.Image],
        title: str,
        subtitle: str,
        style: str,
        size: tuple[int, int],
        config: dict[str, Any],
        index: int,
        total_frames: int,
    ) -> Image.Image:
        phase = index / max(1, total_frames)
        image_count = len(images)
        source_index = int(math.floor(phase * image_count)) % image_count
        next_index = (source_index + 1) % image_count
        local_t = (phase * image_count) % 1
        static_style = self._animated_static_style(style)
        if style == "animated_3":
            offset = int(round(phase * image_count)) % image_count
            shifted = images[offset:] + images[:offset]
            return self._render_static_canvas(shifted, title, subtitle, static_style, size, config).convert("RGBA")
        first = self._render_static_canvas([images[source_index], *images], title, subtitle, static_style, size, config).convert("RGBA")
        second = self._render_static_canvas([images[next_index], *images], title, subtitle, static_style, size, config).convert("RGBA")
        if style == "animated_2":
            t = 0.5 - 0.5 * math.cos(local_t * math.pi)
        elif style == "animated_4":
            t = (math.sin(phase * math.tau) + 1) / 2
        else:
            t = local_t
        return Image.blend(first, second, max(0, min(1, t)))

    def _resolution(self, value: Any) -> tuple[int, int]:
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return int(value[0]), int(value[1])
        if isinstance(value, str) and "x" in value:
            parts = value.lower().split("x", 1)
            return int(parts[0]), int(parts[1])
        return RESOLUTIONS.get(str(value), RESOLUTIONS["1080p"])

    def _open(self, path: Path) -> Image.Image:
        return Image.open(path).convert("RGBA")

    def _open_external_image(self, value: Any) -> Image.Image | None:
        raw = str(value or "").strip()
        if not raw:
            return None
        try:
            if raw.startswith("data:image/") and "," in raw:
                payload = raw.split(",", 1)[1]
                return Image.open(io.BytesIO(base64.b64decode(payload))).convert("RGBA")
            if raw.startswith("/data/"):
                raw = str(self.data_dir / unquote(raw[len("/data/"):]))
            path = Path(raw)
            if not path.is_absolute():
                path = self.data_dir / raw
            try:
                path = path.resolve()
                path.relative_to(self.data_dir.resolve())
            except Exception:
                return None
            if path.exists() and path.is_file():
                return Image.open(path).convert("RGBA")
        except Exception:
            return None
        return None

    def _font(self, size: int, preferred: str = "") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        candidates: list[Path] = []
        if preferred:
            preferred_path = Path(preferred)
            candidates.append(preferred_path if preferred_path.is_absolute() else self.fonts_dir / preferred)
        candidates.extend(sorted(self.fonts_dir.glob("*.*")))
        candidates.extend([
            Path("/System/Library/Fonts/PingFang.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ])
        for candidate in candidates:
            try:
                if candidate.exists():
                    return ImageFont.truetype(str(candidate), size)
            except Exception:
                continue
        return ImageFont.load_default()

    def _fit_cover(self, image: Image.Image, size: tuple[int, int], focus=(0.5, 0.5)) -> Image.Image:
        width, height = size
        scale = max(width / image.width, height / image.height)
        resized = image.resize((math.ceil(image.width * scale), math.ceil(image.height * scale)), Image.Resampling.LANCZOS)
        left = int((resized.width - width) * max(0, min(1, focus[0])))
        top = int((resized.height - height) * max(0, min(1, focus[1])))
        return resized.crop((left, top, left + width, top + height))

    def _fit_image(self, image: Image.Image, size: tuple[int, int], fit: str = "cover", focus=(0.5, 0.5)) -> Image.Image:
        width, height = size
        if width <= 0 or height <= 0:
            return Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        if fit == "stretch":
            return image.resize(size, Image.Resampling.LANCZOS)
        scale = min(width / image.width, height / image.height) if fit == "contain" else max(width / image.width, height / image.height)
        resized = image.resize((max(1, math.ceil(image.width * scale)), max(1, math.ceil(image.height * scale))), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        overflow_x = max(0, resized.width - width)
        overflow_y = max(0, resized.height - height)
        inset_x = max(0, width - resized.width) // 2
        inset_y = max(0, height - resized.height) // 2
        left = int(overflow_x * max(0, min(1, focus[0])))
        top = int(overflow_y * max(0, min(1, focus[1])))
        crop = resized.crop((left, top, left + min(width, resized.width), top + min(height, resized.height)))
        canvas.alpha_composite(crop, (inset_x, inset_y))
        return canvas

    def _rounded(self, image: Image.Image, radius: int) -> Image.Image:
        image = image.convert("RGBA")
        mask = Image.new("L", image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, image.width, image.height), radius=radius, fill=255)
        out = image.copy()
        out.putalpha(ImageChops.multiply(image.getchannel("A"), mask))
        return out

    def _apply_polygon_mask(self, image: Image.Image, mask_polygon: Any) -> Image.Image:
        if not isinstance(mask_polygon, dict) or not isinstance(mask_polygon.get("points"), list):
            return image
        units = str(mask_polygon.get("units") or "relative")
        points = []
        for point in mask_polygon.get("points") or []:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue
            try:
                px, py = float(point[0]), float(point[1])
            except Exception:
                continue
            if units == "relative":
                points.append((px * image.width, py * image.height))
            else:
                points.append((px, py))
        if len(points) < 3:
            return image
        mask = Image.new("L", image.size, 0)
        ImageDraw.Draw(mask).polygon(points, fill=255)
        alpha = image.getchannel("A")
        image = image.copy()
        image.putalpha(ImageChops.multiply(alpha, mask))
        return image

    def _shadow(self, size: tuple[int, int], radius: int, blur: int, opacity: int = 130) -> Image.Image:
        shadow = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(shadow)
        draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=(0, 0, 0, opacity))
        return shadow.filter(ImageFilter.GaussianBlur(blur))

    def _background(self, image: Image.Image, size: tuple[int, int], config: dict[str, Any]) -> Image.Image:
        color = self._hex_to_rgb(str(config.get("background_color") or "#6f8090"))
        ratio = float(config.get("color_ratio", 0.78))
        blur = int(config.get("blur", 42))
        bg = self._fit_cover(image, size).filter(ImageFilter.GaussianBlur(max(1, blur))).convert("RGBA")
        tint = Image.new("RGBA", size, (*color, 255))
        return Image.blend(bg, tint, max(0, min(1, ratio)))

    def _rgb_to_hex(self, rgb: tuple[int, int, int]) -> str:
        return f"#{max(0, min(255, int(rgb[0]))):02x}{max(0, min(255, int(rgb[1]))):02x}{max(0, min(255, int(rgb[2]))):02x}"

    def _extract_auto_color(self, image: Image.Image | None, fallback: str = "#6f8090") -> str:
        if image is None:
            return fallback
        try:
            sample = image.convert("RGBA").resize((48, 48), Image.Resampling.BILINEAR)
            total_r = total_g = total_b = total_weight = 0.0
            for r, g, b, alpha in sample.getdata():
                if alpha < 160:
                    continue
                lightness = (max(r, g, b) + min(r, g, b)) / 510
                if lightness < 0.16 or lightness > 0.88:
                    continue
                saturation = 0 if max(r, g, b) == 0 else (max(r, g, b) - min(r, g, b)) / max(r, g, b)
                weight = 0.55 + min(0.45, saturation)
                total_r += r * weight
                total_g += g * weight
                total_b += b * weight
                total_weight += weight
            if not total_weight:
                return fallback
            return self._adjust_hex_color(
                self._rgb_to_hex((int(total_r / total_weight), int(total_g / total_weight), int(total_b / total_weight))),
                -0.06,
            )
        except Exception:
            return fallback

    def _adjust_hex_color(self, hex_color: str, lightness_offset: float) -> str:
        r, g, b = self._hex_to_rgb(hex_color)
        h, lightness, saturation = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        next_lightness = max(0.18, min(0.84, lightness + lightness_offset))
        next_saturation = max(0.24, min(0.72, saturation))
        nr, ng, nb = colorsys.hls_to_rgb(h, next_lightness, next_saturation)
        return f"#{int(round(nr * 255)):02x}{int(round(ng * 255)):02x}{int(round(nb * 255)):02x}"

    def _resolve_layout_color(self, color_source: Any, custom_color: Any, config: dict[str, Any], fallback: str, allow_none: bool = False) -> tuple[int, int, int] | None:
        source = str(color_source or "custom")
        if source == "none" and allow_none:
            return None
        if source == "config":
            return self._hex_to_rgb(str(config.get("background_color") or config.get("config_color") or fallback))
        if source == "auto":
            return self._hex_to_rgb(str(config.get("auto_color") or fallback))
        return self._hex_to_rgb(str(custom_color or fallback))

    def _layout_background(self, images: list[Image.Image], size: tuple[int, int], layout: dict[str, Any], config: dict[str, Any]) -> Image.Image:
        background = layout.get("background") if isinstance(layout.get("background"), dict) else {}
        bg_type = str(background.get("type") or "blurred-image-color")
        opacity = max(0, min(1, float(background.get("opacity", 1) if background.get("opacity") is not None else 1)))
        if bg_type == "transparent":
            return Image.new("RGBA", size, (0, 0, 0, 0))
        color = self._resolve_layout_color(background.get("colorSource") or "auto", background.get("color"), config, "#6f8090") or (111, 128, 144)
        if bg_type == "solid":
            canvas = Image.new("RGBA", size, (*color, int(255 * opacity)))
            return self._apply_polygon_mask(canvas, background.get("maskPolygon"))
        if bg_type == "gradient":
            color2 = self._hex_to_rgb(str(background.get("color2") or "#0a1628"))
            canvas = Image.new("RGBA", size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(canvas)
            for y in range(size[1]):
                t = y / max(1, size[1] - 1)
                rgb = tuple(int(color[index] * (1 - t) + color2[index] * t) for index in range(3))
                draw.line((0, y, size[0], y), fill=(*rgb, int(255 * opacity)))
            return self._apply_polygon_mask(canvas, background.get("maskPolygon"))
        slot = 1
        try:
            source = background.get("imageSource") or {}
            slot = max(1, int(source.get("slot") or 1))
        except Exception:
            slot = 1
        image = images[(slot - 1) % len(images)] if images else Image.new("RGBA", size, (*color, 255))
        blur = int(background.get("blur", config.get("blur", 42)) or 0)
        ratio = float(background.get("colorRatio", config.get("color_ratio", 0.78)) or 0.78)
        bg = self._fit_cover(image, size).filter(ImageFilter.GaussianBlur(max(0, blur))).convert("RGBA")
        tint = Image.new("RGBA", size, (*color, 255))
        blended = Image.blend(bg, tint, max(0, min(1, ratio)))
        if opacity < 1:
            blended.putalpha(int(255 * opacity))
        return self._apply_polygon_mask(blended, background.get("maskPolygon"))

    def _draw_text(self, canvas: Image.Image, title: str, subtitle: str, box: tuple[int, int, int, int], config: dict[str, Any], align="center") -> None:
        draw = ImageDraw.Draw(canvas)
        scale = canvas.height / 1080
        main_font = self._font(int(config.get("main_font_size", 170) * scale), str(config.get("font") or ""))
        sub_font = self._font(int(config.get("subtitle_font_size", 76) * scale), str(config.get("font") or ""))
        x, y, w, _ = box
        shadow = (0, 0, 0, 90)
        fill = (255, 255, 255, 245)
        self._text_line(draw, title, main_font, (x, y), w, fill, shadow, align)
        if subtitle:
            self._text_line(draw, subtitle, sub_font, (x, y + int(190 * scale)), w, fill, shadow, align)

    def _draw_layout_text(self, size: tuple[int, int], text: str, layer: dict[str, Any], config: dict[str, Any], padding: int = 0) -> Image.Image:
        width, height = size
        padding = max(0, int(padding or 0))
        tile_size = (width + padding * 2, height + padding * 2)
        tile = Image.new("RGBA", tile_size, (0, 0, 0, 0))
        if not text:
            return tile
        font_size = max(1, int(float(layer.get("fontSize") or 72)))
        font = self._font(font_size, self._font_preference(layer, config))
        color = self._resolve_layout_color(layer.get("colorSource") or "custom", layer.get("color"), config, "#ffffff") or (255, 255, 255)
        shadow_blur = max(0, int(float(layer.get("shadowBlur") or layer.get("effects", {}).get("shadow", {}).get("blur") or 0)))
        shadow_x = int(float(layer.get("shadowOffsetX") or layer.get("effects", {}).get("shadow", {}).get("offsetX") or 0))
        shadow_y = int(float(layer.get("shadowOffsetY") or layer.get("effects", {}).get("shadow", {}).get("offsetY") or 0))
        shadow_opacity = max(0, min(1, float(layer.get("shadowOpacity", layer.get("effects", {}).get("shadow", {}).get("opacity", 0.24)) or 0)))
        align = str(layer.get("textAlign") or layer.get("textStyle", {}).get("textAlign") or "center")
        lines = self._wrap_text(text, font, max(1, width))
        line_height = max(1, int(font_size * 1.12))
        probe_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        bboxes = [probe_draw.textbbox((0, 0), line, font=font) for line in lines]
        visual_height = max((bbox[3] - bbox[1] for bbox in bboxes), default=line_height)
        total_height = max(visual_height, visual_height + max(0, len(lines) - 1) * line_height)
        start_y = max(0, (height - total_height) // 2)
        text_layer = Image.new("RGBA", tile_size, (0, 0, 0, 0))
        shadow_layer = Image.new("RGBA", tile_size, (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_layer)
        shadow_draw = ImageDraw.Draw(shadow_layer)
        for index, line in enumerate(lines):
            bbox = bboxes[index]
            text_width = bbox[2] - bbox[0]
            if align == "left":
                x = 0
            elif align == "right":
                x = max(0, width - text_width)
            else:
                x = max(0, (width - text_width) // 2)
            y = start_y + index * line_height
            draw_x = padding + x - bbox[0]
            draw_y = padding + y - bbox[1]
            if shadow_opacity:
                shadow_draw.text((draw_x + shadow_x, draw_y + shadow_y), line, font=font, fill=(0, 0, 0, int(255 * shadow_opacity)))
            text_draw.text((draw_x, draw_y), line, font=font, fill=(*color, 255))
        if shadow_blur:
            shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))
        blur = max(0, int(float(layer.get("blur") or layer.get("effects", {}).get("blur") or 0)))
        if blur:
            text_layer = text_layer.filter(ImageFilter.GaussianBlur(blur))
        return Image.alpha_composite(shadow_layer, text_layer)

    def _draw_layout_text_mask_tile(self, size: tuple[int, int], text: str, layer: dict[str, Any], config: dict[str, Any]) -> Image.Image:
        width, height = size
        tile = Image.new("L", size, 0)
        if not text:
            return tile
        font_size = max(1, int(float(layer.get("fontSize") or 72)))
        font = self._font(font_size, self._font_preference(layer, config))
        align = str(layer.get("textAlign") or layer.get("textStyle", {}).get("textAlign") or "center")
        lines = self._wrap_text(text, font, max(1, width))
        line_height = max(1, int(font_size * 1.12))
        probe_draw = ImageDraw.Draw(Image.new("L", (1, 1)))
        bboxes = [probe_draw.textbbox((0, 0), line, font=font) for line in lines]
        visual_height = max((bbox[3] - bbox[1] for bbox in bboxes), default=line_height)
        total_height = max(visual_height, visual_height + max(0, len(lines) - 1) * line_height)
        start_y = max(0, (height - total_height) // 2)
        draw = ImageDraw.Draw(tile)
        for index, line in enumerate(lines):
            bbox = bboxes[index]
            text_width = bbox[2] - bbox[0]
            if align == "left":
                x = 0
            elif align == "right":
                x = max(0, width - text_width)
            else:
                x = max(0, (width - text_width) // 2)
            draw.text((x - bbox[0], start_y + index * line_height - bbox[1]), line, font=font, fill=255)
        return tile

    def _text_line(self, draw: ImageDraw.ImageDraw, text: str, font, pos: tuple[int, int], width: int, fill, shadow, align: str) -> None:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = pos[0]
        if align == "center":
            x = pos[0] + max(0, (width - text_width) // 2)
        elif align == "right":
            x = pos[0] + max(0, width - text_width)
        y = pos[1]
        draw.text((x + 5, y + 6), text, font=font, fill=shadow)
        draw.text((x, y), text, font=font, fill=fill)

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont, width: int) -> list[str]:
        draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        paragraphs = str(text or "").splitlines() or [str(text or "")]
        lines: list[str] = []
        for paragraph in paragraphs:
            current = ""
            tokens = paragraph.split(" ") if " " in paragraph else list(paragraph)
            separator = " " if " " in paragraph else ""
            for token in tokens:
                candidate = token if not current else f"{current}{separator}{token}"
                bbox = draw.textbbox((0, 0), candidate, font=font)
                if bbox[2] - bbox[0] <= width or not current:
                    current = candidate
                else:
                    lines.append(current)
                    current = token
            if current:
                lines.append(current)
        return lines or [""]

    def _font_preference(self, layer: dict[str, Any], config: dict[str, Any]) -> str:
        family = str(layer.get("fontFamily") or layer.get("textStyle", {}).get("fontFamily") or "")
        font_paths = config.get("font_paths") if isinstance(config.get("font_paths"), dict) else {}
        if family in font_paths:
            return str(font_paths[family])
        normalized_family = "".join(ch for ch in family.lower() if ch.isalnum())
        if normalized_family in font_paths:
            return str(font_paths[normalized_family])
        if family in {"", "main_title"}:
            return str(font_paths.get("main_title") or config.get("font") or "")
        if family == "subtitle":
            return str(font_paths.get("subtitle") or font_paths.get("main_title") or config.get("font") or "")
        if family == "custom_text":
            return str(font_paths.get("custom_text") or font_paths.get("subtitle") or font_paths.get("main_title") or config.get("font") or "")
        return str(font_paths.get("custom_text") or family or config.get("font") or "")

    def _layer_geometry(self, layer: dict[str, Any]) -> tuple[int, int, int, int]:
        frame = layer.get("frame") if isinstance(layer.get("frame"), dict) else {}
        return (
            int(float(layer.get("x", frame.get("x", 0)) or 0)),
            int(float(layer.get("y", frame.get("y", 0)) or 0)),
            max(1, int(float(layer.get("width", frame.get("width", 1)) or 1))),
            max(1, int(float(layer.get("height", frame.get("height", 1)) or 1))),
        )

    def _layer_rotation(self, layer: dict[str, Any]) -> float:
        transform = layer.get("transform") if isinstance(layer.get("transform"), dict) else {}
        try:
            return float(layer.get("rotation", transform.get("rotation", 0)) or 0)
        except Exception:
            return 0.0

    def _layer_pivot(self, layer: dict[str, Any]) -> tuple[float, float]:
        transform = layer.get("transform") if isinstance(layer.get("transform"), dict) else {}
        try:
            pivot_x = float(layer.get("pivotX", transform.get("pivotX", 0.5)) if layer.get("pivotX", transform.get("pivotX", None)) is not None else 0.5)
            pivot_y = float(layer.get("pivotY", transform.get("pivotY", 0.5)) if layer.get("pivotY", transform.get("pivotY", None)) is not None else 0.5)
        except Exception:
            return 0.5, 0.5
        return max(0, min(1, pivot_x)), max(0, min(1, pivot_y))

    def _rotate_tile_around_pivot(self, tile: Image.Image, rotation: float, pivot_x: float, pivot_y: float) -> tuple[Image.Image, tuple[int, int]]:
        if not rotation:
            return tile, (0, 0)
        pivot_px = tile.width * pivot_x
        pivot_py = tile.height * pivot_y
        corners = (
            (0.0, 0.0),
            (float(tile.width), 0.0),
            (0.0, float(tile.height)),
            (float(tile.width), float(tile.height)),
        )
        pivot_radius = max(math.hypot(corner_x - pivot_px, corner_y - pivot_py) for corner_x, corner_y in corners)
        half_size = int(math.ceil(pivot_radius + 4))
        work_size = max(2, half_size * 2)
        center = work_size / 2
        work_canvas = Image.new("RGBA", (work_size, work_size), (0, 0, 0, 0))
        work_canvas.alpha_composite(tile, (int(round(center - pivot_px)), int(round(center - pivot_py))))
        rotated = work_canvas.rotate(-rotation, resample=Image.Resampling.BICUBIC, expand=False, center=(center, center))
        return rotated, (int(round(pivot_px - center)), int(round(pivot_py - center)))

    def _paste_layout_tile(self, canvas: Image.Image, tile: Image.Image, layer: dict[str, Any], x: int, y: int) -> None:
        opacity = max(0, min(1, float(layer.get("opacity", layer.get("transform", {}).get("opacity", 1)) or 1)))
        if opacity < 1:
            alpha = tile.getchannel("A").point(lambda value: int(value * opacity))
            tile = tile.copy()
            tile.putalpha(alpha)
        rotation = self._layer_rotation(layer)
        paste_x, paste_y = x, y
        if rotation:
            pivot_x, pivot_y = self._layer_pivot(layer)
            tile, offset = self._rotate_tile_around_pivot(tile, rotation, pivot_x, pivot_y)
            paste_x = int(round(x + offset[0]))
            paste_y = int(round(y + offset[1]))
        layer_type = str(layer.get("type") or "")
        text_types = {"main_title", "subtitle", "title_zh", "title_en", "text"}
        shadow_blur = 0 if layer_type in text_types else max(0, int(float(layer.get("shadowBlur") or layer.get("effects", {}).get("shadow", {}).get("blur") or 0)))
        shadow_opacity = 0 if layer_type in text_types else max(0, min(1, float(layer.get("shadowOpacity", layer.get("effects", {}).get("shadow", {}).get("opacity", 0)) or 0)))
        if shadow_blur and shadow_opacity:
            offset_x = int(float(layer.get("shadowOffsetX") or layer.get("effects", {}).get("shadow", {}).get("offsetX") or 0))
            offset_y = int(float(layer.get("shadowOffsetY") or layer.get("effects", {}).get("shadow", {}).get("offsetY") or 0))
            pad = max(8, shadow_blur * 3, abs(offset_x) + shadow_blur * 2, abs(offset_y) + shadow_blur * 2)
            shadow = Image.new("RGBA", (tile.width + pad * 2, tile.height + pad * 2), (0, 0, 0, 0))
            shadow_alpha = tile.getchannel("A").point(lambda value: int(value * shadow_opacity))
            shadow_alpha_expanded = Image.new("L", shadow.size, 0)
            shadow_alpha_expanded.paste(shadow_alpha, (pad, pad))
            shadow.putalpha(shadow_alpha_expanded)
            shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))
            self._alpha_composite_clipped(canvas, shadow, (paste_x + offset_x - pad, paste_y + offset_y - pad))
        self._alpha_composite_clipped(canvas, tile, (paste_x, paste_y))

    def _alpha_composite_clipped(self, base: Image.Image, overlay: Image.Image, dest: tuple[int, int]) -> None:
        dest_x, dest_y = int(dest[0]), int(dest[1])
        left = max(0, dest_x)
        top = max(0, dest_y)
        right = min(base.width, dest_x + overlay.width)
        bottom = min(base.height, dest_y + overlay.height)
        if right <= left or bottom <= top:
            return
        crop = overlay.crop((left - dest_x, top - dest_y, right - dest_x, bottom - dest_y))
        base.alpha_composite(crop, (left, top))

    def _paste_group_canvas(self, base: Image.Image, group_canvas: Image.Image, layer: dict[str, Any]) -> None:
        rotation = self._layer_rotation(layer)
        paste_at = (0, 0)
        if rotation:
            x, y, width, height = self._layer_geometry(layer)
            try:
                pivot_x = max(0, min(1, float(layer.get("pivotX", 0.5) if layer.get("pivotX") is not None else 0.5)))
                pivot_y = max(0, min(1, float(layer.get("pivotY", 0.5) if layer.get("pivotY") is not None else 0.5)))
            except Exception:
                pivot_x, pivot_y = 0.5, 0.5
            pivot_abs = (x + width * pivot_x, y + height * pivot_y)
            bbox = group_canvas.getbbox()
            if not bbox:
                return
            group_crop = group_canvas.crop(bbox)
            pivot_in_crop = (pivot_abs[0] - bbox[0], pivot_abs[1] - bbox[1])
            corners = (
                (0.0, 0.0),
                (float(group_crop.width), 0.0),
                (0.0, float(group_crop.height)),
                (float(group_crop.width), float(group_crop.height)),
            )
            pivot_radius = max(
                math.hypot(corner_x - pivot_in_crop[0], corner_y - pivot_in_crop[1])
                for corner_x, corner_y in corners
            )
            half_size = int(math.ceil(pivot_radius + 4))
            work_size = max(2, half_size * 2)
            center = work_size / 2
            work_canvas = Image.new("RGBA", (work_size, work_size), (0, 0, 0, 0))
            work_canvas.alpha_composite(group_crop, (int(round(center - pivot_in_crop[0])), int(round(center - pivot_in_crop[1]))))
            group_canvas = work_canvas.rotate(-rotation, resample=Image.Resampling.BICUBIC, expand=False, center=(center, center))
            paste_at = (int(round(pivot_abs[0] - center)), int(round(pivot_abs[1] - center)))
        opacity = max(0, min(1, float(layer.get("opacity", layer.get("transform", {}).get("opacity", 1)) or 1)))
        if opacity < 1:
            group_canvas = group_canvas.copy()
            group_canvas.putalpha(group_canvas.getchannel("A").point(lambda value: int(value * opacity)))
        self._alpha_composite_clipped(base, group_canvas, paste_at)

    def _resolve_layer_image(self, layer: dict[str, Any], images: list[Image.Image]) -> Image.Image | None:
        is_sticker = layer.get("assetKind") == "sticker" or any(layer.get(key) for key in ("stickerDataUrl", "stickerPath", "stickerUrl"))
        if is_sticker:
            return (
                self._open_external_image(layer.get("stickerDataUrl"))
                or self._open_external_image(layer.get("stickerPath"))
                or self._open_external_image(layer.get("stickerUrl"))
            )
        try:
            slot = max(1, int(layer.get("sourceIndex") or layer.get("source", {}).get("slot") or 1))
        except Exception:
            slot = 1
        return images[(slot - 1) % len(images)] if images else None

    def _render_layout_image_layer(self, layer: dict[str, Any], images: list[Image.Image], config: dict[str, Any]) -> Image.Image | None:
        source = self._resolve_layer_image(layer, images)
        if source is None:
            return None
        _, _, width, height = self._layer_geometry(layer)
        focus = (
            float(layer.get("cropFocusX", 0.5) if layer.get("cropFocusX") is not None else 0.5),
            float(layer.get("cropFocusY", 0.5) if layer.get("cropFocusY") is not None else 0.5),
        )
        tile = self._fit_image(source, (width, height), str(layer.get("fit") or "cover"), focus)
        color_source = str(layer.get("colorSource") or "none")
        color = self._resolve_layout_color(color_source, layer.get("color"), config, "#6f8090", allow_none=True)
        if color is not None:
            ratio = max(0, min(1, float(layer.get("colorRatio", 0) or 0)))
            if ratio > 0:
                overlay = Image.new("RGBA", tile.size, (*color, 0))
                overlay.putalpha(tile.getchannel("A").point(lambda value: int(value * ratio)))
                tile = Image.alpha_composite(tile, overlay)
        blur = max(0, int(float(layer.get("blur") or layer.get("effects", {}).get("blur") or 0)))
        if blur:
            tile = tile.filter(ImageFilter.GaussianBlur(blur))
        radius = max(0, int(float(layer.get("radius") or 0)))
        if radius:
            tile = self._rounded(tile, radius)
        return self._apply_polygon_mask(tile, layer.get("maskPolygon"))

    def _layout_text_value(self, layer: dict[str, Any], title: str, subtitle: str, config: dict[str, Any]) -> str:
        layer_type = str(layer.get("type") or "")
        if layer_type in {"main_title", "title_zh"}:
            return title
        if layer_type in {"subtitle", "title_en"}:
            return subtitle
        if layer_type == "text":
            if layer.get("contentSource") == "library":
                key = str(layer.get("contentKey") or "").strip()
                texts = config.get("custom_texts") if isinstance(config.get("custom_texts"), dict) else {}
                return str(texts.get(key) or layer.get("content") or "")
            return str(layer.get("content") or "")
        return ""

    def _text_mask_mode(self, layer: dict[str, Any]) -> str:
        mode = str(layer.get("maskMode") or layer.get("textMaskMode") or layer.get("textStyle", {}).get("maskMode") or "normal")
        return mode if mode in {"knockout-text", "show-text"} else "normal"

    def _apply_text_mask_tile(self, mask: Image.Image, tile: Image.Image, layer: dict[str, Any], x: int, y: int, fill: int) -> None:
        opacity = max(0, min(1, float(layer.get("opacity", layer.get("transform", {}).get("opacity", 1)) or 1)))
        if opacity < 1 and fill > 0:
            tile = tile.point(lambda value: int(value * opacity))
        rotation = self._layer_rotation(layer)
        paste_x, paste_y = x, y
        if rotation:
            pivot_x, pivot_y = self._layer_pivot(layer)
            tile, offset = self._rotate_tile_around_pivot(tile.convert("RGBA"), rotation, pivot_x, pivot_y)
            tile = tile.getchannel("A")
            paste_x = int(round(x + offset[0]))
            paste_y = int(round(y + offset[1]))
        mask.paste(fill, (paste_x, paste_y), tile)

    def _build_text_mask(
        self,
        layers: list[dict[str, Any]],
        title: str,
        subtitle: str,
        config: dict[str, Any],
        design_size: tuple[int, int],
    ) -> Image.Image | None:
        if not self._has_text_mask_layer(layers):
            return None
        has_show_text = self._has_text_mask_layer(layers, "show-text")
        mask = Image.new("L", design_size, 0 if has_show_text else 255)
        show_shape = Image.new("L", design_size, 0)
        self._draw_text_mask_layers(show_shape, layers, "show-text", title, subtitle, config)
        if show_shape.getbbox():
            mask.paste(255, (0, 0), show_shape)
        knockout_shape = Image.new("L", design_size, 0)
        self._draw_text_mask_layers(knockout_shape, layers, "knockout-text", title, subtitle, config)
        if knockout_shape.getbbox():
            mask.paste(0, (0, 0), knockout_shape)
        return mask

    def _has_text_mask_layer(self, layers: list[Any], mode: str | None = None) -> bool:
        text_types = {"main_title", "subtitle", "title_zh", "title_en", "text"}
        for layer in layers or []:
            if not isinstance(layer, dict):
                continue
            if layer.get("type") == "group":
                if self._has_text_mask_layer(layer.get("children") or [], mode):
                    return True
                continue
            if str(layer.get("type") or "") not in text_types:
                continue
            mask_mode = self._text_mask_mode(layer)
            if mask_mode != "normal" and (mode is None or mask_mode == mode):
                return True
        return False

    def _draw_text_mask_layers(
        self,
        shape: Image.Image,
        layers: list[Any],
        mode: str,
        title: str,
        subtitle: str,
        config: dict[str, Any],
    ) -> None:
        text_types = {"main_title", "subtitle", "title_zh", "title_en", "text"}
        for layer in sorted((item for item in layers or [] if isinstance(item, dict)), key=lambda item: float(item.get("zIndex") or 0)):
            if layer.get("type") == "group":
                group_shape = Image.new("L", shape.size, 0)
                self._draw_text_mask_layers(group_shape, layer.get("children") or [], mode, title, subtitle, config)
                opacity = max(0, min(1, float(layer.get("opacity", layer.get("transform", {}).get("opacity", 1)) or 1)))
                if opacity < 1:
                    group_shape = group_shape.point(lambda value: int(value * opacity))
                rotation = self._layer_rotation(layer)
                if rotation:
                    x, y, width, height = self._layer_geometry(layer)
                    try:
                        pivot_x = max(0, min(1, float(layer.get("pivotX", 0.5) if layer.get("pivotX") is not None else 0.5)))
                        pivot_y = max(0, min(1, float(layer.get("pivotY", 0.5) if layer.get("pivotY") is not None else 0.5)))
                    except Exception:
                        pivot_x, pivot_y = 0.5, 0.5
                    group_shape = group_shape.rotate(
                        -rotation,
                        resample=Image.Resampling.BICUBIC,
                        expand=False,
                        center=(x + width * pivot_x, y + height * pivot_y),
                    )
                shape.paste(ImageChops.lighter(shape, group_shape), (0, 0))
                continue
            if str(layer.get("type") or "") not in text_types or self._text_mask_mode(layer) != mode:
                continue
            text = self._layout_text_value(layer, title, subtitle, config)
            x, y, width, height = self._layer_geometry(layer)
            tile = self._draw_layout_text_mask_tile((width, height), text, layer, config)
            self._apply_text_mask_tile(shape, tile, layer, x, y, 255)

    def _draw_layout_layer(self, canvas: Image.Image, layer: dict[str, Any], images: list[Image.Image], title: str, subtitle: str, config: dict[str, Any]) -> None:
        if layer.get("type") == "group":
            children = sorted(
                (item for item in layer.get("children") or [] if isinstance(item, dict)),
                key=lambda item: float(item.get("zIndex") or 0),
            )
            if not children:
                return
            group_canvas = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            for child in children:
                self._draw_layout_layer(group_canvas, child, images, title, subtitle, config)
            self._paste_group_canvas(canvas, group_canvas, layer)
            return

        x, y, width, height = self._layer_geometry(layer)
        layer_type = str(layer.get("type") or "")
        if layer_type == "image":
            tile = self._render_layout_image_layer(layer, images, config)
        elif layer_type in {"main_title", "subtitle", "title_zh", "title_en", "text"}:
            if self._text_mask_mode(layer) != "normal":
                tile = None
            else:
                shadow_blur = max(0, int(float(layer.get("shadowBlur") or layer.get("effects", {}).get("shadow", {}).get("blur") or 0)))
                shadow_x = int(float(layer.get("shadowOffsetX") or layer.get("effects", {}).get("shadow", {}).get("offsetX") or 0))
                shadow_y = int(float(layer.get("shadowOffsetY") or layer.get("effects", {}).get("shadow", {}).get("offsetY") or 0))
                text_blur = max(0, int(float(layer.get("blur") or layer.get("effects", {}).get("blur") or 0)))
                text_padding = max(0, shadow_blur * 3, text_blur * 3, abs(shadow_x) + shadow_blur * 2, abs(shadow_y) + shadow_blur * 2)
                tile = self._draw_layout_text(
                    (width, height),
                    self._layout_text_value(layer, title, subtitle, config),
                    layer,
                    config,
                    text_padding,
                )
                x -= text_padding
                y -= text_padding
        else:
            tile = None
        if tile is not None:
            self._paste_layout_tile(canvas, tile, layer, x, y)

    def _custom_static(self, images: list[Image.Image], title: str, subtitle: str, size: tuple[int, int], config: dict[str, Any]) -> Image.Image:
        layout = config.get("custom_static_layout")
        if not isinstance(layout, dict) or not isinstance(layout.get("layers"), list) or not layout.get("layers"):
            return self._multi_1(images, title, subtitle, size, config)
        document = layout.get("canvas") or layout.get("document") or {}
        design_size = (
            max(1, int(float(document.get("width") or 1920))),
            max(1, int(float(document.get("height") or 1080))),
        )
        config = dict(config)
        config.setdefault("auto_color", self._extract_auto_color(images[0] if images else None))
        canvas = self._layout_background(images, design_size, layout, config)
        layers = sorted(
            (item for item in layout.get("layers") or [] if isinstance(item, dict)),
            key=lambda item: float(item.get("zIndex") or 0),
        )
        for layer in layers:
            self._draw_layout_layer(canvas, layer, images, title, subtitle, config)
        text_mask = self._build_text_mask(layers, title, subtitle, config, design_size)
        if text_mask is not None:
            alpha = ImageChops.multiply(canvas.getchannel("A"), text_mask)
            canvas.putalpha(alpha)
        if canvas.size != size:
            canvas = canvas.resize(size, Image.Resampling.LANCZOS)
        return canvas

    def _single_1(self, image: Image.Image, title: str, subtitle: str, size: tuple[int, int], config: dict[str, Any]) -> Image.Image:
        w, h = size
        canvas = self._background(image, size, config)
        poster_size = (int(h * 0.70), int(h * 0.70))
        poster = self._rounded(self._fit_cover(image, poster_size), int(94 * h / 1080))
        x = int(w * 0.54)
        y = int(h * 0.15)
        for angle, alpha, offset in ((34, 95, (-18, 18)), (17, 145, (-8, 10)), (0, 255, (0, 0))):
            layer = poster.copy()
            if alpha < 255:
                layer.putalpha(alpha)
            rotated = layer.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
            shadow = self._shadow(rotated.size, int(90 * h / 1080), int(22 * h / 1080), 105)
            canvas.alpha_composite(shadow, (x + offset[0] + 20, y + offset[1] + 24))
            canvas.alpha_composite(rotated, (x + offset[0], y + offset[1]))
        self._draw_text(canvas, title, subtitle, (int(w * 0.04), int(h * 0.33), int(w * 0.43), int(h * 0.28)), config)
        return canvas

    def _static_4(self, image: Image.Image, title: str, subtitle: str, size: tuple[int, int], config: dict[str, Any]) -> Image.Image:
        w, h = size
        canvas = self._background(image, size, config)
        title_scale = max(0.4, min(2.5, float(config.get("title_scale") or 1)))
        local_config = dict(config)
        local_config["main_font_size"] = int(float(local_config.get("main_font_size") or 170) * title_scale)
        local_config["subtitle_font_size"] = int(float(local_config.get("subtitle_font_size") or 76) * title_scale)
        scale = h / 1080
        main_h = int(local_config["main_font_size"] * scale)
        sub_h = int(local_config["subtitle_font_size"] * scale) if subtitle else 0
        spacing = int(34 * scale) if subtitle else 0
        total_h = main_h + sub_h + spacing
        y = max(0, int((h - total_h) / 2) - int(30 * scale))
        self._draw_text(canvas, title, subtitle, (int(w * 0.15), y, int(w * 0.70), int(h * 0.42)), local_config)
        return canvas

    def _single_2(self, image: Image.Image, title: str, subtitle: str, size: tuple[int, int], config: dict[str, Any]) -> Image.Image:
        w, h = size
        canvas = self._background(image, size, config)
        hero = self._fit_cover(image, size, focus=(0.72, 0.5))
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.polygon([(int(w * 0.55), 0), (w, 0), (w, h), (int(w * 0.40), h)], fill=255)
        hero_alpha = ImageChops.multiply(hero.getchannel("A"), mask)
        hero.putalpha(hero_alpha)
        canvas.alpha_composite(hero, (0, 0))
        self._draw_text(canvas, title, subtitle, (int(w * 0.04), int(h * 0.34), int(w * 0.43), int(h * 0.28)), config)
        return canvas

    def _multi_1(self, images: list[Image.Image], title: str, subtitle: str, size: tuple[int, int], config: dict[str, Any]) -> Image.Image:
        w, h = size
        canvas = self._background(images[0], size, config)
        card_w = int(w * 0.215)
        card_h = int(card_w * 1.48)
        radius = int(card_w * 0.11)
        start_x = int(w * 0.51)
        start_y = -int(h * 0.30)
        gap_x = int(card_w * 0.78)
        gap_y = int(card_h * 0.78)
        order = [2, 0, 4, 3, 1, 5, 8, 7, 6]
        slots = [images[index % len(images)] for index in order]
        positions = []
        for col in range(3):
            for row in range(3):
                positions.append((start_x + col * gap_x - row * int(card_w * 0.36), start_y + row * gap_y - col * int(card_h * 0.05)))
        for img, (x, y) in zip(slots, positions):
            card = self._rounded(self._fit_cover(img, (card_w, card_h)), radius)
            rotated = card.rotate(15.8, expand=True, resample=Image.Resampling.BICUBIC)
            shadow = self._shadow(rotated.size, radius, int(18 * h / 1080), 80)
            canvas.alpha_composite(shadow, (x + 12, y + 16))
            canvas.alpha_composite(rotated, (x, y))
        self._draw_text(canvas, title, subtitle, (int(w * 0.03), int(h * 0.37), int(w * 0.44), int(h * 0.3)), config)
        return canvas

    def _hex_to_rgb(self, value: str) -> tuple[int, int, int]:
        value = value.strip().lstrip("#")
        if len(value) == 3:
            value = "".join(ch * 2 for ch in value)
        try:
            return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)
        except Exception:
            return 111, 128, 144
