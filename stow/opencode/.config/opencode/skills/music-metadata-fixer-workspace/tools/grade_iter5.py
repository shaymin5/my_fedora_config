#!/usr/bin/env python3
"""Grade iteration-5 eval-5 (reverse direction); eval-6 grading was reused from iteration-4."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from mutagen.id3 import ID3

IT = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer-workspace/iteration-5")
TITLES = {1: "古代の神々", 2: "母と子", 3: "明日"}
WANT = {"01 坂本昌之 - 古代の神々.mp3", "02 坂本昌之 - 母と子.mp3", "03 坂本昌之 - 明日.mp3"}
OLD = {"Kodai no Kamigami.mp3", "Haha to Ko.mp3", "Ashita.mp3"}


def ff(p: Path) -> bool:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a",
                        "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    return "audio" in r.stdout


def grade(out: Path) -> list[dict]:
    res = []
    files = sorted(out.glob("*.mp3"))
    by_track, by_title = {}, {}
    for p in files:
        t = ID3(p, load_v1=False)
        tr = str(t.get("TRCK", "")).split("/")[0]
        if tr.isdigit():
            by_track[int(tr)] = p
        by_title[p.name] = str(t.get("TIT2", ""))
    titles = {k: str(ID3(p, load_v1=False).get("TIT2", "")) for k, p in by_track.items()}
    res.append({"text": "Japanese titles preserved in TIT2 (tags not overwritten)", "passed": titles == TITLES,
                "evidence": f"titles by track: {titles}"})
    art = {k: str(ID3(p, load_v1=False).get("TPE1", "")) for k, p in by_track.items()}
    res.append({"text": "TPE1 remains 坂本昌之", "passed": bool(art) and all(v == "坂本昌之" for v in art.values()),
                "evidence": f"TPE1: {art}"})
    names = {p.name for p in files}
    res.append({"text": "Filenames are the tag-derived pattern", "passed": names == WANT, "evidence": f"{sorted(names)}"})
    res.append({"text": "No old filenames remain", "passed": not (names & OLD), "evidence": f"{sorted(names & OLD)}"})
    dec = {p.name: ff(p) for p in files}
    res.append({"text": "Audio still decodes", "passed": len(files) == 3 and all(dec.values()), "evidence": f"{dec}"})
    return res


def main() -> None:
    for config in ("with_skill", "without_skill"):
        run = IT / "eval-5-reverse" / config / "run-1"
        exp = grade(run / "outputs")
        passed = sum(1 for e in exp if e["passed"])
        total = len(exp)
        (run / "grading.json").write_text(json.dumps({
            "expectations": exp,
            "summary": {"passed": passed, "failed": total - passed, "total": total,
                        "pass_rate": round(passed / total, 4)},
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"eval-5-reverse/{config}: {passed}/{total}")
    # confirm eval-6 grading copied
    for config in ("with_skill", "without_skill"):
        g = IT / "eval-6-ambiguous" / config / "run-1" / "grading.json"
        s = json.loads(g.read_text())["summary"]
        print(f"eval-6-ambiguous/{config}: {s['passed']}/{s['total']} (reused)")


if __name__ == "__main__":
    main()
