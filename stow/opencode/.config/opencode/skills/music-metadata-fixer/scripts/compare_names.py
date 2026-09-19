#!/usr/bin/env python3
"""Reconcile filenames against embedded tags and hint at which side to trust.

Usage:
    uv run --with mutagen python compare_names.py [DIR] [--recursive] [--json]

Read-only. For every audio file it shows the name-derived title/artist/track
next to the tag-derived ones, marks whether they agree, and — when they
disagree — gives a *hint* (never a decision) about which source looks more
authoritative based on writing system. Use this before changing anything: the
whole point is to find out whether it's the filename that is wrong, the tags
that are wrong, or both, instead of assuming.

Single-level by default. Pass --recursive to walk subfolders (each row is
labelled with its folder); if the top level holds no audio but subfolders do,
the single-level run now says so instead of silently reporting "0 files".

A hint is not ground truth. If both sides look plausible, or the script says
"needs external check", stop and either look up the official release or ask the
user which spelling they want.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from taglib_common import audio_dirs_below, iter_audio, read_info

TRACK_PREFIX = re.compile(r"^\s*(\d{1,3})\s*[-._ ]?\s*(.*)$")


def scripts_of(text: str) -> set[str]:
    found: set[str] = set()
    for ch in text:
        o = ord(ch)
        if 0x3040 <= o <= 0x309F:
            found.add("kana")
        elif 0x30A0 <= o <= 0x30FF:
            found.add("kana")
        elif 0x4E00 <= o <= 0x9FFF:
            found.add("han")
        elif 0xAC00 <= o <= 0xD7AF:
            found.add("hangul")
        elif ch.isascii() and ch.isalpha():
            found.add("latin")
    return found


def parse_filename(stem: str) -> dict[str, Any]:
    track = None
    rest = stem
    m = TRACK_PREFIX.match(stem)
    if m:
        track = int(m.group(1))
        rest = m.group(2)
    artist = title = ""
    if " - " in rest:
        artist, title = rest.split(" - ", 1)
    else:
        title = rest
    return {"track": track, "artist": artist.strip(), "title": title.strip()}


def hint(fn_title: str, tag_title: str) -> str:
    if fn_title == tag_title:
        return "consistent"
    fn_scripts, tag_scripts = scripts_of(fn_title), scripts_of(tag_title)
    native = {"kana", "han", "hangul"}
    fn_native = bool(fn_scripts & native)
    tag_native = bool(tag_scripts & native)
    if fn_native and not tag_native:
        return "filename looks native, tag looks romanized -> filename may be authoritative (verify)"
    if tag_native and not fn_native:
        return "tag looks native, filename looks romanized -> tag may be authoritative (verify)"
    if fn_scripts == tag_scripts:
        return "both same writing system but differ -> needs external check / ask user"
    return "mixed scripts -> needs external check / ask user"


def analyse(path: Path, root: Path) -> dict[str, Any]:
    info = read_info(path)
    name = parse_filename(path.stem)
    tag = info.fields
    tag_track = int(tag["track"]) if tag.get("track", "").isdigit() else None
    return {
        "file": path.name,
        "dir": "." if path.parent == root else str(path.parent.relative_to(root)),
        "filename": name,
        "tag": {"title": tag.get("title", ""), "artist": tag.get("artist", ""), "track": tag_track},
        "title_match": name["title"] == tag.get("title", ""),
        "artist_match": bool(name["artist"]) and name["artist"] == tag.get("artist", ""),
        "track_match": name["track"] is not None and name["track"] == tag_track,
        "hint": hint(name["title"], tag.get("title", "")),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--recursive", "-r", action="store_true", help="walk subfolders too")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    directory = Path(str(args.directory)).expanduser().resolve()
    if not directory.is_dir():
        print(f"not a directory: {directory}", file=sys.stderr)
        return 2

    recursive = bool(args.recursive)
    files = iter_audio(directory, recursive)
    rows = [analyse(p, directory) for p in files]

    if bool(args.json):
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    print(f"directory: {directory}  ({len(rows)} files{', recursive' if recursive else ''})\n")

    if not recursive and not files:
        below = audio_dirs_below(directory)
        if below:
            print("!! no audio directly in this folder, but these subfolders contain audio:")
            for d in below:
                print(f"     {d.relative_to(directory)}")
            print("   Run scan_tree.py for a map, or re-run with --recursive / once per folder.\n")

    current_dir: str | None = None
    full_agree = 0
    for r in rows:
        if r["dir"] != current_dir:
            current_dir = r["dir"]
            print(f"[{current_dir}]")
        fn, tg = r["filename"], r["tag"]
        flags = []
        flags.append("title=" + ("ok" if r["title_match"] else "DIFF"))
        flags.append("artist=" + ("ok" if r["artist_match"] else "DIFF"))
        flags.append("track=" + ("ok" if r["track_match"] else "DIFF"))
        if r["title_match"] and r["track_match"]:
            full_agree += 1
        print(f"{r['file']}")
        print(f"    filename: title={fn['title']!r} artist={fn['artist']!r} track={fn['track']}")
        print(f"    tag     : title={tg['title']!r} artist={tg['artist']!r} track={tg['track']}")
        print(f"    [{' '.join(flags)}]  hint: {r['hint']}")

    print(f"\n{full_agree}/{len(rows)} files have filename title+track matching the tags")
    print(
        "\nNext step is a judgement call, not automatic:\n"
        "  - if one side is clearly native and the other romanized, that side is usually right, but confirm;\n"
        "  - if both look plausible, look up the official release (label / Bangumi / Wikipedia / MusicBrainz)\n"
        "    and, when still unsure, ask the user which spelling and ordering they want before changing anything."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
