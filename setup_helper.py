"""
VAXIS セットアップヘルパースクリプト
ファイル: setup_helper.py

このスクリプトは Blender の --python オプション経由で実行される。
Blender 自身の Python 環境 (sys.executable) を使って依存パッケージを
インストールし、アドオン本体をBlenderのアドオンフォルダへコピーする。

実行方法: blender --background --python setup_helper.py
          ※ install.bat が自動的に呼び出す。直接実行しないこと。
"""

import sys
import subprocess
import os
import shutil
import traceback

# ============================================================
# 定数: このスクリプト自身の場所から各パスを決定
# ============================================================

# このスクリプトが vaxis/ フォルダ内にあるため、
# os.path.dirname(__file__) が vaxis/ フォルダそのものを指す
ADDON_DIR  = os.path.dirname(os.path.abspath(__file__))
ADDON_NAME = os.path.basename(ADDON_DIR)  # → "vaxis"

# インストール先コピー時に除外するファイル/フォルダ名
# (インストーラー自体をアドオンとして配置しない)
EXCLUDE_FROM_COPY = frozenset({
    "install.bat",
    "setup_helper.py",
    "requirements.txt",
    "__pycache__",
    ".git",
    ".gitignore",
    "vaxis.zip",
})

# ============================================================
# ユーティリティ
# ============================================================

def section(title: str) -> None:
    """コンソールにセクションヘッダーを出力する。"""
    print("\n" + "=" * 60)
    print(f"[VAXIS Setup] {title}")
    print("=" * 60)


def run_pip(args: list[str]) -> bool:
    """
    Blender の Python (sys.executable) 経由で pip コマンドを実行する。

    Args:
        args: pip に渡す引数リスト (例: ["install", "requests", "--upgrade"])

    Returns:
        成功した場合 True、失敗した場合 False
    """
    cmd = [sys.executable, "-m", "pip"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"    [警告] stderr: {result.stderr.strip()[:300]}")
    return result.returncode == 0


# ============================================================
# Step 1: pip の確認とアップグレード
# ============================================================
section("Step 1: pip を確認・アップグレード中...")

# pip が存在しない環境向けに ensurepip でブートストラップ
try:
    import ensurepip
    ensurepip.bootstrap(upgrade=True)
    print("  [OK] ensurepip によるブートストラップ完了")
except Exception as e:
    print(f"  [情報] ensurepip スキップ: {e}")

if run_pip(["install", "--upgrade", "pip"]):
    print("  [OK] pip を最新版にアップグレードしました")
else:
    print("  [警告] pip のアップグレードに失敗しましたが、続行します")

# ============================================================
# Step 2: 依存パッケージのインストール
# ============================================================
section("Step 2: 依存パッケージをインストール中...")

# パッケージ名 → 用途の説明
REQUIRED_PACKAGES: dict[str, str] = {
    "requests": "HTTP API呼び出し (SF3D / Panorama360-XL との通信)",
    "Pillow":   "画像処理 (テクスチャ・HDRI変換)",
    "numpy":    "メッシュデータの数値計算",
    "tqdm":     "プログレスバー表示",
}

print(f"  対象パッケージ: {', '.join(REQUIRED_PACKAGES.keys())}\n")

failed_packages: list[str] = []

for package, description in REQUIRED_PACKAGES.items():
    print(f"  インストール中: {package}")
    print(f"    用途: {description}")
    if run_pip(["install", package, "--upgrade"]):
        print(f"    [OK] 完了")
    else:
        print(f"    [失敗] {package} のインストールに失敗しました")
        failed_packages.append(package)

# ============================================================
# Step 3: アドオンを Blender のアドオンフォルダへコピー
# ============================================================
section("Step 3: VAXIS アドオンを Blender へインストール中...")

try:
    import bpy  # type: ignore  # Blender 環境でのみ有効

    # ユーザーのBlenderアドオンディレクトリを取得
    # Blender バージョンによってキーワード引数名が異なるため両方試みる
    addons_dir: str = ""
    try:
        addons_dir = bpy.utils.user_resource("SCRIPTS", path="addons")
    except TypeError:
        try:
            addons_dir = bpy.utils.user_resource("SCRIPTS", subfolder="addons")
        except TypeError:
            pass

    # フォールバック: 手動でパスを構築
    if not addons_dir:
        import pathlib
        ver = f"{bpy.app.version[0]}.{bpy.app.version[1]}"
        addons_dir = str(
            pathlib.Path.home()
            / "AppData" / "Roaming"
            / "Blender Foundation" / "Blender"
            / ver / "scripts" / "addons"
        )
        print(f"  [フォールバック] パスを手動構築: {addons_dir}")

    os.makedirs(addons_dir, exist_ok=True)
    dst = os.path.join(addons_dir, ADDON_NAME)

    print(f"  コピー元: {ADDON_DIR}")
    print(f"  コピー先: {dst}")

    # 既存インストールを削除してクリーンコピー
    if os.path.exists(dst):
        shutil.rmtree(dst)
        print("  [更新] 既存インストールを削除しました")

    # インストーラー関連ファイルを除外してコピー
    def _ignore_func(src: str, names: list[str]) -> set[str]:
        return {n for n in names if n in EXCLUDE_FROM_COPY}

    shutil.copytree(ADDON_DIR, dst, ignore=_ignore_func)
    print(f"  [OK] アドオンファイルをコピーしました")

    # アドオンの有効化を試みる
    # --background モードでは動作しない場合があるため try/except で保護する
    try:
        bpy.ops.preferences.addon_enable(module=ADDON_NAME)
        bpy.ops.wm.save_userpref()
        print(f"  [OK] アドオン '{ADDON_NAME}' を有効化・設定保存しました")
    except Exception as e:
        print(f"  [情報] 自動有効化をスキップしました: {e}")
        print(f"         Blender 起動後に手動で有効化してください")

except Exception as e:
    print(f"\n  [エラー] アドオンのインストール中に例外が発生しました:")
    traceback.print_exc()
    sys.exit(1)

# ============================================================
# 完了サマリー
# ============================================================
section("セットアップ完了!")

if failed_packages:
    print(f"  [警告] インストール失敗パッケージ: {', '.join(failed_packages)}")
    print()
    print("  手動インストールコマンド (Blender Python コンソールで実行):")
    print("    import subprocess, sys")
    for pkg in failed_packages:
        print(f"    subprocess.run([sys.executable, '-m', 'pip', 'install', '{pkg}'])")
else:
    print("  [OK] 全パッケージのインストールに成功しました")

print()
print("  ==== 次のステップ ====")
print("  1. Blender を起動する")
print("  2. Edit > Preferences > Add-ons を開く")
print("  3. 検索欄に「VAXIS」と入力する")
print("  4. 「VAXIS Core」のチェックボックスをオンにする")
print("  5. 3DビューポートのNキーで「VAXIS Core」タブが表示されれば完了")
print()
