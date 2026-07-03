---
name: music-reorganizer
description: >
  Reorganize messy music collections so Jellyfin/Plex/Navidrome recognize them correctly.
  Use this skill whenever the user wants to clean up audio directories, reduce too-many-albums,
  flatten multi-disc subdirectories (Disc 1/Disc 2), tag singles with RELEASETYPE so they
  appear under Singles/EPs instead of Albums, or separate non-music content (drama, SFX,
  dialogue archives) from music files. Trigger on intent to fix/reorganize/clean/tag/flatten
  an audio collection — not on pure analysis/explanation without action, not on single-file
  tag edits, NFO generation, ffmpeg conversion, or Jellyfin server configuration.
compatibility: mutagen (uv add mutagen)
---

# Music Reorganizer

## Overview

When a music collection is dumped into Jellyfin/Plex/Navidrome, common problems arise:

- **Too many albums** — each subdirectory becomes a separate album, even singles
- **Multi-disc splitting** — `Disc 1/`, `Disc 2/` subdirectories each become their own album
- **Non-music mixed in** — drama tracks, SFX archives, dialogue collections pollute the music library
- **Singles vs Albums confusion** — singles show as full albums, cluttering the view

This skill diagnoses these problems and applies a three-step fix.

---

## Phase 1: Analysis

Before touching any files, understand what you're dealing with.

### 1.1 Map the directory tree

Use `find <base> -type d | sort` to see the full hierarchy. Identify:

- Which top-level categories exist (SINGLES, SOUNDTRACKS, ALBUMS, etc.)
- Which subdirectories contain `Disc N/` subdirectories
- Which directories contain non-music content

### 1.2 Sample ID3 tags

Check a few MP3s from each category to see if tags are already populated:

```bash
uv run --with mutagen python3 -c "
import mutagen
audio = mutagen.File('path/to/file.mp3', easy=True)
if audio:
    for k, v in audio.items():
        print(f'  {k}: {v}')
"
```

Key questions:
- Is `album` set? Is it consistent across discs of the same album?
- Is `discnumber` set as `N/M` format?
- Is `artist` and `albumartist` correct?
- Is `date` (year) set?
- Are there any `RELEASETYPE` or MusicBrainz tags?

### 1.3 Classify what's what

Based on directory names and tag content, classify each subdirectory:

| Type | Criteria | Treatment |
|------|----------|-----------|
| Multi-disc album | Has `Disc N/` subdirs, same `album` tag across discs | Flatten (step 2) |
| Single/EP | 1-8 tracks, often a single song + instrumentals | Tag `RELEASETYPE=single` (step 3) |
| Non-music | Drama, SFX, dialogue, work-in-progress archives | Move to `other/` (step 1) |
| Regular album | Single directory, proper tags | Leave as-is |

---

## Phase 2: Reorganization

Three steps, always in this order.

### Step 1: Separate non-music content

Move non-music directories to an `other/` folder, preserving the category-level directory structure:

```
other/
  SOUNDTRACKS/
    S²_WORKS_Annotated_Edition/
  ALBUMS/
    ADDITION/
```

The `other/` directory should NOT be added to the media server's music library.
The user can later decide to make it an "Audiobooks" or "Other" library type.

### Step 2: Flatten multi-disc albums

For each album that has `Disc 1/`, `Disc 2/`, ... subdirectories:

1. Move all audio files from each `Disc N/` into the album's parent directory
2. Prefix filenames with the disc number: `01. Song.mp3` → `1-01. Song.mp3`
3. Move `cover.jpg`/`cover.png` from disc directory to parent only if parent lacks one; discard otherwise
4. Remove the empty `Disc N/` directory

After flattening, Jellyfin groups by the `album` ID3 tag (which is already consistent across discs), and the `discnumber` tag handles ordering within the album. The disc-prefixed filenames are for human readability only.

**Important**: Do NOT flatten discs that were moved to `other/` in step 1 unless the user explicitly requests it. The `other/` content should stay as-is for later review.

### Step 3: Tag singles with RELEASETYPE

For every MP3 under the singles directory, add an ID3 TXXX frame:

```
TXXX:RELEASETYPE = single
```

This tells Jellyfin to classify these releases under "Singles & EPs" rather than "Albums".

Implementation uses mutagen's non-easy API to write custom TXXX frames:

```python
from mutagen.id3 import ID3, TXXX
audio = mutagen.File(path)
audio.tags.add(TXXX(encoding=3, desc='RELEASETYPE', text='single'))
audio.save()
```

Other media servers may use different tag names:
- Plex: reads `RELEASETYPE` (same)
- Navidrome/Subsonic: reads `MUSICBRAINZ_RELEASETYPE` — use `desc='MusicBrainz Album Type'` and `text='single'` instead
- Emby: reads `RELEASETYPE` (same as Jellyfin)

---

## Using the bundled script

A Python script at `scripts/reorganize.py` automates the three steps.

```bash
uv run python3 scripts/reorganize.py \
  --base "/path/to/music/collection" \
  --non-music \
    "SOUNDTRACKS/[1998] S2_WORKS" \
    "ALBUMS/[1996] ADDITION" \
  --singles "SINGLES"
```

Options:
- `--base` — root directory of the collection (required)
- `--non-music` — space-separated relative paths to move to `other/`
- `--singles` — subdirectory containing singles (default: `SINGLES`)
- `--skip-separate` / `--skip-flatten` / `--skip-tag` — skip individual steps

Requirements: `mutagen` (install via `uv add mutagen`).

---

## Common edge cases

### Case: No ID3 tags at all
If files have no embedded tags, directory names are the only metadata source. You'll need to encode album/artist info into tags before reorganizing. Use MusicBrainz Picard or beets for automated tagging.

### Case: Different album tags across discs
If discs of the same album have different `album` tags, Jellyfin won't merge them even after flattening. Fix the tags first: make `album` identical across all discs, set `discnumber` to `1/2`, `2/2`, etc.

### Case: Genre tag is wrong
Many collections have every track tagged `J-Pop` regardless of content. Fixing this is optional — Jellyfin primarily indexes by album/artist, not genre.

### Case: Cover art conflicts
When flattening discs, if each disc has its own `cover.jpg`, keep the parent directory's cover (usually Disc 1's). The script handles this automatically.

### Case: Navidrome/Subsonic target
For Navidrome, modify step 3 to write `MusicBrainz Album Type` instead of `RELEASETYPE`:

```python
audio.tags.add(TXXX(encoding=3, desc='MusicBrainz Album Type', text='single'))
```
