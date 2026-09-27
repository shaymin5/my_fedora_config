#!/usr/bin/env python3
"""Build eval-9 (nested folders) fixture and register the eval.

The fixture is a parent folder holding several releases plus a non-music
subfolder, so the single-level scripts (the old behaviour) find nothing:

    eval-nested/
    ├── Album A/            filename native, tags romanized  -> fix tags
    │   ├── 01 ... .mp3         (real .lrc)
    │   ├── 02 ... .mp3         (junk .lrc)
    │   └── 03 ... .mp3
    ├── Album B/            tags native, filenames romanized -> rename files
    │   ├── Ashita.mp3
    │   └── Ake Mura.mp3
    ├── Album C/            one album? or two? -> must ASK, not flatten
    │   ├── Disc 1/01 ... .mp3
    │   └── Disc 2/01 ... .mp3
    └── scans/cover.jpg     non-music -> leave alone
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from mutagen.id3 import ID3, TALB, TIT2, TPE1, TRCK

SKILL = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer")
WS = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer-workspace")
FIX = WS / "fixtures"
IT = WS / "iteration-7"
COVER = WS / "cover.jpg"

PROMPT = (
    "这个父目录下面有好几个子文件夹，每个里面都有音乐，我想让你按实际情况处理。"
    "Album A 里的文件名是正确的日语原名，但标签里的标题是罗马音——把标签改对；"
    "Album B 里反过来，标签是正确的日语，文件名是罗马音——把文件名改成『两位音轨号 艺术家 - 曲名』的格式。"
    "歌词文件里有的内容对不上，是别的歌的垃圾，帮我清掉垃圾、真的留下。"
    "Album C 下面分成了 Disc 1 / Disc 2，我不确定这算不算同一张专辑——这种你先别动，把你的判断告诉我。"
    "scans 文件夹里不是音乐，别碰。文件名和标签以哪边为准，请按每个文件夹各自的实际情况判断，不要整批套一个规则。"
)

ASSERTIONS = [
    "Album A: every TIT2 equals the native Japanese name from its filename (古代の神々 / 母と子 / アケ村)",
    "Album A: no romanized title tag remains (Kodai no Kamigami / Haha to Ko / Ake Mura gone)",
    "Album A: the junk .lrc was deleted and the real .lrc kept",
    "Album B: filenames become 01 坂本昌之 - 明日.mp3 and 02 坂本昌之 - アケ村.mp3 (tags unchanged, native)",
    "Album C: Disc 1/ and Disc 2/ structure preserved (not flattened) because the user asked first",
    "scans/cover.jpg still exists (non-music untouched)",
    "Album A files keep TALB 'Album A' and Album B files keep TALB 'Album B' (no cross-folder stamping)",
    "all audio files still present and decodable",
]


def gen(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                    "-i", "anullsrc=r=44100:cl=stereo", "-t", "2", "-q:a", "9", str(path)], check=True)


def tag(path: Path, title: str, track: int, album: str) -> None:
    t = ID3()
    t.add(TIT2(encoding=3, text=title))
    t.add(TPE1(encoding=3, text="坂本昌之"))
    t.add(TALB(encoding=3, text=album))
    t.add(TRCK(encoding=3, text=str(track)))
    t.save(path, v1=0, v2_version=3)


def build() -> None:
    d = FIX / "eval-nested"
    if d.exists():
        shutil.rmtree(d)

    a = d / "Album A"
    for stem, tag_title, track in [("01 坂本昌之 - 古代の神々", "Kodai no Kamigami", 1),
                                   ("02 坂本昌之 - 母と子", "Haha to Ko", 2),
                                   ("03 坂本昌之 - アケ村", "Ake Mura", 3)]:
        p = a / f"{stem}.mp3"
        gen(p)
        tag(p, tag_title, track, "Album A")
    (a / "01 坂本昌之 - 古代の神々.lrc").write_text(
        "[ar:坂本昌之]\n[ti:古代の神々]\n[00:01.00]la la\n", encoding="utf-8")
    (a / "02 坂本昌之 - 母と子.lrc").write_text(
        "[ar:arkady sevidov]\n[ti:June]\n[total:320317]\n[00:01.589]纯音乐，请欣赏\n", encoding="utf-8")

    b = d / "Album B"
    for stem, tag_title, track in [("Ashita", "明日", 1), ("Ake Mura", "アケ村", 2)]:
        p = b / f"{stem}.mp3"
        gen(p)
        tag(p, tag_title, track, "Album B")

    c1 = d / "Album C" / "Disc 1"
    p = c1 / "01 坂本昌之 - 王獣.mp3"
    gen(p)
    tag(p, "王獣", 1, "Album C")
    c2 = d / "Album C" / "Disc 2"
    p = c2 / "01 坂本昌之 - 旅立ち.mp3"
    gen(p)
    tag(p, "旅立ち", 1, "Album C")

    scans = d / "scans"
    scans.mkdir(parents=True)
    shutil.copy(COVER, scans / "cover.jpg")

    print("eval-nested:")
    for p in sorted(d.rglob("*")):
        if p.is_file():
            print("   ", p.relative_to(d))


def append_eval() -> None:
    p = SKILL / "evals" / "evals.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    if any(e["name"] == "nested-folders-per-release" for e in data["evals"]):
        print("evals.json already has the nested eval")
        return
    data["evals"].append({
        "id": 9,
        "name": "nested-folders-per-release",
        "prompt": PROMPT,
        "expected_output": " ".join(ASSERTIONS),
        "files": ["fixtures/eval-nested"],
    })
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"evals.json now has {len(data['evals'])} evals")


def setup_runs() -> None:
    if IT.exists():
        shutil.rmtree(IT)
    ed = IT / "eval-9-nested"
    for config in ("with_skill", "without_skill"):
        shutil.copytree(FIX / "eval-nested", ed / config / "run-1" / "outputs")
    meta = {"eval_id": 9, "eval_name": "nested-folders-per-release",
            "prompt": PROMPT, "assertions": ASSERTIONS}
    blob = json.dumps(meta, ensure_ascii=False, indent=2)
    (ed / "eval_metadata.json").write_text(blob, encoding="utf-8")
    for config in ("with_skill", "without_skill"):
        (ed / config / "run-1" / "eval_metadata.json").write_text(blob, encoding="utf-8")
    print(f"{ed}: ready")


if __name__ == "__main__":
    build()
    append_eval()
    setup_runs()
