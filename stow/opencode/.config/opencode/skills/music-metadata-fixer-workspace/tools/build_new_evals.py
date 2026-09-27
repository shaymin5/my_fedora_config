#!/usr/bin/env python3
"""Build eval-3 (ID3v2.4 preservation) and eval-4 (FLAC) fixtures + run dirs."""

from __future__ import annotations

import json
import shutil
import subprocess
from io import BytesIO
from pathlib import Path

from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, ID3, TDRC, TIT2, TPE1, TALB, TRCK, TYER

SKILL = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer")
WS = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer-workspace")
FIX = WS / "fixtures"
IT = WS / "iteration-2"
ALBUM = "獣の奏者 エリン オリジナル・サウンドトラック"


def gen(path: Path, codec: str) -> None:
    args = ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
            "-i", "anullsrc=r=44100:cl=stereo", "-t", "2"]
    args += ["-c:a", "flac"] if codec == "flac" else ["-q:a", "9"]
    subprocess.run(args + [str(path)], check=True)


def jpeg() -> bytes:
    c = WS / "cover.jpg"
    if not c.exists():
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                        "-i", "color=c=red:s=64x64", "-frames:v", "1", str(c)], check=True)
    return c.read_bytes()


def id3_block() -> bytes:
    buf = BytesIO()
    t = ID3()
    t.add(TIT2(encoding=3, text="stray"))
    t.save(buf, v2_version=3)
    return buf.getvalue()


def build_v24() -> None:
    d = FIX / "eval-v24"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    cover = jpeg()

    def make(stem: str, title: str, track: int, stray_tyer: bool, v1: bool) -> None:
        p = d / f"{stem}.mp3"
        gen(p, "mp3")
        t = ID3()
        t.add(TIT2(encoding=3, text=title))
        t.add(TPE1(encoding=3, text="兽的演奏者"))
        t.add(TALB(encoding=3, text="兽的演奏者OST"))
        t.add(TRCK(encoding=3, text=str(track)))
        t.add(TDRC(encoding=3, text="2009"))
        if stray_tyer:
            t.add(TYER(encoding=3, text="2009"))
        t.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="cover", data=cover))
        t.save(p, v1=0, v2_version=4)
        if v1:
            p.write_bytes(p.read_bytes() + b"TAG" + b"z" * 125)

    make("01 坂本昌之 - 古代の神々", "Kodai no Kamigami", 1, stray_tyer=True, v1=True)
    make("02 坂本昌之 - 母と子", "Haha to Ko", 2, stray_tyer=False, v1=False)
    make("03 坂本昌之 - 明日", "Ashita", 3, stray_tyer=True, v1=True)
    make("04 坂本昌之 - アケ村", "Ake Mura", 4, stray_tyer=False, v1=False)
    print(f"eval-v24: {len(list(d.iterdir()))} files")


def build_flac() -> None:
    d = FIX / "eval-flac"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    cover = jpeg()

    def make(stem: str, title: str, track: int, stray: bool) -> None:
        p = d / f"{stem}.flac"
        gen(p, "flac")
        f = FLAC(p)
        f["title"] = title
        f["artist"] = "兽的演奏者"
        f["album"] = "兽的演奏者OST"
        f["tracknumber"] = str(track)
        pic = Picture()
        pic.type = 3
        pic.mime = "image/jpeg"
        pic.data = cover
        f.add_picture(pic)
        f.save()
        if stray:
            p.write_bytes(id3_block() + p.read_bytes())

    make("01 坂本昌之 - 古代の神々", "Kodai no Kamigami", 1, stray=False)
    make("02 坂本昌之 - 母と子", "Haha to Ko", 2, stray=True)
    make("03 坂本昌之 - 明日", "Ashita", 3, stray=False)
    make("04 坂本昌之 - アケ村", "Ake Mura", 4, stray=True)
    print(f"eval-flac: {len(list(d.iterdir()))} files")


EVALS = [
    {
        "id": 3,
        "fixture": "eval-v24",
        "dir": "eval-3-v24",
        "name": "preserve-id3v2.4",
        "prompt": (
            "这个文件夹的 mp3 标签全是罗马音，文件名才是正确的日语原名。请把标签改成和文件名一致的日语，"
            "并把其他非日语字段也统一。权威信息：专辑名『獣の奏者 エリン オリジナル・サウンドトラック』，"
            "艺术家和专辑艺术家都是『坂本昌之』，年份 2009，流派 Soundtrack。"
            "标签里还有些遗留问题（旧的 v1 标签、多余的日期帧），一起清理干净。"
            "注意：这些文件本来就是比较新的标签版本，清理时请保持它们原有的版本，不要降级。封面和音频不要破坏。"
        ),
        "assertions": [
            "All 4 titles equal the Japanese names from the filenames",
            "TPE1 and TPE2 are both 坂本昌之 on every file",
            "TALB is the album and TCON is Soundtrack on every file",
            "Every file keeps ID3 major version 4 (header byte 3 == 4)",
            "Every file has exactly one date frame, and it is TDRC (1 TDRC, 0 TYER)",
            "No file has an ID3v1 tag",
            "APIC cover is preserved on every file",
            "Audio still decodes",
        ],
    },
    {
        "id": 4,
        "fixture": "eval-flac",
        "dir": "eval-4-flac",
        "name": "fix-flac-vorbis-tags",
        "prompt": (
            "这个文件夹是 FLAC 无损文件，标签里全是罗马音，但文件名是正确的日语原名。"
            "请把标签改成和文件名一致的日语，并统一其他字段。权威信息：专辑名『獣の奏者 エリン オリジナル・サウンドトラック』，"
            "艺术家和专辑艺术家都是『坂本昌之』，年份 2009，流派 Soundtrack。"
            "另外有些文件可能带有不该有的历史遗留标签，也一并清理，封面和音频不要破坏。"
        ),
        "assertions": [
            "All 4 FLAC titles equal the Japanese names from the filenames",
            "artist and albumartist are 坂本昌之 on every file",
            "album is the album name and genre is Soundtrack on every file",
            "date is 2009 on every file",
            "No FLAC starts with an ID3 block (all start with fLaC)",
            "Cover picture preserved on every file",
            "Audio still decodes as FLAC",
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
        (ed / "eval_metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        for config in ("with_skill", "without_skill"):
            (ed / config / "run-1" / "eval_metadata.json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{spec['dir']}: ready")


def append_evals() -> None:
    p = SKILL / "evals" / "evals.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    existing = {e["name"] for e in data["evals"]}
    for spec in EVALS:
        if spec["name"] in existing:
            continue
        data["evals"].append({
            "id": spec["id"], "name": spec["name"], "prompt": spec["prompt"],
            "expected_output": " ".join(spec["assertions"]), "files": [f"fixtures/{spec['fixture']}"],
        })
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"evals.json now has {len(data['evals'])} evals")


if __name__ == "__main__":
    WS.mkdir(parents=True, exist_ok=True)
    build_v24()
    build_flac()
    append_evals()
    setup_runs()
