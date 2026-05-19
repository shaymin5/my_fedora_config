#!/usr/bin/env bash

# ==================== SSH Key 自动生成 ====================

SSH_DIR="$HOME/.ssh"
KEY_PATH="$SSH_DIR/id_ed25519"

if [ ! -f "$KEY_PATH" ] || [ ! -f "$KEY_PATH.pub" ]; then
  echo "Generating new SSH Ed25519 key..."

  mkdir -p "$SSH_DIR"
  chmod 700 "$SSH_DIR"

  ssh-keygen -t ed25519 \
    -f "$KEY_PATH" \
    -N "" \
    -q \
    -C "$(whoami)@$(hostname)-$(date +%Y%m%d)"

  chmod 600 "$KEY_PATH"
  chmod 644 "$KEY_PATH.pub"

  echo "✅ SSH key created successfully!"
else
  echo "SSH key already exists, skipping generation."
fi

echo
echo "Public key:"
cat "$KEY_PATH.pub"
echo
