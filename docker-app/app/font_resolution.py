from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
import unicodedata
from typing import Any


@dataclass(frozen=True)
class FontCoverage:
    supported: bool
    missing_characters: tuple[str, ...]
    missing_codepoints: tuple[int, ...]
    checked_characters: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResolvedRenderText:
    original_text: str
    rendered_text: str
    requested_font_path: str
    resolved_font_path: str
    resolved_script: str
    conversion_applied: bool
    conversion_profile: str | None
    missing_characters_before: tuple[str, ...]
    missing_characters_after: tuple[str, ...]
    used_fallback_font: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_explicit_font(value: Any, font_index: dict[str, str] | None = None) -> Path | None:
    """Resolve a user-selected font reference without inferring coverage from its name."""
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw.startswith("font:"):
        raw = raw[5:].strip()
    candidate = Path(raw).expanduser()
    if candidate.is_file():
        return candidate.resolve()
    index = font_index or {}
    for key in (raw, Path(raw).name, Path(raw).stem):
        resolved = str(index.get(key) or "").strip()
        if resolved and Path(resolved).is_file():
            return Path(resolved).resolve()
    return None


def _font_cache_key(path: Path, face_index: int) -> tuple[str, int, int, int]:
    resolved = path.resolve()
    stat = resolved.stat()
    return str(resolved), int(stat.st_size), int(stat.st_mtime_ns), int(face_index)


@lru_cache(maxsize=128)
def _cached_font_codepoints(cache_key: tuple[str, int, int, int]) -> frozenset[int]:
    from fontTools.ttLib import TTFont  # type: ignore

    path, _size, _mtime_ns, face_index = cache_key
    kwargs = {"fontNumber": face_index} if Path(path).suffix.lower() in {".ttc", ".otc"} else {}
    font = TTFont(path, lazy=True, **kwargs)
    try:
        codepoints: set[int] = set()
        cmap = font.get("cmap")
        if cmap:
            for table in cmap.tables:
                if table.isUnicode():
                    codepoints.update(int(value) for value in table.cmap.keys())
        return frozenset(codepoints)
    finally:
        font.close()


def get_font_codepoints(font_path: str | Path, face_index: int = 0) -> frozenset[int]:
    path = Path(font_path)
    if not path.is_file():
        return frozenset()
    return _cached_font_codepoints(_font_cache_key(path, face_index))


def _characters_to_check(text: str) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for character in unicodedata.normalize("NFC", str(text or "")):
        category = unicodedata.category(character)
        if category.startswith("C") or category.startswith("Z") or character in seen:
            continue
        seen.add(character)
        result.append(character)
    return tuple(result)


def check_font_text_coverage(font_path: str | Path, text: str, face_index: int = 0) -> FontCoverage:
    characters = _characters_to_check(text)
    codepoints = get_font_codepoints(font_path, face_index)
    missing = tuple(character for character in characters if ord(character) not in codepoints)
    return FontCoverage(
        supported=bool(codepoints) and not missing,
        missing_characters=missing,
        missing_codepoints=tuple(ord(character) for character in missing),
        checked_characters=len(characters),
    )


def _conversion_profiles(target: str, traditional_variant: str) -> tuple[str, ...]:
    traditional = {"taiwan": "s2tw", "hongkong": "s2hk"}.get(traditional_variant, "s2t")
    if target == "simplified":
        return ("t2s",)
    if target == "traditional":
        return (traditional,)
    return ("t2s", traditional)


@lru_cache(maxsize=8)
def _opencc(profile: str):
    from opencc import OpenCC  # type: ignore

    return OpenCC(profile)


def _convert(text: str, profile: str) -> str:
    try:
        return str(_opencc(profile).convert(text))
    except Exception:
        return text


def _script_name(profile: str | None) -> str:
    if profile == "t2s":
        return "simplified"
    if profile in {"s2t", "s2tw", "s2hk"}:
        return "traditional"
    return "original"


def resolve_render_text_and_font(
    original_text: Any,
    requested_font_path: str | Path,
    fallback_font_path: str | Path = "",
    *,
    adaptation_enabled: bool = True,
    target: str = "auto",
    traditional_variant: str = "standard",
    face_index: int = 0,
) -> ResolvedRenderText:
    original = str(original_text or "")
    requested = str(requested_font_path or "")
    fallback = str(fallback_font_path or "")
    before = check_font_text_coverage(requested, original, face_index)
    if before.supported or not original:
        return ResolvedRenderText(original, original, requested, requested, "original", False, None, before.missing_characters, before.missing_characters, False)

    candidates: list[tuple[str, str, FontCoverage, int]] = []
    if adaptation_enabled:
        seen = {original}
        for order, profile in enumerate(_conversion_profiles(str(target or "auto"), str(traditional_variant or "standard"))):
            converted = _convert(original, profile)
            if converted in seen:
                continue
            seen.add(converted)
            coverage = check_font_text_coverage(requested, converted, face_index)
            edit_count = sum(1 for left, right in zip(original, converted) if left != right) + abs(len(original) - len(converted))
            candidates.append((profile, converted, coverage, edit_count * 10 + order))
        complete = [candidate for candidate in candidates if candidate[2].supported]
        if complete:
            profile, rendered, after, _score = min(complete, key=lambda item: item[3])
            return ResolvedRenderText(original, rendered, requested, requested, _script_name(profile), True, profile, before.missing_characters, after.missing_characters, False)

    fallback_coverage = check_font_text_coverage(fallback, original, face_index) if fallback else before
    # A configured fallback is the final safety net even when its own cmap is
    # incomplete. Keeping the original text is more important than rendering a
    # converted string with the wrong requested face, and the remaining glyphs
    # stay visible in diagnostics for the caller.
    resolved_path = fallback if fallback and get_font_codepoints(fallback, face_index) else requested
    used_fallback = resolved_path != requested
    after_missing = fallback_coverage.missing_characters if used_fallback else before.missing_characters
    return ResolvedRenderText(original, original, requested, resolved_path, "original", False, None, before.missing_characters, after_missing, used_fallback)


def font_internal_names(font_path: str | Path, face_index: int = 0) -> list[str]:
    from fontTools.ttLib import TTFont  # type: ignore

    path = Path(font_path)
    kwargs = {"fontNumber": face_index} if path.suffix.lower() in {".ttc", ".otc"} else {}
    font = TTFont(str(path), lazy=True, **kwargs)
    try:
        names: list[str] = []
        for record in font["name"].names if "name" in font else []:
            if record.nameID not in {1, 2, 4, 6}:
                continue
            try:
                value = record.toUnicode().strip()
            except Exception:
                continue
            if value and value not in names:
                names.append(value)
        return names
    finally:
        font.close()
