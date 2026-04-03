#!/bin/bash
# ============================================================
#  VAXIS Installer - macOS ランチャー
#  Install_macOS.command
#
#  初回のみ実行権限の付与が必要です:
#    chmod +x Install_macOS.command
#  または Finder で右クリック → 「開く」を選択してください。
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALLER="$SCRIPT_DIR/installer.py"

# ── osascript でエラーダイアログを表示するヘルパー ──────────
show_error() {
    osascript -e "display dialog \"$1\" buttons {\"OK\"} default button \"OK\" with icon stop with title \"VAXIS Installer\""
}

# ── Python 3 の検索 ─────────────────────────────────────────
PYTHON3=""

# 1. 標準コマンドを順に試す
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" --version 2>&1 | grep -Eo '3\.[0-9]+\.[0-9]+' | head -1)
        if [ -n "$ver" ]; then
            PYTHON3="$cmd"
            break
        fi
    fi
done

# 2. Homebrew (Intel / Apple Silicon)
if [ -z "$PYTHON3" ]; then
    for p in /opt/homebrew/bin/python3 /usr/local/bin/python3; do
        [ -x "$p" ] && PYTHON3="$p" && break
    done
fi

# 3. pyenv
if [ -z "$PYTHON3" ] && [ -x "$HOME/.pyenv/shims/python3" ]; then
    PYTHON3="$HOME/.pyenv/shims/python3"
fi

# Python が見つからない場合
if [ -z "$PYTHON3" ]; then
    show_error "Python 3 が見つかりません。\nhttps://www.python.org からインストールしてください。\n\nインストール後にもう一度このファイルを開いてください。"
    exit 1
fi

echo "[VAXIS] Python: $PYTHON3 ($($PYTHON3 --version 2>&1))"

# ── tkinter の確認 ──────────────────────────────────────────
if ! "$PYTHON3" -c "import tkinter" &>/dev/null; then
    show_error "tkinter が利用できません。\n\n以下のいずれかを実行してください:\n・Homebrew: brew install python-tk\n・または python.org から Python をインストール"
    exit 1
fi

# ── インストーラーを起動 ────────────────────────────────────
echo "[VAXIS] インストーラーを起動しています..."
"$PYTHON3" "$INSTALLER"
