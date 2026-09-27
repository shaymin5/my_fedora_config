#!/usr/bin/env python3
"""Put the track's info at the top of each .lrc as *displayable* lines.

Songs with lyrics get five ordinary timestamped lyric lines instead of ID tags:

    [00:00.00]残酷な天使のテーゼ
    [00:00.29]新世紀エヴァンゲリオン｜EVANGELION FINALLY
    [00:00.58]作词：及川眠子
    [00:00.87]作曲：佐藤英敏
    [00:01.16]歌手：高橋洋子
    [00:01.46]残酷な天使のように      <- first real lyric

The five timestamps divide the first lyric's time T into five equal parts
(0, T/5, 2T/5, 3T/5, 4T/5), so they always stop short of the first lyric.

A genuinely instrumental track (no lyrics by nature) still gets an .lrc, but as
plain text with no timestamps: four info lines, a blank line, then 纯音乐:

    孤独の戦士 (Instrumental)
    Some Album
    作词：—
    作曲：鷺巣詩郎

    纯音乐

A track whose lyrics exist but could not be found is *not* given a placeholder;
it is left alone so it can be resolved (that is not the same as instrumental).

Existing top ID tags ([ti:] [al:] [ly:] …) and any previously inserted info lines
are removed first; the lyric body (including translations you added) is kept.

    uv run --with mutagen python scripts/format_lrc.py DIR [--write] [--recursive]
        [--credits report.json] [--no-netease] [--instrumental FILE,...]

Idempotent: running it again replaces the info block instead of stacking it.
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
from tag_common import (fmt_ts, iter_audio, line_seconds, normalize_lrc, read_tags, sim,  # noqa: E402
                        strip_top_metadata)

NE = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)", "Referer": "https://music.163.com/",
      "Accept": "application/json"}
CREDIT_RE = re.compile(r"^\s*(作词|作詞|作曲|编曲|編曲|词|曲|Lyricist|Composer|Music)\s*[:：]\s*(.+?)\s*$")
INFO_LINE = re.compile(r"^\s*(作词|作詞|作曲|编曲|編曲|歌手|歌者)\s*[:：]")
PLACEHOLDER_TEXT = "纯音乐"
DEFAULT_CREDIT = "—"


def http_json(url):
    req = urllib.request.Request(url, headers=NE)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)


def netease_credits(title, artist):
    try:
        d = http_json("https://music.163.com/api/search/get/?"
                      + urllib.parse.urlencode({"s": f"{title} {artist}", "type": 1, "limit": 5}))
    except Exception:
        return {}
    for s in d.get("result", {}).get("songs", []):
        if sim(s.get("name", ""), title) < 0.6:
            continue
        try:
            ly = http_json(f"https://music.163.com/api/song/lyric?id={s['id']}&lv=1&kv=1&tv=-1")
        except Exception:
            continue
        cr = {}
        for line in ((ly.get("lrc") or {}).get("lyric", "") or "").splitlines():
            line = re.sub(r"^\[\d{1,2}:\d{2}[.:]\d{1,3}\]\s*", "", line)
            m = CREDIT_RE.match(line)
            if not m:
                continue
            if m.group(1) in ("作词", "作詞", "词", "Lyricist"):
                cr.setdefault("lyricist", m.group(2))
            elif m.group(1) in ("作曲", "曲", "Composer", "Music"):
                cr.setdefault("composer", m.group(2))
        if cr:
            return cr
    return {}


def load_report(path: Path):
    """Map relative-audio-path -> entry from a fetch_lyrics.py report."""
    if not path or not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {e.get("file", ""): e for e in data}
    return {k: v for k, v in data.items()}


def strip_info_lines(body: str, title: str, album: str) -> str:
    """Drop info lines inserted by a previous run (5 timed lines, or 4 + 纯音乐)."""
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        text = re.sub(r"^\[[^\]]*\]\s*", "", lines[i]).strip()
        if text and (text == title or text == album or text == PLACEHOLDER_TEXT or INFO_LINE.match(text)):
            i += 1
        elif lines[i].strip() == "" and i < 6:
            i += 1
        else:
            break
    return "\n".join(lines[i:]).strip("\n")


def timed_block(title, album, lyricist, composer, artist, first):
    gap = first / 5.0
    texts = [title, album, f"作词：{lyricist}", f"作曲：{composer}", f"歌手：{artist}"]
    return "\n".join(f"{fmt_ts(i * gap)}{t}" for i, t in enumerate(texts)), gap


def instrumental_block(title, album, lyricist, composer):
    return "\n".join([title, album, f"作词：{lyricist}", f"作曲：{composer}", "", PLACEHOLDER_TEXT])


def main():
    ap = argparse.ArgumentParser(description="Add displayable info lines to .lrc files.")
    ap.add_argument("directory")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("--credits", default="", help="fetch_lyrics.py report, or JSON map file->{lyricist,composer}")
    ap.add_argument("--no-netease", action="store_true")
    ap.add_argument("--instrumental", default="", help="comma-separated filenames known to be instrumental")
    ap.add_argument("--placeholder", default=DEFAULT_CREDIT, help="used when a credit cannot be found")
    args = ap.parse_args()

    root = Path(args.directory)
    report = load_report(Path(args.credits)) if args.credits else {}
    forced = {x.strip() for x in args.instrumental.split(",") if x.strip()}

    for audio in iter_audio(root, args.recursive):
        lrc = audio.with_suffix(".lrc")
        rel = str(audio.relative_to(root))
        entry = {}
        for key in (rel, audio.name, audio.stem):
            if key in report:
                entry = report[key]
                break
        tags = read_tags(audio)
        title = tags["title"] or audio.stem
        album = tags["album"]
        artist = tags["artist"]
        cr = entry.get("credits") if isinstance(entry, dict) and "credits" in entry else entry
        cr = cr or {}
        lyricist, composer = cr.get("lyricist", ""), cr.get("composer", "")
        if (not lyricist or not composer) and not args.no_netease:
            f = netease_credits(title, artist)
            lyricist = lyricist or f.get("lyricist", "")
            composer = composer or f.get("composer", "")
        lyricist = lyricist or args.placeholder
        composer = composer or args.placeholder

        instrumental = bool(entry.get("instrumental")) or audio.name in forced or rel in forced

        if instrumental:
            content = instrumental_block(title, album, lyricist, composer) + "\n"
            if args.write:
                lrc.write_text(content, encoding="utf-8")
            print(f"{lrc.name:52} [纯音乐] ly={lyricist} mu={composer}")
            time.sleep(0.2)
            continue

        if not lrc.exists():
            print(f"skip (no lrc, not instrumental): {audio.name}")
            continue
        body = strip_top_metadata(lrc.read_text(encoding="utf-8"))
        body = strip_info_lines(body, title, album)
        body = normalize_lrc(body)
        first = None
        for line in body.splitlines():
            s = line_seconds(line)
            if s is not None:
                first = s if first is None else min(first, s)
        if first is None:
            print(f"skip (lrc has no timed lyrics, not instrumental): {audio.name}")
            continue
        header, gap = timed_block(title, album, lyricist, composer, artist or args.placeholder, first)
        content = header + "\n" + body + "\n"
        if args.write:
            lrc.write_text(content, encoding="utf-8")
        print(f"{lrc.name:52} ly={lyricist} mu={composer} gap={gap:.4f}s first={first}")
        time.sleep(0.2)


if __name__ == "__main__":
    main()
