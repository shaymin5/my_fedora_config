return {
    "nickjvandyke/opencode.nvim",
    version = "*", -- Latest stable release
    config = function()
        vim.o.autoread = true -- Required for `vim.g.opencode_opts.events.reload`

        -- Recommended/example keymaps
        vim.keymap.set({ "n", "x" }, "<leader>oa", function()
            require("opencode").ask("@this: ")
        end, { desc = "Ask OpenCode…" })
        vim.keymap.set({ "n", "x" }, "<leader>os", function()
            require("opencode").select()
        end, { desc = "Select OpenCode…" })

        vim.keymap.set({ "n", "x" }, "go", function()
            return require("opencode").operator("@this ")
        end, { desc = "Append range to OpenCode", expr = true })
    end,
}
