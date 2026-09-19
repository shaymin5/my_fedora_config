#!/usr/bin/env python3
"""Grade iteration-8 by reusing the existing per-eval graders."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable

WS = Path("/home/shaymin/.config/opencode/skills/music-metadata-fixer-workspace")
sys.path.insert(0, str(WS / "tools"))

from grade_new import grade_flac  # noqa: E402
from grade_nested import grade as grade_nested  # noqa: E402
from grade_regression import grade_romaji  # noqa: E402

IT = WS / "iteration-8"
G: dict[str, Callable[[Path], list[dict]]] = {
    "eval-0-romaji": grade_romaji,
    "eval-4-flac": grade_flac,
    "eval-9-nested": grade_nested,
}


def main() -> None:
    for name, fn in G.items():
        for config in ("with_skill", "without_skill"):
            run = IT / name / config / "run-1"
            exp = fn(run / "outputs")
            passed = sum(1 for e in exp if e["passed"])
            total = len(exp)
            (run / "grading.json").write_text(json.dumps({
                "expectations": exp,
                "summary": {"passed": passed, "failed": total - passed, "total": total,
                            "pass_rate": round(passed / total, 4)},
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{name}/{config}: {passed}/{total}")
            for e in exp:
                if not e["passed"]:
                    print("    FAIL:", e["text"], "->", e["evidence"][:180])


if __name__ == "__main__":
    main()
