return {
    "sphamba/smear-cursor.nvim",

    opts = {
        -- Smear cursor when switching buffers or windows.
        smear_between_buffers = true,

        -- Smear cursor when moving within line or to neighbor lines.
        -- Use `min_horizontal_distance_smear` and `min_vertical_distance_smear` for finer control
        smear_between_neighbor_lines = true,

        -- Draw the smear in buffer space instead of screen space when scrolling
        scroll_buffer_space = true,

        -- Set to `true` if your font supports legacy computing symbols (block unicode symbols).
        -- Smears and particles will look a lot less blocky.
        legacy_computing_symbols_support = false,

        -- Smear cursor in insert mode.
        -- See also `vertical_bar_cursor_insert_mode` and `distance_stop_animating_vertical_bar`.
        smear_insert_mode = true,

        trail_length = 15, -- 长拖影长度
        stiffness = 0.4, -- 中慢动画速度
        trailing_stiffness = 0.2, -- 缓慢拖影消失速度
        cterm_cursor_colors = { 226, 230, 231 },
    },
}
