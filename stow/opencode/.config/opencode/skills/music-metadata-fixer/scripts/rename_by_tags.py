#!/usr/bin/env python3
"""Rename MP3/FLAC files (and their .lrc) from their embedded tags.

Usage:
    uv run --with mutagen python rename_by_tags.py [DIR] \
        --pattern "{track:02d} {artist} - {title}" --sync-lrc [--recursive] [--apply]

Pattern fields: {track} (int), {title}, {artist}, {album}.
  --artist-field artist|albumartist   which tag feeds {artist} (default: artist)

Files are named from their TAGS, not by editing the old name, so tags and names
stay consistent. With --sync-lrc the matching .lrc is renamed in lockstep --
players match lyrics by identical basename, so renaming only the audio silently
breaks lyrics. Defaults to dry-run; pass --apply to rename.

This is safe to run with --recursive: each file is named from its own tags, so
different albums/folders do not affect each other. Collision checks are done per
folder (two folders may legitimately contain the same filename), and every
folder is validated before anything is renamed.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from taglib_common import iter_audio, read_info

ILLEGAL = str.maketrans({"/": "／", "\\": "＼", "\0": ""})

Plan = tuple[Path, Path, Path | None, Path | None]  # old_audio, new_audio, old_lrc, new_lrc


def field_values(path: Path, artist_field: str) -> dict[str, object]:
    info = read_info(path)
    track_txt = info.fields.get("track", "")
    return {
        "track": int(track_txt) if track_txt.isdigit() else None,
        "title": info.fields.get("title", ""),
        "artist": info.fields.get(artist_field, ""),
        "album": info.fields.get("album", ""),
    }


def build_plan(files: list[Path], pattern: str, artist_field: str, root: Path) -> dict[Path, list[Plan]]:
    per_dir: dict[Path, list[Plan]] = {}
    for path in files:
        values = field_values(path, artist_field)
        if values["track"] is None:
            print(f"!! skip {path.name}: no usable track number")
            continue
        new_stem = pattern.format(**values).translate(ILLEGAL)
        new_audio = path.with_name(new_stem + path.suffix)
        old_lrc = path.with_suffix(".lrc")
        new_lrc = old_lrc.with_name(new_stem + ".lrc") if old_lrc.exists() else None
        if new_audio == path and (new_lrc is None or new_lrc == old_lrc):
            print(f"skip {path.name}: name already matches pattern")
            continue
        rel = "" if path.parent == root else f"{path.parent.relative_to(root)}/"
        print(f"{rel}{path.stem}\n   -> {new_stem}")
        per_dir.setdefault(path.parent, []).append(
            (path, new_audio, old_lrc if old_lrc.exists() else None, new_lrc)
        )
    return per_dir


def validate(per_dir: dict[Path, list[Plan]]) -> list[str]:
    problems: list[str] = []
    for folder, items in per_dir.items():
        originals = {p.name for p, *_ in items}
        originals |= {old_lrc.name for _, _, old_lrc, _ in items if old_lrc is not None}
        targets = [t.name for _, t, _, _ in items] + [t.name for *_, t in items if t]
        if len(set(targets)) != len(targets):
            problems.append(f"{folder}: target name collision")
        existing = {q.name for q in folder.iterdir()}
        clash = [name for name in targets if name in existing and name not in originals]
        if clash:
            problems.append(f"{folder}: target already exists: {clash}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--pattern", default="{track:02d} {artist} - {title}")
    ap.add_argument("--artist-field", default="artist", choices=["artist", "albumartist"])
    ap.add_argument("--sync-lrc", action="store_true", help="rename matching .lrc too")
    ap.add_argument("--recursive", "-r", action="store_true", help="walk subfolders too")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    directory = Path(str(args.directory)).expanduser().resolve()
    pattern = str(args.pattern)
    artist_field = str(args.artist_field)
    recursive = bool(args.recursive)
    apply = bool(args.apply)
    sync_lrc = bool(args.sync_lrc)

    if not directory.is_dir():
        print(f"not a directory: {directory}")
        return 2

    files = iter_audio(directory, recursive)
    print(f"{'APPLY' if apply else 'DRY-RUN'}  {directory}  ({len(files)} files"
          f"{', recursive' if recursive else ''})")
    print(f"pattern: {pattern}   artist from: {artist_field}\n")

    per_dir = build_plan(files, pattern, artist_field, directory)
    if not per_dir:
        print("nothing to do.")
        return 0

    problems = validate(per_dir)
    if problems:
        print("!! abort:")
        for p in problems:
            print(f"   {p}")
        return 1

    if not apply:
        print("\nDry-run complete, no collision. Re-run with --apply.")
        return 0

    renamed = 0
    missing: list[str] = []
    for folder, items in per_dir.items():
        for old_audio, new_audio, old_lrc, new_lrc in items:
            _ = old_audio.rename(new_audio)
            if sync_lrc and old_lrc and new_lrc:
                _ = old_lrc.rename(new_lrc)
            renamed += 1
        if sync_lrc:
            missing += [
                p.name for p in sorted(folder.iterdir())
                if p.suffix.lower() in {".mp3", ".flac"} and not p.with_suffix(".lrc").exists()
            ]

    print(f"\nDone. renamed {renamed} file(s).")
    if missing:
        print(f"warning: audio without matching .lrc after rename: {missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
