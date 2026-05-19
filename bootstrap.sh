#!/usr/bin/env bash

sudo -v
set -e

# git config
bash ./git.sh

# ssh auto generate
bash ./ssh.sh

# 换源
bash ./network.sh

# DNF
bash ./packages/dnf.sh

# Flatpak
bash ./packages/flatpak.sh
