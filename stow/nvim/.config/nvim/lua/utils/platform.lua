-- utils/platform.lua
-- 跨平台工具模块：统一检测操作系统和路径差异

local M = {}

--- 当前是否为 Windows
function M.is_windows()
  return vim.fn.has("win32") == 1 or vim.fn.has("win64") == 1
end

--- 当前是否为 Linux
function M.is_linux()
  return vim.fn.has("unix") == 1 and not M.is_mac()
end

--- 当前是否为 macOS
function M.is_mac()
  return vim.fn.has("macunix") == 1
end

--- 当前是否为 Unix 类系统（Linux / macOS）
function M.is_unix()
  return vim.fn.has("unix") == 1
end

--- 返回 Python 虚拟环境中解释器的路径
--- Windows:  .venv/Scripts/python.exe
--- Unix:     .venv/bin/python
---@param venv_root string 虚拟环境根目录路径
---@return string
function M.python_venv_executable(venv_root)
  if M.is_windows() then
    return venv_root .. "/Scripts/python.exe"
  else
    return venv_root .. "/bin/python"
  end
end

--- 返回系统 PATH 分隔符
--- Windows: ";", Unix: ":"
function M.path_separator()
  if M.is_windows() then
    return ";"
  else
    return ":"
  end
end

--- 将路径转换为当前平台风格
--- Windows 上将 / 转为 \\，Unix 保持原样
function M.normalize_path(path)
  if M.is_windows() then
    return path:gsub("/", "\\")
  end
  return path
end

return M
