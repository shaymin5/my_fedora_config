#!/usr/bin/env bash

# rime
# 安装fcitx5 rime
rm -rf "$HOME/.local/share/fcitx5/rime"
git clone https://github.com/iDvel/rime-ice.git "$HOME/.local/share/fcitx5/rime"
rm -rf "$HOME/.local/share/fcitx5/rime/.git" "$HOME/.local/share/fcitx5/rime/.github"

ln -sf "$HOME/dotfiles/backups/rime/default.custom.yaml" "$HOME/.local/share/fcitx5/rime/default.custom.yaml"
ln -sf "$HOME/dotfiles/backups/rime/double_pinyin_flypy.custom.yaml" "$HOME/.local/share/fcitx5/rime/double_pinyin_flypy.custom.yaml"

mv "$HOME/.local/share/fcitx5/rime/rime_ice.dict.yaml" "$HOME/.local/share/fcitx5/rime/rime_ice.dict.yaml.bak"
ln -sf "$HOME/dotfiles/backups/rime/rime_ice.dict.yaml" "$HOME/.local/share/fcitx5/rime/rime_ice.dict.yaml"

# ACG词库，来自仓库 https://github.com/suiginko/moetype.git
cp "$HOME/dotfiles/backups/rime/toneless_moe.dict.yaml" "$HOME/.local/share/fcitx5/rime/cn_dicts/toneless_moe.dict.yaml"

fcitx5-remote -r
fcitx5 -r -d
