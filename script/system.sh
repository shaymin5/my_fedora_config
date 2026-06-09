#!/usr/bin/env bash

# 恢复root目录下的内容

sudo mkdir -p /etc/keyd
sudo cp "$HOME/dotfiles/system/keyd/default.conf" /etc/keyd/default.conf
# sudo chown root:root /etc/keyd/default.conf
sudo chmod 644 /etc/keyd/default.conf
