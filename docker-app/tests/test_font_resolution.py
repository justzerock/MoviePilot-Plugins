from __future__ import annotations

import os
import tempfile
import time
import unittest
from copy import deepcopy
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image

from app.cover.presets import create_preset_layout
from app.cover.renderer import CoverRenderer
from app.font_preview import PreviewFontService
from app.font_resolution import (
    check_font_text_coverage,
    font_internal_names,
    resolve_render_text_and_font,
)
from app.services import CoverService


ROOT = Path(__file__).resolve().parents[1]
BUNDLED_FONTS = Path("/app/app/bundled_fonts") if Path("/app/app/bundled_fonts").is_dir() else ROOT / "bundled-fonts"
CHAOHEI = BUNDLED_FONTS / "chaohei.ttf"
MELETE = BUNDLED_FONTS / "Melete.otf"


def make_traditional_only_font(source: Path, target: Path) -> None:
    pairs = {"动": "動", "画": "畫", "电": "電", "测": "測", "试": "試"}
    font = TTFont(str(source))
    try:
        for table in font["cmap"].tables:
            if not table.isUnicode():
                continue
            for simplified, traditional in pairs.items():
                glyph = table.cmap.get(ord(simplified))
                if glyph:
                    table.cmap[ord(traditional)] = glyph
                    table.cmap.pop(ord(simplified), None)
        font.save(str(target))
    finally:
        font.close()


class FontCoverageTests(unittest.TestCase):
    def test_real_font_cmap_and_internal_names_are_read(self) -> None:
        coverage = check_font_text_coverage(CHAOHEI, "动画电影")
        self.assertTrue(coverage.supported)
        self.assertEqual(coverage.missing_characters, ())
        self.assertIn("文道潮黑", font_internal_names(CHAOHEI))

    def test_original_text_is_preserved_when_requested_font_covers_it(self) -> None:
        result = resolve_render_text_and_font("动画电影", CHAOHEI, CHAOHEI)
        self.assertEqual(result.original_text, "动画电影")
        self.assertEqual(result.rendered_text, "动画电影")
        self.assertFalse(result.conversion_applied)
        self.assertFalse(result.used_fallback_font)

    def test_traditional_text_uses_simplified_candidate_only_for_rendering(self) -> None:
        for target in ("auto", "simplified"):
            with self.subTest(target=target):
                result = resolve_render_text_and_font("動畫電影", CHAOHEI, CHAOHEI, target=target)
                self.assertEqual(result.original_text, "動畫電影")
                self.assertEqual(result.rendered_text, "动画电影")
                self.assertEqual(result.conversion_profile, "t2s")
                self.assertTrue(result.conversion_applied)
                self.assertFalse(result.used_fallback_font)

    def test_simplified_text_can_match_a_traditional_only_font(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            traditional_font = Path(raw_dir) / "traditional.ttf"
            make_traditional_only_font(CHAOHEI, traditional_font)
            for target in ("auto", "traditional"):
                with self.subTest(target=target):
                    result = resolve_render_text_and_font("动画电影", traditional_font, CHAOHEI, target=target)
                    self.assertEqual(result.original_text, "动画电影")
                    self.assertEqual(result.rendered_text, "動畫電影")
                    self.assertEqual(result.conversion_profile, "s2t")
                    self.assertFalse(result.used_fallback_font)

    def test_adaptation_disabled_uses_fallback_with_original_text(self) -> None:
        result = resolve_render_text_and_font(
            "动画电影",
            MELETE,
            CHAOHEI,
            adaptation_enabled=False,
        )
        self.assertEqual(result.rendered_text, "动画电影")
        self.assertEqual(Path(result.resolved_font_path), CHAOHEI.resolve())
        self.assertTrue(result.used_fallback_font)

    def test_incomplete_conversion_still_falls_back_to_original_text(self) -> None:
        result = resolve_render_text_and_font("動畫電影", MELETE, CHAOHEI, target="traditional")
        self.assertEqual(result.rendered_text, "動畫電影")
        self.assertEqual(Path(result.resolved_font_path), CHAOHEI.resolve())
        self.assertTrue(result.used_fallback_font)
        self.assertIn("動", result.missing_characters_after)

    def test_cmap_cache_invalidates_when_font_file_is_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            target = Path(raw_dir) / "replaceable.ttf"
            target.write_bytes(CHAOHEI.read_bytes())
            self.assertTrue(check_font_text_coverage(target, "动").supported)
            font = TTFont(str(target))
            try:
                for table in font["cmap"].tables:
                    if table.isUnicode():
                        table.cmap.pop(ord("动"), None)
                font.save(str(target))
            finally:
                font.close()
            time.sleep(0.002)
            os.utime(target, None)
            self.assertFalse(check_font_text_coverage(target, "动").supported)


class FormalRenderFontTests(unittest.TestCase):
    def test_preview_and_formal_render_share_one_resolved_payload(self) -> None:
        service = CoverService()
        service.config = {
            "main_title_font_custom": str(CHAOHEI),
            "subtitle_font_custom": str(CHAOHEI),
            "custom_text_font_custom": str(CHAOHEI),
            "font_script_adaptation_enabled": True,
            "font_script_target": "auto",
            "font_traditional_variant": "standard",
        }
        layout = create_preset_layout("static_1")
        original_layout = deepcopy(layout)
        payload = service.resolve_render_payload(
            "動畫電影",
            "中文測試",
            {},
            layout,
            {"main_title": str(CHAOHEI), "subtitle": str(CHAOHEI), "custom_text": str(CHAOHEI), "chaohei": str(CHAOHEI)},
        )
        self.assertEqual(payload["original_title"], "動畫電影")
        self.assertEqual(payload["title"], "动画电影")
        self.assertEqual(payload["subtitle"], "中文测试")
        self.assertEqual(Path(payload["font_paths"]["main_title"]), CHAOHEI.resolve())
        title_layers = [layer for layer in payload["layout"]["layers"] if layer.get("type") in {"main_title", "title_zh"}]
        self.assertTrue(title_layers)
        self.assertTrue(all(layer.get("content") == "动画电影" for layer in title_layers))
        self.assertEqual(layout, original_layout)

    def test_subset_manifest_contains_the_resolved_render_characters(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            service = PreviewFontService(Path(raw_dir))
            assets = service.assets([CHAOHEI])
            font_id = next(iter(assets))
            config = {
                "preview_font_enabled": True,
                "font_subset_enabled": True,
                "font_script_adaptation_enabled": True,
                "font_script_target": "auto",
                "font_traditional_variant": "standard",
                "preview_rendered_characters": "动画电影",
            }
            info = service.info(font_id, assets, config, lambda asset_id, variant, version: f"/{asset_id}/{variant}/{version}")
            self.assertIsNotNone(info)
            deadline = time.monotonic() + 8
            status = service.status(font_id, assets, config)
            while status and status.get("status") != "ready" and time.monotonic() < deadline:
                time.sleep(0.05)
                status = service.status(font_id, assets, config)
            self.assertEqual(status and status.get("status"), "ready")
            ready = service.info(font_id, assets, config, lambda asset_id, variant, version: f"/{asset_id}/{variant}/{version}")
            self.assertEqual(ready and ready.get("source_type"), "subset")
            subset_path = service.subsets_root / font_id / f"{ready['charset_hash']}.woff2"
            self.assertTrue(check_font_text_coverage(subset_path, "动画电影").supported)
            service._executor.shutdown(wait=True)

    def test_resolved_font_and_rendered_text_reach_real_cover_renderer(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            source = root / "source.jpg"
            output = root / "cover.png"
            Image.new("RGB", (960, 640), "#4f8cff").save(source)
            resolved = resolve_render_text_and_font("動畫電影", CHAOHEI, CHAOHEI)
            layout = create_preset_layout("static_1")
            for layer in layout["layers"]:
                if layer.get("type") in {"main_title", "title_zh"}:
                    layer["content"] = resolved.rendered_text
            renderer = CoverRenderer(root / "fonts")
            renderer.render(
                [source],
                resolved.rendered_text,
                "Anime Films",
                "static_1",
                {
                    "resolution": "720p",
                    "output_format": "png",
                    "font_paths": {"main_title": resolved.resolved_font_path, "subtitle": resolved.resolved_font_path},
                    "custom_static_layout": layout,
                },
                output,
            )
            self.assertTrue(output.is_file())
            with Image.open(output) as image:
                self.assertEqual(image.size, (1280, 720))
                self.assertIsNotNone(image.getbbox())


if __name__ == "__main__":
    unittest.main()
