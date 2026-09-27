#!/usr/bin/env python3
"""Rebuild eval-reverse with plausible romanized filenames; set up iteration-5
(eval-5 re-run) and reuse iteration-4's eval-6 results."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from mutagen.id3 import ID3, TALB, TCON, TIT2, TPE1, TRCK, TYER

SKILL = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer")
WS = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer-workspace")
FIX = WS / "fixtures"
IT4 = WS / "iteration-4"
IT5 = WS / "iteration-5"
ALBUM = "獣の奏者 エリン オリジナル・サウンドトラック"


def gen(path: Path) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                    "-i", "anullsrc=r=44100:cl=stereo", "-t", "2", "-q:a", "9", str(path)], check=True)


def tag(path: Path, title: str, track: int) -> None:
    t = ID3()
    t.add(TIT2(encoding=3, text=title))
    t.add(TPE1(encoding=3, text="坂本昌之"))
    t.add(TALB(encoding=3, text=ALBUM))
    t.add(TCON(encoding=3, text="Soundtrack"))
    t.add(TRCK(encoding=3, text=str(track)))
    t.add(TYER(encoding=3, text="2009"))
    t.save(path, v1=0, v2_version=3)


def build_reverse() -> None:
    d = FIX / "eval-reverse"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    # filenames look like plausible romanized titles; the TAGS hold the correct Japanese
    for stem, title, track in [("Kodai no Kamigami", "古代の神々", 1),
                               ("Haha to Ko", "母と子", 2),
                               ("Ashita", "明日", 3)]:
        p = d / f"{stem}.mp3"
        gen(p)
        tag(p, title, track)
    print(f"eval-reverse rebuilt: {sorted(p.name for p in d.iterdir())}")


PROMPT = (
    "这个文件夹的文件名和里面的标签对不上。请先判断哪一边才是正确的，再让文件名和标签一致起来。"
    "文件名请用『两位音轨号 艺术家 - 曲名』的格式。不要想当然——先把你的判断依据讲清楚；"
    "如果两边都可能对、你无法确定，就先别改，告诉我你需要什么信息。"
)
ASSERTIONS = [
    "The correct Japanese titles are preserved in TIT2 for all 3 files (tags were NOT overwritten from the romanized filenames)",
    "TPE1 remains 坂本昌之 for all 3 files",
    "Filenames become the tag-derived pattern (01 坂本昌之 - 古代の神々.mp3, 02 坂本昌之 - 母と子.mp3, 03 坂本昌之 - 明日.mp3)",
    "No old filenames (Kodai no Kamigami.mp3, Haha to Ko.mp3, Ashita.mp3) remain",
    "Audio still decodes",
]


def setup() -> None:
    if IT5.exists():
        shutil.rmtree(IT5)
    ed = IT5 / "eval-5-reverse"
    for config in ("with_skill", "without_skill"):
        shutil.copytree(FIX / "eval-reverse", ed / config / "run-1" / "outputs")
    meta = {"eval_id": 5, "eval_name": "tags-authoritative-rename-files",
            "prompt": PROMPT, "assertions": ASSERTIONS}
    blob = json.dumps(meta, ensure_ascii=False, indent=2)
    (ed / "eval_metadata.json").write_text(blob, encoding="utf-8")
    for config in ("with_skill", "without_skill"):
        (ed / config / "run-1" / "eval_metadata.json").write_text(blob, encoding="utf-8")
    # reuse eval-6 results from iteration-4
    shutil.copytree(IT4 / "eval-6-ambiguous", IT5 / "eval-6-ambiguous")
    print("iteration-5 ready (eval-5 new, eval-6 reused)")


if __name__ == "__main__":
    build_reverse()
    setup()
