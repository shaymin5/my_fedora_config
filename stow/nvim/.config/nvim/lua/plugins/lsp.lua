return {
  "neovim/nvim-lspconfig",
  opts = {
    servers = {
      pyright = {
        before_init = function(_, config)
          local root = config.root_dir
          local venv = root .. "/.venv" or root .. "/venv" or root .. "/.uv"

          if vim.fn.isdirectory(venv) == 1 then
            config.settings = config.settings or {}
            config.settings.python = {
              pythonPath = require("utils.platform").python_venv_executable(venv),
            }
          end
        end,
      },
    },
  },
}
