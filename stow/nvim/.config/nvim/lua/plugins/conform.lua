return {
    "stevearc/conform.nvim",
    opts = {
        -- 配置不同文件类型对应的格式化工具
        formatters_by_ft = {
            python = { "ruff-fix" },
            lua = { "stylua" },
            json = { "prettierd" },
            css = { "prettierd" },
        },
    },
}
