return {
    "jakewvincent/mkdnflow.nvim",
    ft = { "markdown" },
    config = function()
        require("mkdnflow").setup({
            modules = {
                links = true,
                tables = false,
            },
            links = {
                style = "markdown",
                implicit_extension = ".md",
            },
            perspective = {
                priority = "first", -- 优先用当前文件所在目录解析相对路径
            },
            mappings = {
                -- 关键修复：用 MkdnEnter 而不是 MkdnFollowLink
                MkdnEnter = { { "n", "v" }, "<CR>" }, -- 回车跳转链接
                MkdnFollowLink = false, -- 避免冲突
                MkdnCreateLink = { "n", "<leader>ml" },
                -- 可选：增加 gf 跳转（更符合 nvim 习惯）
                MkdnGoBack = { "n", "<BS>" }, -- Backspace 返回上一个文件
            },
        })
    end,
}
