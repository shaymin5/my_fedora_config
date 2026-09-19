#!/usr/bin/env python3
"""Build broken-metadata fixtures for the music-metadata-fixer evals."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from mutagen.id3 import APIC, ID3, TALB, TCON, TIT2, TPE1, TPE2, TRCK, TYER

WS = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer-workspace")
FIX = WS / "fixtures"
ALBUM = "獣の奏者 エリン オリジナル・サウンドトラック"

JUNK_LRC = (
    "[ar:arkady sevidov]\n[ti:June]\n[hash:4399c9872c7235b60b58ce88dc487897]\n"
    "[total:320317]\n[00:01.589]纯音乐，请欣赏\n"
)


def mp3(path: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
         "-i", "anullsrc=r=44100:cl=stereo", "-t", "2", "-q:a", "9", str(path)],
        check=True,
    )


def cover_bytes() -> bytes:
    cover = WS / "cover.jpg"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
         "-i", "color=c=red:s=64x64", "-frames:v", "1", str(cover)],
        check=True,
    )
    return cover.read_bytes()


def write_tags(path: Path, title: str, artist: str, album: str, track: int, year: str,
               genre: str, cover: bytes, albumartist: str | None = None) -> None:
    t = ID3()
    t.add(TIT2(encoding=3, text=title))
    t.add(TPE1(encoding=3, text=artist))
    t.add(TPE2(encoding=3, text=albumartist or artist))
    t.add(TALB(encoding=3, text=album))
    t.add(TCON(encoding=3, text=genre))
    t.add(TRCK(encoding=3, text=str(track)))
    t.add(TYER(encoding=3, text=year))
    t.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="cover", data=cover))
    t.save(path, v1=0, v2_version=3)


def add_duplicate_date(path: Path) -> None:
    """Reproduce the mutagen trap: load (TYER->TDRC in memory), set TYER, save v2.3."""
    t = ID3(path)
    t.setall("TYER", [TYER(encoding=3, text="2009")])
    t.save(path, v1=0, v2_version=3)


def add_id3v1(path: Path) -> None:
    block = (b"TAG" + b"Stale Title".ljust(30, b"\x00") + b"Bad Artist".ljust(30, b"\x00")
             + b"Wrong Album".ljust(30, b"\x00") + b"1999" + b"\x00" * 30 + b"\x00")
    with path.open("ab") as fh:
        fh.write(block)


def main() -> None:
    WS.mkdir(parents=True, exist_ok=True)
    cover = cover_bytes()

    # ---------- eval-romaji : romanized tags + legacy junk ----------
    d = FIX / "eval-romaji"
    d.mkdir(parents=True, exist_ok=True)
    specs = [
        ("01 坂本昌之 - 古代の神々", "Kodai no Kamigami", 1, dict(dup=True, v1=True)),
        ("02 坂本昌之 - 母と子", "Haha to Ko", 2, dict(dup=False, v1=True)),
        ("03 坂本昌之 - 明日", "Ashita", 3, dict(dup=True, v1=False)),
        ("04 坂本昌之 - アケ村", "Ake Mura", 4, dict(dup=False, v1=False)),
    ]
    for stem, romaji, track, opts in specs:
        p = d / f"{stem}.mp3"
        mp3(p)
        write_tags(p, romaji, "兽的演奏者", "兽的演奏者OST", track, "2009", "Anime", cover)
        if opts["dup"]:
            add_duplicate_date(p)
        if opts["v1"]:
            add_id3v1(p)

    # ---------- eval-rename : messy filenames, correct tags + real lrc ----------
    d = FIX / "eval-rename"
    d.mkdir(parents=True, exist_ok=True)
    rename_specs = [
        ("t1", "夜明け", "坂本昌之", 7),
        ("mystery", "安堵", "坂本昌之", 34),
        ("x", "After the rain～TVサイズ", "cossami", 46),
    ]
    for stem, title, artist, track in rename_specs:
        p = d / f"{stem}.mp3"
        mp3(p)
        write_tags(p, title, artist, ALBUM, track, "2009", "Soundtrack", cover,
                   albumartist="坂本昌之")
        (d / f"{stem}.lrc").write_text(
            f"[ar:{artist}]\n[ti:{title}]\n[00:01.00]（纯音乐）\n", encoding="utf-8"
        )

    # ---------- eval-lrc : 3 junk lrc + 1 real lrc ----------
    d = FIX / "eval-lrc"
    d.mkdir(parents=True, exist_ok=True)
    lrc_specs = [
        ("01 坂本昌之 - 古代の神々", "古代の神々", "junk"),
        ("02 坂本昌之 - 母と子", "母と子", "real"),
        ("03 坂本昌之 - 明日", "明日", "junk"),
        ("04 坂本昌之 - アケ村", "アケ村", "junk"),
    ]
    for stem, title, kind in lrc_specs:
        p = d / f"{stem}.mp3"
        mp3(p)
        track = int(stem[:2])
        write_tags(p, title, "坂本昌之", ALBUM, track, "2009", "Soundtrack", cover,
                   albumartist="坂本昌之")
        if kind == "junk":
            (d / f"{stem}.lrc").write_text(JUNK_LRC, encoding="utf-8")
        else:
            (d / f"{stem}.lrc").write_text(
                f"[ar:坂本昌之]\n[ti:{title}]\n[00:02.00]（纯音乐）\n", encoding="utf-8"
            )

    print("fixtures built:")
    for sub in sorted(FIX.iterdir()):
        print(f"  {sub.name}: {len(list(sub.iterdir()))} files")

    # ---------- evals.json ----------
    evals = {
        "skill_name": "music-metadata-fixer",
        "evals": [
            {
                "id": 0,
                "name": "romaji-to-japanese-and-legacy-cleanup",
                "prompt": (
                    "这个文件夹是我下载的动画OST。文件名是正确的日语原名，但里面的标签全是罗马音，"
                    "而且有些字段是中文的。请把标签改成和文件名一致的日语，其他罗马音/非日语字段也统一。"
                    "权威信息：专辑名『獣の奏者 エリン オリジナル・サウンドトラック』，"
                    "艺术家和专辑艺术家都是『坂本昌之』，年份 2009，流派 Soundtrack。"
                    "另外标签里有些历史遗留问题（旧的 v1 标签、重复的日期），也一起清理干净。"
                    "封面和音频不要破坏。"
                ),
                "expected_output": "所有 title 变为文件名中的日语名；TPE1/TPE2=坂本昌之；TALB=专辑名；TCON=Soundtrack；TYER=2009；无 ID3v1；磁盘上只有一个日期帧；封面与音频保留。",
                "files": ["fixtures/eval-romaji"],
            },
            {
                "id": 1,
                "name": "rename-by-tags-and-sync-lrc",
                "prompt": (
                    "这三首歌的文件名很乱，但标签里的信息是对的。请把文件名改成"
                    "『两位音轨号 艺术家 - 曲名』的格式（例如 07 坂本昌之 - 夜明け.mp3），"
                    "音轨号补零到两位，艺术家取标签里的艺术家。每个音频都有一个同名的 .lrc 歌词文件，"
                    "改名时歌词文件也要一起改，别让歌词失效。"
                ),
                "expected_output": "文件名变为 07 坂本昌之 - 夜明け.mp3 / 34 坂本昌之 - 安堵.mp3 / 46 cossami - After the rain～TVサイズ.mp3，且每个都有同名 .lrc，标签不变。",
                "files": ["fixtures/eval-rename"],
            },
            {
                "id": 2,
                "name": "remove-junk-lrc-keep-real",
                "prompt": (
                    "这个文件夹里的 lrc 歌词文件很多是别的歌的垃圾占位（内容对不上），"
                    "但也有真歌词。请帮我清理掉垃圾歌词，真的那些一定要保留，不要误删。"
                    "mp3 文件不要动。"
                ),
                "expected_output": "删除 01/03/04 三个垃圾 lrc，保留 02 的真歌词，4 个 mp3 不变。",
                "files": ["fixtures/eval-lrc"],
            },
        ],
    }
    evals_dir = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer/evals")
    evals_dir.mkdir(parents=True, exist_ok=True)
    (evals_dir / "evals.json").write_text(
        json.dumps(evals, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"wrote {evals_dir / 'evals.json'}")


if __name__ == "__main__":
    main()
