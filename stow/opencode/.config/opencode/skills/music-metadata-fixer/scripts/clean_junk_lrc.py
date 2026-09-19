#!/usr/bin/env python3
"""Delete only provably-junk .lrc lyric files.

Usage:
    uv run --with mutagen python clean_junk_lrc.py [DIR] [--recursive] [--apply]

Junk is proven by a placeholder signature (default: "纯音乐，请欣赏", the QQ
Music instrumental marker). Add --signature for other markers. Optional
--check-duration / --check-header catch lyrics whose [total:] or [ti:]/[ar:]
disagree with the audio, but keep them off unless the user wants that, so a
legitimate translation is never deleted.

Works with MP3 and FLAC audio. Files matching no criterion are always kept.
Prints the plan first; deletes only with --apply. --recursive is safe: each .lrc
is always checked against the audio sitting in its own folder.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from taglib_common import AUDIO_EXTS, iter_lrc, read_info

DEFAULT_SIGNATURES = ("纯音乐，请欣赏",)


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-16", "gb18030", "shift_jis", "latin1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def header_value(text: str, tag: str) -> str:
    m = re.search(rf"\[{tag}:([^\]]*)\]", text, re.IGNORECASE)
    return m.group(1) if m else ""


def matching_audio(lrc: Path) -> Path | None:
    return next((lrc.with_suffix(ext) for ext in sorted(AUDIO_EXTS) if lrc.with_suffix(ext).exists()), None)


def junk_reasons(
    lrc: Path,
    signatures: tuple[str, ...],
    check_duration: bool,
    check_header: bool,
    max_drift: float,
) -> list[str]:
    text = read_text(lrc)
    reasons = [f"signature {sig!r}" for sig in signatures if sig in text]

    audio = matching_audio(lrc)
    if audio is None:
        return reasons

    info = read_info(audio)
    title = info.fields.get("title", "")
    artist = info.fields.get("artist", "")

    if check_header:
        lrc_title = header_value(text, "ti")
        lrc_artist = header_value(text, "ar")
        if lrc_title and title and lrc_title not in title and title not in lrc_title:
            reasons.append(f"title mismatch ({lrc_title!r} vs {title!r})")
        if lrc_artist and artist and lrc_artist not in artist and artist not in lrc_artist:
            reasons.append(f"artist mismatch ({lrc_artist!r} vs {artist!r})")

    if check_duration:
        total = header_value(text, "total")
        if total.isdigit() and info.duration is not None:
            drift = abs(int(total) / 1000.0 - info.duration)
            if drift > max_drift:
                reasons.append(f"duration off by {drift:.0f}s")

    return reasons


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--recursive", "-r", action="store_true", help="walk subfolders too")
    ap.add_argument("--signature", action="append", default=None,
                    help="extra junk signature (repeatable)")
    ap.add_argument("--check-duration", action="store_true")
    ap.add_argument("--check-header", action="store_true")
    ap.add_argument("--max-drift", type=float, default=10.0)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    directory = Path(str(args.directory)).expanduser().resolve()
    raw_signatures: list[str] | None = args.signature
    signatures = tuple(str(s) for s in raw_signatures) if raw_signatures else DEFAULT_SIGNATURES
    check_duration = bool(args.check_duration)
    check_header = bool(args.check_header)
    max_drift = float(args.max_drift)
    recursive = bool(args.recursive)
    apply = bool(args.apply)

    lrcs = iter_lrc(directory, recursive)
    print(f"{'APPLY' if apply else 'DRY-RUN'}  {directory}  ({len(lrcs)} lrc files"
          f"{', recursive' if recursive else ''})")
    print(f"signatures: {signatures}  check_duration={check_duration}  "
          f"check_header={check_header}\n")

    doomed: list[Path] = []
    current_dir: Path | None = None
    for lrc in lrcs:
        if lrc.parent != current_dir:
            current_dir = lrc.parent
            rel = "." if current_dir == directory else str(current_dir.relative_to(directory))
            print(f"[{rel}]")
        reasons = junk_reasons(lrc, signatures, check_duration, check_header, max_drift)
        if reasons:
            doomed.append(lrc)
            print(f"DELETE  {lrc.name}  <- {', '.join(reasons)}")
        else:
            print(f"keep    {lrc.name}")

    print(f"\n{len(doomed)} of {len(lrcs)} lrc files flagged as junk")
    if not apply:
        print("Dry-run complete. Re-run with --apply to delete.")
        return 0

    for lrc in doomed:
        _ = lrc.unlink()
    print(f"Deleted {len(doomed)} junk lrc file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
