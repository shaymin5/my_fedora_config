#!/usr/bin/env python3
"""Build flexibility evals: eval-reverse (tags authoritative) and eval-ambiguous (must not guess)."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from mutagen.id3 import ID3, TALB, TCON, TIT2, TPE1, TRCK, TYER

SKILL = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer")
WS = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer-workspace")
FIX = WS / "fixtures"
IT = WS / "iteration-4"
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
    # filenames are wrong (romanized / opaque); tags hold the correct Japanese
    for stem, title, track in [("track1_romaji", "古代の神々", 1),
                               ("002", "母と子", 2),
                               ("song-C", "明日", 3)]:
        p = d / f"{stem}.mp3"
        gen(p)
        tag(p, title, track)
    print(f"eval-reverse: {len(list(d.iterdir()))} files")


def build_ambiguous() -> None:
    d = FIX / "eval-ambiguous"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    # filename title and tag title are both plausible, same writing system, no tie-breaker
    for name, tag_title, track in [("01 坂本昌之 - 暁.mp3", "夜明け", 1),
                                   ("02 坂本昌之 - 静寂.mp3", "静けさ", 2),
                                   ("03 坂本昌之 - 光.mp3", "ひかり", 3)]:
        p = d / name
        gen(p)
        tag(p, tag_title, track)
    print(f"eval-ambiguous: {len(list(d.iterdir()))} files")


EVALS = [
    {
        "id": 5,
        "fixture": "eval-reverse",
        "dir": "eval-5-reverse",
        "name": "tags-authoritative-rename-files",
        "prompt": (
            "这个文件夹的文件名和里面的标签对不上。请先判断哪一边才是正确的，再让文件名和标签一致起来。"
            "文件名请用『两位音轨号 艺术家 - 曲名』的格式。不要想当然——先把你的判断依据讲清楚；"
            "如果两边都可能对、你无法确定，就先别改，告诉我你需要什么信息。"
        ),
        "assertions": [
            "The correct Japanese titles are preserved in TIT2 for all 3 files (tags were NOT overwritten from the filenames)",
            "TPE1 remains 坂本昌之 for all 3 files",
            "Filenames become the tag-derived pattern (01 坂本昌之 - 古代の神々.mp3, 02 坂本昌之 - 母と子.mp3, 03 坂本昌之 - 明日.mp3)",
            "No old filenames (track1_romaji.mp3, 002.mp3, song-C.mp3) remain",
            "Audio still decodes",
        ],
    },
    {
        "id": 6,
        "fixture": "eval-ambiguous",
        "dir": "eval-6-ambiguous",
        "name": "ambiguous-do-not-guess",
        "prompt": (
            "这个文件夹里文件名的曲名和标签里的曲名对不上，请让它们一致。"
            "但如果无法确定哪个才是正确的曲名，就先不要修改任何文件，把情况告诉我。"
        ),
        "assertions": [
            "TIT2 is unchanged for all 3 files (no tag was overwritten by a guessed title)",
            "Filenames are unchanged (no rename was performed on a guess)",
            "All 3 mp3 files still exist and audio still decodes",
        ],
    },
]


def setup_runs() -> None:
    if IT.exists():
        shutil.rmtree(IT)
    for spec in EVALS:
        ed = IT / spec["dir"]
        for config in ("with_skill", "without_skill"):
            shutil.copytree(FIX / spec["fixture"], ed / config / "run-1" / "outputs")
        meta = {"eval_id": spec["id"], "eval_name": spec["name"],
                "prompt": spec["prompt"], "assertions": spec["assertions"]}
        blob = json.dumps(meta, ensure_ascii=False, indent=2)
        (ed / "eval_metadata.json").write_text(blob, encoding="utf-8")
        for config in ("with_skill", "without_skill"):
            (ed / config / "run-1" / "eval_metadata.json").write_text(blob, encoding="utf-8")
        print(f"{spec['dir']}: ready")


def append_evals() -> None:
    p = SKILL / "evals" / "evals.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    existing = {e["name"] for e in data["evals"]}
    for spec in EVALS:
        if spec["name"] in existing:
            continue
        data["evals"].append({"id": spec["id"], "name": spec["name"], "prompt": spec["prompt"],
                              "expected_output": " ".join(spec["assertions"]),
                              "files": [f"fixtures/{spec['fixture']}"]})
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"evals.json now has {len(data['evals'])} evals")


if __name__ == "__main__":
    WS.mkdir(parents=True, exist_ok=True)
    build_reverse()
    build_ambiguous()
    append_evals()
    setup_runs()
