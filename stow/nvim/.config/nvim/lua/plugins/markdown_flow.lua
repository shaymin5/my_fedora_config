return {
    "jakewvincent/mkdnflow.nvim",
    ft = { "markdown" },
    config = function()
        require("mkdnflow").setup({
            modules = {
                links = true, -- 链接处理
                tables = false, -- 不需要可以关
            },
            links = {
                style = "markdown", -- 或 "wiki"
                implicit_extension = ".md",
                relative_path = true, -- 强烈推荐
            },
            create_missing = true, -- 跳转到不存在文件时自动创建
            mappings = {
                MkdnFollowLink = { { "n", "v" }, "<CR>" }, -- 回车跳转
                MkdnCreateLink = { "n", "<leader>ml" }, -- 创建链接
            },
        })
    end,
}
