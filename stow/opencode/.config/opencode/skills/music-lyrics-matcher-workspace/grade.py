#!/usr/bin/env python3
"""Grade an iteration of music-lyrics-matcher runs and build benchmark.json."""
import json
import re
import sys
from pathlib import Path

WS = Path(__file__).resolve().parent
SKILL = WS.parent / "music-lyrics-matcher"
sys.path.insert(0, str(SKILL / "scripts"))
from tag_common import SPACE_AFTER_TAG, TIMED_RE, iter_audio, line_seconds, normalize_lrc, read_tags  # noqa: E402

FIX = WS / "fixtures"
ID_TAG = re.compile(r"^\[(ti|ar|al|au|by|ly|mu|offset|re|ve|length):", re.I)
INSTR = re.compile(r"(instrumental|off[\s-]?vocal|カラオケ|karaoke|インスト|纯音乐|伴奏)", re.I)
INFO3 = ("作词：", "作词:")
INFO4 = ("作曲：", "作曲:")
INFO5 = ("歌手：", "歌手:")
PLACEHOLDER = "纯音乐"

EVALS = [(0, "basic-mp3-album"), (1, "mixed-formats"),
         (2, "clean-top-keep-translations"), (3, "instrumental-and-normal")]


def text_of(line):
    return re.sub(r"^\[[^\]]*\]\s*", "", line).strip()


def check_run(eval_id, evdir, config):
    indir, outdir = evdir / config / "input", evdir / config / "outputs"
    audios = list(iter_audio(indir))
    e = {k: True for k in "12345678"}
    ev = {k: [] for k in "12345678"}

    for audio in audios:
        lrc = outdir / (audio.stem + ".lrc")
        if not lrc.exists():
            e["1"] = False
            ev["1"].append(f"{audio.name}: 缺 lrc")
            continue
        lines = lrc.read_text(encoding="utf-8").splitlines()
        tags = read_tags(audio)
        title = tags["title"] or audio.stem
        album = tags["album"]
        if any(ID_TAG.match(l) for l in lines):
            e["5"] = False
            ev["5"].append(f"{audio.name}: {next(l for l in lines if ID_TAG.match(l))}")
        spaced = [l for l in lines if SPACE_AFTER_TAG.match(l)]
        if spaced:
            e["8"] = False
            ev["8"].append(f"{audio.name}: {len(spaced)} 行，例如 {spaced[0]!r}")
        timed = [(s, l) for l in lines if (s := line_seconds(l)) is not None]

        if INSTR.search(title):
            # instrumental: plain text, 4 info lines + blank + 纯音乐
            if timed:
                e["3"] = False
                ev["3"].append(f"{audio.name}: 纯音乐不应有时间戳")
            body = list(lines)
            while body and not body[0].strip():
                body.pop(0)
            non_empty = [l for l in body if l.strip()]
            if not non_empty or text_of(non_empty[-1]) != PLACEHOLDER:
                e["7"] = False
                ev["7"].append(f"{audio.name}: 缺少『纯音乐』行")
                continue
            ph = max(i for i, l in enumerate(body) if l.strip())
            if body[ph - 1].strip() != "":
                e["7"] = False
                ev["7"].append(f"{audio.name}: 纯音乐前应有空行")
            info = [text_of(l) for l in body[:ph - 1] if l.strip()]
            if len(info) < 4 or info[0] != title or (album and info[1] != album) \
                    or not info[2].startswith(INFO3) or not info[3].startswith(INFO4):
                e["2"] = False
                ev["2"].append(f"{audio.name}: {info}")
        else:
            if len(timed) < 6:
                e["4"] = False
                ev["4"].append(f"{audio.name}: 时间轴行不足({len(timed)})")
                continue
            top, T = timed[:5], timed[5][0]
            tt = [text_of(l) for _, l in top]
            if tt[0] != title or tt[1] != album or not tt[2].startswith(INFO3) \
                    or not tt[3].startswith(INFO4) or not tt[4].startswith(INFO5):
                e["2"] = False
                ev["2"].append(f"{audio.name}: {tt}")
            expect = [T * i / 5 for i in range(5)]
            got = [s for s, _ in top]
            if any(abs(g - x) > 0.03 for g, x in zip(got, expect)):
                e["3"] = False
                ev["3"].append(f"{audio.name}: got {got} expect {[round(x, 2) for x in expect]}")
            for (s1, _), (s2, _) in zip(timed[4:], timed[5:]):
                if s2 < s1 - 0.001:
                    e["4"] = False
                    ev["4"].append(f"{audio.name}: 时间轴非递增")
                    break

    if eval_id == 2:
        for audio in audios:
            src = FIX / "eval-existing" / (audio.stem + ".lrc")
            lrc = outdir / (audio.stem + ".lrc")
            if not (src.exists() and lrc.exists()):
                continue
            body = [normalize_lrc(l).strip() for l in src.read_text(encoding="utf-8").splitlines()
                    if l.strip() and not ID_TAG.match(l)]
            out = {normalize_lrc(l).strip() for l in lrc.read_text(encoding="utf-8").splitlines()}
            missing = [b for b in body if b not in out]
            if missing:
                e["6"] = False
                ev["6"].append(f"{audio.name}: 丢失 {len(missing)} 行，例如 {missing[0]}")

    exp = [
        ("所有音频都有同名 .lrc", e["1"], "; ".join(ev["1"]) or f"{len(audios)} 个齐全"),
        ("顶部信息行顺序正确", e["2"], "; ".join(ev["2"]) or "全部正确"),
        ("时间戳规则正确（有歌词 0..4T/5；纯音乐无时间戳）", e["3"],
         "; ".join(ev["3"]) or "全部正确"),
        ("歌词带时间轴且递增", e["4"], "; ".join(ev["4"]) or "全部正确"),
        ("顶部无 [ti:]/[al:]/[ly:] 等 ID 头部标签", e["5"], "; ".join(ev["5"]) or "无残留"),
        ("歌词行时间戳后没有多余空格", e["8"], "; ".join(ev["8"]) or "无多余空格"),
    ]
    if eval_id == 2:
        exp.append(("原手动中文翻译行仍存在且未被替换", e["6"], "; ".join(ev["6"]) or "翻译完整保留"))
    if eval_id == 3:
        exp.append(("纯音乐文件为 4 行信息 + 空行 + 纯音乐", e["7"], "; ".join(ev["7"]) or "结构正确"))

    passed = sum(1 for _, p, _ in exp if p)
    return {"expectations": [{"text": t, "passed": p, "evidence": v} for t, p, v in exp],
            "summary": {"passed": passed, "failed": len(exp) - passed, "total": len(exp),
                        "pass_rate": round(passed / len(exp), 4)}}


def main():
    it = WS / (sys.argv[1] if len(sys.argv) > 1 else "iteration-2")
    evals_json = json.loads((SKILL / "evals" / "evals.json").read_text(encoding="utf-8"))
    prompts = {e["id"]: e for e in evals_json["evals"]}
    runs = []
    for eval_id, name in EVALS:
        evdir = it / name
        meta = prompts[eval_id]
        (evdir / "eval_metadata.json").write_text(json.dumps({
            "eval_id": eval_id, "eval_name": name, "prompt": meta["prompt"],
            "assertions": meta["expectations"]}, ensure_ascii=False, indent=1), encoding="utf-8")
        for config in ("with_skill", "without_skill"):
            g = check_run(eval_id, evdir, config)
            (evdir / config / "grading.json").write_text(
                json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
            runs.append({"eval_id": eval_id, "eval_name": name, "configuration": config,
                         "run_number": 1, "result": {
                             "pass_rate": g["summary"]["pass_rate"],
                             "passed": g["summary"]["passed"], "failed": g["summary"]["failed"],
                             "total": g["summary"]["total"], "time_seconds": 0, "tokens": 0},
                         "expectations": g["expectations"]})
            print(f"{name:28} {config:14} {g['summary']['passed']}/{g['summary']['total']}")

    ws = [r["result"]["pass_rate"] for r in runs if r["configuration"] == "with_skill"]
    wo = [r["result"]["pass_rate"] for r in runs if r["configuration"] == "without_skill"]
    bench = {
        "metadata": {"skill_name": "music-lyrics-matcher", "skill_path": str(SKILL),
                     "executor_model": "general-subagent", "evals_run": [0, 1, 2, 3],
                     "runs_per_configuration": 1},
        "runs": runs,
        "run_summary": {
            "with_skill": {"pass_rate": {"mean": sum(ws) / len(ws), "stddev": 0.0, "min": min(ws), "max": max(ws)},
                           "time_seconds": {"mean": 0, "stddev": 0, "min": 0, "max": 0},
                           "tokens": {"mean": 0, "stddev": 0, "min": 0, "max": 0}},
            "without_skill": {"pass_rate": {"mean": sum(wo) / len(wo), "stddev": 0.0, "min": min(wo), "max": max(wo)},
                              "time_seconds": {"mean": 0, "stddev": 0, "min": 0, "max": 0},
                              "tokens": {"mean": 0, "stddev": 0, "min": 0, "max": 0}},
            "delta": {"pass_rate": f"{sum(ws)/len(ws) - sum(wo)/len(wo):+.2f}", "time_seconds": "+0", "tokens": "+0"},
        },
        "notes": ["基线通过明确禁用 skill 实现（本环境 skill 全局注册）。",
                  "with_skill 与 baseline 的差距主要在输出格式偏好：5 行信息 / T/5 间隔 / 纯音乐占位。",
                  "未捕获 token/时长数据，time/tokens 记为 0。"],
    }
    (it / "benchmark.json").write_text(json.dumps(bench, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nbenchmark.json written")


if __name__ == "__main__":
    main()
