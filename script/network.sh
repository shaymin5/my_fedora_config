#!/usr/bin/env bash

set -e
# ------------------------------------------------------------
# DNF 换源
# ------------------------------------------------------------

# 备份 Fedora 官方仓库配置
sudo cp /etc/yum.repos.d/fedora.repo \
    /etc/yum.repos.d/fedora.repo.bak

sudo cp /etc/yum.repos.d/fedora-updates.repo \
    /etc/yum.repos.d/fedora-updates.repo.bak

# 禁用 metalink，启用清华镜像的 baseurl
#
# 保留 repo 文件原本的 $releasever / $basearch 等变量，
# 只修改镜像站域名。
sudo sed -i \
    -e 's|^metalink=|#metalink=|' \
    -e 's|^#baseurl=.*|baseurl=https://mirrors.tuna.tsinghua.edu.cn/fedora/linux/$releasever/Everything/$basearch/os/|' \
    /etc/yum.repos.d/fedora.repo

sudo sed -i \
    -e 's|^metalink=|#metalink=|' \
    -e 's|^#baseurl=.*|baseurl=https://mirrors.tuna.tsinghua.edu.cn/fedora/linux/updates/$releasever/Everything/$basearch/|' \
    /etc/yum.repos.d/fedora-updates.repo

# 清理 DNF 缓存并重新生成缓存
sudo dnf clean all
sudo dnf makecache

# ------------------------------------------------------------
# DNF 还原方式
# ------------------------------------------------------------
#
# sudo cp /etc/yum.repos.d/fedora.repo.bak \
#         /etc/yum.repos.d/fedora.repo
#
# sudo cp /etc/yum.repos.d/fedora-updates.repo.bak \
#         /etc/yum.repos.d/fedora-updates.repo
#
# sudo dnf clean all
# sudo dnf makecache

# ------------------------------------------------------------
# Flatpak 换源
# ------------------------------------------------------------

# 使用中科大 Flathub 镜像
sudo flatpak remote-modify flathub \
    --url=https://mirrors.ustc.edu.cn/flathub

# ------------------------------------------------------------
# Flatpak 还原方式
# ------------------------------------------------------------
#
# sudo flatpak remote-modify flathub \
#   --url=https://flathub.org/repo/flathub.flatpakrepo
