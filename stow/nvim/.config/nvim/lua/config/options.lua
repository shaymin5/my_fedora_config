-- Options are automatically loaded before lazy.nvim startup
-- Default options that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua
-- Add any additional options here

-- lua/config/options.lua

-- Tab 基础行为
vim.opt.expandtab = true
vim.opt.tabstop = 4
vim.opt.shiftwidth = 4
vim.opt.softtabstop = 4

-- 关键：补全不自动选中，不吃回车
vim.opt.completeopt = { "menu", "menuone", "noselect" }

vim.opt.wrap = true -- 启用自动换行
vim.opt.linebreak = true -- 在单词边界处断行，避免在字符中间断开
vim.opt.breakindent = true -- 保持缩进（可选，让折行后的内容保持缩进）

-- 根据进程 ID 创建独立的 shada 文件
local cwd = vim.fn.getcwd()
local project_name = vim.fn.fnamemodify(cwd, ":t") -- 只取文件夹名
vim.opt.shadafile = vim.fn.stdpath("data") .. "/shada/main." .. project_name .. ".shada"
