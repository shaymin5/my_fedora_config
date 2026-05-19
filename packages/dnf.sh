#!/usr/bin/env bash

# 更新
sudo dnf upgrade -y

# Nvidia
# sudo dnf install kernel-devel-matched kernel-headers
# sudo dnf config-manager addrepo --from-repofile=https://developer.download.nvidia.com/compute/cuda/repos/${distro}/${arch}/cuda-${distro}.repo
# sudo dnf clean expire-cache
sudo dnf install cuda-drivers -y
sudo dnf install akmod-nvidia -y

# niri 桌面配套装备
sudo dnf install niri fuzzel alacritty swaybg maple-fonts -y

# 输入法
sudo dnf install fcitx5 fcitx5-autostart fcitx5-configtool fcitx5-rime fcitx5-chinese-addons -y

# keyd，改键位软件，按需安装
sudo dnf install keyd -y

# chrome
sudo dnf install chrome -y

# steam
sudo dnf install steam -y

sudo dnf install noctalia-shell
