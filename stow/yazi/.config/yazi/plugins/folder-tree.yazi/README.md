# folder-tree.yazi

Toggle Yazi's directory preview between the default one-level listing and a
recursive tree.

## Usage

- `T` — switch between **one-level** and **tree** preview.
- The mode is global and starts in tree mode (`tree = true` in `main.lua`).
- A notification shows the new mode.

Enable it in `yazi.toml`:

```toml
[plugin]
prepend_previewers = [
  { url = "*/", run = "folder-tree" },
]
```

and bind the toggle in `keymap.toml`:

```toml
[[mgr.prepend_keymap]]
on   = "T"
run  = "plugin folder-tree"
desc = "Toggle directory preview: tree / one level"
```

## Behavior

- **One-level mode** delegates to Yazi's built-in `folder` previewer, so icons,
  linemode, scrolling and empty/error states stay the same.
- **Tree mode** runs:

  ```sh
  tree -L <depth> --dirsfirst --noreport -C --filelimit 200 [-a] -- <dir>
  ```

  `-a` follows `[mgr].show_hidden`. Output is capped and cached briefly so
  scrolling with `J`/`K` does not repeatedly spawn `tree`.

Only local directories use tree mode. Remote URLs, missing `tree`, or tree
errors fall back to the one-level previewer.

## Configuration

Edit the constants at the top of `main.lua`:

| Constant    | Default | Meaning                                  |
| ----------- | ------- | ---------------------------------------- |
| `depth`     | `2`     | Levels below the hovered directory.      |
| `max_lines` | `5000`  | Maximum captured `tree` output.          |
| `cache_ttl` | `2.0`   | Seconds before the tree is generated again. |

## Notes

- Requires the `tree` command. Tested with tree 2.2.1.
- Tree output uses `tree`'s `LS_COLORS` colors, not Yazi theme icons.
- The one-level fallback contains a copy of Yazi's preset `folder` previewer
  (MIT) for the case where `require("folder")` is unavailable.
