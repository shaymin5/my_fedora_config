#!/usr/bin/env bash

# dnf换源
sudo cp /etc/yum.repos.d/fedora.repo /etc/yum.repos.d/fedora.repo.bak
sudo cp /etc/yum.repos.d/fedora-updates.repo /etc/yum.repos.d/fedora-updates.repo.bak
sudo sed -e 's|^metalink=|#metalink=|g' -e 's|^#baseurl=http://download.example/pub/fedora/linux|baseurl=https://mirrors.tuna.tsinghua.edu.cn/fedora|g' -i.bak /etc/yum.repos.d/fedora.repo /etc/yum.repos.d/fedora-updates.repo
sudo dnf clean all
sudo dnf makecache
sudo dnf update -y
# 还原方式
# sudo cp /etc/yum.repos.d/fedora.repo.bak /etc/yum.repos.d/fedora.repo
# sudo cp /etc/yum.repos.d/fedora-updates.repo.bak /etc/yum.repos.d/fedora-updates.repo

# flatpak换源
sudo flatpak remote-modify flathub --url=https://mirrors.ustc.edu.cn/flathub
# 还原方式
# sudo flatpak remote-modify flathub --url=https://flathub.org/repo/flathub.flatpakrepo
