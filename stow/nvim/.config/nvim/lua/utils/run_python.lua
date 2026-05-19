-- utils/run_python.lua
local M = {}

-- 存储项目目录到 Python 终端实例的映射
M.python_terminals = {}
M.python_ready = {} -- 跟踪终端是否已准备好
M.python_id_counter = 200 -- 从 200 开始的 ID 范围

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

-- 计算目录的哈希值，用于生成固定ID
function M.get_project_id(project_root)
    local hash = 5381
    for i = 1, #project_root do
        hash = ((hash * 33) + project_root:byte(i)) % 1000
    end
    return 200 + (hash % 100) -- 返回 200-299 之间的ID
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

-- 获取或创建当前项目的 Python 终端实例
function M.get_python_terminal_for_project()
    local project_root = M.get_project_root()
    local Terminal = require("toggleterm.terminal").Terminal

    -- 检查是否已存在该项目的 Python 终端
    if M.python_terminals[project_root] then
        local term = M.python_terminals[project_root]
        -- 确保终端对象有效
        if term and type(term) == "table" and term.toggle then
            return term
        else
            -- 如果无效，清除并重新创建
            M.python_terminals[project_root] = nil
        end
    end

    -- 获取项目的固定ID
    local term_id = M.get_project_id(project_root)

    -- 检查这个ID是否已被其他项目使用
    for stored_root, stored_term in pairs(M.python_terminals) do
        if stored_root ~= project_root and stored_term.id == term_id then
            -- 如果ID冲突，尝试不同的ID
            for i = 1, 100 do
                term_id = 200 + ((M.get_project_id(project_root) + i) % 100)

                -- 检查新ID是否可用
                local id_available = true
                for _, other_term in pairs(M.python_terminals) do
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

    -- 为新项目创建 Python 终端实例
    local term = Terminal:new({
        cmd = vim.o.shell,
        dir = project_root, -- 设置初始目录为项目根目录
        id = term_id, -- 使用计算得到的固定ID
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
        close_on_exit = false,
        on_open = function(term_obj)
            -- 设置一个标志，表示终端已准备好
            M.python_ready[project_root] = true
            -- 确保进入终端模式
            M.ensure_terminal_mode(term_obj.id)
        end,
        on_close = function(term_obj)
            -- 不清除就绪标志，但设置标志为 false
            M.python_ready[project_root] = false
        end,
    })

    -- 存储映射
    M.python_terminals[project_root] = term
    return term
end

-- 获取当前文件的绝对路径
function M.get_absolute_file_path()
    return vim.fn.expand("%:p")
end

-- 运行当前 Python 文件
function M.run_python_file()
    -- 检查文件类型
    if vim.bo.filetype ~= "python" then
        vim.notify("当前文件不是 Python 文件", vim.log.levels.WARN)
        return
    end

    -- 保存文件
    vim.cmd("write")

    local absolute_path = M.get_absolute_file_path()
    local project_root = M.get_project_root()
    local term = M.get_python_terminal_for_project()

    -- 路径处理
    absolute_path = require("utils.platform").normalize_path(absolute_path)

    -- 记录之前的状态
    local was_open = term:is_open()

    -- 如果终端已打开，先关闭
    if was_open then
        term:close()
    end

    -- 重新打开终端，确保从项目根目录启动
    term.dir = project_root
    term:open()

    -- 等待终端打开，然后发送命令
    vim.defer_fn(function()
        -- 确保进入插入模式
        vim.cmd("startinsert!")

        -- 使用绝对路径运行 Python 文件
        local run_cmd = 'uv run python "' .. absolute_path .. '"'

        -- 发送命令
        term:send(run_cmd)

        -- 确保焦点在终端窗口
        if term.window and vim.api.nvim_win_is_valid(term.window) then
            vim.api.nvim_set_current_win(term.window)
            M.ensure_terminal_mode(term.id)
        end
    end, 150)
end

-- 打开终端但不运行任何命令
function M.focus_terminal()
    local project_root = M.get_project_root()
    local term = M.get_python_terminal_for_project()

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

    -- 如果终端窗口有效，聚焦到终端窗口
    if term.window and vim.api.nvim_win_is_valid(term.window) then
        vim.api.nvim_set_current_win(term.window)
    end
end

-- 获取当前项目的终端
function M.get_terminal()
    return M.get_python_terminal_for_project()
end

-- 获取终端历史（不切换，只返回终端对象）
function M.get_terminal_history()
    return M.get_python_terminal_for_project()
end

-- 关闭当前项目的 Python 终端
function M.close_terminal()
    local term = M.get_python_terminal_for_project()
    if term:is_open() then
        term:close()
    end
end

-- 获取当前项目的终端状态
function M.get_terminal_status()
    local term = M.get_python_terminal_for_project()
    return {
        is_open = term:is_open(),
        terminal_id = term.id,
        project_root = M.get_project_root(),
    }
end

return M
