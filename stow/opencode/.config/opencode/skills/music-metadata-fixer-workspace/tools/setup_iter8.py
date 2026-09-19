#!/usr/bin/env python3
"""Set up iteration-8: regression (eval-0, eval-4) + nested (eval-9)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

WS = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer-workspace")
FIX = WS / "fixtures"
IT8 = WS / "iteration-8"
IT7 = WS / "iteration-7"

EVALS = [
    {"dir": "eval-0-romaji", "fixture": "eval-romaji", "id": 0,
     "name": "romaji-to-japanese-and-legacy-cleanup",
     "prompt": "这个文件夹是我下载的动画OST。文件名是正确的日语原名，但里面的标签全是罗马音，而且有些字段是中文的。请把标签改成和文件名一致的日语，其他罗马音/非日语字段也统一。权威信息：专辑名『獣の奏者 エリン オリジナル・サウンドトラック』，艺术家和专辑艺术家都是『坂本昌之』，年份 2009，流派 Soundtrack。另外标签里有些历史遗留问题（旧的 v1 标签、重复的日期），也一起清理干净。封面和音频不要破坏。",
     "assertions": [
         "titles equal filename Japanese names",
         "TPE1=TPE2=坂本昌之",
         "TALB album, TCON Soundtrack",
         "TYER is 2009",
         "no ID3v1",
         "one date frame (1 TYER, 0 TDRC)",
         "APIC preserved",
         "audio decodes",
     ]},
    {"dir": "eval-4-flac", "fixture": "eval-flac", "id": 4,
     "name": "fix-flac-vorbis-tags",
     "prompt": "这个文件夹是 FLAC 无损文件，标签里全是罗马音，但文件名是正确的日语原名。请把标签改成和文件名一致的日语，并统一其他字段。权威信息：专辑名『獣の奏者 エリン オリジナル・サウンドトラック』，艺术家和专辑艺术家都是『坂本昌之』，年份 2009，流派 Soundtrack。另外有些文件可能带有不该有的历史遗留标签，也一并清理，封面和音频不要破坏。",
     "assertions": [
         "FLAC titles equal filename Japanese names",
         "artist and albumartist are 坂本昌之",
         "album is the album name and genre is Soundtrack",
         "date is 2009",
         "no FLAC starts with an ID3 block (all start with fLaC)",
         "cover picture preserved",
         "audio still decodes as FLAC",
     ]},
    {"dir": "eval-9-nested", "fixture": "eval-nested", "id": 9,
     "name": "nested-folders-per-release",
     "prompt": "这个父目录下面有好几个子文件夹，每个里面都有音乐，我想让你按实际情况处理。Album A 里的文件名是正确的日语原名，但标签里的标题是罗马音——把标签改对；Album B 里反过来，标签是正确的日语，文件名是罗马音——把文件名改成『两位音轨号 艺术家 - 曲名』的格式。歌词文件里有的内容对不上，是别的歌的垃圾，帮我清掉垃圾、真的留下。Album C 下面分成了 Disc 1 / Disc 2，我不确定这算不算同一张专辑——这种你先别动，把你的判断告诉我。scans 文件夹里不是音乐，别碰。文件名和标签以哪边为准，请按每个文件夹各自的实际情况判断，不要整批套一个规则。",
     "assertions": [
         "Album A: TIT2 == native name from filename",
         "Album A: no romanized title left",
         "Album A: junk .lrc deleted, real .lrc kept",
         "Album B: renamed from tags to 0N 坂本昌之 - <title>",
         "Album B: no old romanized filenames",
         "Album C: Disc 1/Disc 2 preserved, not flattened",
         "scans/cover.jpg untouched",
         "Album A keeps TALB 'Album A', Album B keeps 'Album B'",
         "7 audio files present and decodable",
     ]},
]


def main() -> None:
    if IT8.exists():
        shutil.rmtree(IT8)
    for spec in EVALS:
        ed = IT8 / spec["dir"]
        for config in ("with_skill", "without_skill"):
            dest = ed / config / "run-1" / "outputs"
            if spec["id"] == 9:
                shutil.copytree(IT7 / "eval-9-nested" / config / "run-1" / "outputs", dest)
            else:
                shutil.copytree(FIX / spec["fixture"], dest)
        meta = {"eval_id": spec["id"], "eval_name": spec["name"],
                "prompt": spec["prompt"], "assertions": spec["assertions"]}
        blob = json.dumps(meta, ensure_ascii=False, indent=2)
        (ed / "eval_metadata.json").write_text(blob, encoding="utf-8")
        for config in ("with_skill", "without_skill"):
            (ed / config / "run-1" / "eval_metadata.json").write_text(blob, encoding="utf-8")
        print(f"{spec['dir']}: ready")


if __name__ == "__main__":
    main()
