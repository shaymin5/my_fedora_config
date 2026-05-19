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
        list = {
          -- ✅ 正确类型：table
          selection = {
            auto_insert = true,
            preselect = true,
          },
        },
      },

      signature = {
        enabled = true,
      },
    },
  },
}
