#!/usr/bin/env bash

# rime
# 安装fcitx5 rime
RIME_DIR="$HOME/.local/share/fcitx5/rime"

rm -rf "$RIME_DIR"
# 克隆失败时不要中断 bootstrap（比如首次还没连上代理），给提示后跳过
if git clone https://github.com/iDvel/rime-ice.git "$RIME_DIR"; then
    rm -rf "$RIME_DIR/.git" "$RIME_DIR/.github"

    ln -sf "$HOME/dotfiles/backups/rime/default.custom.yaml" "$RIME_DIR/default.custom.yaml"
    ln -sf "$HOME/dotfiles/backups/rime/double_pinyin_flypy.custom.yaml" "$RIME_DIR/double_pinyin_flypy.custom.yaml"

    mv "$RIME_DIR/rime_ice.dict.yaml" "$RIME_DIR/rime_ice.dict.yaml.bak"
    ln -sf "$HOME/dotfiles/backups/rime/rime_ice.dict.yaml" "$RIME_DIR/rime_ice.dict.yaml"

    # ACG词库，来自仓库 https://github.com/suiginko/moetype.git
    cp "$HOME/dotfiles/backups/rime/toneless_moe.dict.yaml" "$RIME_DIR/cn_dicts/toneless_moe.dict.yaml"

    # 重新加载并启动 fcitx5；未运行时忽略失败
    fcitx5-remote -r 2>/dev/null || true
    fcitx5 -r -d 2>/dev/null || true
else
    echo "警告: rime-ice 克隆失败，已跳过 rime 配置（请检查网络/代理后重跑本脚本）" >&2
fi
