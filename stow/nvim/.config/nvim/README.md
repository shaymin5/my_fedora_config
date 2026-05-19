# 💤 LazyVim

## 介绍

我的lazyvim配置

- 语法检测和代码补全识别到项目目录下的.venv虚拟环境
- \<leader\>rr用uv使用项目下的.venv虚拟环境运行当前.py文件
- Tab键补全，拒绝Enter键补全

## 快速开始

1. 下载scoop
2. 用scoop安装一堆东西

```powershell
scoop bucket add extras
scoop install neovim nodejs python lazygit fzf ripgrep fd tree-sitter-cli 7zip gzip wget curl
```

1. 安装终端和字体
2. 终端打开nvim，然后:q关掉
3. 克隆仓库
- Windows
把这个仓库里面所有东西都复制到C:/Users/User/AppData/Local/nvim/文件夹下覆盖
- Linux
```bash
git clone git@github.com:shaymin5/lazyvim_pythonIDE_config.git ~/.config/nvim
nvim
```
4. 进入:Mason打开Mason，安装ruff和pyright
