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

        -- 收集 markdown 标题的 { 行号, 级别 }
        local function md_headings()
            local ok, parser = pcall(vim.treesitter.get_parser, 0, "markdown")
            if not ok or not parser then
                return nil
            end
            local ok2, trees = pcall(parser.parse, parser)
            if not ok2 or not trees[1] then
                return nil
            end
            local headings = {}
            local function walk(node)
                local t = node:type()
                if t == "atx_heading" or t == "setext_heading" then
                    local level = 0
                    for child in node:iter_children() do
                        local ct = child:type()
                        local l = ct:match("^atx_h(%d)_marker$") or ct:match("^setext_h(%d)_underline$")
                        if l then
                            level = tonumber(l)
                        end
                    end
                    if level > 0 then
                        headings[#headings + 1] = { line = node:start() + 1, level = level }
                    end
                end
                for child in node:iter_children() do
                    walk(child)
                end
            end
            walk(trees[1]:root())
            return headings
        end

        -- 折叠到第 N 层：markdown 按标题层级，其它文件类型按折叠层级
        local function fold_to_level(level)
            if vim.bo.filetype:match("^markdown") then
                local headings = md_headings()
                if headings and #headings > 0 then
                    -- 先全部展开，让级别以内的内容（含代码块、列表）正常显示
                    require("ufo").openAllFolds()
                    -- 再把“标题级别 > N”的小节折叠起来
                    -- 必须从后往前（深的先关），否则 foldclose 落在已关闭折叠内会误关外层
                    for i = #headings, 1, -1 do
                        local h = headings[i]
                        if h.level > level then
                            vim.cmd("silent! " .. h.line .. "foldclose")
                        end
                    end
                    return
                end
            end
            require("ufo").closeFoldsWith(level)
        end

        -- 新增：z1~z9 折叠到指定层级（保留前 N 层展开，关闭更深的折叠）
        for i = 1, 9 do
            vim.keymap.set("n", "z" .. i, function()
                fold_to_level(i)
            end, { desc = "Fold to level " .. i })
        end

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
