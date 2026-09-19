#!/usr/bin/env python3
"""Map a music folder tree: which subfolders hold audio, and how they differ.

Usage:
    uv run --with mutagen python scan_tree.py [DIR] [--json] [--signature S]

Read-only. The single-level scripts (`compare_names`, `inspect_tags`,
`set_fields`, `rename_by_tags`, `clean_*`) only look at files directly inside
DIR. Real collections are nested -- ``<root>/<album>/`` or
``<root>/<album>/Disc 1/`` -- so pointing them at the parent finds nothing and
can misleadingly look "clean". Run this first whenever DIR contains subfolders.

For every folder that directly holds audio it reports the tag situation inside
that folder, flags folders that look like one release split across discs (ask the
user before treating them as one album), and lists subfolders with no audio
(scans / artwork / drama) so they are not mistaken for music.

Nothing here is a decision -- it is the map you read before deciding, per folder,
which source is authoritative.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from taglib_common import AUDIO_EXTS, discover_audio_dirs, iter_audio, iter_lrc, read_info
from inspect_tags import DEFAULT_JUNK_SIGNATURES, read_text

DISC_DIR = re.compile(r"^(?:disc|disk|cd|碟|ディスク)\s*[-_.]?\s*\d+$", re.IGNORECASE)


def _distinct(values: list[str]) -> list[str]:
    return sorted({v for v in values if v})


def _show(values: list[str], limit: int = 3) -> str:
    if not values:
        return "(none)"
    if len(values) <= limit:
        return " | ".join(values)
    return f"{len(values)} distinct values"


def folder_report(folder: Path, root: Path, signatures: tuple[str, ...],
                  all_dirs: list[Path]) -> dict[str, Any]:
    files = iter_audio(folder)
    infos = [read_info(p) for p in files]

    titles = [i.fields.get("title", "") for i in infos]
    duplicates = [t for t, n in Counter(t for t in titles if t).items() if n > 1]
    tracks = [i.fields.get("track", "") for i in infos]
    dup_tracks = [t for t, n in Counter(t for t in tracks if t).items() if n > 1]

    lrcs = iter_lrc(folder)
    junk_lrc = [p.name for p in lrcs if any(s in read_text(p) for s in signatures)]

    child_audio = [d for d in all_dirs if d != folder and folder in d.parents]
    siblings_disc = sorted(
        d.name for d in all_dirs
        if d.parent == folder.parent and d != folder and DISC_DIR.match(d.name)
    )

    rel = "." if folder == root else str(folder.relative_to(root))
    return {
        "dir": rel,
        "n_audio": len(files),
        "n_mp3": sum(1 for p in files if p.suffix.lower() == ".mp3"),
        "n_flac": sum(1 for p in files if p.suffix.lower() == ".flac"),
        "versions": sorted({f"v2.{i.version}" if i.version else i.container for i in infos}),
        "titles": len([t for t in titles if t]),
        "dup_titles": duplicates,
        "tracks": len([t for t in tracks if t]),
        "dup_tracks": dup_tracks,
        "albums": _distinct([i.fields.get("album", "") for i in infos]),
        "artists": _distinct([i.fields.get("artist", "") for i in infos]),
        "albumartists": _distinct([i.fields.get("albumartist", "") for i in infos]),
        "genres": _distinct([i.fields.get("genre", "") for i in infos]),
        "dates": _distinct([i.date for i in infos]),
        "n_lrc": len(lrcs),
        "junk_lrc": junk_lrc,
        "id3v1": sum(1 for i in infos if i.id3v1),
        "dup_dates": sum(1 for i in infos if i.tyer_frames and i.tdrc_frames),
        "stray_id3": sum(1 for i in infos if i.stray_id3),
        "missing_title": sum(1 for i in infos if not i.fields.get("title")),
        "unreadable": sum(1 for i in infos if i.unreadable),
        "notes": [f"{p.name}: {i.note}" for p, i in zip(files, infos) if i.note],
        "has_subdirs": any(d.is_dir() for d in folder.iterdir()),
        "child_audio_dirs": [str(d.relative_to(root)) for d in sorted(child_audio)],
        "disc_like": bool(DISC_DIR.match(folder.name)),
        "disc_siblings": siblings_disc,
    }


def non_music_dirs(root: Path, audio_dirs: list[Path]) -> list[str]:
    known = set(audio_dirs)
    out: list[str] = []
    for d in sorted(p for p in root.rglob("*") if p.is_dir()):
        if d in known:
            continue
        if any(a.parent == d or d in a.parents for a in audio_dirs):
            continue
        out.append(str(d.relative_to(root)))
    return out


def multi_disc_groups(audio_dirs: list[Path], root: Path) -> list[dict[str, Any]]:
    by_parent: dict[Path, list[Path]] = {}
    for d in audio_dirs:
        by_parent.setdefault(d.parent, []).append(d)
    groups: list[dict[str, Any]] = []
    for parent, dirs in by_parent.items():
        discs = sorted(d for d in dirs if DISC_DIR.match(d.name))
        if len(discs) >= 2:
            where = "." if parent == root else str(parent.relative_to(root))
            groups.append({"parent": where, "discs": [d.name for d in discs]})
    return groups


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--signature", action="append", default=None)
    args = ap.parse_args()

    directory = Path(str(args.directory)).expanduser().resolve()
    if not directory.is_dir():
        print(f"not a directory: {directory}", file=sys.stderr)
        return 2

    raw = args.signature
    signatures = tuple(str(s) for s in raw) if raw else DEFAULT_JUNK_SIGNATURES

    all_dirs = discover_audio_dirs(directory)
    top = iter_audio(directory)
    reports = [folder_report(d, directory, signatures, all_dirs) for d in all_dirs]
    non_music = non_music_dirs(directory, all_dirs)
    groups = multi_disc_groups(all_dirs, directory)

    if bool(args.json):
        print(json.dumps({
            "root": str(directory),
            "top_level_audio": len(top),
            "audio_dirs": reports,
            "non_music_dirs": non_music,
            "multi_disc_groups": groups,
        }, ensure_ascii=False, indent=2))
        return 0

    print(f"root: {directory}")
    print(f"  {len(all_dirs)} folder(s) contain audio; {len(top)} audio file(s) at the top level\n")

    if not all_dirs:
        print("no audio found anywhere under this path.")
        if non_music:
            print(f"non-music subfolders: {', '.join(non_music)}")
        return 0

    if not top and len(all_dirs) >= 1:
        print("!! the top level holds NO audio, but subfolders do.")
        print("   A single-level scan of this path would find 0 files and look clean.")
        print("   Run the other scripts with --recursive, or run them once per folder below.\n")

    for r in reports:
        v = ",".join(r["versions"]) or "?"
        lrc = f"{r['n_lrc']} lrc"
        if r["junk_lrc"]:
            lrc += f" ({len(r['junk_lrc'])} junk)"
        print(f"[{r['dir']}]  {r['n_audio']} audio ({r['n_mp3']} mp3/{r['n_flac']} flac, {v})   {lrc}")
        print(f"    album: {_show(r['albums'])}   artist: {_show(r['artists'])}   "
              f"albumartist: {_show(r['albumartists'])}")
        print(f"    genre: {_show(r['genres'])}   date: {_show(r['dates'])}   "
              f"titles: {r['titles']}   tracks: {r['tracks']}")
        probs = []
        if r["id3v1"]:
            probs.append(f"{r['id3v1']} ID3v1")
        if r["dup_dates"]:
            probs.append(f"{r['dup_dates']} dup date")
        if r["stray_id3"]:
            probs.append(f"{r['stray_id3']} stray ID3")
        if r["missing_title"]:
            probs.append(f"{r['missing_title']} missing title")
        if r["unreadable"]:
            probs.append(f"{r['unreadable']} unreadable")
        if r["notes"]:
            probs.extend(r["notes"])
        if r["dup_titles"]:
            probs.append(f"duplicate titles {r['dup_titles']}")
        if r["dup_tracks"]:
            probs.append(f"duplicate tracks {r['dup_tracks']}")
        if r["junk_lrc"]:
            probs.append(f"junk lrc {r['junk_lrc']}")
        print(f"    problems: {', '.join(probs) if probs else 'none'}")
        if r["child_audio_dirs"]:
            print(f"    also has audio in subfolders: {', '.join(r['child_audio_dirs'])}")
        if r["disc_like"] and r["disc_siblings"]:
            print(f"    ?? disc-like folder; siblings: {', '.join(r['disc_siblings'])}")
        print()

    if groups:
        print("!! possible multi-disc release(s) -- confirm with the user whether these are")
        print("   ONE album split across discs (share album/albumartist) or separate releases:")
        for g in groups:
            print(f"   - {g['parent']}: {', '.join(g['discs'])}")
        print()

    if non_music:
        print(f"subfolders with no audio (not music, leave alone): {', '.join(non_music)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
