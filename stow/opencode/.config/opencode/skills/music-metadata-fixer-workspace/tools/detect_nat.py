#!/usr/bin/env python3
"""Detect, from the OpenCode session logs, which skill each natural-task subagent engaged."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB = "file:/home/shaymin/.local/share/opencode/opencode.db?mode=ro"
PARENT = "ses_f47e0a1cdffeY77yH2sgtR0mC7"
SKILLS = ["music-metadata-fixer", "music-reorganizer", "anime-nfo-generator",
          "architecture-tracker", "skill-creator", "opencode", "report"]


def main() -> None:
    con = sqlite3.connect(DB, uri=True)
    c = con.cursor()
    sessions = list(c.execute(
        "select id,title from session_v2 where parent_id=? order by time_created", (PARENT,)))
    nat = [(sid, title) for sid, title in sessions if title and title.startswith("nat")]
    print(f"nat sessions: {len(nat)}\n")
    out = {}
    for sid, title in nat:
        engaged = []
        toolnames = set()
        rows = list(c.execute("select data from session_message where session_id=? and type='assistant'", (sid,)))
        for (d,) in rows:
            try:
                p = json.loads(d)
            except Exception:
                continue
            for entry in p.get("content", []):
                if entry.get("type") != "tool":
                    continue
                name = entry.get("name")
                toolnames.add(name)
                inp = json.dumps((entry.get("state") or {}).get("input") or {}, ensure_ascii=False)
                if name == "skill":
                    engaged.append(("skill-tool", inp[:120]))
                for sk in SKILLS:
                    if f"skills/{sk}/" in inp:
                        engaged.append((f"path:{sk}", name))
        # dedupe
        seen, uniq = set(), []
        for e in engaged:
            if e not in seen:
                seen.add(e)
                uniq.append(e)
        out[title] = uniq
        print(f"{title}: tools={sorted(toolnames)}")
        for e in uniq:
            print(f"    engaged {e[0]} via {e[1]}")
    Path("/tmp/opencode/nat_detect.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
