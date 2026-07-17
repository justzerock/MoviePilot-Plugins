from __future__ import annotations

import tempfile
import unittest
import asyncio
from pathlib import Path

import yaml
from PIL import Image

from app.cover.presets import create_preset_layout
from app.cover.renderer import CoverRenderer
from app.media_client import MediaServerClient
from app.font_preview import PreviewFontService
from app.services import CoverService, library_title_background, library_title_payload
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

    def test_media_count_badge_is_persisted_into_formal_cover(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            source = root / "source.jpg"
            output = root / "cover.png"
            Image.new("RGB", (640, 960), "#445566").save(source)
            layout = create_preset_layout("static_1")
            layout["layers"].append({
                "id": "library-count",
                "type": "badge",
                "content": "{count} 部",
                "shape": "pill",
                "x": 1400,
                "y": 80,
                "width": 360,
                "height": 120,
                "zIndex": 20,
                "backgroundColor": "#007aff",
                "borderColor": "#ffffff",
                "borderWidth": 0,
                "fontSize": 46,
                "fontFamily": "main_title",
                "color": "#ffffff",
                "opacity": 1,
            })
            renderer = CoverRenderer(root / "fonts")
            renderer.render(
                [source], "动画电影", "Anime Films", "static_1",
                {
                    "resolution": "720p",
                    "output_format": "png",
                    "library_item_count": 128,
                    "custom_static_layout": layout,
                },
                output,
            )
            with Image.open(output).convert("RGB") as image:
                blue = image.getpixel((950, 70))
                self.assertGreater(blue[2], blue[0])
                self.assertGreater(blue[2], blue[1])

    def test_badge_uses_its_selected_count_mode(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            renderer = CoverRenderer(Path(raw_dir) / "fonts")
            captured: list[str] = []

            def capture_text(size, text, layer, config):
                captured.append(text)
                return Image.new("RGBA", size, (0, 0, 0, 0))

            renderer._draw_layout_text = capture_text  # type: ignore[method-assign]
            renderer._draw_layout_badge(
                (360, 120),
                {"type": "badge", "content": "{count} 部", "countMode": "titles"},
                {
                    "library_item_count": 128,
                    "library_item_counts": {"episodes": 128, "titles": 12, "seasons": 18},
                },
            )
            self.assertEqual(captured, ["12 部"])

    def test_gradient_direction_preserves_transparent_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            renderer = CoverRenderer(Path(raw_dir) / "fonts")
            image = renderer._layout_background(
                [],
                (4, 3),
                {
                    "background": {
                        "type": "gradient",
                        "colorSource": "custom",
                        "color": "#ff0000",
                        "color2": "#0000ff",
                        "gradientDirection": "horizontal",
                        "gradientStartOpacity": 1,
                        "gradientEndOpacity": 0,
                    }
                },
                {},
            )
            self.assertEqual(image.getpixel((0, 1))[3], 255)
            self.assertEqual(image.getpixel((3, 1))[3], 0)
            self.assertGreater(image.getpixel((0, 1))[0], image.getpixel((0, 1))[2])
            self.assertGreater(image.getpixel((3, 1))[2], image.getpixel((3, 1))[0])


class MediaCountTests(unittest.TestCase):
    def test_nonempty_sources_only_fallback_when_server_counts_are_all_missing(self) -> None:
        self.assertEqual(
            CoverService.normalized_library_item_counts({"episodes": 0, "titles": 0, "seasons": 0}, 9),
            {"episodes": 9, "titles": 9, "seasons": 9},
        )
        self.assertEqual(
            CoverService.normalized_library_item_counts({"episodes": 0, "titles": 12, "seasons": 0}, 9),
            {"episodes": 0, "titles": 12, "seasons": 0},
        )

    def test_server_counts_use_episode_title_and_season_units(self) -> None:
        client = MediaServerClient("http://example.test", "token")
        requested_types: list[str] = []
        totals = {"Episode,Movie": 128, "Series,Movie": 12, "Season,Movie": 18}

        async def fake_get_json(path, params):
            self.assertEqual(path, "Items")
            self.assertEqual(params["Limit"], 0)
            requested_types.append(params["IncludeItemTypes"])
            return {"Items": [], "TotalRecordCount": totals[params["IncludeItemTypes"]]}

        client._get_json = fake_get_json  # type: ignore[method-assign]
        result = asyncio.run(client.get_library_item_counts("library-1"))
        self.assertEqual(result, {"episodes": 128, "titles": 12, "seasons": 18})
        self.assertEqual(requested_types, ["Episode,Movie", "Series,Movie", "Season,Movie"])


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
