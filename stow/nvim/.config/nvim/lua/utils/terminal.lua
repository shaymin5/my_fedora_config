-- utils/terminal.lua
local M = {}

-- 存储项目目录到终端实例的映射
M.project_terminals = {}
M.terminal_ready = {} -- 跟踪终端是否已准备好

-- 计算目录的简单哈希值
function M.hash_string(str)
    local hash = 5381
    for i = 1, #str do
        -- 使用乘法和加法代替位运算
        hash = ((hash * 33) + str:byte(i)) % 1000
    end
    return 100 + (hash % 100) -- 返回 100-199 之间的ID
end

-- 获取项目根目录
function M.get_project_root()
    -- 尝试获取git根目录
    local git_root = vim.fn.system({ "git", "rev-parse", "--show-toplevel" })
    if vim.v.shell_error == 0 then
        return vim.trim(git_root)
    end

    -- 如果没有git，使用当前目录
    return vim.fn.getcwd()
end

-- 确保进入终端模式
function M.ensure_terminal_mode(term_id)
    -- 延迟确保进入终端模式
    vim.defer_fn(function()
        -- 先检查当前缓冲区是否是对应的终端
        local term = require("toggleterm.terminal").get(term_id)
        if term and term:is_open() then
            vim.cmd("startinsert!")

            -- 再次检查，确保真的进入了终端模式
            vim.defer_fn(function()
                local current_mode = vim.api.nvim_get_mode().mode
                if current_mode ~= "t" and current_mode ~= "i" then
                    vim.cmd("startinsert!")
                end
            end, 20)
        end
    end, 30)
end

-- 为项目目录获取或创建终端实例
function M.get_terminal_for_project(project_root)
    local Terminal = require("toggleterm.terminal").Terminal

    -- 检查是否已存在该目录的终端
    if M.project_terminals[project_root] then
        local term = M.project_terminals[project_root]
        -- 确保终端对象有效
        if term and type(term) == "table" and term.toggle then
            return term
        else
            -- 如果无效，清除并重新创建
            M.project_terminals[project_root] = nil
        end
    end

    -- 为新项目目录创建终端
    local term_id = M.hash_string(project_root)

    -- 检查这个ID是否已被其他目录使用
    for stored_root, stored_term in pairs(M.project_terminals) do
        if stored_root ~= project_root and stored_term.id == term_id then
            -- 如果ID冲突，尝试不同的ID
            for i = 1, 100 do
                term_id = 100 + ((M.hash_string(project_root) + i) % 100)

                -- 检查新ID是否可用
                local id_available = true
                for _, other_term in pairs(M.project_terminals) do
                    if other_term.id == term_id then
                        id_available = false
                        break
                    end
                end

                if id_available then
                    break
                end
            end
            break
        end
    end

    -- 创建新的终端实例
    local term = Terminal:new({
        cmd = vim.o.shell,
        dir = project_root,
        id = term_id,
        direction = "float",
        float_opts = {
            border = "rounded",
            width = function()
                return math.floor(vim.o.columns * 0.8)
            end,
            height = function()
                return math.floor(vim.o.lines * 0.8)
            end,
        },
        auto_scroll = true,
        on_open = function(term_obj)
            -- 设置一个标志，表示终端已准备好
            M.terminal_ready[term_obj.id] = true
            -- 确保进入终端模式
            M.ensure_terminal_mode(term_obj.id)
        end,
        on_close = function(term_obj)
            -- 清除就绪标志
            M.terminal_ready[term_obj.id] = nil
        end,
    })

    -- 存储映射
    M.project_terminals[project_root] = term
    return term
end

-- 打开/切换终端
function M.toggle_project_terminal()
    local project_root = M.get_project_root()
    local term = M.get_terminal_for_project(project_root)

    -- 记录之前的状态
    local was_open = term:is_open()

    -- 切换终端
    term:toggle()

    -- 如果终端从关闭变为打开，确保进入终端模式
    if not was_open and term:is_open() then
        M.ensure_terminal_mode(term.id)
    end

    -- 如果终端已经打开，也检查是否为终端模式
    if was_open and term:is_open() then
        -- 检查当前模式
        local current_mode = vim.api.nvim_get_mode().mode
        if current_mode ~= "t" and current_mode ~= "i" then
            M.ensure_terminal_mode(term.id)
        end
    end
end

-- 关闭当前项目的终端
function M.close_terminal()
    local project_root = M.get_project_root()
    local term = M.get_terminal_for_project(project_root)
    if term:is_open() then
        term:close()
    end
end

-- 关闭所有终端
function M.close_all_terminals()
    for project_root, term in pairs(M.project_terminals) do
        if term:is_open() then
            term:close()
        end
    end
end

-- 获取当前终端的ID
function M.get_current_terminal_id()
    local project_root = M.get_project_root()
    local term = M.project_terminals[project_root]
    if term then
        return term.id
    end
    return nil
end

-- 获取所有终端的映射
function M.get_terminal_mappings()
    local mappings = {}
    for project_root, term in pairs(M.project_terminals) do
        table.insert(mappings, {
            project = project_root,
            terminal_id = term.id,
            is_open = term:is_open(),
        })
    end
    return mappings
end

return M
