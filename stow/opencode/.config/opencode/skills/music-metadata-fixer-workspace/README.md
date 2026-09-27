# music-metadata-fixer — eval workspace

Kept here (for future iteration): reusable **fixtures**, the **tooling** that builds
and grades eval runs, and the **results** history. Transient per-run outputs
(audio copies, review.html) were removed — regenerate them with the tooling.

```
music-metadata-fixer-workspace/
├── README.md                  # this file
├── cover.jpg                  # shared art used by the fixture builders
├── fixtures/                  # 10 hand-built "broken" inputs, one per eval case
│   ├── eval-romaji/           # romanized tags + ID3v1 + duplicate dates
│   ├── eval-rename/           # messy filenames, correct tags + .lrc
│   ├── eval-lrc/              # 3 junk .lrc + 1 real .lrc
│   ├── eval-v24/              # ID3v2.4 with a stray TYER
│   ├── eval-flac/             # FLAC, two with an illegal leading ID3 block
│   ├── eval-reverse/          # tags authoritative, filenames romanized
│   ├── eval-ambiguous/        # both titles plausible -> must not guess
│   ├── eval-mislead/          # plausible-but-wrong native filenames
│   ├── eval-mixed/            # per-file mixed authority
│   └── eval-nested/           # parent of several releases + Disc 1/Disc 2 + scans/
├── tools/                     # reusable builders / graders / trigger probe
│   ├── build_fixtures.py      # builds eval-romaji/rename/lrc
│   ├── build_new_evals.py     # builds eval-v24 / eval-flac
│   ├── build_flex_evals.py    # builds eval-reverse / eval-ambiguous
│   ├── build_hard_evals.py    # builds eval-mislead / eval-mixed
│   ├── build_nested_eval.py   # builds eval-nested + iteration-7 run dirs
│   ├── build_trigger_templates.py
│   ├── setup_runs.py, setup_regression.py, setup_iter5.py, finalize_and_grade.py
│   ├── grade_regression.py    # eval-0/1/2
│   ├── grade_new.py           # eval-3/4
│   ├── grade_iter5.py         # eval-5 (reuses eval-6)
│   ├── grade_iter6.py         # eval-7/8
│   ├── grade_nested.py        # eval-9
│   ├── test_nested_tools.py   # deterministic nested-folder tooling checks (13)
│   ├── detect_nat.py          # reads the session log to see which skill a run engaged
│   └── test_enhancements.py   # direct script tests (v2.3/v2.4/FLAC/stray-ID3)
└── results/
    ├── functional_evals.md    # the 9 cases, outcomes, and takeaways
    ├── trigger_routing.json   # 22-query routing probe
    ├── trigger_natural.json   # 22-query natural-task probe
    └── benchmarks/            # iteration-N.json / .md summaries
```

Canonical eval definitions live with the skill: `../music-metadata-fixer/evals/evals.json`.

All builders/graders use absolute paths to `~/.../music-metadata-fixer` and
`~/.../music-metadata-fixer-workspace`, so they keep working after this reorg.

Run tooling with `uv run --with mutagen python <script>`.
