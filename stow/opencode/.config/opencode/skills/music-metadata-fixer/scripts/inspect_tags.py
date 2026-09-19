#!/usr/bin/env python3
"""Diagnose embedded-metadata problems in a folder of MP3/FLAC files.

Usage:
    uv run --with mutagen python inspect_tags.py [DIR] [--recursive] [--json] [--signature S]

For every audio file it reports the canonical tag fields, the container and
ID3 version, legacy ID3v1 residue, duplicate date frames, an illegal leading
ID3 block on a FLAC, matching .lrc pairing, and junk-lyric signatures. It also
prints a filename-prefix histogram.

Single-level by default. Pass --recursive to walk subfolders (each file is
grouped under its folder); if the top level holds no audio but subfolders do,
the single-level run now says so and points at scan_tree.py instead of silently
reporting "0 files, all clean".

Read-only: never modifies anything.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from taglib_common import audio_dirs_below, iter_audio, iter_lrc, read_info

DEFAULT_JUNK_SIGNATURES = ("纯音乐，请欣赏",)


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-16", "gb18030", "shift_jis", "latin1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def parse_lrc_header(text: str) -> dict[str, str]:
    header: dict[str, str] = {}
    for tag in ("ti", "ar", "al", "total", "offset"):
        m = re.search(rf"\[{tag}:([^\]]*)\]", text, re.IGNORECASE)
        if m:
            header[tag] = m.group(1)
    return header


def inspect_one(path: Path, junk_signatures: tuple[str, ...], root: Path) -> dict[str, Any]:
    info = read_info(path)
    report: dict[str, Any] = {
        "file": path.name,
        "dir": "." if path.parent == root else str(path.parent.relative_to(root)),
        "container": info.container,
        "id3_version": info.version,
        "fields": {k: v for k, v in info.fields.items() if v},
        "date": info.date,
        "duration": round(info.duration, 1) if info.duration is not None else None,
        "has_cover": info.has_cover,
        "has_lyrics": info.has_lyrics,
        "id3v1": info.id3v1,
        "stray_id3": info.stray_id3,
        "note": info.note,
        "unreadable": info.unreadable,
        "tyer_frames": info.tyer_frames,
        "tdrc_frames": info.tdrc_frames,
        "lrc": None,
        "problems": [],
    }

    lrc = path.with_suffix(".lrc")
    if lrc.exists():
        text = read_text(lrc)
        header = parse_lrc_header(text)
        junk_hits = [sig for sig in junk_signatures if sig in text]
        lrc_info: dict[str, Any] = {"header": header, "junk_hits": junk_hits}
        if junk_hits:
            report["problems"].append(f"junk .lrc ({junk_hits[0]!r})")
        mp3_title = info.fields.get("title", "")
        lrc_title = header.get("ti", "")
        if lrc_title and mp3_title and lrc_title not in mp3_title and mp3_title not in lrc_title:
            report["problems"].append(f".lrc title mismatch ({lrc_title!r} vs {mp3_title!r})")
        total = header.get("total", "")
        if total.isdigit() and info.duration is not None:
            drift = abs(int(total) / 1000.0 - info.duration)
            lrc_info["duration_drift_s"] = round(drift, 1)
            if drift > 10:
                report["problems"].append(f".lrc duration off by {drift:.0f}s")
        report["lrc"] = lrc_info
    else:
        report["problems"].append("no matching .lrc")

    if info.id3v1:
        report["problems"].append("ID3v1 residue")
    if info.stray_id3:
        report["problems"].append("illegal leading ID3 block on FLAC")
    if info.unreadable:
        report["problems"].append("unreadable container")
    if info.note:
        report["problems"].append(info.note)
    if info.container == "id3" and info.version == 4 and info.tyer_frames:
        report["problems"].append("legacy TYER frame inside a v2.4 tag")
    if info.container == "id3" and info.version == 3 and info.tdrc_frames:
        report["problems"].append("TDRC frame inside a v2.3 tag")
    if info.tyer_frames and info.tdrc_frames:
        report["problems"].append("duplicate date frames (TYER + TDRC)")
    if not info.fields.get("title"):
        report["problems"].append("missing title")

    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--recursive", "-r", action="store_true", help="walk subfolders too")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--signature", action="append", default=None)
    args = ap.parse_args()

    directory = Path(str(args.directory)).expanduser().resolve()
    if not directory.is_dir():
        print(f"not a directory: {directory}", file=sys.stderr)
        return 2

    raw_signatures: list[str] | None = args.signature
    signatures = tuple(str(s) for s in raw_signatures) if raw_signatures else DEFAULT_JUNK_SIGNATURES
    recursive = bool(args.recursive)
    files = iter_audio(directory, recursive)
    lrc_files = iter_lrc(directory, recursive)
    reports = [inspect_one(p, signatures, directory) for p in files]

    if bool(args.json):
        print(json.dumps(reports, ensure_ascii=False, indent=2))
        return 0

    print(f"directory: {directory}")
    print(f"audio files: {len(files)}   lrc files: {len(lrc_files)}{'   (recursive)' if recursive else ''}\n")

    if not recursive and not files:
        below = audio_dirs_below(directory)
        if below:
            print("!! no audio directly in this folder, but these subfolders contain audio:")
            for d in below:
                print(f"     {d.relative_to(directory)}")
            print("   Run scan_tree.py for a map, or re-run with --recursive / once per folder.\n")

    prefix_hist: dict[str, int] = {}
    current_dir: str | None = None
    for report in reports:
        if report["dir"] != current_dir:
            current_dir = str(report["dir"])
            print(f"[{current_dir}]")
        stem = Path(str(report["file"])).stem
        prefix = stem.split(" - ", 1)[0] if " - " in stem else "(no prefix)"
        prefix_hist[prefix] = prefix_hist.get(prefix, 0) + 1

        version = report["id3_version"]
        print(f"{report['file']}  [{report['container']}{'' if version is None else ' v2.' + str(version)}]")
        for key, val in report["fields"].items():
            print(f"    {key}={val}")
        print(f"    date={report['date']}  cover={report['has_cover']}  lyrics={report['has_lyrics']}  dur={report['duration']}")
        if report["container"] == "id3":
            print(f"    id3v1={report['id3v1']}  TYER={report['tyer_frames']}  TDRC={report['tdrc_frames']}")
        if report["stray_id3"]:
            print("    stray_id3=True")
        if report["lrc"]:
            print(f"    lrc={report['lrc']['header']}")
        if report["problems"]:
            print(f"    !! {', '.join(report['problems'])}")

    print("\nfilename prefixes:")
    for prefix, count in sorted(prefix_hist.items(), key=lambda kv: -kv[1]):
        print(f"    {count:>3}  {prefix}")

    n_v1 = sum(1 for r in reports if r["id3v1"])
    n_dup = sum(1 for r in reports if r["tyer_frames"] and r["tdrc_frames"])
    n_junk = sum(1 for r in reports if r["lrc"] and r["lrc"]["junk_hits"])
    n_stray = sum(1 for r in reports if r["stray_id3"])
    print(f"\nsummary: {n_v1} ID3v1, {n_dup} duplicate dates, {n_stray} stray ID3 on FLAC, {n_junk} junk lrc")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
