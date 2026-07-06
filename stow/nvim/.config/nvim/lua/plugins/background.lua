return {
    {
        "catppuccin/nvim",
        name = "catppuccin",
        lazy = false,
        priority = 1000,
        config = function()
            require("catppuccin").setup({
                flavour = "mocha", -- latte / frappe / macchiato / mocha（推荐 mocha）
                background = {
                    light = "latte",
                    dark = "mocha",
                },
                transparent_background = true, -- 核心：主背景透明
                float = {
                    transparent = true, -- 浮动窗口透明
                    solid = false,
                },
                term_colors = true,
                dim_inactive = {
                    enabled = false, -- 建议关闭，否则会变暗
                },
                show_end_of_buffer = false,
                integrations = {
                    -- blink_cmp = true,
                    -- blink_indent = true,
                    -- blink_pairs = true,
                    -- cmp = true,
                    -- gitsigns = true,
                    -- nvimtree = true,
                    -- neotree = true, -- 如果你用 neo-tree
                    -- telescope = true,
                    -- notify = true,
                    -- mini = true,
                    -- render_markdown = true,
                    -- noice = true,
                    -- 添加你使用的其他插件
                },
                custom_highlights = function(colors)
                    return {
                        Normal = { bg = "NONE" },
                        NormalNC = { bg = "NONE" },
                        NormalFloat = { bg = "NONE" },
                        FloatBorder = { fg = colors.surface2, bg = "NONE" },

                        NeoTreeNormal = { bg = "NONE" },
                        TelescopeNormal = { bg = "NONE" },

                        markdownCode = { bg = "NONE" },
                        markdownCodeBlock = { bg = "NONE" },
                        markdownCodeDelimiter = { bg = "NONE" },

                        ["@markup.raw"] = { bg = "NONE" },
                        ["@markup.raw.markdown"] = { bg = "NONE" },

                        -- render-markdown 关键组
                        RenderMarkdownCode = { bg = "NONE" },
                        RenderMarkdownCodeBlock = { bg = "NONE" },
                        RenderMarkdownCodeInline = { bg = "NONE" },
                        RenderMarkdownH1Bg = { bg = "NONE" }, -- 如果标题也有背景
                        RenderMarkdownH2Bg = { bg = "NONE" },

                        -- Blink 补全菜单透明
                        -- Pmenu 系列（Blink 补全的核心）
                        Pmenu = { bg = "NONE" },
                        PmenuSel = { bg = colors.surface0 }, -- 选中项保留一点颜色
                        PmenuThumb = { bg = colors.surface2 },
                        PmenuSbar = { bg = colors.surface1 },
                        -- Blink 相关
                        BlinkCmpMenu = { bg = "NONE" },
                        BlinkCmpMenuBorder = { fg = colors.surface2, bg = "NONE" },
                        BlinkCmpMenuSelection = { bg = colors.surface0 },

                        BlinkCmpDoc = { bg = "NONE" },
                        BlinkCmpDocBorder = { fg = colors.surface2, bg = "NONE" },
                    }
                end,
            })
            vim.cmd.colorscheme("catppuccin") -- 必须在 setup 之后调用
        end,
    },
    {
        "xiyaowong/transparent.nvim",
        lazy = false,
        opts = {
            extra_groups = {
                "NormalFloat",
                "NvimTreeNormal",
                "NeoTreeNormal",
                "TelescopeNormal",
                "WhichKeyNormal",
                "NotifyBackground",
            },
        },
    },
}
