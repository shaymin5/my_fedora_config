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

stow --dir "$HOME/dotfiles/stow" -t "$HOME" "${packages[@]}"

# root的配置

# sudo stow --dir "$HOME/dotfiles/system" -t / keyd
