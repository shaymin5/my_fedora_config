"""
Scan anime video files in a directory and output metadata as JSON.

Anime releases ship in many containers, not just MKV (MP4/M4V, AVI, TS,
WebM, ...). By default this script auto-detects the common video extensions
recursively. Pass --pattern to restrict the search to specific globs.

Usage:
    uv run python scan_media.py <directory>
    uv run python scan_media.py <directory> --pattern "*.mp4"
    uv run python scan_media.py <directory> --pattern "*.mkv,*.mp4"

Output JSON to stdout:
{
  "files": [
    {
      "path": "relative/path/to/file.mkv",
      "basename": "file",
      "tracks": [{"type": "video", "codec": "...", "properties": {...}}, ...],
      "container": {"duration_ns": 1372540000000, ...}
    }
  ]
}
"""
import json, subprocess, sys, os, glob as globmod
from typing import Any

# Containers anime releases commonly use. Keep this list broad so a stray
# .mp4/.m4v release is picked up without the caller having to think about it.
VIDEO_EXTS = {
    ".mkv", ".mp4", ".m4v", ".avi", ".mov", ".webm",
    ".ts", ".m2ts", ".flv", ".wmv", ".mpg", ".mpeg",
    ".rmvb", ".rm", ".ogv", ".3gp",
}


def scan_one(filepath: str) -> dict[str, Any]:
    """Return metadata for a single video file.

    Never returns None for an existing file: if probing fails we still emit
    the file (with an `error` field and empty tracks) so it is not silently
    dropped from the pipeline. A missing NFO is far worse than missing track
    info, and mkvmerge refuses some otherwise-fine files (e.g. exotic
    containers) while still being useful for reading the ones it knows.
    """
    basename = os.path.splitext(os.path.basename(filepath))[0]
    info = {"path": filepath, "basename": basename, "tracks": [], "container": {}}

    try:
        result = subprocess.run(
            ["mkvmerge", "-J", filepath],
            capture_output=True, text=True, timeout=60,
        )
    except Exception as e:  # mkvmerge missing or timed out
        info["error"] = f"probe failed: {e}"
        return info

    # mkvmerge -J prints valid JSON even when it exits non-zero (exit 1 just
    # means warnings), so parse stdout rather than gating on the return code.
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        info["error"] = (result.stderr or "").strip() or f"mkvmerge exit {result.returncode}"
        return info

    tracks = []
    for t in data.get("tracks", []):
        props = t.get("properties", {})
        tracks.append({
            "type": t.get("type"),
            "codec": t.get("codec"),
            "properties": {
                k: v for k, v in props.items()
                if k in (
                    "pixel_dimensions", "display_dimensions",
                    "audio_channels", "audio_sampling_frequency",
                    "audio_bits_per_sample", "language", "language_ietf",
                    "default_track", "track_name"
                )
            }
        })
    container = data.get("container", {}).get("properties", {})
    info["tracks"] = tracks
    info["container"] = {
        "duration_ns": container.get("duration", 0),
        "writing_application": container.get("writing_application", ""),
    }
    return info


def collect_files(directory: str, patterns: list[str]) -> list[str]:
    """Recursively collect files matching any glob pattern, de-duplicated."""
    seen, files = set(), []
    for pat in patterns:
        for p in sorted(globmod.glob(os.path.join(directory, "**", pat), recursive=True)):
            if os.path.isfile(p) and p not in seen:
                seen.add(p)
                files.append(p)
    return files


def main():
    args = sys.argv[1:]
    directory = "."
    patterns = None

    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--pattern="):
            patterns = [p.strip() for p in a.split("=", 1)[1].split(",") if p.strip()]
        elif a == "--pattern" and i + 1 < len(args):
            i += 1
            patterns = [p.strip() for p in args[i].split(",") if p.strip()]
        else:
            directory = a
        i += 1

    if not patterns:
        patterns = [f"*{ext}" for ext in sorted(VIDEO_EXTS)]

    results = []
    for filepath in collect_files(directory, patterns):
        info = scan_one(filepath)
        info["path"] = os.path.relpath(filepath, directory)
        results.append(info)

    print(json.dumps({"files": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
