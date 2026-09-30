#!/usr/bin/env bash

# 安装fcitx5 rime
rm -rf ~/.local/share/fcitx5/rime
git clone https://github.com/iDvel/rime-ice.git ~/.local/share/fcitx5/rime
rm -rf ~/.local/share/fcitx5/rime/.git ~/.local/share/fcitx5/rime/.github
ln -s "$HOME/dotfiles/backups/rime/default.custom.yaml" ~/.local/share/fcitx5/rime/default.custom.yaml
ln -s "$HOME/dotfiles/backups/rime/double_pinyin_flypy.custom.yaml" ~/.local/share/fcitx5/rime/double_pinyin_flypy.custom.yaml
fcitx5-remote -r
fcitx5 -r -d
