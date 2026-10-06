#!/usr/bin/env bash

set -e
sudo -v

# ssh auto generate
bash $HOME/dotfiles/script/ssh.sh

# 配置github端口
bash $HOME/dotfiles/script/github.sh

# 换源
bash $HOME/dotfiles/script/network.sh

# DNF
bash $HOME/dotfiles/packages/dnf.sh

# stow
bash $HOME/dotfiles/script/stow.sh

# Flatpak
bash $HOME/dotfiles/packages/flatpak.sh

# System
bash $HOME/dotfiles/script/system.sh

# Other installing
bash $HOME/dotfiles/packages/other.sh
