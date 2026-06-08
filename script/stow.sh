#!/usr/bin/env bash

# home的配置

packages=(
    # alacritty
    autostart
    bash
    build-stow
    fcitx5
    git
    kitty
    lx-music-desktop
    mihomo-party
    mise
    niri
    noctalia
    nvim
    opencode
    starship
    yazi
)

# stow 在目标位置已存在文件时会失败
# .bashrc 若为普通文件则备份，若为错误软链接则删除
if [ -f "$HOME/.bashrc" ] && [ ! -L "$HOME/.bashrc" ]; then
    mv "$HOME/.bashrc" "$HOME/.bashrc.bak"
elif [ -L "$HOME/.bashrc" ]; then
    rm "$HOME/.bashrc"
fi

# 批量执行stow恢复config
stow --dir "$HOME/dotfiles/stow" -t "$HOME" "${packages[@]}"

# root的配置，未研究明白，下次研究下

# sudo stow --dir "$HOME/dotfiles/system" -t / keyd
