-- 在 lua/config/keymaps.lua 文件中添加以下内容
local run_python = require("utils.run_python")

-- 运行 Python 文件
vim.keymap.set("n", "<leader>rr", function()
    run_python.run_python_file()
end, { desc = "运行当前 Python 文件" })

-- 打开 Python 终端（查看历史，不会运行新命令）
vim.keymap.set("n", "<leader>rt", function()
    run_python.focus_terminal()
end, { desc = "打开 Python 终端（查看历史）" })

-- keymap.lua
local term_utils = require("utils.terminal")

-- Normal / Insert mode: 打开/切换终端
vim.keymap.set({ "n", "i" }, "<C-_>", function()
    term_utils.toggle_project_terminal()
end, { desc = "Toggle terminal at project root" })

vim.keymap.set({ "n", "i" }, "<C-/>", function()
    term_utils.toggle_project_terminal()
end, { desc = "Toggle terminal at project root" })

-- Terminal mode: 关闭终端
vim.keymap.set("t", "<C-_>", "<C-\\><C-n>:q<CR>", { desc = "Close terminal" })
vim.keymap.set("t", "<C-/>", "<C-\\><C-n>:q<CR>", { desc = "Close terminal" })
