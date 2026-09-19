#!/usr/bin/env python3
"""Build hard flexibility evals: eval-7 (misleading native filenames) and eval-8 (mixed per-file)."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from mutagen.id3 import ID3, TALB, TCON, TIT2, TPE1, TRCK, TYER

SKILL = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer")
WS = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer-workspace")
FIX = WS / "fixtures"
IT = WS / "iteration-6"
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


def build_mislead() -> None:
    """Filenames are plausible native Japanese titles but WRONG; tags hold the truth."""
    d = FIX / "eval-mislead"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    # real Kemono no Souja Erin track names, but at the wrong positions
    for stem, tag_title, track in [("01 坂本昌之 - 王獣", "古代の神々", 1),
                                   ("02 坂本昌之 - 旅立ち", "母と子", 2),
                                   ("03 坂本昌之 - 荘厳", "明日", 3)]:
        p = d / f"{stem}.mp3"
        gen(p)
        tag(p, tag_title, track)
    print(f"eval-mislead: {sorted(p.name for p in d.iterdir())}")


def build_mixed() -> None:
    """Files 1-2: filename right / tag wrong.  Files 3-4: tag right / filename wrong."""
    d = FIX / "eval-mixed"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    # filename-correct, tag romanized (wrong)
    for stem, tag_title, track in [("01 坂本昌之 - 古代の神々", "Kodai no Kamigami", 1),
                                   ("02 坂本昌之 - 母と子", "Haha to Ko", 2)]:
        p = d / f"{stem}.mp3"
        gen(p)
        tag(p, tag_title, track)
    # tag-correct, filename wrong
    for stem, tag_title, track in [("Ashita", "明日", 3), ("Ake Mura", "アケ村", 4)]:
        p = d / f"{stem}.mp3"
        gen(p)
        tag(p, tag_title, track)
    print(f"eval-mixed: {sorted(p.name for p in d.iterdir())}")


EVALS = [
    {
        "id": 7, "fixture": "eval-mislead", "dir": "eval-7-mislead", "name": "misleading-native-filename",
        "prompt": (
            "这个文件夹里文件名的曲名和标签里的曲名对不上，而且文件名看起来也是正常的日文，不是明显的乱码。"
            "请核对清楚到底哪个才是正确的曲名，再让文件名和标签一致（文件名格式：两位音轨号 艺术家 - 曲名）。"
            "别想当然，先说明你的判断依据；如果确实无法确定，就先别改。"
        ),
        "assertions": [
            "TIT2 is unchanged for all 3 files (the tags were not overwritten by the plausible-but-wrong filenames)",
            "TPE1 remains 坂本昌之",
            "Filenames become the tag-derived pattern (01 坂本昌之 - 古代の神々.mp3, 02 坂本昌之 - 母と子.mp3, 03 坂本昌之 - 明日.mp3)",
            "No old filenames (王獣/旅立ち/荘厳) remain",
            "Audio still decodes",
        ],
    },
    {
        "id": 8, "fixture": "eval-mixed", "dir": "eval-8-mixed", "name": "mixed-per-file-authority",
        "prompt": (
            "这个文件夹里文件名和标签对不上，而且情况不止一种。请逐个文件判断哪一边是对的，"
            "再让每个文件的名字和标签都一致起来（文件名格式：两位音轨号 艺术家 - 曲名）。"
            "不要整批套同一个规则——不同文件可能要以不同的那边为准。"
        ),
        "assertions": [
            "Every TIT2 equals the correct native title {1:古代の神々, 2:母と子, 3:明日, 4:アケ村}",
            "TPE1 remains 坂本昌之 on all 4 files",
            "Every filename matches 0N 坂本昌之 - <native title> (all 4)",
            "No old filenames (Ashita.mp3, Ake Mura.mp3) remain",
            "Audio still decodes",
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
        meta = {"eval_id": spec["id"], "eval_name": spec["name"], "prompt": spec["prompt"],
                "assertions": spec["assertions"]}
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
    build_mislead()
    build_mixed()
    append_evals()
    setup_runs()
