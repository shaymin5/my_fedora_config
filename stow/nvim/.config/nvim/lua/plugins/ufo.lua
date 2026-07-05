return {
    "kevinhwang91/nvim-ufo",
    dependencies = { "kevinhwang91/promise-async" },
    event = "VeryLazy",
    config = function()
        vim.o.foldcolumn = "1"
        vim.o.foldlevel = 99
        vim.o.foldlevelstart = 99
        vim.o.foldenable = true

        vim.keymap.set("n", "zR", require("ufo").openAllFolds)
        vim.keymap.set("n", "zM", require("ufo").closeAllFolds)

        -- 新增：Tab 切换折叠（推荐）
        vim.keymap.set("n", "<Tab>", "za", { desc = "Toggle current fold" })
        vim.keymap.set("n", "<S-Tab>", "zA", { desc = "Toggle recursively" })

        require("ufo").setup({
            provider_selector = function(bufnr, filetype, buftype)
                return { "treesitter", "indent" }
            end,
            fold_virt_text_handler = function(virtText, lnum, endLnum, width, truncate)
                local newVirtText = {}
                local suffix = ("  󰁂 %d lines"):format(endLnum - lnum)
                local sufWidth = vim.fn.strdisplaywidth(suffix)
                local targetWidth = width - sufWidth
                local curWidth = 0
                for _, chunk in ipairs(virtText) do
                    local chunkText = chunk[1]
                    local chunkWidth = vim.fn.strdisplaywidth(chunkText)
                    if targetWidth > curWidth + chunkWidth then
                        table.insert(newVirtText, chunk)
                    else
                        chunkText = truncate(chunkText, targetWidth - curWidth)
                        table.insert(newVirtText, { chunkText, chunk[2] })
                        break
                    end
                    curWidth = curWidth + chunkWidth
                end
                table.insert(newVirtText, { suffix, "MoreMsg" })
                return newVirtText
            end,
        })
    end,
}
