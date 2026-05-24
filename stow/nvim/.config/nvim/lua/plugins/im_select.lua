return {
    "keaising/im-select.nvim",
    config = function()
        vim.g.im_select_command = "fcitx5-remote"

        require("im_select").setup({
            default_im_select = "keyboard-us",
        })
    end,
}
