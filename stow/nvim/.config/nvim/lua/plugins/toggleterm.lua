return {
    "akinsho/toggleterm.nvim",
    version = "*",
    cmd = "ToggleTerm",
    opts = {
        -- 基本设置
        size = 20,
        open_mapping = false, -- 禁用内置快捷键
        hide_numbers = false, -- 显示行号
        shade_filetypes = {},
        shade_terminals = false, -- 重要：必须为 false 才能使高亮生效
        start_in_insert = true,
        insert_mappings = true,
        persist_size = false,
        direction = "float", -- 浮动终端

        -- 浮动窗口设置
        float_opts = {
            border = "rounded", -- 圆角边框
            width = function() -- 动态宽度
                return math.floor(vim.o.columns * 0.8) -- 80% 屏幕宽度
            end,
            height = function() -- 动态高度
                return math.floor(vim.o.lines * 0.8) -- 80% 屏幕高度
            end,
            winblend = 20, -- 透明度
        },

        -- 终端高亮
        highlights = {
            -- 这些高亮会应用于终端内容
            Normal = {
                link = "Normal", -- 继承常规 Normal 高亮
            },
            NormalFloat = {
                link = "NormalFloat", -- 继承浮动窗口高亮
            },
            FloatBorder = {
                guifg = "#9a9efa", -- 紫色边框
            },
            -- 为了避免光标闪烁穿透背景，手动设置一个不透明的背景色
            TermBackground = {
                guibg = "#1e1e1e", -- 设置为一个不透明的背景色
            },
        },
    },
}
