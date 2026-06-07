#!/usr/bin/env bash

# 更新
sudo flatpak upgrade -y

# localsend
flatpak install flathub org.localsend.localsend_app -y

# jellyfin desktop
flatpak install org.jellyfin.JellyfinDesktop -y
