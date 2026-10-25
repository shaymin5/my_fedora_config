# merge-paste.yazi (vendored)

Conflict-aware paste for Yazi. Upstream:
[`PHONE1X/merge-paste.yazi`](https://github.com/PHONE1X/merge-paste.yazi),
using the maintained copy from
[`PHONE1X/far2yazi`](https://github.com/PHONE1X/far2yazi/tree/main/plugins/merge-paste.yazi)
at commit `b46079d` (it fixes `cx.yanked` File-vs-URL handling and supports
the `cwd` argument).

The unmodified upstream README is kept as `README.upstream.md`.

## Binding in this config

```toml
[[mgr.prepend_keymap]]
on   = "p"
run  = "plugin merge-paste -- cwd"
desc = "Paste (ask on conflict: overwrite/merge/skip/rename)"
```

- `p` pastes into the **current directory**, never into a hovered folder.
- `P` remains Yazi's built-in `paste --force` (silent overwrite).
- `y` / `x` remain the normal copy / cut yank actions.

## Conflict choices

When an item with the same name already exists at the destination:

| Key | Action |
| --- | --- |
| `o` | Overwrite (delete the destination, then paste) |
| `m` | Merge folders (overwrite same-named contents; keep destination-only files) |
| `s` | Skip |
| `r` | Rename with a `_1`, `_2`, ... suffix |
| `q` | Cancel the paste |

After choosing, `y` / `n` decides whether to apply the same choice to all
remaining conflicts.

## Local changes

Two safety guards were added to `main.lua`:

1. **Same-path paste** (pasting an item back into its own directory): instead
   of offering Overwrite/Merge (which would `rm -rf` the source), it
   automatically pastes under a `_1` suffix.
2. **Directory into its own subdirectory**: refused, because `cp -a` would
   recurse until the disk fills. Symlinks are exempt since `cp -a` copies the
   link itself.

## Caveats

- Uses `cp -a` / `mv` / `rm -rf`, so large transfers do not appear in Yazi's
  task progress UI; a notification is shown when the paste finishes.
- "Merge" is an overwrite-style merge, not a per-file diff/3-way merge.
- When nothing is yanked inside Yazi, it falls back to the system clipboard
  (`wl-clipboard` on Wayland, `xclip` on X11).
