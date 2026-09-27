#!/usr/bin/env python3
"""Set up iteration-3: regression re-run of eval-0/1/2 with the enhanced skill."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

WS = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer-workspace")
FIX = WS / "fixtures"
IT = WS / "iteration-3"

PROMPTS = {
    "eval-0-romaji": "这个文件夹是我下载的动画OST。文件名是正确的日语原名，但里面的标签全是罗马音，而且有些字段是中文的。请把标签改成和文件名一致的日语，其他罗马音/非日语字段也统一。权威信息：专辑名『獣の奏者 エリン オリジナル・サウンドトラック』，艺术家和专辑艺术家都是『坂本昌之』，年份 2009，流派 Soundtrack。另外标签里有些历史遗留问题（旧的 v1 标签、重复的日期），也一起清理干净。封面和音频不要破坏。",
    "eval-1-rename": "这三首歌的文件名很乱，但标签里的信息是对的。请把文件名改成『两位音轨号 艺术家 - 曲名』的格式（例如 07 坂本昌之 - 夜明け.mp3），音轨号补零到两位，艺术家取标签里的艺术家。每个音频都有一个同名的 .lrc 歌词文件，改名时歌词文件也要一起改，别让歌词失效。",
    "eval-2-lrc": "这个文件夹里的 lrc 歌词文件很多是别的歌的垃圾占位（内容对不上），但也有真歌词。请帮我清理掉垃圾歌词，真的那些一定要保留，不要误删。mp3 文件不要动。",
}

ASSERTIONS = {
    "eval-0-romaji": [
        "All 4 titles equal the Japanese names from the filenames (古代の神々, 母と子, 明日, アケ村)",
        "TPE1 and TPE2 are both 坂本昌之 on every file",
        "TALB is the album and TCON is Soundtrack on every file",
        "TYER is 2009 on every file",
        "No file has an ID3v1 tag",
        "Every file has exactly one date frame (1 TYER, 0 TDRC)",
        "APIC cover frame is preserved on every file",
        "Audio still decodes (ffprobe reports an audio stream ~2s)",
    ],
    "eval-1-rename": [
        "Filenames are exactly 07 坂本昌之 - 夜明け.mp3, 34 坂本昌之 - 安堵.mp3, 46 cossami - After the rain～TVサイズ.mp3",
        "Each mp3 has a matching .lrc with the identical basename",
        "Embedded tags are unchanged (TRCK/TIT2/TPE1 match the originals)",
        "No old filenames (t1.mp3, mystery.mp3, x.mp3) remain",
        "Audio still decodes",
    ],
    "eval-2-lrc": [
        "The 3 junk lrc files (01, 03, 04) are deleted",
        "The real lrc file (02 坂本昌之 - 母と子.lrc) is kept",
        "All 4 mp3 files remain and their tags are intact",
        "No mp3 files were deleted or renamed",
    ],
}

FIXTURE = {"eval-0-romaji": "eval-romaji", "eval-1-rename": "eval-rename", "eval-2-lrc": "eval-lrc"}
IDS = {"eval-0-romaji": 0, "eval-1-rename": 1, "eval-2-lrc": 2}


def main() -> None:
    if IT.exists():
        shutil.rmtree(IT)
    for name, fixture in FIXTURE.items():
        ed = IT / name
        for config in ("with_skill", "without_skill"):
            shutil.copytree(FIX / fixture, ed / config / "run-1" / "outputs")
        meta = {"eval_id": IDS[name], "eval_name": name, "prompt": PROMPTS[name],
                "assertions": ASSERTIONS[name]}
        blob = json.dumps(meta, ensure_ascii=False, indent=2)
        (ed / "eval_metadata.json").write_text(blob, encoding="utf-8")
        for config in ("with_skill", "without_skill"):
            (ed / config / "run-1" / "eval_metadata.json").write_text(blob, encoding="utf-8")
        print(f"{name}: ready")


if __name__ == "__main__":
    main()
