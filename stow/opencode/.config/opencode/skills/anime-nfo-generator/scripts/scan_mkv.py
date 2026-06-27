"""
Scan MKV files in a directory and output metadata as JSON.

Usage:
    uv run python scan_mkv.py <directory> [--pattern "*.mkv"]
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


def scan_mkv(filepath: str) -> dict | None:
    """Run mkvmerge -J on a single MKV file and return parsed result."""
    try:
        result = subprocess.run(
            ["mkvmerge", "-J", filepath],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
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
        return {
            "path": filepath,
            "basename": os.path.splitext(os.path.basename(filepath))[0],
            "tracks": tracks,
            "container": {
                "duration_ns": container.get("duration", 0),
                "writing_application": container.get("writing_application", ""),
            }
        }
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        return None


def main():
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    pattern = "*.mkv"
    for a in sys.argv[2:]:
        if a.startswith("--pattern="):
            pattern = a.split("=", 1)[1]

    results = []
    for filepath in sorted(globmod.glob(os.path.join(directory, "**", pattern), recursive=True)):
        info = scan_mkv(filepath)
        if info:
            info["path"] = os.path.relpath(filepath, directory)
            results.append(info)

    print(json.dumps({"files": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
