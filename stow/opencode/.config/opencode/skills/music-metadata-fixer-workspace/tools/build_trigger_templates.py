#!/usr/bin/env python3
"""Build 4 tiny template working dirs for natural-task trigger probing."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from mutagen.flac import FLAC
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK

WS = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer-workspace")
TPL = WS / "trigger-natural" / "templates"
RUNS = WS / "trigger-natural" / "runs"


def mp3(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                    "-i", "anullsrc=r=44100:cl=stereo", "-t", "2", "-q:a", "9", str(path)], check=True)


def flac(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                    "-i", "anullsrc=r=44100:cl=stereo", "-t", "2", "-c:a", "flac", str(path)], check=True)


def mkv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                    "-i", "anullsrc=r=44100:cl=stereo", "-t", "1", "-f", "lavfi",
                    "-i", "color=c=black:s=64x64:r=5", "-t", "1", "-shortest", str(path)], check=True)


def tag_mp3(path: Path, title: str, track: int) -> None:
    t = ID3()
    t.add(TIT2(encoding=3, text=title))
    t.add(TPE1(encoding=3, text="Artist"))
    t.add(TALB(encoding=3, text="Album"))
    t.add(TRCK(encoding=3, text=str(track)))
    t.save(path, v1=0, v2_version=3)


def build() -> None:
    if TPL.exists():
        shutil.rmtree(TPL)
    if RUNS.exists():
        shutil.rmtree(RUNS)

    # album: romanized titles + a junk lrc and a real lrc
    d = TPL / "album"
    for stem, title, track in [("01 Artist - 王獣", "Ou Kemono", 1),
                               ("02 Artist - 旅立ち", "Tabidachi", 2),
                               ("03 Artist - 荘厳", "Sougon", 3)]:
        p = d / f"{stem}.mp3"
        mp3(p)
        tag_mp3(p, title, track)
    (d / "01 Artist - 王獣.lrc").write_text(
        "[ar:arkady sevidov]\n[ti:June]\n[total:320317]\n[00:01.589]纯音乐，请欣赏\n", encoding="utf-8")
    (d / "02 Artist - 旅立ち.lrc").write_text(
        "[ar:Artist]\n[ti:旅立ち]\n[00:01.00]la la\n", encoding="utf-8")

    # flac: two clean + one with a stray leading ID3
    d = TPL / "flac"
    for i, title in enumerate(["Kodai no Kamigami", "Haha to Ko"], start=1):
        p = d / f"{i:02d} artist - {title}.flac"
        flac(p)
        f = FLAC(p)
        f["title"] = title
        f["artist"] = "Some Artist"
        f["album"] = "Some Album"
        f["tracknumber"] = str(i)
        f.save()
    p = d / "03 artist - Ashita.flac"
    flac(p)
    f = FLAC(p)
    f["title"] = "Ashita"
    f["tracknumber"] = "3"
    f.save()
    p.write_bytes(b"ID3\x03\x00\x00\x00\x00\x00\x00" + p.read_bytes())

    # structure: disc dirs + non-music + singles
    d = TPL / "structure"
    for disc in ("Disc 1", "Disc 2"):
        for i in (1, 2):
            p = d / "Album" / disc / f"{i:02d} track.mp3"
            mp3(p)
            tag_mp3(p, f"track {i}", i)
    p = d / "Album" / "drama" / "01 dialogue.mp3"
    mp3(p)
    tag_mp3(p, "dialogue", 1)
    p = d / "Album" / "SINGLES" / "01 single.mp3"
    mp3(p)
    tag_mp3(p, "single", 1)

    # video: an mkv and an mp4
    mkv(TPL / "video" / "show01.mkv")
    mkv(TPL / "video" / "clip.mp4")

    print("templates:", sorted(p.name for p in TPL.iterdir()))


if __name__ == "__main__":
    build()
