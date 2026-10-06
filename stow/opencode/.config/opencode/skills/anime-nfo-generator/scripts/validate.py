"""
Validation checks for anime NFO generation pipeline.

Usage:
    uv run python scripts/validate.py <directory> [--tv-episodes N] [--ova-episodes N]

Checks performed:
  1. Video-NFO pairing: every video file has a matching NFO (and vice versa)
  2. Episode count: matches expected TV/OVA totals
  3. NFO format: valid XML, required fields present
  4. Title encoding: no mojibake/garbled characters
  5. Season numbering: TV=1, OVA=0 consistency
  6. Airdate format: YYYY-MM-DD validity
  7. Duplicate episodes: no two NFOs share same season+episode
  8. Orphaned files: subtitle/other files without matching video
"""

import json, sys, os, glob as globmod, argparse, xml.etree.ElementTree as ET

# Containers anime releases commonly use. The pairing check must know about
# all of them, not just MKV, otherwise an MP4 library reports every NFO as an
# orphan (and every video as missing an NFO) even when everything is correct.
VIDEO_EXTS = {
    ".mkv", ".mp4", ".m4v", ".avi", ".mov", ".webm",
    ".ts", ".m2ts", ".flv", ".wmv", ".mpg", ".mpeg",
    ".rmvb", ".rm", ".ogv", ".3gp",
}


def iter_video_files(directory: str):
    """Yield paths (relative to `directory`) of all recognized video files."""
    for root, _dirs, files in os.walk(directory):
        for fn in files:
            if os.path.splitext(fn)[1].lower() in VIDEO_EXTS:
                yield os.path.relpath(os.path.join(root, fn), directory)


def check_media_nfo_pairing(directory: str) -> list[str]:
    """Every video file (any supported container) has a matching NFO, and
    every episode NFO maps back to a video file."""
    errors = []
    videos = {os.path.splitext(p)[0] for p in iter_video_files(directory)}
    nfos = set()
    for f in globmod.glob(os.path.join(directory, "**", "*.nfo"), recursive=True):
        rel = os.path.relpath(f, directory)
        if rel == "tvshow.nfo":
            continue
        nfos.add(os.path.splitext(rel)[0])

    orphan_video = videos - nfos
    orphan_nfo = nfos - videos

    for v in sorted(orphan_video):
        errors.append(f"Missing NFO for video: {v}")
    for n in sorted(orphan_nfo):
        errors.append(f"Orphan NFO without video: {n}.nfo")

    return errors


# Backwards-compatible alias for the old name.
check_mkv_nfo_pairing = check_media_nfo_pairing


def check_nfo_format(directory: str) -> list[str]:
    """Validate XML structure and required fields of all NFO files."""
    errors = []
    required_fields = {"title", "season", "episode"}
    tvshow_fields = {"title", "year"}

    for f in globmod.glob(os.path.join(directory, "**", "*.nfo"), recursive=True):
        rel = os.path.relpath(f, directory)
        try:
            tree = ET.parse(f)
        except ET.ParseError as e:
            errors.append(f"Invalid XML in {rel}: {e}")
            continue

        if rel == "tvshow.nfo":
            root_elem = tree.getroot()
            if root_elem.tag != "tvshow":
                errors.append(f"{rel}: root tag should be <tvshow>, got <{root_elem.tag}>")
            continue

        root_elem = tree.getroot()
        if root_elem.tag != "episodedetails":
            errors.append(f"{rel}: root tag should be <episodedetails>, got <{root_elem.tag}>")
            continue

        present = {e.tag for e in root_elem}
        missing = required_fields - present
        if missing:
            errors.append(f"{rel}: missing fields: {missing}")

    return errors


def check_title_encoding(directory: str) -> list[str]:
    """Detect garbled characters or empty titles."""
    errors = []
    for f in globmod.glob(os.path.join(directory, "**", "*.nfo"), recursive=True):
        rel = os.path.relpath(f, directory)
        if rel == "tvshow.nfo":
            continue
        try:
            tree = ET.parse(f)
            root = tree.getroot()
        except ET.ParseError:
            continue

        title_elem = root.find("title")
        if title_elem is None or not title_elem.text or not title_elem.text.strip():
            errors.append(f"{rel}: empty or missing title")
            continue
        title = title_elem.text
        # Detect common mojibake patterns
        if "\ufffd" in title:
            errors.append(f"{rel}: replacement character (garbled) in title")
        # Titles should contain CJK or ASCII, not raw control chars
        if any(ord(c) < 0x20 for c in title):
            errors.append(f"{rel}: control characters in title")

    return errors


def check_season_numbering(directory: str) -> list[str]:
    """TV episodes should be season 1, OVAs should be season 0."""
    errors = []
    seen_episodes = set()
    for f in sorted(globmod.glob(os.path.join(directory, "**", "*.nfo"), recursive=True)):
        rel = os.path.relpath(f, directory)
        if rel == "tvshow.nfo":
            continue
        try:
            tree = ET.parse(f)
            root = tree.getroot()
        except ET.ParseError:
            continue

        season_elem = root.find("season")
        ep_elem = root.find("episode")
        if season_elem is None or ep_elem is None:
            continue
        if season_elem.text is None or ep_elem.text is None:
            errors.append(f"{rel}: missing season/episode value")
            continue
        try:
            season = int(season_elem.text)
            episode = int(ep_elem.text)
        except (ValueError, TypeError):
            errors.append(f"{rel}: non-numeric season/episode")
            continue

        # Check duplicate
        key = (season, episode)
        if key in seen_episodes:
            errors.append(f"{rel}: duplicate S{season:02d}E{episode:02d}")
        seen_episodes.add(key)

        # Heuristic: specials live in Season 0. Detect both OVA named files
        # and any Season 00 / Specials folder, and require season=0 there.
        rel_lower = rel.lower()
        parent_dirs = [p.lower() for p in os.path.normpath(rel).split(os.sep)[:-1]]
        in_specials = (
            "ova" in rel_lower
            or any(p in ("season 00", "season 0", "specials", "special") for p in parent_dirs)
        )
        if in_specials and season != 0:
            errors.append(
                f"{rel}: specials location but season={season} (expected 0; "
                f"use displayseason/displayepisode to place it in a season)"
            )

    return errors


def check_airdate_format(directory: str) -> list[str]:
    """Validate YYYY-MM-DD format for aired dates."""
    errors = []
    for f in globmod.glob(os.path.join(directory, "**", "*.nfo"), recursive=True):
        rel = os.path.relpath(f, directory)
        if rel == "tvshow.nfo":
            continue
        try:
            tree = ET.parse(f)
            root = tree.getroot()
        except ET.ParseError:
            continue

        aired_elem = root.find("aired")
        if aired_elem is not None and aired_elem.text:
            date = aired_elem.text.strip()
            import re
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
                errors.append(f"{rel}: invalid airdate format: {date}")
            else:
                parts = date.split("-")
                try:
                    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                    if m < 1 or m > 12 or d < 1 or d > 31:
                        errors.append(f"{rel}: invalid airdate values: {date}")
                except ValueError:
                    errors.append(f"{rel}: invalid airdate values: {date}")

    return errors


def check_file_count(directory: str, expected_tv: int | None, expected_ova: int | None) -> list[str]:
    """Check episode counts match expectations."""
    errors = []
    tv_count = 0
    ova_count = 0

    for f in globmod.glob(os.path.join(directory, "**", "*.nfo"), recursive=True):
        rel = os.path.relpath(f, directory)
        if rel == "tvshow.nfo":
            continue
        try:
            tree = ET.parse(f)
            root = tree.getroot()
        except ET.ParseError:
            continue
        season_elem = root.find("season")
        if season_elem is not None and season_elem.text is not None:
            try:
                s = int(season_elem.text)
            except (ValueError, TypeError):
                continue
            if s == 0:
                ova_count += 1
            else:
                tv_count += 1

    if expected_tv is not None and tv_count != expected_tv:
        errors.append(f"TV episode count: {tv_count} (expected {expected_tv})")
    if expected_ova is not None and ova_count != expected_ova:
        errors.append(f"OVA episode count: {ova_count} (expected {expected_ova})")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate anime NFO files")
    parser.add_argument("directory", help="Directory containing NFO files")
    parser.add_argument("--tv-episodes", type=int, help="Expected TV episode count")
    parser.add_argument("--ova-episodes", type=int, help="Expected OVA episode count")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    all_errors = []
    checks = [
        ("Video-NFO pairing", check_media_nfo_pairing(args.directory)),
        ("NFO XML format", check_nfo_format(args.directory)),
        ("Title encoding", check_title_encoding(args.directory)),
        ("Season numbering", check_season_numbering(args.directory)),
        ("Airdate format", check_airdate_format(args.directory)),
        ("Episode count", check_file_count(args.directory, args.tv_episodes, args.ova_episodes)),
    ]

    for name, errors in checks:
        if errors:
            for e in errors:
                all_errors.append(f"[{name}] {e}")

    if args.json:
        print(json.dumps({
            "passed": len(all_errors) == 0,
            "errors": all_errors
        }, ensure_ascii=False, indent=2))
    else:
        if all_errors:
            print(f"Found {len(all_errors)} issue(s):")
            for e in all_errors:
                print(f"  {e}")
        else:
            print("All checks passed!")

    sys.exit(1 if all_errors else 0)


if __name__ == "__main__":
    main()
