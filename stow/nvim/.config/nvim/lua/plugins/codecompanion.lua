return {
    "olimorris/codecompanion.nvim",
    version = "^19.0.0",
    opts = {
        interactions = {
            chat = {
                adapter = "opencode",
                model = "deepseek-v4-pro",
            },
        },
    },
    dependencies = {
        "nvim-lua/plenary.nvim",
        "nvim-treesitter/nvim-treesitter",
    },
}
