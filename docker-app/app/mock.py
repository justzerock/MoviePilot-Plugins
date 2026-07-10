from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


MOCK_LIBRARIES = [
    {"id": "mock-anime", "name": "动漫", "server": "mock", "collection_type": "shows"},
    {"id": "mock-music", "name": "音乐", "server": "mock", "collection_type": "music"},
    {"id": "mock-movie", "name": "电影", "server": "mock", "collection_type": "movies"},
]

PALETTES = [
    ("#87d9ff", "#4f8cff", "#152238"),
    ("#ffd166", "#ff8a65", "#2c1d12"),
    ("#b39cff", "#ff8fd8", "#201633"),
    ("#70e1b5", "#2cc8a4", "#10241f"),
    ("#f6c2d9", "#ff6b9d", "#2f1725"),
    ("#a7c7ff", "#6b8cff", "#17203b"),
    ("#f6e6a8", "#ffb547", "#30220b"),
    ("#9fe7f5", "#4ac6df", "#102a31"),
    ("#d4b8ff", "#8d6bff", "#21183a"),
]


def mock_library_by_name(name: str) -> dict[str, str] | None:
    for library in MOCK_LIBRARIES:
        if library["name"] == name or library["id"] == name:
            return library
    return None


def ensure_mock_images(input_dir: Path, slug: str, title: str, limit: int) -> list[Path]:
    library_dir = input_dir / slug
    library_dir.mkdir(parents=True, exist_ok=True)
    count = max(1, min(limit, len(PALETTES)))
    paths: list[Path] = []
    for index in range(count):
        path = library_dir / f"mock_{index + 1:02d}.jpg"
        if not path.exists():
            _create_mock_image(path, title, index)
        paths.append(path)
    return paths


def _create_mock_image(path: Path, title: str, index: int) -> None:
    width, height = 1280, 720
    start, end, ink = PALETTES[index % len(PALETTES)]
    image = Image.new("RGB", (width, height), start)
    pixels = image.load()
    sr, sg, sb = _hex(start)
    er, eg, eb = _hex(end)
    for y in range(height):
        t = y / max(1, height - 1)
        for x in range(width):
            drift = (x / max(1, width - 1)) * 0.22
            mix = min(1, t * 0.78 + drift)
            pixels[x, y] = (
                int(sr + (er - sr) * mix),
                int(sg + (eg - sg) * mix),
                int(sb + (eb - sb) * mix),
            )
    draw = ImageDraw.Draw(image, "RGBA")
    for step in range(5):
        offset = index * 37 + step * 180
        draw.rounded_rectangle(
            (offset % width - 140, 80 + step * 92, offset % width + 420, 210 + step * 92),
            radius=42,
            fill=(255, 255, 255, 24 + step * 7),
        )
    font = _font(78)
    small = _font(30)
    draw.text((78, 456), title, fill=(*_hex(ink), 245), font=font)
    draw.text((84, 548), f"Mock Source {index + 1:02d}", fill=(*_hex(ink), 170), font=small)
    image.save(path, "JPEG", quality=92)


def _font(size: int):
    for candidate in (
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _hex(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)
