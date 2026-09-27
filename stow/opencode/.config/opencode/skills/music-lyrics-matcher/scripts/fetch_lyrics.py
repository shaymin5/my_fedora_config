#!/usr/bin/env python3
"""Match lyrics to every audio file in a folder and (optionally) write .lrc.

The point is *quality of the match*, not a fixed source: each track is matched
against whatever sources are enabled, scored on title / album / artist / duration
and version, and the best-scoring timed lyric wins. Timed lyrics are preferred;
untimed text is only used as a last resort.

    uv run --with mutagen python scripts/fetch_lyrics.py DIR [--write] [--recursive]
        [--sources lrclib,netease] [--duration-tol 12] [--report out.json]

Dry-run by default: it prints what it would use and writes nothing. Add --write
to drop `<name>.lrc` next to each audio file (lyric body only; the display-info
lines are added later by format_lrc.py).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tag_common import (artist_sim, clean_title, iter_audio, normalize_lrc, read_tags, sim)  # noqa: E402

LRCLIB = "https://lrclib.net/api"
UA = {"User-Agent": "music-lyrics-matcher/1.0", "Accept": "application/json"}
NE = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)", "Referer": "https://music.163.com/",
      "Accept": "application/json"}

CREDIT_RE = re.compile(r"^\s*(作词|作詞|作曲|编曲|編曲|词|曲|Lyricist|Composer|Music)\s*[:：]\s*(.+?)\s*$")
# a track is *by nature* instrumental (not merely "lyrics not found") when the
# source says so, or its title clearly marks it as an instrumental/backing track
INSTRUMENTAL_RE = re.compile(r"(instrumental|off[\s-]?vocal|カラオケ|karaoke|インスト|纯音乐|伴奏)", re.I)
PLACEHOLDER_RE = re.compile(r"^[\s\[].*?\]?\s*(纯音乐|純音樂|请欣赏|請欣賞|instrumental)[，,。\s]*$")


def is_placeholder(lyric: str) -> bool:
    text = re.sub(r"\[\d{1,2}:\d{2}[.:]\d{1,3}\]", "", lyric).strip()
    return bool(text) and len(text) < 20 and bool(re.search(r"纯音乐|純音樂|请欣赏|請欣賞|instrumental", text, re.I))


def http_json(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


# --------------------------------------------------------------------------- sources
def lrclib_candidates(title, artist, album):
    out = []
    queries = [
        {"track_name": title, "artist_name": artist},
        {"track_name": clean_title(title), "artist_name": artist},
        {"q": f"{clean_title(title)} {artist}"},
        {"q": clean_title(title)},
    ]
    seen = set()
    for params in queries:
        try:
            res = http_json(f"{LRCLIB}/search?" + urllib.parse.urlencode(params), UA)
        except Exception:
            res = []
        for c in res if isinstance(res, list) else []:
            if c.get("id") in seen:
                continue
            seen.add(c.get("id"))
            out.append({
                "source": "lrclib", "id": c.get("id"),
                "title": c.get("trackName", ""), "artist": c.get("artistName", ""),
                "album": c.get("albumName", ""), "duration": c.get("duration") or 0,
                "timed": bool(c.get("syncedLyrics")), "lyrics": c.get("syncedLyrics") or c.get("plainLyrics") or "",
                "instrumental": bool(c.get("instrumental")),
            })
    return out


def netease_candidates(title, artist):
    out = []
    try:
        d = http_json("https://music.163.com/api/search/get/?"
                      + urllib.parse.urlencode({"s": f"{title} {artist}", "type": 1, "limit": 10}), NE)
        songs = d.get("result", {}).get("songs", [])
    except Exception:
        return out
    for s in songs:
        names = " / ".join(a.get("name", "") for a in s.get("artists", []))
        lyric = ""
        try:
            ly = http_json(f"https://music.163.com/api/song/lyric?id={s['id']}&lv=1&kv=1&tv=-1", NE)
            lyric = (ly.get("lrc") or {}).get("lyric", "") or ""
        except Exception:
            pass
        out.append({
            "source": "netease", "id": s["id"], "title": s.get("name", ""), "artist": names,
            "album": (s.get("album") or {}).get("name", ""), "duration": (s.get("duration") or 0) / 1000.0,
            "timed": bool(re.search(r"\[\d{1,2}:\d{2}[.:]\d", lyric)), "lyrics": lyric,
            "instrumental": is_placeholder(lyric) or not lyric.strip(),
        })
    return out


def credits_from_lyric(lyric):
    cr = {}
    for line in lyric.splitlines():
        line = re.sub(r"^\[\d{1,2}:\d{2}[.:]\d{1,3}\]\s*", "", line)
        m = CREDIT_RE.match(line)
        if m:
            key = m.group(1)
            if key in ("作词", "作詞", "词", "Lyricist"):
                cr.setdefault("lyricist", m.group(2))
            elif key in ("作曲", "曲", "Composer", "Music"):
                cr.setdefault("composer", m.group(2))
    return cr


def lookup_credits(title, artist):
    """Best-effort lyricist/composer from NetEase song info."""
    try:
        d = http_json("https://music.163.com/api/search/get/?"
                      + urllib.parse.urlencode({"s": f"{title} {artist}", "type": 1, "limit": 5}), NE)
    except Exception:
        return {}
    for s in d.get("result", {}).get("songs", []):
        if sim(s.get("name", ""), title) < 0.6:
            continue
        try:
            ly = http_json(f"https://music.163.com/api/song/lyric?id={s['id']}&lv=1&kv=1&tv=-1", NE)
        except Exception:
            continue
        cr = credits_from_lyric((ly.get("lrc") or {}).get("lyric", "") or "")
        if cr:
            return cr
    return {}


# --------------------------------------------------------------------------- scoring
def score(cand, title, artist, album, duration, tol):
    cd = cand.get("duration") or 0
    if duration and cd and abs(cd - duration) > tol:
        return -1.0
    dtol = abs(cd - duration) if (duration and cd) else 0.0
    s = sim(cand["title"], title) * 2.2
    s += artist_sim(cand["artist"], artist) * 1.4
    s += sim(cand.get("album", ""), album) * 0.6
    s += max(0.0, 1.5 - dtol / 8)
    if cand.get("timed"):
        s += 3.0
    return s


def pick(cands, title, artist, album, duration, tol):
    best, best_s = None, -1.0
    for c in cands:
        s = score(c, title, artist, album, duration, tol)
        if s > best_s:
            best, best_s = c, s
    return best


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Match lyrics to an audio folder.")
    ap.add_argument("directory")
    ap.add_argument("--write", action="store_true", help="write .lrc files (default: dry-run)")
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("--sources", default="lrclib,netease")
    ap.add_argument("--duration-tol", type=float, default=12.0)
    ap.add_argument("--report", default="", help="write a JSON report of matches here")
    ap.add_argument("--no-credits", action="store_true", help="skip lyricist/composer lookup")
    args = ap.parse_args()

    root = Path(args.directory)
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    report = []

    for audio in iter_audio(root, args.recursive):
        tags = read_tags(audio)
        title, artist, album, dur = tags["title"], tags["artist"], tags["album"], tags["duration"]
        print(f"\n[{audio.relative_to(root)}] {title} / {artist} / {album} / {dur:.0f}s")

        cands = []
        if "lrclib" in sources:
            cands += lrclib_candidates(title, artist, album)
        if "netease" in sources:
            cands += netease_candidates(title, artist)
        best = pick(cands, title, artist, album, dur, args.duration_tol)

        entry = {"file": str(audio.relative_to(root)), "title": title, "artist": artist,
                 "album": album, "duration": dur, "matched": None, "credits": {},
                 "instrumental": False}
        has_lyrics = bool(best and best.get("lyrics", "").strip() and not is_placeholder(best["lyrics"]))
        if not has_lyrics:
            instrumental = bool(best and best.get("instrumental")) or bool(INSTRUMENTAL_RE.search(title))
            entry["instrumental"] = instrumental
            if instrumental:
                print("    -> INSTRUMENTAL (纯音乐)")
            else:
                print("    -> NO MATCH (lyrics not found)")
            report.append(entry)
            continue

        kind = "timed" if best["timed"] else "plain"
        print(f"    -> {kind} [{best['source']}] {best['title']} / {best['artist']} "
              f"/ {best['duration']}s")
        entry["matched"] = {k: best[k] for k in ("source", "id", "title", "artist", "album", "duration", "timed")}
        cr = credits_from_lyric(best["lyrics"])
        if not cr and not args.no_credits:
            cr = lookup_credits(title, artist)
        entry["credits"] = cr
        if cr:
            print(f"       credits: {cr}")

        if args.write:
            lrc = audio.with_suffix(".lrc")
            lrc.write_text(normalize_lrc(best["lyrics"]).strip() + "\n", encoding="utf-8")
            print(f"       wrote {lrc.name}")
        report.append(entry)
        time.sleep(0.3)

    if args.report:
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nreport -> {args.report}")


if __name__ == "__main__":
    main()
