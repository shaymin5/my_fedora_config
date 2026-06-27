"""
Generate Kodi/Jellyfin compatible NFO files from structured episode data.

Usage:
    uv run python generate_nfo.py <spec.json>

Spec JSON format:
{
  "directory": "/path/to/anime",
  "tvshow": {
    "title": "地獄先生ぬ〜べ〜",
    "originaltitle": "Jigoku Sensei Nūbē",
    "year": 1996,
    "premiered": "1996-04-13",
    "studio": "Toei Animation",
    "genres": ["Animation", "Comedy", "Horror"]
  },
  "episodes": [
    {
      "mkv_basename": "[Group][Series][01][...]",
      "title": "恐怖の新学期！謎の鬼の手",
      "season": 1,
      "episode": 1,
      "aired": "1996-04-13"
    }
  ]
}

Creates:
  - <directory>/tvshow.nfo
  - <directory>/<mkv_basename>.nfo for each episode
"""
import json, sys, os


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") \
            .replace('"', "&quot;").replace("'", "&apos;")


def write_tvshow_nfo(directory: str, tvshow: dict):
    genres = "\n".join(f"  <genre>{esc(g)}</genre>" for g in tvshow.get("genres", []))
    content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<tvshow>
  <title>{esc(tvshow.get("title", ""))}</title>
  <originaltitle>{esc(tvshow.get("originaltitle", ""))}</originaltitle>
  <showtitle>{esc(tvshow.get("showtitle", ""))}</showtitle>
  <year>{tvshow.get("year", "")}</year>
  <premiered>{tvshow.get("premiered", "")}</premiered>
  <studio>{esc(tvshow.get("studio", ""))}</studio>
{genres}
</tvshow>
"""
    path = os.path.join(directory, "tvshow.nfo")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def write_episode_nfo(directory: str, ep: dict):
    basename = ep["mkv_basename"]
    content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<episodedetails>
  <title>{esc(ep.get("title", ""))}</title>
  <showtitle>{esc(ep.get("showtitle", ""))}</showtitle>
  <season>{ep.get("season", 1)}</season>
  <episode>{ep.get("episode", 0)}</episode>
  <aired>{ep.get("aired", "")}</aired>
  <plot>{esc(ep.get("plot", ""))}</plot>
</episodedetails>
"""
    path = os.path.join(directory, basename + ".nfo")
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def main():
    if len(sys.argv) < 2:
        # Read from stdin
        spec = json.load(sys.stdin)
    else:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            spec = json.load(f)

    directory = spec["directory"]

    # Write tvshow.nfo
    if "tvshow" in spec and spec["tvshow"]:
        path = write_tvshow_nfo(directory, spec["tvshow"])
        print(f"Created: {path}")

    # Write episode NFOs
    for ep in spec.get("episodes", []):
        path = write_episode_nfo(directory, ep)
        print(f"Created: {path}")

    print(f"Done: {len(spec.get('episodes', []))} episode NFOs generated")


if __name__ == "__main__":
    main()
