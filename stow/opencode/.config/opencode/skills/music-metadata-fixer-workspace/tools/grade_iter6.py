#!/usr/bin/env python3
"""Grade iteration-6: eval-7 (misleading native names) and eval-8 (mixed per-file)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from mutagen.id3 import ID3

IT = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer-workspace/iteration-6")


def ff(p: Path) -> bool:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a",
                        "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    return "audio" in r.stdout


def titles_by_track(out: Path):
    d = {}
    for p in sorted(out.glob("*.mp3")):
        tr = str(ID3(p, load_v1=False).get("TRCK", "")).split("/")[0]
        if tr.isdigit():
            d[int(tr)] = str(ID3(p, load_v1=False).get("TIT2", ""))
    return d


def grade_mislead(out: Path) -> list[dict]:
    res = []
    exp = {1: "古代の神々", 2: "母と子", 3: "明日"}
    t = titles_by_track(out)
    res.append({"text": "TIT2 unchanged (wrong native filenames did not overwrite correct tags)",
                "passed": t == exp, "evidence": f"TIT2 by track: {t}"})
    art = {p.name: str(ID3(p, load_v1=False).get("TPE1", "")) for p in out.glob("*.mp3")}
    res.append({"text": "TPE1 remains 坂本昌之", "passed": bool(art) and all(v == "坂本昌之" for v in art.values()),
                "evidence": f"{art}"})
    want = {"01 坂本昌之 - 古代の神々.mp3", "02 坂本昌之 - 母と子.mp3", "03 坂本昌之 - 明日.mp3"}
    names = {p.name for p in out.glob("*.mp3")}
    res.append({"text": "Filenames are the tag-derived pattern", "passed": names == want,
                "evidence": f"{sorted(names)}"})
    old = {n for n in names if any(w in n for w in ("王獣", "旅立ち", "荘厳"))}
    res.append({"text": "No old filenames (王獣/旅立ち/荘厳) remain", "passed": not old, "evidence": f"{old}"})
    dec = {p.name: ff(p) for p in out.glob("*.mp3")}
    res.append({"text": "Audio still decodes", "passed": len(dec) == 3 and all(dec.values()), "evidence": f"{dec}"})
    return res


def grade_mixed(out: Path) -> list[dict]:
    res = []
    exp = {1: "古代の神々", 2: "母と子", 3: "明日", 4: "アケ村"}
    t = titles_by_track(out)
    res.append({"text": "Every TIT2 is the correct native title", "passed": t == exp, "evidence": f"TIT2 by track: {t}"})
    art = {p.name: str(ID3(p, load_v1=False).get("TPE1", "")) for p in out.glob("*.mp3")}
    res.append({"text": "TPE1 remains 坂本昌之 on all 4", "passed": len(art) == 4 and all(v == "坂本昌之" for v in art.values()),
                "evidence": f"{art}"})
    want = {f"{k:02d} 坂本昌之 - {v}.mp3" for k, v in exp.items()}
    names = {p.name for p in out.glob("*.mp3")}
    res.append({"text": "Every filename is 0N 坂本昌之 - <native>", "passed": names == want,
                "evidence": f"{sorted(names)}"})
    old = {n for n in names if n in ("Ashita.mp3", "Ake Mura.mp3")}
    res.append({"text": "No old filenames (Ashita.mp3, Ake Mura.mp3) remain", "passed": not old, "evidence": f"{old}"})
    dec = {p.name: ff(p) for p in out.glob("*.mp3")}
    res.append({"text": "Audio still decodes", "passed": len(dec) == 4 and all(dec.values()), "evidence": f"{dec}"})
    return res


G = {"eval-7-mislead": grade_mislead, "eval-8-mixed": grade_mixed}


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
                    print("    FAIL:", e["text"], "->", e["evidence"][:200])


if __name__ == "__main__":
    main()
