#!/usr/bin/env python3
"""Build fixtures and exercise the enhanced skill scripts (MP3 v2.3/v2.4, FLAC, stray ID3)."""

from __future__ import annotations

import subprocess
import sys
from io import BytesIO
from pathlib import Path

from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3, TDRC, TIT2, TPE1, TALB, TRCK, TYER

SKILL = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer")
OUT = Path("/tmp/opencode/enhtest")
MUTAGEN = ["uv", "run", "--with", "mutagen", "python"]


def sh(*args: str) -> str:
    r = subprocess.run(list(args), capture_output=True, text=True)
    if r.returncode != 0:
        print("STDOUT:", r.stdout)
        print("STDERR:", r.stderr)
        raise SystemExit(f"failed: {' '.join(args)}")
    return r.stdout


def script(name: str, *args: str) -> str:
    return sh(*MUTAGEN, str(SKILL / "scripts" / name), *args)


def gen_audio(path: Path, codec: str) -> None:
    args = ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
            "-i", "anullsrc=r=44100:cl=stereo", "-t", "2"]
    if codec == "flac":
        args += ["-c:a", "flac"]
    else:
        args += ["-q:a", "9"]
    subprocess.run(args + [str(path)], check=True)


def id3v2_block() -> bytes:
    buf = BytesIO()
    t = ID3()
    t.add(TIT2(encoding=3, text="stray id3 on flac"))
    t.save(buf, v2_version=3)
    return buf.getvalue()


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.iterdir():
        f.unlink()

    # MP3 v2.3: TYER + TDRC duplicate + ID3v1 residue
    p = OUT / "01 artist - SongOne.mp3"
    gen_audio(p, "mp3")
    t = ID3()
    t.add(TIT2(encoding=3, text="Romaji One"))
    t.add(TPE1(encoding=3, text="Someone"))
    t.add(TALB(encoding=3, text="Album"))
    t.add(TRCK(encoding=3, text="1"))
    t.add(TYER(encoding=3, text="2009"))
    t.save(p, v1=0, v2_version=3)
    t2 = ID3(p)  # default API: TYER -> TDRC in memory
    t2.setall("TYER", [TYER(encoding=3, text="2009")])
    t2.save(p, v1=0, v2_version=3)
    p.write_bytes(p.read_bytes() + b"TAG" + b"x" * 125)

    # MP3 v2.4: TDRC plus an invalid legacy TYER
    p = OUT / "02 artist - SongTwo.mp3"
    gen_audio(p, "mp3")
    t = ID3()
    t.add(TIT2(encoding=3, text="Romaji Two"))
    t.add(TPE1(encoding=3, text="Someone"))
    t.add(TRCK(encoding=3, text="2"))
    t.add(TDRC(encoding=3, text="2009"))
    t.add(TYER(encoding=3, text="2009"))
    t.save(p, v1=0, v2_version=4)

    # FLAC plain (romanized title)
    p = OUT / "03 artist - SongThree.flac"
    gen_audio(p, "flac")
    f = FLAC(p)
    f["title"] = "Romaji Three"
    f["artist"] = "Someone"
    f["album"] = "Album"
    f["tracknumber"] = "3"
    pic = Picture()
    pic.type = 3
    pic.mime = "image/jpeg"
    pic.data = b"\xff\xd8\xff\xd9"
    f.add_picture(pic)
    f.save()

    # FLAC with an illegal leading ID3 block
    p = OUT / "04 artist - SongFour.flac"
    gen_audio(p, "flac")
    f = FLAC(p)
    f["title"] = "Romaji Four"
    f["artist"] = "Someone"
    f["tracknumber"] = "4"
    f.save()
    p.write_bytes(id3v2_block() + p.read_bytes())

    print(f"built {len(list(OUT.iterdir()))} fixtures in {OUT}")
    print(script("inspect_tags.py", str(OUT)))


def main() -> None:
    build()
    print("=" * 70)
    print(">>> clean_legacy_tags --apply")
    print(script("clean_legacy_tags.py", str(OUT), "--year", "2009", "--apply"))

    print("=" * 70)
    print(">>> set_fields --title-from-filename --genre Soundtrack --albumartist Someone --apply")
    print(script("set_fields.py", str(OUT), "--title-from-filename",
                 "--genre", "Soundtrack", "--albumartist", "Someone", "--apply"))

    print("=" * 70)
    print(">>> rename_by_tags --pattern '{track:02d} {artist} - {title}' --sync-lrc --apply")
    print(script("rename_by_tags.py", str(OUT),
                 "--pattern", "{track:02d} {artist} - {title}", "--sync-lrc", "--apply"))

    print("=" * 70)
    print(">>> verify")
    from mutagen.flac import FLAC as _FLAC

    ok = True

    def check(label, cond, detail=""):
        nonlocal ok
        ok = ok and cond
        print(f"  {'PASS' if cond else 'FAIL'} {label} {detail}")

    p1 = OUT / "01 Someone - SongOne.mp3"
    raw1 = p1.read_bytes()
    check("mp3 v2.3 preserved", raw1[3] == 3, f"header v2.{raw1[3]}")
    check("mp3 single TYER, no TDRC", raw1.count(b"TYER") == 1 and raw1.count(b"TDRC") == 0)
    check("mp3 no ID3v1", raw1[-128:-125] != b"TAG")

    p2 = OUT / "02 Someone - SongTwo.mp3"
    raw2 = p2.read_bytes()
    check("mp3 v2.4 preserved", raw2[3] == 4, f"header v2.{raw2[3]}")
    check("mp3 v2.4 single TDRC, no TYER", raw2.count(b"TDRC") == 1 and raw2.count(b"TYER") == 0)

    p3 = OUT / "03 Someone - SongThree.flac"
    f3 = _FLAC(p3)
    check("flac title set", f3.get("title") == ["SongThree"])
    check("flac genre set", f3.get("genre") == ["Soundtrack"])
    check("flac picture preserved", len(f3.pictures) == 1)

    p4 = OUT / "04 Someone - SongFour.flac"
    raw4 = p4.read_bytes()
    check("flac stray ID3 removed", raw4[:4] == b"fLaC", f"magic={raw4[:4]!r}")
    check("flac title set", _FLAC(p4).get("title") == ["SongFour"])

    print("\nALL PASS" if ok else "\nSOME CHECKS FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
