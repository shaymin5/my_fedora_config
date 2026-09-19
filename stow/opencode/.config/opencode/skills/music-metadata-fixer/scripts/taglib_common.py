#!/usr/bin/env python3
"""Shared tag read/write helpers for MP3 (ID3) and FLAC (Vorbis comments).

The public surface is deliberately small so the individual scripts stay thin:

    read_info(path)              -> AudioInfo  (canonical fields + diagnostics)
    write_fields(path, updates)  -> None       (preserves the file's ID3 version)
    strip_id3v1(path)            -> int        (drop trailing 128-byte ID3v1 block)
    strip_leading_id3(path)      -> int        (drop an illegal ID3 block in front of a FLAC)
    media_duration(path)         -> float | None

    iter_audio(dir, recursive)   -> list[Path] (single-level by default)
    iter_lrc(dir, recursive)     -> list[Path]
    discover_audio_dirs(dir)     -> list[Path] (folders that directly hold audio)
    audio_dirs_below(dir)        -> list[Path] (same, but excluding dir itself)

Canonical field names used everywhere: title, artist, albumartist, album,
genre, track (str), date (str).

Version policy: MP3 date frames are written back in the same ID3 major version
the file already used -- v2.3 files keep a single TYER, v2.4 files keep a single
TDRC. Passing v2_version=3 blindly would silently upgrade v2.4 files (and vice
versa), which is exactly what we avoid.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

from mutagen import File as MutagenFile
from mutagen.flac import FLAC
from mutagen.id3 import ID3, TALB, TCON, TDRC, TIT2, TPE1, TPE2, TRCK, TYER, ID3NoHeaderError

AUDIO_EXTS = {".mp3", ".flac"}
ID3_DATE_FRAMES = ("TYER", "TDRC", "TDAT", "TIME", "TRDA")

_ID3_FRAME = {
    "title": ("TIT2", TIT2),
    "artist": ("TPE1", TPE1),
    "albumartist": ("TPE2", TPE2),
    "album": ("TALB", TALB),
    "genre": ("TCON", TCON),
}
_VORBIS_KEY = {
    "title": "title",
    "artist": "artist",
    "albumartist": "albumartist",
    "album": "album",
    "genre": "genre",
}


@dataclass
class AudioInfo:
    path: Path
    container: str = ""            # "id3" | "vorbis"
    version: int | None = None     # ID3 major version (3/4); None for FLAC
    fields: dict[str, str] = field(default_factory=dict)
    date: str = ""
    id3v1: bool = False
    tyer_frames: int = 0
    tdrc_frames: int = 0
    stray_id3: bool = False        # FLAC with an illegal leading ID3 block
    has_cover: bool = False
    has_lyrics: bool = False
    duration: float | None = None
    note: str = ""                 # e.g. extension/content mismatch
    unreadable: bool = False       # could not parse the container at all


def _syncsafe(b: bytes) -> int:
    return ((b[0] & 0x7F) << 21) | ((b[1] & 0x7F) << 14) | ((b[2] & 0x7F) << 7) | (b[3] & 0x7F)


def leading_id3_size(raw: bytes) -> int:
    """Size of a leading ID3v2 block (0 if none)."""
    if raw[:3] != b"ID3":
        return 0
    size = 10 + _syncsafe(raw[6:10])
    if len(raw) > 5 and raw[5] & 0x10:  # footer present
        size += 10
    return size


MP3_SYNCS = (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"\xff\xfa", b"\xff\xe3")


def sniff_container(raw: bytes) -> str:
    """Identify the real container from the bytes, not the extension.

    Returns "flac", "flac_stray_id3", "mp3" or "unknown". Extensions lie: a file
    named ``.flac`` can actually be an MP3 (a leading ID3 tag followed by MPEG
    frame sync) and vice versa, so the choice of parser must follow the magic
    bytes or the file will fail to load.
    """
    if raw[:4] == b"fLaC":
        return "flac"
    if raw[:3] == b"ID3":
        if raw[leading_id3_size(raw):leading_id3_size(raw) + 4] == b"fLaC":
            return "flac_stray_id3"
        return "mp3"
    if raw[:2] in MP3_SYNCS:
        return "mp3"
    return "unknown"


def strip_id3v1(path: Path) -> int:
    """Drop trailing ID3v1 block(s). Returns how many 128-byte blocks were removed."""
    raw = path.read_bytes()
    removed = 0
    while len(raw) >= 128 and raw[-128:-125] == b"TAG":
        raw = raw[:-128]
        removed += 1
    if removed:
        path.write_bytes(raw)
    return removed


def strip_leading_id3(path: Path) -> int:
    """Remove an illegal ID3v2 block at the very start of a file. Returns bytes removed."""
    raw = path.read_bytes()
    size = leading_id3_size(raw)
    if size:
        path.write_bytes(raw[size:])
    return size


def media_duration(path: Path) -> float | None:
    try:
        media = MutagenFile(str(path))
    except Exception:
        return None
    if media is None or media.info is None:
        return None
    length = media.info.length
    return float(length) if isinstance(length, (int, float)) else None


def _is_audio(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in AUDIO_EXTS


def iter_audio(directory: Path, recursive: bool = False) -> list[Path]:
    """Audio files in `directory`.

    Single-level by default (matching the historical behaviour); pass
    ``recursive=True`` to walk subdirectories. A music collection is often laid
    out as ``<root>/<album>/...`` or ``<root>/<album>/Disc N/...``, so a
    single-level scan of the parent silently finds nothing -- callers that get
    zero files should check :func:`audio_dirs_below`.
    """
    if recursive:
        return sorted(p for p in directory.rglob("*") if _is_audio(p))
    return sorted(p for p in directory.iterdir() if _is_audio(p))


def iter_lrc(directory: Path, recursive: bool = False) -> list[Path]:
    if recursive:
        return sorted(p for p in directory.rglob("*.lrc") if p.is_file())
    return sorted(p for p in directory.glob("*.lrc") if p.is_file())


def discover_audio_dirs(directory: Path) -> list[Path]:
    """Every directory at or below `directory` that *directly* holds audio files.

    This is the natural unit of a "release": one run per returned folder keeps
    per-album values (album/artist/date) from leaking across separate releases.
    """
    return sorted({p.parent for p in directory.rglob("*") if _is_audio(p)})


def audio_dirs_below(directory: Path) -> list[Path]:
    """Subdirectories of `directory` that directly hold audio (excludes itself)."""
    return [d for d in discover_audio_dirs(directory) if d != directory]


def _first(tags, key: str) -> str:
    value = tags.get(key)
    if isinstance(value, list):
        return str(value[0]).strip() if value else ""
    return str(value).strip() if value is not None else ""


def _read_id3(path: Path, raw: bytes) -> AudioInfo:
    info = AudioInfo(path=path)
    info.container = "id3"
    info.version = raw[3] if raw[:3] == b"ID3" else None
    try:
        tag = ID3(path, translate=False, load_v1=False)
    except ID3NoHeaderError:
        info.note = "no ID3 tag"
        return info
    info.fields = {k: str(tag.get(fid, "")).strip() for k, (fid, _) in _ID3_FRAME.items()}
    info.fields["track"] = str(tag.get("TRCK", "")).split("/")[0].strip()
    info.date = str(tag.get("TYER", "") or tag.get("TDRC", "")).strip()
    info.tyer_frames = raw.count(b"TYER")
    info.tdrc_frames = raw.count(b"TDRC")
    info.has_cover = bool(tag.getall("APIC"))
    info.has_lyrics = bool(tag.getall("USLT"))
    return info


def _read_vorbis(path: Path, raw: bytes, stray_id3: bool) -> AudioInfo:
    info = AudioInfo(path=path)
    info.container = "vorbis"
    info.stray_id3 = stray_id3
    try:
        f = FLAC(BytesIO(raw[leading_id3_size(raw):])) if stray_id3 else FLAC(path)
    except Exception:
        info.unreadable = True
        info.note = "FLAC container could not be parsed"
        return info
    info.fields = {k: _first(f, key) for k, key in _VORBIS_KEY.items()}
    info.fields["track"] = _first(f, "tracknumber").split("/")[0].strip()
    info.date = _first(f, "date") or _first(f, "year")
    info.has_cover = bool(f.pictures)
    info.has_lyrics = any(_first(f, k) for k in ("lyrics", "unsyncedlyrics", "syncedlyrics"))
    return info


def read_info(path: Path) -> AudioInfo:
    raw = path.read_bytes()
    kind = sniff_container(raw)
    suffix = path.suffix.lower()

    if kind in ("flac", "flac_stray_id3"):
        info = _read_vorbis(path, raw, stray_id3=(kind == "flac_stray_id3"))
        if suffix == ".mp3":
            info.note = "named .mp3 but content is FLAC"
    elif kind == "mp3":
        info = _read_id3(path, raw)
        if suffix == ".flac":
            info.note = "named .flac but content is MP3 (ID3 + MPEG audio)"
    else:
        info = AudioInfo(path=path)
        info.unreadable = True
        info.note = "unrecognized audio container"

    info.id3v1 = len(raw) >= 128 and raw[-128:-125] == b"TAG"
    info.duration = media_duration(path)
    return info


def write_fields(path: Path, updates: dict[str, str]) -> None:
    """Update canonical fields; everything else (cover, lyrics, version) is preserved.

    Recognised keys: title, artist, albumartist, album, genre, track, date.
    Only the keys present in `updates` are touched. The parser is chosen from
    the file's magic bytes, so a mis-named file is still tagged correctly.
    """
    raw = path.read_bytes()
    kind = sniff_container(raw)

    if kind == "mp3" or kind == "unknown":
        version = raw[3] if raw[:3] == b"ID3" else 3  # default to widely-compatible v2.3
        try:
            tag = ID3(path, translate=False, load_v1=False)
        except ID3NoHeaderError:
            tag = ID3()
        for key, (fid, cls) in _ID3_FRAME.items():
            if key in updates:
                tag.setall(fid, [cls(encoding=3, text=updates[key])])
        if "track" in updates:
            tag.setall("TRCK", [TRCK(encoding=3, text=str(updates["track"]))])
        if "date" in updates:
            for fid in ID3_DATE_FRAMES:
                tag.delall(fid)
            if updates["date"]:
                date_cls = TDRC if version == 4 else TYER
                tag.setall(date_cls.__name__, [date_cls(encoding=3, text=updates["date"])])
        tag.save(path, v1=0, v2_version=version)
        _ = strip_id3v1(path)
        return

    if kind == "flac_stray_id3":
        _ = strip_leading_id3(path)
    f = FLAC(path)
    for key in ("title", "artist", "albumartist", "album", "genre"):
        if key in updates:
            f[_VORBIS_KEY[key]] = updates[key]
    if "track" in updates:
        f["tracknumber"] = str(updates["track"])
    if "date" in updates:
        if updates["date"]:
            f["date"] = updates["date"]
        else:
            f.pop("date", None)
            f.pop("year", None)
    f.save()
