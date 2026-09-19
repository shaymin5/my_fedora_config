#!/usr/bin/env python3
"""Bulk-set canonical tag fields on MP3/FLAC files, preserving the ID3 version.

Usage:
    uv run --with mutagen python set_fields.py [DIR] \
        --album "..." --artist "..." --albumartist "..." --genre "..." --date 2009 \
        [--title-from-filename] [--track-from-filename] \
        [--recursive] [--allow-cross-dir-constants] [--apply]

Options (any combination; only the ones you pass are written):
    --title TEXT            set title verbatim (applies to every file)
    --artist TEXT           set artist (TPE1 / vorbis artist)
    --albumartist TEXT      set album artist (TPE2 / vorbis albumartist)
    --album TEXT            set album (TALB / vorbis album)
    --genre TEXT            set genre (TCON / vorbis genre)
    --date TEXT             set date (TYER for ID3v2.3, TDRC for ID3v2.4, 'date' for FLAC)
    --title-from-filename   set title from the filename (part after ' - ', else strip a leading number)
    --track-from-filename   set track number from a leading number in the filename
    --recursive             also process audio in subfolders
    --allow-cross-dir-constants   override the cross-folder safety gate (see below)

`--title-from-filename` is the workhorse for the common "the filename holds the
correct native title but the tag is romanized" case. Everything not named here
(cover art, lyrics, other tags, audio) is left untouched, and the file's ID3
major version is never changed. Defaults to dry-run; pass --apply to write.

Cross-folder safety gate: `--title/--artist/--albumartist/--album/--genre/--date`
are *one value for the whole run*. Applying them recursively to a tree that
holds more than one folder of audio would stamp a single album/artist across
different releases. When that combination is detected the script refuses and
lists the folders, so you run it once per release instead; pass
`--allow-cross-dir-constants` only when you are sure every folder really shares
the value. The per-file options (`--title-from-filename`, `--track-from-filename`)
are always safe to combine with --recursive.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from taglib_common import iter_audio, read_info, write_fields

SHARED_FIELDS = ("title", "artist", "albumartist", "album", "genre", "date")


def title_from_filename(stem: str) -> str:
    if " - " in stem:
        return stem.split(" - ", 1)[1]
    m = re.match(r"^\s*\d+\s*[-._ ]+\s*(.+)$", stem)
    return m.group(1) if m else stem


def track_from_filename(stem: str) -> str | None:
    m = re.match(r"^\s*(\d+)", stem)
    return m.group(1) if m else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--title")
    ap.add_argument("--artist")
    ap.add_argument("--albumartist")
    ap.add_argument("--album")
    ap.add_argument("--genre")
    ap.add_argument("--date")
    ap.add_argument("--title-from-filename", action="store_true")
    ap.add_argument("--track-from-filename", action="store_true")
    ap.add_argument("--recursive", "-r", action="store_true", help="also process subfolders")
    ap.add_argument("--allow-cross-dir-constants", action="store_true",
                    help="allow shared --album/--artist/... across several folders")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    directory = Path(str(args.directory)).expanduser().resolve()
    base: dict[str, str] = {}
    for key in SHARED_FIELDS:
        value = getattr(args, key)
        if value is not None:
            base[key] = str(value)
    title_from_name = bool(args.title_from_filename)
    track_from_name = bool(args.track_from_filename)
    recursive = bool(args.recursive)
    allow_cross = bool(args.allow_cross_dir_constants)
    apply = bool(args.apply)

    if not base and not title_from_name and not track_from_name:
        print("nothing to do: pass at least one field option.")
        return 1

    files = iter_audio(directory, recursive)
    dirs = sorted({p.parent for p in files})

    if recursive and base and len(dirs) > 1 and not allow_cross:
        print("!! refusing to apply shared fields across several folders.")
        print(f"   shared fields: {sorted(base)}")
        print("   these fields hold ONE value for the whole run, so applying them to")
        print("   more than one release would stamp the wrong album/artist:")
        for d in dirs:
            print(f"     {d if d == directory else d.relative_to(directory)}")
        print("\n   Run set_fields.py once per folder, or pass --allow-cross-dir-constants")
        print("   if every folder truly shares the same value.")
        return 1

    print(f"{'APPLY' if apply else 'DRY-RUN'}  {directory}  ({len(files)} files"
          f"{', recursive' if recursive else ''})")
    print(f"updates: {base}  title_from_filename={title_from_name}  track_from_filename={track_from_name}\n")

    current_dir: Path | None = None
    for path in files:
        if path.parent != current_dir:
            current_dir = path.parent
            rel = "." if current_dir == directory else str(current_dir.relative_to(directory))
            print(f"[{rel}]")
        info = read_info(path)
        ver = f" v2.{info.version}" if info.version else ""
        updates = dict(base)
        if title_from_name:
            updates["title"] = title_from_filename(path.stem)
        if track_from_name:
            derived = track_from_filename(path.stem)
            if derived:
                updates["track"] = derived

        changes = {k: (info.fields.get(k, ""), v) for k, v in updates.items()
                   if info.fields.get(k, "") != v or k == "date"}
        print(f"{path.name}  [{info.container}{ver}]")
        for key, (old, new) in changes.items():
            print(f"    {key}: {old!r} -> {new!r}")
        if not changes:
            print("    (no change)")

        if apply and changes:
            write_fields(path, updates)

    if not apply:
        print("\nDry-run complete. Re-run with --apply to write.")
    else:
        print(f"\nDone. {len(files)} file(s) processed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
