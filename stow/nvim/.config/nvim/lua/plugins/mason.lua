return {
    {
        "mason-org/mason.nvim",
        opts = {
            ensure_installed = {
                -- LSP
                "basedpyright",
                "lua-language-server",

                -- formatter
                "stylua",
                "prettierd",
                "taplo",
                "xmlformatter",
                "ruff",
                "markdown-toc",
                "markdownlint-cli2",
                "shfmt",

                -- lint
            },
        },
    },
}
