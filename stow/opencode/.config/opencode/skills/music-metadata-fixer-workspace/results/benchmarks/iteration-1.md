# Skill Benchmark: music-metadata-fixer

**Model**: <model-name>
**Date**: 2026-09-19T05:54:51Z
**Evals**: 0, 1, 2 (3 runs each per configuration)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 100% ± 0% | 92% ± 14% | +0.08 |
| Time | 0.0s ± 0.0s | 0.0s ± 0.0s | +0.0s |
| Tokens | 0 ± 0 | 0 ± 0 | +0 |
## Notes

- eval-0 (romaji→japanese) is the only discriminating eval: baseline 6/8, skill 8/8.
- Baseline failed "TYER is 2009" and "exactly one date frame": it silently upgraded ID3v2.3 → v2.4 and kept a lone TDRC, discarding TYER. The skill prevents exactly this.
- eval-1 (rename+sync lrc) and eval-2 (junk lrc): 100% in BOTH configs — easy for the base model. Keep them as regression guards, not discriminators.
- No run damaged audio, cover art, or deleted a real lyric.
- Timing/tokens unavailable in this harness (no total_tokens/duration_ms in task notifications), so those columns read 0.
