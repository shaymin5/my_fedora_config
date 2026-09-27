#!/usr/bin/env python3
"""Grade iteration-3 (regression of eval-0/1/2)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from mutagen.id3 import ID3

IT = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer-workspace/iteration-3")
ALBUM = "獣の奏者 エリン オリジナル・サウンドトラック"
TITLES = {1: "古代の神々", 2: "母と子", 3: "明日", 4: "アケ村"}


def ff(a: Path) -> bool:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a",
                        "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(a)],
                       capture_output=True, text=True)
    return "audio" in r.stdout


def grade_romaji(out: Path) -> list[dict]:
    res = []
    files = sorted(out.glob("*.mp3"))
    by_track = {}
    for p in files:
        t = ID3(p, translate=False, load_v1=False)
        tr = str(t.get("TRCK", "")).split("/")[0]
        if tr.isdigit():
            by_track[int(tr)] = p
    titles = {k: str(ID3(p, load_v1=False).get("TIT2", "")) for k, p in by_track.items()}
    res.append({"text": "titles equal filename Japanese names", "passed": titles == TITLES, "evidence": f"{titles}"})
    art = {k: (str(ID3(p, load_v1=False).get("TPE1", "")), str(ID3(p, load_v1=False).get("TPE2", ""))) for k, p in by_track.items()}
    res.append({"text": "TPE1=TPE2=坂本昌之", "passed": bool(art) and all(a == "坂本昌之" and b == "坂本昌之" for a, b in art.values()), "evidence": f"{art}"})
    alb = {k: (str(ID3(p, load_v1=False).get("TALB", "")), str(ID3(p, load_v1=False).get("TCON", ""))) for k, p in by_track.items()}
    res.append({"text": "TALB album, TCON Soundtrack", "passed": bool(alb) and all(a == ALBUM and b == "Soundtrack" for a, b in alb.values()), "evidence": f"{alb}"})
    yrs = {k: str(ID3(p, translate=False, load_v1=False).get("TYER", "")) for k, p in by_track.items()}
    res.append({"text": "TYER is 2009", "passed": bool(yrs) and all(v == "2009" for v in yrs.values()), "evidence": f"{yrs}"})
    v1 = {p.name: p.read_bytes()[-128:-125] == b"TAG" for p in files}
    res.append({"text": "no ID3v1", "passed": bool(v1) and not any(v1.values()), "evidence": f"{v1}"})
    dates = {p.name: (p.read_bytes().count(b"TYER"), p.read_bytes().count(b"TDRC")) for p in files}
    res.append({"text": "one date frame (1 TYER, 0 TDRC)", "passed": bool(dates) and all(a == 1 and b == 0 for a, b in dates.values()), "evidence": f"{dates}"})
    apic = {p.name: bool(ID3(p, load_v1=False).getall("APIC")) for p in files}
    res.append({"text": "APIC preserved", "passed": bool(apic) and all(apic.values()), "evidence": f"{apic}"})
    dec = {p.name: ff(p) for p in files}
    res.append({"text": "audio decodes", "passed": len(files) == 4 and all(dec.values()), "evidence": f"{dec}"})
    return res


def grade_rename(out: Path) -> list[dict]:
    res = []
    files = sorted(p for p in out.iterdir() if p.suffix == ".mp3")
    names = sorted(p.name for p in files)
    want = ["07 坂本昌之 - 夜明け.mp3", "34 坂本昌之 - 安堵.mp3", "46 cossami - After the rain～TVサイズ.mp3"]
    res.append({"text": "3 expected filenames", "passed": names == want, "evidence": f"{names}"})
    pair = {p.name: p.with_suffix(".lrc").exists() for p in files}
    res.append({"text": "each mp3 has matching lrc", "passed": bool(pair) and all(pair.values()), "evidence": f"{pair}"})
    tagmap = {}
    for p in files:
        t = ID3(p, load_v1=False)
        tagmap[str(t.get("TRCK", "")).split("/")[0]] = (str(t.get("TIT2", "")), str(t.get("TPE1", "")))
    exp = {"7": ("夜明け", "坂本昌之"), "34": ("安堵", "坂本昌之"), "46": ("After the rain～TVサイズ", "cossami")}
    res.append({"text": "tags unchanged", "passed": tagmap == exp, "evidence": f"{tagmap}"})
    old = [n for n in ("t1.mp3", "mystery.mp3", "x.mp3") if (out / n).exists()]
    res.append({"text": "no old names", "passed": not old, "evidence": f"{old}"})
    dec = {p.name: ff(p) for p in files}
    res.append({"text": "audio decodes", "passed": bool(dec) and all(dec.values()), "evidence": f"{dec}"})
    return res


def grade_lrc(out: Path) -> list[dict]:
    res = []
    lrc = {p.name for p in out.glob("*.lrc")}
    junk = ["01 坂本昌之 - 古代の神々.lrc", "03 坂本昌之 - 明日.lrc", "04 坂本昌之 - アケ村.lrc"]
    real = "02 坂本昌之 - 母と子.lrc"
    res.append({"text": "3 junk lrc deleted", "passed": all(j not in lrc for j in junk), "evidence": f"{sorted(lrc)}"})
    res.append({"text": "real lrc kept", "passed": real in lrc, "evidence": f"{real in lrc}"})
    files = sorted(p for p in out.iterdir() if p.suffix == ".mp3")
    exp = {"01 坂本昌之 - 古代の神々": "古代の神々", "02 坂本昌之 - 母と子": "母と子",
           "03 坂本昌之 - 明日": "明日", "04 坂本昌之 - アケ村": "アケ村"}
    obs = {s: (out / f"{s}.mp3").exists() and str(ID3(out / f"{s}.mp3", load_v1=False).get("TIT2", "")) == t for s, t in exp.items()}
    res.append({"text": "4 mp3 intact", "passed": len(files) == 4 and all(obs.values()), "evidence": f"{obs}"})
    res.append({"text": "no mp3 renamed/deleted", "passed": sorted(p.name for p in files) == sorted(f"{s}.mp3" for s in exp), "evidence": f"{sorted(p.name for p in files)}"})
    return res


G = {"eval-0-romaji": grade_romaji, "eval-1-rename": grade_rename, "eval-2-lrc": grade_lrc}


def main() -> None:
    for name, fn in G.items():
        for config in ("with_skill", "without_skill"):
            run = IT / name / config / "run-1"
            exp = fn(run / "outputs")
            passed = sum(1 for e in exp if e["passed"])
            total = len(exp)
            (run / "grading.json").write_text(json.dumps({
                "expectations": exp,
                "summary": {"passed": passed, "failed": total - passed, "total": total,
                            "pass_rate": round(passed / total, 4)},
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{name}/{config}: {passed}/{total}")
            for e in exp:
                if not e["passed"]:
                    print("    FAIL:", e["text"], "->", e["evidence"][:160])


if __name__ == "__main__":
    main()
