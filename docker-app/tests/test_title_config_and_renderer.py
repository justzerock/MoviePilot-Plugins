from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml
from PIL import Image

from app.cover.presets import create_preset_layout
from app.cover.renderer import CoverRenderer
from app.font_preview import PreviewFontService
from app.services import library_title_background, library_title_payload
from app.title_config import normalize_title_config


class TitleConfigTests(unittest.TestCase):
    def test_object_and_legacy_formats_normalize_identically(self) -> None:
        object_value = {
            "emby_动画电影": {
                "title": "动画电影", "subtitle": "Anime Films", "background": "#5f7185",
                "texts": {"slogan": "自定义文本", "any_key": "任意文本"},
            }
        }
        legacy_value = {
            "emby_动画电影": [
                "动画电影", "Anime Films", "#5f7185",
                {"texts": {"slogan": "自定义文本", "any_key": "任意文本"}},
            ]
        }
        normalized_object, object_warnings = normalize_title_config(object_value)
        normalized_legacy, legacy_warnings = normalize_title_config(legacy_value)
        self.assertEqual(normalized_object, normalized_legacy)
        self.assertEqual(object_warnings, [])
        self.assertEqual(legacy_warnings, [])

    def test_invalid_item_does_not_discard_valid_library(self) -> None:
        normalized, warnings = normalize_title_config({"音乐": {"title": "音乐"}, "坏项目": object()})
        self.assertEqual(normalized["音乐"]["title"], "音乐")
        self.assertNotIn("坏项目", normalized)
        self.assertTrue(any(message.startswith("坏项目:") for message in warnings))

    def test_safe_yaml_round_trip_preserves_hash_color_and_custom_keys(self) -> None:
        source = {"音乐": {"title": "音乐", "subtitle": "Music", "background": "#abc", "texts": {"slogan": "随便听"}}}
        first, _ = normalize_title_config(source)
        dumped = yaml.safe_dump(first, allow_unicode=True, sort_keys=False)
        second, warnings = normalize_title_config(yaml.safe_load(dumped))
        self.assertEqual(second, first)
        self.assertEqual(warnings, [])
        self.assertIn("'#abc'", dumped)

    def test_legacy_short_forms_and_direct_text_map_are_supported(self) -> None:
        normalized, warnings = normalize_title_config({
            "单标题": ["单标题"],
            "双标题": ["双标题", "Subtitle"],
            "直接文本": ["直接文本", "Direct", "#5f7185", {"slogan": "你好", "note": "备注"}],
            "字符串": "字符串标题",
        })
        self.assertEqual(warnings, [])
        self.assertEqual(normalized["单标题"]["subtitle"], "")
        self.assertEqual(normalized["双标题"]["subtitle"], "Subtitle")
        self.assertEqual(normalized["直接文本"]["texts"], {"slogan": "你好", "note": "备注"})
        self.assertEqual(normalized["字符串"]["title"], "字符串标题")

    def test_normalized_fields_reach_preview_payload(self) -> None:
        normalized, warnings = normalize_title_config({
            "emby_动画电影": {
                "title": "动画电影",
                "subtitle": "Anime Films",
                "background": "#5f7185",
                "texts": {"slogan": "自定义文本", "any_key": "任意文本"},
            }
        })
        config = {"title_config": normalized, "distinguish_same_name_libraries": True}
        title, subtitle, texts = library_title_payload(config, "动画电影", "emby")
        self.assertEqual((title, subtitle), ("动画电影", "Anime Films"))
        self.assertEqual(texts, {"slogan": "自定义文本", "any_key": "任意文本"})
        self.assertEqual(library_title_background(config, "动画电影", "emby"), "#5f7185")


class RendererLayoutTests(unittest.TestCase):
    def test_all_static_presets_use_complete_canvas_schema(self) -> None:
        expected_layers = {"static_1": 5, "static_2": 3, "static_3": 11, "static_4": 2}
        for style, count in expected_layers.items():
            layout = create_preset_layout(style)
            self.assertEqual(layout["canvas"]["width"], 1920)
            self.assertEqual(layout["canvas"]["height"], 1080)
            self.assertEqual(len(layout["layers"]), count)
            self.assertTrue(all("frame" in layer and "transform" in layer for layer in layout["layers"]))

    def test_static_preset_is_routed_through_generic_layout_renderer(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            source = root / "source.jpg"
            output = root / "cover.jpg"
            Image.new("RGB", (640, 960), "#4f8cff").save(source)
            renderer = CoverRenderer(root / "fonts")
            renderer.render(
                [source], "动画电影", "Anime Films", "static_1",
                {"resolution": "720p", "custom_static_layout": create_preset_layout("static_1")}, output,
            )
            with Image.open(output) as image:
                self.assertEqual(image.size, (1280, 720))
                self.assertGreater(len(image.getcolors(maxcolors=1_000_000) or []), 8)


class PreviewFontTests(unittest.TestCase):
    def test_original_font_family_uses_complete_source_version(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            source = root / "custom.ttf"
            source.write_bytes(b"font-version-test")
            service = PreviewFontService(root)
            assets = service.assets([source])
            asset = next(iter(assets.values()))
            info = service.info(
                str(asset["font_id"]),
                assets,
                {"preview_font_enabled": True, "font_subset_enabled": False},
                lambda font_id, variant, version: f"/api/fonts/{font_id}/file?variant={variant}&v={version}",
            )
            self.assertIsNotNone(info)
            self.assertEqual(info["version"], asset["source_sha256"])
            self.assertEqual(info["font_family"], f"YahahaPreview_{asset['font_id']}_{asset['source_sha256']}")
            self.assertEqual(info["source_type"], "original")


if __name__ == "__main__":
    unittest.main()
