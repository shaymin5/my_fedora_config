#!/usr/bin/env python3
"""Deterministic tests for the nested-folder tooling (no subagents).

Covers the actual increment over the old behaviour:
  * scan_tree maps a parent folder (audio folders, disc group, non-music)
  * single-level diagnostics WARN instead of silently reporting "0 files"
  * --recursive finds everything
  * set_fields refuses shared literals across folders
  * extension lies (.flac that is really MP3) are read/written by content

Run: uv run --with mutagen python test_nested_tools.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer")
SCRIPTS = SKILL / "scripts"
FIX = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer-workspace/fixtures/eval-nested")

sys.path.insert(0, str(SCRIPTS))
from taglib_common import read_info, write_fields  # noqa: E402

PASS: list[str] = []
FAIL: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    (PASS if ok else FAIL).append(name)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""))


def run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args],
                          capture_output=True, text=True)


def test_scan_tree() -> None:
    r = run("scan_tree.py", str(FIX), "--json")
    data = json.loads(r.stdout)
    dirs = {d["dir"] for d in data["audio_dirs"]}
    check("scan_tree finds all audio folders",
          dirs == {"Album A", "Album B", "Album C/Disc 1", "Album C/Disc 2"}, f"{dirs}")
    check("scan_tree reports 0 top-level audio", data["top_level_audio"] == 0,
          str(data["top_level_audio"]))
    groups = {(g["parent"], tuple(g["discs"])) for g in data["multi_disc_groups"]}
    check("scan_tree flags the disc group (to ask about)",
          any(p == "Album C" for p, _ in groups), f"{groups}")
    check("scan_tree lists the non-music folder", "scans" in data["non_music_dirs"],
          f"{data['non_music_dirs']}")


def test_single_level_warns() -> None:
    r = run("compare_names.py", str(FIX))
    check("compare_names single-level warns about subfolders",
          "no audio directly in this folder" in r.stdout, r.stdout[:120])
    r2 = run("inspect_tags.py", str(FIX))
    check("inspect_tags single-level warns about subfolders",
          "no audio directly in this folder" in r2.stdout, r2.stdout[:120])


def test_recursive_finds_all() -> None:
    r = run("compare_names.py", str(FIX), "--recursive")
    check("compare_names --recursive sees 7 files", "(7 files" in r.stdout, r.stdout[:80])
    r2 = run("inspect_tags.py", str(FIX), "--recursive")
    check("inspect_tags --recursive sees 7 files", "audio files: 7" in r2.stdout, r2.stdout[:80])


def test_set_fields_gate() -> None:
    r = run("set_fields.py", str(FIX), "--album", "X", "--recursive")
    check("set_fields refuses cross-folder constants",
          r.returncode == 1 and "refusing" in r.stdout, f"rc={r.returncode}")
    r2 = run("set_fields.py", str(FIX), "--title-from-filename", "--recursive")
    check("set_fields allows per-file option recursively",
          r2.returncode == 0 and "(7 files" in r2.stdout, f"rc={r2.returncode}")
    r3 = run("set_fields.py", str(FIX), "--album", "X", "--recursive",
             "--allow-cross-dir-constants")
    check("set_fields override flag bypasses the gate", r3.returncode == 0, f"rc={r3.returncode}")


def test_extension_lie() -> None:
    src = next((FIX / "Album A").glob("*.mp3"))
    tmp = Path(tempfile.mkdtemp(prefix="mmf-lie-"))
    try:
        lie = tmp / "actually_mp3.flac"
        shutil.copy(src, lie)
        info = read_info(lie)
        check("extension lie read as MP3 by content",
              info.container == "id3" and "named .flac but content is MP3" in info.note,
              f"container={info.container} note={info.note!r}")
        write_fields(lie, {"title": "ContentSniffed"})
        after = read_info(lie)
        check("extension lie writable without crashing",
              after.fields.get("title") == "ContentSniffed", f"{after.fields.get('title')!r}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    test_scan_tree()
    test_single_level_warns()
    test_recursive_finds_all()
    test_set_fields_gate()
    test_extension_lie()
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
