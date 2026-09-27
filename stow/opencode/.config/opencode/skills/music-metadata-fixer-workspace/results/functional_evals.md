# Functional eval results — music-metadata-fixer

9 cases. Baseline = no skill. "Discriminating" = the skill's config scored higher than baseline.

| # | Fixture | What it tests | With skill | Without skill | Discriminates? |
|---|---|---|---|---|---|
| 0 | `eval-romaji` | romanized tags → Japanese from filenames; ID3v1 residue; duplicate TYER+TDRC | 8/8 | 6/8 (iter-1), 8/8 (iter-3) | partly — version hygiene; baseline is flaky |
| 1 | `eval-rename` | rename from tags + keep `.lrc` in sync | 5/5 | 5/5 | no |
| 2 | `eval-lrc` | delete junk `.lrc`, keep the real one | 4/4 | 4/4 | no |
| 3 | `eval-v24` | preserve an existing ID3v2.4 (single TDRC, no TYER) | 8/8 | 8/8 | no (prompt hinted) |
| 4 | `eval-flac` | FLAC Vorbis tags **+ illegal leading ID3 block** | **7/7** | **6/7** | **yes — most reliable** |
| 5 | `eval-reverse` | tags authoritative, filenames romanized → rename from tags | 5/5 | 5/5 | no |
| 6 | `eval-ambiguous` | both titles plausible → must NOT guess | 3/3 | 3/3 | no |
| 7 | `eval-mislead` | filenames are plausible-but-wrong native titles | 5/5 | 5/5 | no |
| 8 | `eval-mixed` | per-file mixed authority (some filename-right, some tag-right) | 5/5 | 5/5 | no |
| 9 | `eval-nested` | parent folder of several releases + `Disc 1/Disc 2` + `scans/` | 9/9 | 9/9 | no (behaviour parity; the gap was tooling) |

Iterations live in `results/benchmarks/` (iteration-1 re-ran as iteration-3 after the
version-preservation + FLAC refactor; no regression).

## Takeaway

- The skill's **measurable** edge is **format-specific hygiene**: FLAC stray-ID3
  removal (eval-4) and ID3 version preservation (eval-0). Spend future effort there.
- The judgement cases (5–8) already pass for the base model; they are kept as
  **regression guards** so a future skill change doesn't make the guidance dogmatic
  (e.g. hard-coding "always trust the filename").
- eval-9 (nested folders) is also behaviour parity: both configs handled the
  folders correctly, so the model judgement was never the gap. The real increment
  there is **tooling** and is measured deterministically by
  `tools/test_nested_tools.py` (13 checks): `scan_tree` maps the tree, single-level
  diagnostics now warn instead of reporting "0 files, clean", `--recursive` works,
  `set_fields` refuses cross-folder shared literals, and a mis-named `.flac`
  (really MP3) is read/written by content sniffing.

## Trigger results

- `results/trigger_routing.json` — routing probe, 22/22 (upper bound; meta-prompted).
- `results/trigger_natural.json` — natural-task probe (raw request + working dir,
  engagement read from the session log), 21/22. Positive trigger 13/13; negative
  avoidance 8/9 (the "change the cover" request opened the skill body but did not
  load it; possibly nudged by the workspace path).

## How to re-run

```bash
cd <workspace>/tools
uv run --with mutagen python build_fixtures.py       # eval-0/1/2 fixtures
uv run --with mutagen python build_new_evals.py      # eval-3/4
uv run --with mutagen python build_flex_evals.py     # eval-5/6
uv run --with mutagen python build_hard_evals.py     # eval-7/8
uv run --with mutagen python build_nested_eval.py    # eval-9 + iteration-7 run dirs
# then spawn with-skill / baseline subagents on copies of fixtures/<name>,
# and grade each run dir with the matching grade_*.py.
uv run --with mutagen python test_nested_tools.py    # deterministic nested tooling checks
```
