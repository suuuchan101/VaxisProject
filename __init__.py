# ============================================================
# VAXIS Blender アドオン - エントリーポイント
# プロジェクト: VAXIS (Virtual AI Xenomorphic Integration System)
# バージョン: 0.2.0 (Universal Reality Forge)
#
# このファイルはBlenderがアドオンとして認識するための
# エントリーポイントです。bl_infoの定義と各モジュールの
# 登録・登録解除を一元管理します。
#
# v0.2.0 変更点:
#   - blender: (4, 2, 0) → (5, 1, 0)
#   - version: (0, 1, 0) → (0, 2, 0)
#   - description を Universal Reality Forge のコンセプトに更新
#   - pipelines/ パッケージを追加（panelsより先に読み込まれる）
# ============================================================

# --- Blender アドオンメタデータ ---
# Blenderはこの辞書を読み込んでアドオン情報を表示します。
bl_info = {
    "name": "VAXIS Core",
    "author": "VAXIS Development Team",
    "version": (0, 2, 0),
    "blender": (5, 1, 0),
    "location": "View3D > Sidebar > VAXIS Core",
    "description": (
        "Universal Reality Forge - 人物・動物・環境・プロップを統合的に生成する"
        "万能3D生成エンジン。ローカルAI（SF3D, Panorama360-XL）との統合を目指す。"
    ),
    "warning": "フェーズ1: 開発中 (Development Build)",
    "category": "3D View",
}

# --- 標準ライブラリ・Blender APIのインポート ---
import bpy
import sys
import os

# Blender 5.1 (Windows) のsite-packagesを起動時に追加
_SP = r"C:\5.1\python\Lib\site-packages"
if os.path.isdir(_SP) and _SP not in sys.path:
    sys.path.insert(0, _SP)

# Windowsコンソールの文字化け対策
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
    except Exception:
        pass

# --- 内部モジュールのインポート ---
# クリーンアーキテクチャに従い、各レイヤーを分離したモジュールを読み込む。
# pipelines/ は operators.py が依存するため、operators より先に読み込まれる
# 必要があるが、Python の相対インポートにより自動的に解決される。
from . import operators
from . import panels


# ============================================================
# アドオン登録処理
# ============================================================

def register() -> None:
    """
    アドオンをBlenderに登録する関数。
    Blenderが「アドオンを有効化」した際に自動的に呼び出される。

    登録順序:
        1. operators （Panelより先にOperatorを登録する）
        2. panels    （PropertyGroupとPanelを登録しシーンに紐付ける）

    pipelines/ パッケージは bpy.utils.register_class() が不要な
    純粋なPythonクラス群であり、operators のインポート時に
    自動的に読み込まれるため、個別の register() 呼び出しは不要。
    """
    operators.register()
    panels.register()
    print("[VAXIS] v0.2.0 Universal Reality Forge - アドオンを登録しました。")


def unregister() -> None:
    """
    アドオンをBlenderから登録解除する関数。
    Blenderが「アドオンを無効化」した際に自動的に呼び出される。

    登録の逆順（panels → operators）で解除することで
    依存関係の問題を防ぐ。
    """
    panels.unregister()
    operators.unregister()
    print("[VAXIS] アドオンの登録を解除しました。")


# --- スクリプトとして直接実行された場合の処理 ---
# Blenderのテキストエディタから直接実行した場合にも動作するよう対応。
if __name__ == "__main__":
    register()
