#!/usr/bin/env python3
"""Create iteration-1 run directories and eval_metadata.json files."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

WS = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer-workspace")
FIX = WS / "fixtures"
IT = WS / "iteration-1"

EVALS = [
    {
        "dir": "romaji-to-japanese-and-legacy-cleanup",
        "fixture": "eval-romaji",
        "assertions": [
            "All 4 titles equal the Japanese names from the filenames (古代の神々, 母と子, 明日, アケ村)",
            "TPE1 and TPE2 are both 坂本昌之 on every file",
            "TALB is 獣の奏者 エリン オリジナル・サウンドトラック and TCON is Soundtrack on every file",
            "TYER is 2009 on every file",
            "No file has an ID3v1 tag (last 128 bytes are not b'TAG')",
            "Every file has exactly one date frame on disk (1 TYER, 0 TDRC)",
            "APIC cover frame is preserved on every file",
            "Audio still decodes (ffprobe reports an audio stream ~2s)",
        ],
    },
    {
        "dir": "rename-by-tags-and-sync-lrc",
        "fixture": "eval-rename",
        "assertions": [
            "Filenames are exactly 07 坂本昌之 - 夜明け.mp3, 34 坂本昌之 - 安堵.mp3, 46 cossami - After the rain～TVサイズ.mp3",
            "Each mp3 has a matching .lrc with the identical basename",
            "Embedded tags are unchanged (TRCK/TIT2/TPE1 match the originals)",
            "No old filenames (t1.mp3, mystery.mp3, x.mp3) remain",
            "Audio still decodes",
        ],
    },
    {
        "dir": "remove-junk-lrc-keep-real",
        "fixture": "eval-lrc",
        "assertions": [
            "The 3 junk lrc files (01, 03, 04) are deleted",
            "The real lrc file (02 坂本昌之 - 母と子.lrc) is kept",
            "All 4 mp3 files remain and their tags are intact",
            "No mp3 files were deleted or renamed",
        ],
    },
]


def main() -> None:
    IT.mkdir(parents=True, exist_ok=True)
    for spec in EVALS:
        eval_dir = IT / spec["dir"]
        for config in ("with_skill", "without_skill"):
            dest = eval_dir / config
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(FIX / spec["fixture"], dest)
        meta = {
            "eval_id": spec["dir"],
            "eval_name": spec["dir"],
            "fixture": spec["fixture"],
            "assertions": spec["assertions"],
        }
        (eval_dir / "eval_metadata.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"{spec['dir']}: {len(spec['assertions'])} assertions, 2 run dirs")
    print(f"\nruns ready under {IT}")


if __name__ == "__main__":
    main()
