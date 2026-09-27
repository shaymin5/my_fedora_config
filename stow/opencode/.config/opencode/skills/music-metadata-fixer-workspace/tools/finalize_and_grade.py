#!/usr/bin/env python3
"""Restructure run dirs to the layout the skill-creator viewer/aggregator expect,
then grade each run objectively into grading.json."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from mutagen.id3 import ID3

WS = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer-workspace")
IT = WS / "iteration-1"
ALBUM = "獣の奏者 エリン オリジナル・サウンドトラック"

EVALS = {
    "romaji-to-japanese-and-legacy-cleanup": {
        "new": "eval-0-romaji",
        "id": 0,
        "expected": {1: "古代の神々", 2: "母と子", 3: "明日", 4: "アケ村"},
    },
    "rename-by-tags-and-sync-lrc": {
        "new": "eval-1-rename",
        "id": 1,
        "expected": {7: ("夜明け", "坂本昌之"), 34: ("安堵", "坂本昌之"),
                     46: ("After the rain～TVサイズ", "cossami")},
    },
    "remove-junk-lrc-keep-real": {
        "new": "eval-2-lrc",
        "id": 2,
        "expected": {"01 坂本昌之 - 古代の神々": "古代の神々",
                     "02 坂本昌之 - 母と子": "母と子",
                     "03 坂本昌之 - 明日": "明日",
                     "04 坂本昌之 - アケ村": "アケ村"},
    },
}


def ffprobe_audio(path: Path) -> bool:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a",
         "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    return "audio" in r.stdout


def raw(path: Path) -> bytes:
    return path.read_bytes()


def tags(path: Path):
    return ID3(path, translate=False)


def restructure() -> None:
    for old, spec in EVALS.items():
        src = IT / old
        dst = IT / spec["new"]
        if dst.exists():
            shutil.rmtree(dst)
        dst.mkdir(parents=True)
        meta = json.loads((src / "eval_metadata.json").read_text(encoding="utf-8"))
        meta["eval_id"] = spec["id"]
        (dst / "eval_metadata.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        for config in ("with_skill", "without_skill"):
            run = dst / config / "run-1"
            out = run / "outputs"
            out.mkdir(parents=True)
            for f in (src / config).iterdir():
                if f.is_file():
                    shutil.move(str(f), str(out / f.name))
            (run / "eval_metadata.json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        shutil.rmtree(src)
    print("restructured to eval-*/{config}/run-1/outputs/")


def grade_romaji(out: Path) -> list[dict]:
    res = []
    files = sorted(out.glob("*.mp3"))
    by_track: dict[int, Path] = {}
    for p in files:
        t = tags(p)
        trck = str(t.get("TRCK", "")).split("/")[0]
        if trck.isdigit():
            by_track[int(trck)] = p
    expected = EVALS["romaji-to-japanese-and-legacy-cleanup"]["expected"]

    titles = {k: str(tags(p).get("TIT2", "")) for k, p in by_track.items()}
    res.append({
        "text": "All 4 titles equal the Japanese names from the filenames",
        "passed": len(by_track) == 4 and all(titles[k] == v for k, v in expected.items()),
        "evidence": f"titles by track: {titles}",
    })
    art = {k: (str(tags(p).get("TPE1", "")), str(tags(p).get("TPE2", ""))) for k, p in by_track.items()}
    res.append({
        "text": "TPE1 and TPE2 are both 坂本昌之 on every file",
        "passed": bool(art) and all(a == "坂本昌之" and b == "坂本昌之" for a, b in art.values()),
        "evidence": f"(TPE1,TPE2) by track: {art}",
    })
    alb = {k: (str(tags(p).get("TALB", "")), str(tags(p).get("TCON", ""))) for k, p in by_track.items()}
    res.append({
        "text": "TALB is the album and TCON is Soundtrack on every file",
        "passed": bool(alb) and all(a == ALBUM and b == "Soundtrack" for a, b in alb.values()),
        "evidence": f"(TALB,TCON) by track: {alb}",
    })
    years = {k: str(tags(p).get("TYER", "")) for k, p in by_track.items()}
    res.append({
        "text": "TYER is 2009 on every file",
        "passed": bool(years) and all(v == "2009" for v in years.values()),
        "evidence": f"TYER by track: {years}",
    })
    v1 = {p.name: raw(p)[-128:-125] == b"TAG" for p in files}
    res.append({
        "text": "No file has an ID3v1 tag",
        "passed": bool(v1) and not any(v1.values()),
        "evidence": f"id3v1 by file: {v1}",
    })
    dates = {p.name: (raw(p).count(b"TYER"), raw(p).count(b"TDRC")) for p in files}
    res.append({
        "text": "Every file has exactly one date frame (1 TYER, 0 TDRC)",
        "passed": bool(dates) and all(a == 1 and b == 0 for a, b in dates.values()),
        "evidence": f"(TYER,TDRC) by file: {dates}",
    })
    apic = {p.name: bool(tags(p).getall("APIC")) for p in files}
    res.append({
        "text": "APIC cover frame is preserved on every file",
        "passed": bool(apic) and all(apic.values()),
        "evidence": f"APIC present: {apic}",
    })
    dec = {p.name: ffprobe_audio(p) for p in files}
    res.append({
        "text": "Audio still decodes (ffprobe reports an audio stream)",
        "passed": bool(dec) and all(dec.values()) and len(files) == 4,
        "evidence": f"ffprobe audio: {dec}",
    })
    return res


def grade_rename(out: Path) -> list[dict]:
    res = []
    files = sorted(p for p in out.iterdir() if p.suffix == ".mp3")
    names = sorted(p.name for p in files)
    want = ["07 坂本昌之 - 夜明け.mp3", "34 坂本昌之 - 安堵.mp3",
            "46 cossami - After the rain～TVサイズ.mp3"]
    res.append({"text": "Filenames are the 3 expected names", "passed": names == want,
                "evidence": f"found: {names}"})
    pairing = {p.name: p.with_suffix(".lrc").exists() for p in files}
    res.append({"text": "Each mp3 has a matching .lrc with identical basename",
                "passed": bool(pairing) and all(pairing.values()), "evidence": f"lrc pairing: {pairing}"})
    tagmap = {}
    for p in files:
        t = tags(p)
        trck = str(t.get("TRCK", "")).split("/")[0]
        tagmap[trck] = (str(t.get("TIT2", "")), str(t.get("TPE1", "")))
    expected = {"7": ("夜明け", "坂本昌之"), "34": ("安堵", "坂本昌之"),
                "46": ("After the rain～TVサイズ", "cossami")}
    res.append({"text": "Embedded tags are unchanged (TRCK/TIT2/TPE1 correct)",
                "passed": tagmap == expected, "evidence": f"tags by track: {tagmap}"})
    old = [n for n in ("t1.mp3", "mystery.mp3", "x.mp3", "t1.lrc", "mystery.lrc", "x.lrc")
           if (out / n).exists()]
    res.append({"text": "No old filenames remain", "passed": not old, "evidence": f"leftovers: {old}"})
    dec = {p.name: ffprobe_audio(p) for p in files}
    res.append({"text": "Audio still decodes", "passed": bool(dec) and all(dec.values()),
                "evidence": f"ffprobe: {dec}"})
    return res


def grade_lrc(out: Path) -> list[dict]:
    res = []
    lrc = {p.name for p in out.glob("*.lrc")}
    junk = ["01 坂本昌之 - 古代の神々.lrc", "03 坂本昌之 - 明日.lrc", "04 坂本昌之 - アケ村.lrc"]
    real = "02 坂本昌之 - 母と子.lrc"
    res.append({"text": "The 3 junk lrc files are deleted",
                "passed": all(j not in lrc for j in junk), "evidence": f"remaining lrc: {sorted(lrc)}"})
    res.append({"text": "The real lrc file is kept", "passed": real in lrc,
                "evidence": f"present: {real in lrc}"})
    files = sorted(p for p in out.iterdir() if p.suffix == ".mp3")
    expected = EVALS["remove-junk-lrc-keep-real"]["expected"]
    ok_tags = len(files) == 4
    obs = {}
    for stem, title in expected.items():
        p = out / f"{stem}.mp3"
        obs[stem] = bool(p.exists()) and str(tags(p).get("TIT2", "")) == title
        ok_tags = ok_tags and obs[stem]
    res.append({"text": "All 4 mp3 remain with tags intact",
                "passed": ok_tags, "evidence": f"per file: {obs}"})
    res.append({"text": "No mp3 files were deleted or renamed",
                "passed": sorted(p.name for p in files) == sorted(f"{k}.mp3" for k in expected),
                "evidence": f"mp3 names: {sorted(p.name for p in files)}"})
    return res


GRADERS = {"eval-0-romaji": grade_romaji, "eval-1-rename": grade_rename, "eval-2-lrc": grade_lrc}


def grade_all() -> None:
    for name, fn in GRADERS.items():
        for config in ("with_skill", "without_skill"):
            run = IT / name / config / "run-1"
            out = run / "outputs"
            expectations = fn(out)
            passed = sum(1 for e in expectations if e["passed"])
            total = len(expectations)
            grading = {
                "expectations": expectations,
                "summary": {"passed": passed, "failed": total - passed, "total": total,
                            "pass_rate": round(passed / total, 4) if total else 0.0},
            }
            (run / "grading.json").write_text(
                json.dumps(grading, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{name}/{config}: {passed}/{total}")


if __name__ == "__main__":
    restructure()
    grade_all()
