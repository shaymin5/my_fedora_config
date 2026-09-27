#!/usr/bin/env python3
"""Build small test fixtures for the music-lyrics-matcher evals.

Uses ffmpeg-generated silent audio whose duration matches the real songs, so
lyrics matching (which leans on duration) still works while files stay tiny.
"""
import re
import subprocess
from pathlib import Path

WS = Path(__file__).resolve().parent
FIX = WS / "fixtures"
ALBUM = "新世紀エヴァンゲリオン｜EVANGELION FINALLY"


def audio(path: Path, dur: float, container: str, meta: dict):
    enc = {
        "mp3": ["-c:a", "libmp3lame", "-q:a", "9"],
        "flac": ["-c:a", "flac", "-compression_level", "12"],
        "opus": ["-c:a", "libopus", "-b:a", "6k"],
    }[container]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
           "-i", "anullsrc=r=44100:cl=stereo", "-t", f"{dur}"]
    cmd += enc
    for k, v in meta.items():
        cmd += ["-metadata", f"{k}={v}"]
    cmd += [str(path)]
    subprocess.run(cmd, check=True)
    print("built", path.relative_to(WS))


def strip_info_and_make_messy(src: Path, dst: Path, title: str, album: str):
    """Turn a finished lrc into a 'user-edited' messy one: no info lines, but
    leftover [ti:]/[al:] ID tags and the bilingual body kept."""
    info = re.compile(r"^\s*(作词|作曲|歌手)\s*[:：]")
    body = []
    started = False
    for l in src.read_text(encoding="utf-8").splitlines():
        text = re.sub(r"^\[[^\]]*\]\s*", "", l).strip()
        if not started and (not l.strip() or text == title or text == album
                            or info.match(text) or text == "纯音乐"):
            continue
        started = True
        if l.strip():
            body.append(l)
    messy = [f"[ti:{title}]", f"[al:{album}]", "[by:anonymous]", ""] + body
    dst.write_text("\n".join(messy) + "\n", encoding="utf-8")


def main():
    if FIX.exists():
        subprocess.run(["rm", "-rf", str(FIX)], check=True)

    # --- eval 1: basic, mp3 only ---
    b = FIX / "eval-basic"
    b.mkdir(parents=True)
    audio(b / "01. 残酷な天使のテーゼ.mp3", 246.36, "mp3",
          {"title": "残酷な天使のテーゼ", "artist": "高橋洋子", "album": ALBUM})
    audio(b / "03. 魂のルフラン.mp3", 312.48, "mp3",
          {"title": "魂のルフラン", "artist": "高橋洋子", "album": ALBUM})
    audio(b / "09. 心よ原始に戻れ 2020.mp3", 309.81, "mp3",
          {"title": "心よ原始に戻れ 2020", "artist": "高橋洋子", "album": ALBUM})

    # --- eval 2: mixed formats ---
    m = FIX / "eval-multiformat"
    m.mkdir(parents=True)
    audio(m / "06. 今日の日はさようなら.flac", 163.03, "flac",
          {"title": "今日の日はさようなら", "artist": "林原めぐみ", "album": ALBUM})
    audio(m / "10. 無限抱擁.opus", 324.21, "opus",
          {"title": "無限抱擁", "artist": "高橋洋子", "album": ALBUM})
    audio(m / "02. FLY ME TO THE MOON (YOKO TAKAHASHI Acid Bossa Version).mp3", 230.68, "mp3",
          {"title": "FLY ME TO THE MOON (YOKO TAKAHASHI Acid Bossa Version)",
           "artist": "YOKO TAKAHASHI", "album": ALBUM})

    # --- eval 3: a normal song plus an inherently instrumental track ---
    ins = FIX / "eval-instrumental"
    ins.mkdir(parents=True)
    audio(ins / "01. 残酷な天使のテーゼ.mp3", 246.36, "mp3",
          {"title": "残酷な天使のテーゼ", "artist": "高橋洋子", "album": ALBUM})
    audio(ins / "99. 孤独の戦士 (Instrumental).mp3", 137.0, "mp3",
          {"title": "孤独の戦士 (Instrumental)", "artist": "鷺巣詩郎", "album": ALBUM})

    # --- eval-existing: pre-existing, user-edited lrc (tags + translations) ---
    e = FIX / "eval-existing"
    e.mkdir(parents=True)
    audio(e / "06. 今日の日はさようなら.mp3", 163.03, "mp3",
          {"title": "今日の日はさようなら", "artist": "林原めぐみ", "album": ALBUM})
    audio(e / "07. 翼をください.mp3", 294.52, "mp3",
          {"title": "翼をください", "artist": "林原めぐみ", "album": ALBUM})
    # reuse the finished lrc files (with translations) as the messy source
    user_album = Path("/home/shaymin/Music/[2020.10.07] 新世紀エヴァンゲリオン｜EVANGELION FINALLY")
    for stem, title in [("06. 今日の日はさようなら", "今日の日はさようなら"),
                        ("07. 翼をください", "翼をください")]:
        src = user_album / f"{stem}.lrc"
        strip_info_and_make_messy(src, e / f"{stem}.lrc", title, ALBUM)
        print("built messy lrc", stem)


if __name__ == "__main__":
    main()
