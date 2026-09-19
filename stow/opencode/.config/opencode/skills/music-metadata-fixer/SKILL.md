---
name: music-metadata-fixer
description: >
  修复音乐文件的元数据（标签）和/或文件名，并在动手前先判断文件名与标签到底哪边才是错的。
  当用户想改动【音乐文件的文件名】或【音乐文件的元数据/标签】时使用本 skill。例如：
  音乐文件名整理/规范/修复/重命名；文件名里的歌名或艺术家不对；标题是罗马音/拼音，
  要改回日文/中文/韩文原名；文件名和标签对不上（缺音轨号、乱码、格式不统一）；
  专辑名/艺术家/专辑艺术家/流派/年份/音轨号 不一致或错误；mp3/flac 标签、ID3 标签的
  修复与统一；ID3v1 残留、重复日期帧、FLAC 上多余的 ID3 块；歌词文件(.lrc)错乱、
  是别的歌的、需要清理。支持 MP3(ID3v2.3/v2.4) 与 FLAC(Vorbis)，并保留文件原有的 ID3 版本。
  支持父目录下还有子文件夹（多个专辑、Disc 1/Disc 2 多碟）：会先扫描目录树，再逐张处理。
  English: fix embedded tags and filenames in a music collection — romanized titles
  back to the original script, tags that disagree across an album, filenames that
  don't match the tags, legacy/duplicate ID3, junk .lrc lyrics.
  边界：只有当用户想改【文件名或标签值】时才触发。若意图是【目录/库结构】——例如
  "整理音乐库"、"整理文件夹/目录"、"专辑太多"、"合并或拆分专辑"、"Disc 1/Disc 2 拉平"、
  "单曲归类"——那是 music-reorganizer 的职责，不要用本 skill。但"整理音乐库的标签/元数据"
  这类明确指向标签的请求，仍要用本 skill（看的是想改什么，不是出现了"整理"二字）。
  生成 NFO/刮削交给 anime-nfo-generator。不用于音频转码/格式转换、单纯更换封面、
  播放器或服务器配置。
compatibility: mutagen (uv run --with mutagen python); internet access for looking up official releases
---

# Music Metadata Fixer

Fix what's *inside* the tags and what the files are *called* — but only after
establishing what the correct values actually are and what the user wants.

## Core principle: diagnose first, never assume

**Do not assume the filename is right and the tags are wrong — or the reverse.**
Any of these is common, and they can even differ file by file within one folder:

- filename correct, tags wrong (or missing)
- tags correct, filename wrong or messy
- **both wrong** — the real title has to be found from an external source
- both present but disagreeing, with no way to tell which is right

The five capabilities below are a **toolbox, not a mandatory pipeline**. Pick the
ones the evidence calls for, in whatever order makes sense. Do not start editing
because a workflow says so; start editing because you have established the
target values (or the user told you them) and a safe way to get there.

## Step 0 — Understand the situation (always do this)

1. **What does the user actually want?** Fix how it displays in the player? Tidy
   the filenames? Remove junk lyrics? All of it? Ask if it isn't clear from the
   request — the right action differs a lot.
2. **Is this one folder, or a tree?** If the target contains subfolders, run
   (read-only):
   ```bash
   uv run --with mutagen python scripts/scan_tree.py "/path/to/music"
   ```
   It lists every folder that directly holds audio, summarises the tags inside
   each, flags disc-like siblings, and points out subfolders with no audio.
   A collection is usually `<root>/<album>/` or `<root>/<album>/Disc N/`, which
   is why the single-level scripts below find nothing in the parent — do not
   read "0 files" as "clean".
3. **Look before you touch.** Run both of these (read-only), adding
   `--recursive` if the tree scan showed several audio folders:
   ```bash
   uv run --with mutagen python scripts/compare_names.py "/path/to/album" [--recursive]
   uv run --with mutagen python scripts/inspect_tags.py  "/path/to/album" [--recursive]
   ```
   `compare_names.py` puts the name-derived title/artist/track next to the
   tag-derived ones and flags agreement, so you can see *which side is off*.
   `inspect_tags.py` reports tag values, container, ID3 version, legacy junk,
   lyric-file problems, and any extension/content mismatch (e.g. a file named
   `.flac` that is really an MP3).
4. **Decide, per field (and possibly per file), which source is authoritative:**
   the filename, the existing tags, or an external release listing. Summarize
   what you found for the user when it isn't obvious.

### One folder = one release

The scripts are built to be run **once per release folder** — that keeps
per-album values (album, artist, date) from leaking across different releases.
`--recursive` is safe for the read-only scripts and for operations that depend
only on each file's own content (`rename_by_tags.py`, `clean_legacy_tags.py`,
`clean_junk_lrc.py`, and `set_fields.py --title-from-filename`). It is
**not** safe to push one `--album "..."` across a tree of several albums;
`set_fields.py` refuses that unless you pass `--allow-cross-dir-constants`, and
you should instead run it once per folder. See "Subfolders and multiple
releases" below.

### Which side to trust — the decision, not an assumption

| Evidence | Likely situation | Direction |
|---|---|---|
| filename native script, tags romanized/translated | tags wrong | set tags from filename, then clean |
| tags native, filename romanized/messy/wrong | filenames wrong | rename from tags (+ sync lrc) |
| both present but both look wrong / differ, same script | **ground truth unknown** | look up the official release; if still unsure, ask the user |
| tags missing, filename plausible | tags incomplete | fill from filename (confirm first) |
| filename and tags agree but both look improbable | source itself unreliable | external lookup + confirm |
| different files point different ways | mixed sources in one folder | decide per file — do not batch |

A writing-system mismatch (one side kana/han/hangul, the other Latin) is a
*useful hint*, not proof. If both sides look plausible, treat it as unknown.

## Finding ground truth

When neither the filename nor the tags can be trusted, find the real release
before editing: label/artist site, Bandai/Aniplex pages, Bangumi, AniDB,
Japanese Wikipedia, MusicBrainz, soundtrack review blogs. Match on **track
count, durations, composer/artist and ordering**, not just one title. A 46-track
album may legitimately be missing a few files, so track numbers come from the
real listing, never from `enumerate()`.

**Confirm the found values with the user before mass-applying them** — especially
artist/album/albumartist spellings, the year, and any one-off guest track (a
vocal theme on an OST needs an explicit decision about its artist and filename
prefix).

## Subfolders and multiple releases

When the target is a parent folder, the subfolders are **not** all the same
thing. Classify each folder that holds audio before touching anything:

| What the subfolder is | How to recognise it | What to do |
|---|---|---|
| one release split across discs | siblings named `Disc 1`/`Disc 2`, `CD1`…; same album/artist | **ask the user first** (see below) |
| separate releases in one parent | different album/artist values per folder | process each folder as its own run; never push one `--album` across them |
| non-music | no audio directly (scans, artwork, `drama/`, SFX) | leave alone; do not tag or rename |

Rules:

- Operate **one release per invocation**. `scan_tree.py` gives you the list of
  audio folders; run the toolbox once per folder with that folder's own values.
- Disc-like siblings: do **not** assume they are one album. Detect them
  (`scan_tree.py` flags them) and **ask the user** whether to treat them as one
  release (share album/albumartist, disc numbers) or as separate releases.
- A subfolder with no audio is not a bug — but do not treat its presence as
  "nothing to do" for the whole tree; say so explicitly in your report.
- `--recursive` is fine for the read-only scripts and for content-derived
  operations; for shared literals in `set_fields.py`, run per folder (the
  script enforces this).

## When to stop and ask the user

Ask rather than guess whenever any of these is true:

- the filename and the tags disagree and no authoritative release was found;
- you would have to invent a spelling, romanization, or title ordering;
- it's unclear whether the user wants native script or keeps an English title;
- the folder may actually contain several releases, artists, or discs — or
  disc-like subfolders (`Disc 1`/`Disc 2`) that could be one album **or**
  separate releases;
- you're about to **delete** files (junk lyrics, duplicates) or **bulk-rename**
  and the intended scope isn't explicit;
- the evidence conflicts (e.g. durations don't match the presumed tracklist).

For non-trivial or ambiguous sets, present your diagnosis and the proposed
changes, and get a yes/no before applying. For a small, unambiguous case where
the user already stated the values, you can proceed directly.

---

## The toolbox

All scripts are `uv run --with mutagen python scripts/<name>.py ...`, share
`scripts/taglib_common.py`, default to **dry-run** (write only with `--apply`),
and support **MP3 (ID3v2.3/v2.4)** and **FLAC (Vorbis)**. The file's ID3 major
version is always preserved. Read-only scripts accept `--recursive`; write
scripts that are safe to recurse do too (see the table).

| Script | What it's for |
|---|---|
| `scan_tree.py` | Read-only. Map a folder **tree**: which subfolders hold audio, per-folder tag summary, disc-like siblings, non-music folders. **Run this first when the target has subfolders.** |
| `compare_names.py` | Read-only. Filename vs tag reconciliation + a hint at which side is authoritative. **Start here.** |
| `inspect_tags.py` | Read-only. Tag values, container/version, ID3v1 residue, duplicate dates, stray ID3 on FLAC, lyric pairing/junk, extension/content mismatch. |
| `set_fields.py` | Write chosen tag values (artist/album/albumartist/genre/date); `--title-from-filename` copies the native name from the filename across a folder. `--recursive` is gated for shared literals. |
| `rename_by_tags.py` | Rename audio (and `.lrc`) *from the tags*; `--pattern`, `--artist-field`, `--sync-lrc`, `--recursive` (collision-checked per folder). |
| `clean_legacy_tags.py` | MP3: strip ID3v1, collapse date frames to one version-correct frame. FLAC: strip an illegal leading ID3. Safe with `--recursive`. |
| `clean_junk_lrc.py` | Delete only provably-junk `.lrc` (signature-based; never guesses). Safe with `--recursive`. |

Examples of *different* situations, each using a different subset:

```bash
# a parent folder of several albums -> map it, then act per folder
uv run --with mutagen python scripts/scan_tree.py DIR
uv run --with mutagen python scripts/set_fields.py "DIR/Album A" --artist "..." --album "..." --apply

# filename right, tags romanized -> copy names from filename into tags, then clean
# (safe across a tree: the value comes from each file's own name)
uv run --with mutagen python scripts/set_fields.py DIR --title-from-filename --recursive --apply
uv run --with mutagen python scripts/clean_legacy_tags.py DIR --recursive --apply

# tags right, filenames messy -> rename from tags, keep lyrics in sync
uv run --with mutagen python scripts/rename_by_tags.py DIR \
    --pattern "{track:02d} {artist} - {title}" --sync-lrc --apply

# both wrong -> first establish the real titles (web + user confirm), then
# set the tags AND rename, using the two commands above with the real values
```

### Known pitfalls (so you don't create new problems)

**Version policy.** Never change a file's ID3 major version. A v2.3 file keeps
`TYER`; a v2.4 file keeps `TDRC`. `taglib_common.write_fields()` reads the version
from the header and writes the matching frame, so both directions are safe; do
not hand-write `v2_version=3` blindly.

**The mutagen double-date trap.** mutagen translates frames in memory on load
(v2.3 `TYER` shows up as `TDRC`). If you set a fresh `TYER` and save without
deleting `TDRC` first, the file gets **both** frames — two dates — and reading it
back the default way hides this. Load with `ID3(path, translate=False)` and
delete every date frame before writing one. Verify on disk (raw `b"TYER"` /
`b"TDRC"` counts, and the last 128 bytes are not `TAG`), not through mutagen's
translated view.

**Don't contaminate v2 from v1.** Load with `load_v1=False` so a stale ID3v1
genre/comment doesn't leak into `TCON`/`COMM`.

**Rename lyrics together.** Players match `.lrc` by identical basename; renaming
only the audio silently breaks lyrics. Use `--sync-lrc`.

**Extensions lie.** A `.flac` can actually be an MP3 (a leading `ID3` block then
MPEG frame sync) or the reverse. The scripts pick the parser from the magic
bytes, so a mis-named file is still tagged correctly, and `inspect_tags.py` /
`scan_tree.py` report the mismatch. Do not "fix" it by renaming the extension
unless the user asks — and never assume a `.flac` is lossless FLAC.

**Delete conservatively.** Junk lyrics are proven by a placeholder signature
(`纯音乐，请欣赏` by default), never by "looks suspicious". Run without `--apply`
and read the list first. Embedded `USLT` junk is a separate decision.

## Safety checklist

- **Check for subfolders first** (`scan_tree.py`); never read a single-level
  "0 files" as "nothing wrong".
- Diagnose (`compare_names.py` + `inspect_tags.py`) before editing.
- Operate one release per folder; never push shared `--album/--artist` values
  across a tree, and **ask before assuming disc siblings are one album**.
- Confirm ground truth, and confirm the plan when the case is ambiguous.
- Dry-run first; `--apply` only after reading the plan output.
- Preserve ID3 version, cover art, lyrics, and audio data; verify after writing.
- Rename audio and `.lrc` together.
- Only delete files that match a proven junk signature.
- Re-run `inspect_tags.py` at the end and confirm the result matches the intent.
