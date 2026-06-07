#!/usr/bin/env bash

sudo -v
set -e

# ssh auto generate
bash $HOME/dotfiles/script/ssh.sh

# 配置github端口
bash $HOME/dotfiles/script/github.sh

# 换源
bash $HOME/dotfiles/script/network.sh

# stow
bash $HOME/dotfiles/script/stow.sh

# DNF
bash $HOME/dotfiles/packages/dnf.sh

# Flatpak
bash $HOME/dotfiles/packages/flatpak.sh
