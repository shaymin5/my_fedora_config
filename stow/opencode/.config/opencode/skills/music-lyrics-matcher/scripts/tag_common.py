#!/usr/bin/env python3
"""Shared helpers: read tags/duration from any common audio format, text matching.

Uses mutagen so mp3 / flac / opus / ogg / m4a / wav all work the same way.
"""
from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

AUDIO_EXTS = {".mp3", ".flac", ".opus", ".ogg", ".oga", ".m4a", ".mp4", ".aac", ".wav", ".aiff", ".aif", ".wma"}


def iter_audio(root: Path, recursive: bool = False):
    it = root.rglob("*") if recursive else root.glob("*")
    for p in sorted(it):
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS:
            yield p


def read_tags(path: Path) -> dict:
    """Return {title, artist, album, duration}. Empty string / 0.0 when absent."""
    import mutagen

    info = {"title": "", "artist": "", "album": "", "duration": 0.0}
    try:
        f = mutagen.File(path, easy=True)
    except Exception:
        f = None
    if f is None:
        return info
    if getattr(f, "info", None) is not None:
        info["duration"] = float(getattr(f.info, "length", 0.0) or 0.0)

    def first(key):
        try:
            v = f.get(key)  # type: ignore[union-attr]
        except Exception:
            v = None
        if isinstance(v, list) and v:
            return str(v[0])
        return str(v) if v else ""

    info["title"] = first("title") or path.stem
    info["artist"] = first("artist")
    info["album"] = first("album")
    return info


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower()
    return re.sub(r"[\s\-_、。・'’\"“”()（）\[\]{}<>／/&,]+", "", s)


def sim(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def name_variants(s: str) -> list[str]:
    """Alias-aware variants: '高橋洋子 [Yoko Takahashi]' -> several strings."""
    s = unicodedata.normalize("NFKC", s)
    out = [s]
    stripped = re.sub(r"[(\[{（【].*?[)\]}）】]", "", s).strip()
    if stripped:
        out.append(stripped)
    out += re.findall(r"[(\[{（【](.*?)[)\]}）】]", s)
    out += re.split(r"[,/&、]", s)
    return [norm(v) for v in out if v.strip()]


def artist_sim(a: str, b: str) -> float:
    return max((SequenceMatcher(None, x, y).ratio()
                for x in name_variants(a) for y in name_variants(b)), default=0.0)


def clean_title(t: str) -> str:
    """Drop a trailing parenthetical/version suffix to widen a search."""
    t = re.sub(r"\s*[（(\[][^)）\]]*[)）\]]\s*$", "", t).strip()
    return t or t


TIMED_RE = re.compile(r"^\[(\d{1,2}):(\d{2})[.:](\d{1,3})\]")
# a timestamp followed by whitespace before the text, e.g. "[00:00.15] 歌詞"
SPACE_AFTER_TAG = re.compile(r"^(\s*(?:\[[^\]]*\])+)[ \t\u3000]+\S")
_TAG_PREFIX = re.compile(r"^(\s*(?:\[[^\]]*\])+)\s*(.*)$")


def normalize_lrc(text: str) -> str:
    """Make the lyric body uniform: no whitespace between/after the leading
    timestamp tags, and no trailing whitespace. Content is otherwise untouched
    (bilingual translation lines are preserved)."""
    out: list[str] = []
    for line in text.splitlines():
        m = _TAG_PREFIX.match(line)
        if m:
            tags = re.sub(r"\s+", "", m.group(1))
            out.append((tags + m.group(2)).rstrip())
        else:
            out.append(line.rstrip())
    return "\n".join(out)


def line_seconds(line: str) -> float | None:
    m = TIMED_RE.match(line)
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2)) + int(m.group(3)) / (10 ** len(m.group(3)))


def fmt_ts(seconds: float) -> str:
    cs = int(round(seconds * 100))
    return f"[{cs // 6000:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}]"


def strip_top_metadata(text: str) -> str:
    """Remove leading header tags ([ti:] [al:] ...) and previously inserted
    display-info lines, keeping the actual lyric body untouched."""
    header_tags = {"ti", "ar", "al", "au", "by", "ly", "mu", "offset", "re", "ve", "length"}
    lines = text.splitlines()
    body: list[str] = []
    i = 0
    # drop leading ID tags
    while i < len(lines):
        m = re.match(r"^\[([A-Za-z]+):", lines[i])
        if m and m.group(1).lower() in header_tags:
            i += 1
        else:
            break
    return "\n".join(lines[i:]).strip("\n")
