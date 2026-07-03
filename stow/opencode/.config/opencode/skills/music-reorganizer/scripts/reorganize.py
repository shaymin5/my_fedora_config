#!/usr/bin/env python3
"""Music collection reorganizer — flatten multi-disc, tag singles, separate non-music.

Run this with: uv run python3 reorganize.py --base <path>

Steps (always in order):
  1. Separate: move specified non-music dirs to other/
  2. Flatten: move files from Disc N/ subdirs into parent, prefixing filename with "N-"
  3. Tag: add RELEASETYPE=single TXXX frame to all MP3s under singles/

See SKILL.md for the full workflow.
"""

import argparse
import os
import re
import shutil

# ─── step: separate non-music ────────────────────────────────────────────

def step_separate(base: str, non_music: list[dict]) -> None:
    """Move non-music directories to other/ preserving category hierarchy."""
    other = os.path.join(base, "other")
    for item in non_music:
        src = os.path.join(base, item["src"])
        dst = os.path.join(other, item["dst"])
        if not os.path.exists(src):
            print(f"  [SKIP] not found: {item['src']}")
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
        print(f"  [MOVE] {item['src']} -> other/{item['dst']}")


# ─── step: flatten multi-disc ────────────────────────────────────────────

DISC_RE = re.compile(r"^Disc (\d+)$")


def step_flatten(base: str) -> None:
    """Flatten Disc N/ subdirectories into their parent album directory.

    Files are renamed from '01. Song.mp3' to '1-01. Song.mp3'.
    Cover images (jpg/png) move to parent only if parent lacks one.
    """
    for root, dirs, files in os.walk(base, topdown=False):
        basename = os.path.basename(root)
        m = DISC_RE.match(basename)
        if not m:
            continue

        disc_num = int(m.group(1))
        parent = os.path.dirname(root)
        print(f"  Flattening: {os.path.relpath(root, base)} -> {os.path.relpath(parent, base)}")

        for fname in sorted(os.listdir(root)):
            src = os.path.join(root, fname)
            if fname.lower().endswith((".mp3", ".flac", ".m4a", ".aac", ".ogg", ".wma", ".wav")):
                new_name = f"{disc_num}-{fname}"
                dst = os.path.join(parent, new_name)
                if os.path.exists(dst):
                    print(f"    [WARN] collision, skipping: {new_name}")
                    continue
                shutil.move(src, dst)
            elif fname.lower().endswith((".jpg", ".jpeg", ".png")):
                parent_has_cover = any(
                    c.lower().endswith((".jpg", ".jpeg", ".png"))
                    for c in os.listdir(parent)
                )
                if not parent_has_cover:
                    shutil.move(src, os.path.join(parent, fname))
                else:
                    os.remove(src)
            else:
                dst = os.path.join(parent, fname)
                if not os.path.exists(dst):
                    shutil.move(src, dst)

        remaining = os.listdir(root)
        if remaining:
            print(f"    [WARN] not empty, leaving: {remaining}")
        else:
            os.rmdir(root)

    # Verify there are no more Disc directories
    leftover = []
    for root, dirs, files in os.walk(base):
        for d in dirs:
            if DISC_RE.match(d):
                leftover.append(os.path.join(root, d))
    if leftover:
        print(f"  [WARN] {len(leftover)} Disc dir(s) still exist (check permissions)")


# ─── step: tag singles ───────────────────────────────────────────────────

def step_tag_singles(base: str, singles_path: str) -> None:
    """Add RELEASETYPE=single TXXX frame to all MP3s under the singles tree."""
    import mutagen
    from mutagen.id3 import ID3, TXXX

    target_dir = os.path.join(base, singles_path)
    count = 0

    for root, dirs, files in os.walk(target_dir):
        for fname in files:
            if not fname.lower().endswith(".mp3"):
                continue
            fpath = os.path.join(root, fname)
            try:
                audio = mutagen.File(fpath)
                if audio is None:
                    print(f"  [SKIP] cannot read: {os.path.relpath(fpath, base)}")
                    continue
                if audio.tags is None:
                    audio.add_tags()
                existing = audio.tags.getall("TXXX:RELEASETYPE")
                if existing and any("single" in str(e) for e in existing):
                    continue
                audio.tags.add(TXXX(encoding=3, desc="RELEASETYPE", text="single"))
                audio.save()
                count += 1
            except Exception as e:
                print(f"  [ERROR] {os.path.relpath(fpath, base)}: {e}")

    print(f"  Tagged {count} files with RELEASETYPE=single")


# ─── main ─────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Music collection reorganizer")
    p.add_argument("--base", required=True, help="Root directory of the collection")
    p.add_argument("--non-music", nargs="*", default=[],
                   help="Paths under base/ to move to other/ (e.g. 'SOUNDTRACKS/S2_WORKS')")
    p.add_argument("--singles", default="SINGLES",
                   help="Subdirectory containing singles (default: SINGLES)")
    p.add_argument("--skip-separate", action="store_true")
    p.add_argument("--skip-flatten", action="store_true")
    p.add_argument("--skip-tag", action="store_true")
    args = p.parse_args()

    base = args.base

    if not args.skip_separate and args.non_music:
        print("=" * 60)
        print("Step: Separating non-music content")
        print("=" * 60)
        step_separate(base, args.non_music)

    if not args.skip_flatten:
        print("=" * 60)
        print("Step: Flattening multi-disc albums")
        print("=" * 60)
        step_flatten(base)

    if not args.skip_tag:
        print("=" * 60)
        print("Step: Tagging singles with RELEASETYPE")
        print("=" * 60)
        step_tag_singles(base, args.singles)

    print("\nAll done.")


if __name__ == "__main__":
    main()
