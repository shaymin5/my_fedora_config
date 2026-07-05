-- lua/plugins/blink.lua

return {
    {
        "saghen/blink.cmp",
        version = "*",
        opts = {
            keymap = {
                preset = "none",

                -- 回车：永远只是换行
                ["<CR>"] = { "fallback" },

                -- Tab：直接接受当前 / 第一个候选项
                ["<Tab>"] = { "accept", "fallback" },

                -- 可选
                ["<S-Tab>"] = { "fallback" },

                -- 手动选择候选项
                ["<C-n>"] = { "select_next", "fallback" },
                ["<C-p>"] = { "select_prev", "fallback" },
            },
            completion = {
                trigger = {
                    show_on_keyword = true, -- 正常字母/下划线触发
                    show_on_trigger_character = true, -- 关键：开启 trigger character（包括 . ）
                    show_on_accept_on_trigger_character = true, -- 接受补全后继续打 . 还能触发
                    show_on_insert_on_trigger_character = true, -- 进入 insert 模式后遇到 . 也触发
                },
                list = {
                    -- ✅ 正确类型：table
                    selection = {
                        auto_insert = true,
                        preselect = true,
                    },
                },
            },
            sources = {
                -- Either enable LSP (and optionally buffer) source globally
                default = { "lsp", "path", "snippets", "buffer" },
                -- Or only for Ask
                per_filetype = {
                    opencode_ask = { "lsp", "path", "buffer" },
                },
                -- Display buffer completions (if included above) when no LSP completions are available
                providers = { lsp = { fallbacks = {} } },
            },

            signature = {
                enabled = true,
            },
        },
    },
}
