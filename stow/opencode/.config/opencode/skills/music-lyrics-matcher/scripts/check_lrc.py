#!/usr/bin/env python3
"""Sanity-check the generated .lrc files.

For every audio file a matching .lrc must exist and be one of two shapes:

* timed song   — top five lines are title / album / 作词：/ 作曲：/ 歌手： with
                 timestamps at 0, T/5, 2T/5, 3T/5, 4T/5 (T = first lyric time);
* instrumental — plain text: four lines (title / album / 作词：/ 作曲：), a blank
                 line, then 纯音乐, with no timestamps at all.

Also flags leftover [ti:]/[al:]/… ID tags and non-monotonic timestamps.

    uv run python scripts/check_lrc.py DIR [--recursive]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tag_common import SPACE_AFTER_TAG, TIMED_RE, iter_audio, line_seconds, read_tags  # noqa: E402

HEADER_TAG = re.compile(r"^\[([A-Za-z]+):")
ID_TAGS = {"ti", "ar", "al", "au", "by", "ly", "mu", "offset", "re", "ve", "length"}
INFO_PREFIX = ("作词：", "作词:", "作曲：", "作曲:")
PLACEHOLDER = "纯音乐"


def text_of(line):
    return re.sub(r"^\[[^\]]*\]\s*", "", line).strip()


def check_one(audio: Path, lrc: Path) -> list[str]:
    problems: list[str] = []
    lines = lrc.read_text(encoding="utf-8").splitlines()
    tags = {m.group(1).lower() for l in lines if (m := HEADER_TAG.match(l))}
    if tags & ID_TAGS:
        problems.append(f"残留头部标签: {sorted(tags & ID_TAGS)}")
    spaced = [l for l in lines if SPACE_AFTER_TAG.match(l)]
    if spaced:
        problems.append(f"时间戳后有多余空格（{len(spaced)} 行），例如 {spaced[0]!r}")

    info = read_tags(audio)
    title, album = info["title"] or audio.stem, info["album"]

    timed = [(s, l) for l in lines if (s := line_seconds(l)) is not None]
    if not timed:
        # instrumental shape: 4 info lines, blank, 纯音乐
        body = list(lines)
        while body and not body[0].strip():
            body.pop(0)
        non_empty = [l for l in body if l.strip()]
        if len(non_empty) < 5 or text_of(non_empty[-1]) != PLACEHOLDER:
            problems.append(f"纯音乐文件结构不对（应有 4 行信息 + 空行 + 纯音乐），实际 {len(non_empty)} 行")
            return problems
        ph_idx = max(i for i, l in enumerate(body) if l.strip())
        if body[ph_idx - 1].strip() != "":
            problems.append("纯音乐前应有一个空行")
        info = [text_of(l) for l in body[:ph_idx - 1] if l.strip()]
        t = info
        if len(t) < 4:
            problems.append(f"纯音乐信息行不足: {t}")
            return problems
        if t[0] != title:
            problems.append(f"第 1 行应为标题 '{title}'，实际 '{t[0]}'")
        if album and t[1] != album:
            problems.append(f"第 2 行应为专辑 '{album}'，实际 '{t[1]}'")
        if not t[2].startswith(INFO_PREFIX) or not t[3].startswith(INFO_PREFIX):
            problems.append(f"第 3/4 行应为 作词：/作曲：，实际 '{t[2]}' / '{t[3]}'")
        return problems

    if len(timed) < 6:
        problems.append(f"带时间轴的行太少({len(timed)})")
        return problems
    top = timed[:5]
    T = timed[5][0]
    expect = [0.0, T * 1 / 5, T * 2 / 5, T * 3 / 5, T * 4 / 5]
    got = [s for s, _ in top]
    if any(abs(g - e) > 0.03 for g, e in zip(got, expect)):
        problems.append(f"顶部时间戳应为 {[round(e, 3) for e in expect]}，实际 {got}")
    tt = [text_of(l) for _, l in top]
    if title and tt[0] != title:
        problems.append(f"第 1 行应为标题 '{title}'，实际 '{tt[0]}'")
    if album and tt[1] != album:
        problems.append(f"第 2 行应为专辑 '{album}'，实际 '{tt[1]}'")
    if not tt[2].startswith(INFO_PREFIX):
        problems.append(f"第 3 行应为 '作词：…'，实际 '{tt[2]}'")
    if not tt[3].startswith(INFO_PREFIX):
        problems.append(f"第 4 行应为 '作曲：…'，实际 '{tt[3]}'")
    if not tt[4].startswith(("歌手：", "歌手:")):
        problems.append(f"第 5 行应为 '歌手：…'，实际 '{tt[4]}'")
    for (s1, _), (s2, _) in zip(timed[4:], timed[5:]):
        if s2 < s1 - 0.001:
            problems.append(f"时间轴非递增: {s1} -> {s2}")
            break
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--recursive", action="store_true")
    args = ap.parse_args()

    root = Path(args.directory)
    audios = list(iter_audio(root, args.recursive))
    bad = 0
    for audio in audios:
        lrc = audio.with_suffix(".lrc")
        if not lrc.exists():
            print(f"MISSING  {audio.relative_to(root)}")
            bad += 1
            continue
        problems = check_one(audio, lrc)
        if problems:
            bad += 1
            print(f"FAIL     {audio.relative_to(root)}")
            for p in problems:
                print(f"           - {p}")
        else:
            print(f"ok       {audio.relative_to(root)}")
    print(f"\n{len(audios) - bad}/{len(audios)} ok")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
