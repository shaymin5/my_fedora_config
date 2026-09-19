#!/usr/bin/env python3
"""Remove legacy tag junk from MP3/FLAC files, preserving the ID3 version.

Usage:
    uv run --with mutagen python clean_legacy_tags.py [DIR] [--recursive] [--year YYYY] [--apply]

MP3  - strip the trailing 128-byte ID3v1 block, and collapse any duplicate /
       version-mismatched date frames into ONE frame that matches the file's
       own ID3 version: v2.3 keeps a single TYER, v2.4 keeps a single TDRC.
       The file's major version is never changed.
FLAC - remove an illegal ID3v2 block sitting in front of the Vorbis comments
       (a common tagger mistake), if present.

Everything else (cover art, lyrics, other frames) is preserved.
Defaults to dry-run; pass --apply to write. --recursive is safe here: the
operation depends only on each file's own container/version, not on any shared
per-album value.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from taglib_common import iter_audio, read_info, strip_leading_id3, write_fields


def needs_cleanup(info) -> bool:
    if info.container == "id3":
        expected = 1 if info.date else 0
        wrong_version_date = (info.version == 4 and info.tyer_frames > 0) or (
            info.version == 3 and info.tdrc_frames > 0
        )
        return (
            info.id3v1
            or (info.tyer_frames + info.tdrc_frames) != expected
            or wrong_version_date
        )
    return info.stray_id3


def fix_file(path: Path, year: str | None, apply: bool) -> tuple[bool, str]:
    info = read_info(path)
    target_date = year or info.date
    if not apply:
        return needs_cleanup(info), target_date or "(none)"

    if info.container == "id3":
        updates = {"date": target_date} if target_date else {}
        write_fields(path, updates)
    else:
        if info.stray_id3:
            strip_leading_id3(path)
    after = read_info(path)
    return needs_cleanup(info), after.date or "(none)"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--recursive", "-r", action="store_true", help="walk subfolders too")
    ap.add_argument("--year", default=None, help="date to write (default: keep existing)")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    directory = Path(str(args.directory)).expanduser().resolve()
    year = str(args.year) if args.year else None
    recursive = bool(args.recursive)
    apply = bool(args.apply)
    files = iter_audio(directory, recursive)
    print(f"{'APPLY' if apply else 'DRY-RUN'}  {directory}  ({len(files)} files"
          f"{', recursive' if recursive else ''})\n")

    current_dir: Path | None = None
    for path in files:
        if path.parent != current_dir:
            current_dir = path.parent
            rel = "." if current_dir == directory else str(current_dir.relative_to(directory))
            print(f"[{rel}]")
        info = read_info(path)
        need = needs_cleanup(info)
        ver = f" v2.{info.version}" if info.version else ""
        note = (
            f"container={info.container}{ver} "
            f"v1={info.id3v1} TYER={info.tyer_frames} TDRC={info.tdrc_frames} "
            f"stray_id3={info.stray_id3}"
        )
        if apply:
            fix_file(path, year, True)
            print(f"OK  {path.name}: {note} -> date={read_info(path).date or '(none)'}")
        else:
            flag = "NEEDS" if need else "clean"
            print(f"{flag}  {path.name}: {note}")

    if not apply:
        print("\nDry-run complete. Re-run with --apply to write.")
    else:
        print(f"\nDone. {len(files)} file(s) processed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
