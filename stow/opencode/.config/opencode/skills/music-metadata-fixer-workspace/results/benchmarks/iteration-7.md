# iteration-7 — nested folders (eval-9) + tooling tests

## eval-9 `nested-folders-per-release`

Fixture: a parent folder with `Album A` (filename native / tags romanized),
`Album B` (tags native / filenames romanized), `Album C/{Disc 1,Disc 2}`, and a
non-music `scans/` folder.

| config | score |
|---|---|
| with_skill | 9/9 |
| without_skill | 9/9 |

Both configurations fixed A and B, deleted the junk `.lrc` and kept the real one,
left `scans/` alone, and stopped at Album C to ask about the disc structure
instead of flattening it. So this eval is a **regression guard**, not a
differentiator: the model's judgement was never the gap.

## Deterministic tooling test — `tools/test_nested_tools.py`

13/13. This is where the real increment is, and it is measured without subagents:

- `scan_tree.py` finds all four audio folders, reports 0 top-level audio, flags
  the `Album C` disc group, and lists `scans/` as non-music.
- `compare_names.py` / `inspect_tags.py` **warn** when the top level is empty but
  subfolders hold audio (previously they printed "0 files / all clean").
- `--recursive` sees all 7 files.
- `set_fields.py --album X --recursive` **refuses** (would stamp one album across
  releases); `--title-from-filename --recursive` is allowed; the override flag
  bypasses the gate.
- A file named `.flac` that is really an MP3 (ID3 + MPEG sync) is read and
  written by content sniffing, not by extension, and is flagged in diagnostics.

## Real-world finding

Running `scan_tree.py` on `~/Music/兽之奏者艾琳` (the motivating parent folder)
surfaced, among other things, that three files named `.flac` under
`After the rain/` are actually MP3s. This crashed the old `read_info`; the
content-sniffing fix makes the whole toolbox robust to it. The collection itself
was **not** modified by these tests.
