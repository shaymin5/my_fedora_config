#!/usr/bin/env python3
"""Grade eval-9 (nested folders) — per-folder authority + disc caution + non-music."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from mutagen.id3 import ID3

IT = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer-workspace/iteration-7")
NESTED = "eval-9-nested"

A_TITLES = {"01 坂本昌之 - 古代の神々": "古代の神々", "02 坂本昌之 - 母と子": "母と子",
            "03 坂本昌之 - アケ村": "アケ村"}
A_ROMAN = {"Kodai no Kamigami", "Haha to Ko", "Ake Mura"}
B_WANT = ["01 坂本昌之 - 明日.mp3", "02 坂本昌之 - アケ村.mp3"]


def ff(a: Path) -> bool:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a",
                        "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(a)],
                       capture_output=True, text=True)
    return "audio" in r.stdout


def tit(path: Path) -> str:
    return str(ID3(path, translate=False, load_v1=False).get("TIT2", ""))


def talb(path: Path) -> str:
    return str(ID3(path, translate=False, load_v1=False).get("TALB", ""))


def grade(out: Path) -> list[dict]:
    res: list[dict] = []
    a = out / "Album A"
    b = out / "Album B"
    c = out / "Album C"

    # 1. Album A titles fixed from filenames
    a_ok = {stem: (a / f"{stem}.mp3").exists() and tit(a / f"{stem}.mp3") == native
            for stem, native in A_TITLES.items()}
    res.append({"text": "Album A: TIT2 == native name from filename",
                "passed": all(a_ok.values()), "evidence": f"{a_ok}"})

    # 2. no romanized title remains
    a_titles = {p.name: tit(p) for p in a.glob("*.mp3")}
    bad = {n: t for n, t in a_titles.items() if t in A_ROMAN}
    res.append({"text": "Album A: no romanized title left", "passed": not bad, "evidence": f"{bad}"})

    # 3. junk lrc deleted, real kept
    junk = a / "02 坂本昌之 - 母と子.lrc"
    real = a / "01 坂本昌之 - 古代の神々.lrc"
    res.append({"text": "Album A: junk .lrc deleted, real .lrc kept",
                "passed": (not junk.exists()) and real.exists(),
                "evidence": f"junk_gone={not junk.exists()} real_kept={real.exists()}"})

    # 4. Album B renamed from tags
    b_names = sorted(p.name for p in b.glob("*.mp3"))
    res.append({"text": "Album B: renamed from tags to 0N 坂本昌之 - <title>",
                "passed": b_names == B_WANT, "evidence": f"{b_names}"})
    b_old = [n for n in ("Ashita.mp3", "Ake Mura.mp3") if (b / n).exists()]
    res.append({"text": "Album B: no old romanized filenames", "passed": not b_old, "evidence": f"{b_old}"})

    # 5. Album C structure preserved (asked first, not flattened)
    c_discs = (c / "Disc 1").is_dir() and (c / "Disc 2").is_dir()
    c_files = (c / "Disc 1" / "01 坂本昌之 - 王獣.mp3").exists() and (c / "Disc 2" / "01 坂本昌之 - 旅立ち.mp3").exists()
    c_flat = list(c.glob("*.mp3"))
    res.append({"text": "Album C: Disc 1/Disc 2 preserved, not flattened",
                "passed": c_discs and c_files and not c_flat,
                "evidence": f"discs={c_discs} files={c_files} flattened={[p.name for p in c_flat]}"})

    # 6. non-music untouched
    res.append({"text": "scans/cover.jpg untouched", "passed": (out / "scans" / "cover.jpg").exists(),
                "evidence": f"{(out / 'scans' / 'cover.jpg').exists()}"})

    # 7. no cross-folder album stamping
    a_albums = {talb(a / f"{s}.mp3") for s in A_TITLES if (a / f"{s}.mp3").exists()}
    b_albums = {talb(p) for p in b.glob("*.mp3")}
    res.append({"text": "Album A keeps TALB 'Album A', Album B keeps 'Album B'",
                "passed": a_albums == {"Album A"} and b_albums == {"Album B"},
                "evidence": f"A={a_albums} B={b_albums}"})

    # 8. all audio present + decodable
    allmp3 = sorted(out.rglob("*.mp3"))
    dec = {str(p.relative_to(out)): ff(p) for p in allmp3}
    res.append({"text": "7 audio files present and decodable",
                "passed": len(allmp3) == 7 and all(dec.values()), "evidence": f"n={len(allmp3)}"})
    return res


def main() -> None:
    for config in ("with_skill", "without_skill"):
        run = IT / NESTED / config / "run-1"
        exp = grade(run / "outputs")
        passed = sum(1 for e in exp if e["passed"])
        total = len(exp)
        (run / "grading.json").write_text(json.dumps({
            "expectations": exp,
            "summary": {"passed": passed, "failed": total - passed, "total": total,
                        "pass_rate": round(passed / total, 4)},
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{NESTED}/{config}: {passed}/{total}")
        for e in exp:
            if not e["passed"]:
                print("    FAIL:", e["text"], "->", e["evidence"][:200])


if __name__ == "__main__":
    main()
