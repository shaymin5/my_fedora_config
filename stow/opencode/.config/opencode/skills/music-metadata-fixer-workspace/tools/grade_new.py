#!/usr/bin/env python3
"""Grade iteration-2 (eval-3 v2.4, eval-4 FLAC) into grading.json."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from mutagen.flac import FLAC
from mutagen.id3 import ID3

WS = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer-workspace")
IT = WS / "iteration-2"
ALBUM = "獣の奏者 エリン オリジナル・サウンドトラック"
TITLES = {"1": "古代の神々", "2": "母と子", "3": "明日", "4": "アケ村"}


def ffprobe_codec(path: Path) -> str:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a",
                        "-show_entries", "stream=codec_name", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return r.stdout.strip()


def grade_v24(out: Path) -> list[dict]:
    res = []
    files = sorted(out.glob("*.mp3"))
    by_track = {}
    for p in files:
        trck = str(ID3(p, load_v1=False).get("TRCK", "")).split("/")[0]
        if trck.isdigit():
            by_track[str(int(trck))] = p
    titles = {k: str(ID3(p, load_v1=False).get("TIT2", "")) for k, p in by_track.items()}
    res.append({"text": "All 4 titles equal the Japanese names from the filenames",
                "passed": titles == TITLES, "evidence": f"titles: {titles}"})
    art = {k: (str(ID3(p, load_v1=False).get("TPE1", "")), str(ID3(p, load_v1=False).get("TPE2", "")))
           for k, p in by_track.items()}
    res.append({"text": "TPE1 and TPE2 are both 坂本昌之 on every file",
                "passed": bool(art) and all(a == "坂本昌之" and b == "坂本昌之" for a, b in art.values()),
                "evidence": f"(TPE1,TPE2): {art}"})
    alb = {k: (str(ID3(p, load_v1=False).get("TALB", "")), str(ID3(p, load_v1=False).get("TCON", "")))
           for k, p in by_track.items()}
    res.append({"text": "TALB is the album and TCON is Soundtrack on every file",
                "passed": bool(alb) and all(a == ALBUM and b == "Soundtrack" for a, b in alb.values()),
                "evidence": f"(TALB,TCON): {alb}"})
    vers = {p.name: p.read_bytes()[3] for p in files}
    res.append({"text": "Every file keeps ID3 major version 4",
                "passed": bool(vers) and all(v == 4 for v in vers.values()), "evidence": f"version bytes: {vers}"})
    dates = {p.name: (p.read_bytes().count(b"TYER"), p.read_bytes().count(b"TDRC")) for p in files}
    res.append({"text": "Every file has exactly one date frame, and it is TDRC (1 TDRC, 0 TYER)",
                "passed": bool(dates) and all(t == 0 and d == 1 for t, d in dates.values()),
                "evidence": f"(TYER,TDRC): {dates}"})
    v1 = {p.name: p.read_bytes()[-128:-125] == b"TAG" for p in files}
    res.append({"text": "No file has an ID3v1 tag", "passed": bool(v1) and not any(v1.values()),
                "evidence": f"id3v1: {v1}"})
    apic = {p.name: bool(ID3(p, load_v1=False).getall("APIC")) for p in files}
    res.append({"text": "APIC cover is preserved on every file", "passed": bool(apic) and all(apic.values()),
                "evidence": f"APIC: {apic}"})
    dec = {p.name: ffprobe_codec(p) for p in files}
    res.append({"text": "Audio still decodes", "passed": len(files) == 4 and all(v == "mp3" for v in dec.values()),
                "evidence": f"codec: {dec}"})
    return res


def grade_flac(out: Path) -> list[dict]:
    res = []
    files = sorted(out.glob("*.flac"))
    by_track = {}
    for p in files:
        tn = str((FLAC(p).get("tracknumber") or [""])[0]).split("/")[0]
        if tn.isdigit():
            by_track[str(int(tn))] = p
    titles = {k: (FLAC(p).get("title") or [""])[0] for k, p in by_track.items()}
    res.append({"text": "All 4 FLAC titles equal the Japanese names from the filenames",
                "passed": titles == TITLES, "evidence": f"titles: {titles}"})
    art = {k: ((FLAC(p).get("artist") or [""])[0], (FLAC(p).get("albumartist") or [""])[0])
           for k, p in by_track.items()}
    res.append({"text": "artist and albumartist are 坂本昌之 on every file",
                "passed": bool(art) and all(a == "坂本昌之" and b == "坂本昌之" for a, b in art.values()),
                "evidence": f"(artist,albumartist): {art}"})
    alb = {k: ((FLAC(p).get("album") or [""])[0], (FLAC(p).get("genre") or [""])[0])
           for k, p in by_track.items()}
    res.append({"text": "album is the album name and genre is Soundtrack on every file",
                "passed": bool(alb) and all(a == ALBUM and b == "Soundtrack" for a, b in alb.values()),
                "evidence": f"(album,genre): {alb}"})
    dates = {k: (FLAC(p).get("date") or [""])[0] for k, p in by_track.items()}
    res.append({"text": "date is 2009 on every file",
                "passed": bool(dates) and all(v.startswith("2009") for v in dates.values()),
                "evidence": f"date: {dates}"})
    magic = {p.name: p.read_bytes()[:4] for p in files}
    res.append({"text": "No FLAC starts with an ID3 block (all start with fLaC)",
                "passed": bool(magic) and all(v == b"fLaC" for v in magic.values()),
                "evidence": f"magic: {magic}"})
    pics = {p.name: len(FLAC(p).pictures) for p in files}
    res.append({"text": "Cover picture preserved on every file",
                "passed": bool(pics) and all(v >= 1 for v in pics.values()), "evidence": f"pictures: {pics}"})
    dec = {p.name: ffprobe_codec(p) for p in files}
    res.append({"text": "Audio still decodes as FLAC", "passed": len(files) == 4 and all(v == "flac" for v in dec.values()),
                "evidence": f"codec: {dec}"})
    return res


def main() -> None:
    for name, fn in (("eval-3-v24", grade_v24), ("eval-4-flac", grade_flac)):
        for config in ("with_skill", "without_skill"):
            run = IT / name / config / "run-1"
            expectations = fn(run / "outputs")
            passed = sum(1 for e in expectations if e["passed"])
            total = len(expectations)
            (run / "grading.json").write_text(json.dumps({
                "expectations": expectations,
                "summary": {"passed": passed, "failed": total - passed, "total": total,
                            "pass_rate": round(passed / total, 4)},
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{name}/{config}: {passed}/{total}")
            for e in expectations:
                if not e["passed"]:
                    print("    FAIL:", e["text"], "->", e["evidence"][:180])


if __name__ == "__main__":
    main()
