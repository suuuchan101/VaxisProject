#!/usr/bin/env python3
# =============================================================================
# build_package.py — IsekaiPipeline 自動ビルドスクリプト
# =============================================================================
# MobilisFrontier XR Project — v1.0.0
#
# 目的:
#   1. Blender Extension (/Blender_Extension/) を ZIP 圧縮して出力する
#   2. Unity CLI を通じて IsekaiAgentSystem.unitypackage を出力する
#
# 依存:
#   Python 3 標準ライブラリのみ（os, zipfile, subprocess）
#   外部パッケージは一切不使用。
#
# 使用方法:
#   python build_package.py
#
# 事前準備:
#   - UNITY_EXE_PATH: 実行環境に合わせて変更してください
#   - PROJECT_PATH: Unity プロジェクトルートへのパス（通常は変更不要）
# =============================================================================

import os
import sys
import zipfile
import subprocess
import shutil

# Windowsのコンソール出力で絵文字などを表示するためのエンコーディング設定
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# 設定定数
# =============================================================================

# このスクリプトが存在するディレクトリ（= プロジェクトルート）
_ROOT = os.path.dirname(os.path.abspath(__file__))

# --- Blender Extension ---
# 圧縮対象: /Blender_Extension/ フォルダ全体
BLENDER_EXT_DIR = os.path.join(_ROOT, "Blender_Extension")

# 出力 ZIP ファイル名（Blender 5.1 の「Extensions からインストール」に対応）
ZIP_OUTPUT_NAME = "IsekaiAssetStudio_v1.0.0.zip"
ZIP_OUTPUT_PATH = os.path.join(_ROOT, ZIP_OUTPUT_NAME)

# --- Unity CLI ---
# ▼ 使用している Unity バージョンに合わせてパスを変更してください ▼
UNITY_EXE_PATH = r"C:\Program Files\Unity\Hub\Editor\6000.0.0f1\Editor\Unity.exe"

# Unity プロジェクトのパス（このスクリプトの隣にある Unity_Package フォルダ）
PROJECT_PATH = os.path.normpath(os.path.join(_ROOT, "Unity_Package"))

# エクスポートするパッケージ内のアセットパス（Unity Project 相対）
UNITY_EXPORT_PACKAGE_ASSET = "Assets/IsekaiSystem"

# 出力される .unitypackage ファイル名
UNITY_PACKAGE_NAME = "IsekaiAgentSystem.unitypackage"


# =============================================================================
# 処理 1: Blender Extension ZIP 圧縮
# =============================================================================

def build_blender_extension() -> bool:
    """
    /Blender_Extension/ フォルダ全体を ZIP 圧縮し、
    Blender 5.1 の Extensions インストール用 ZIP を生成する。

    除外ファイル:
        - __pycache__/ ディレクトリ
        - .pyc バイトコードファイル

    Returns:
        bool: 成功した場合 True、失敗した場合 False。
    """
    print("=" * 64)
    print("[処理1] Blender Extension ZIP の生成を開始します...")
    print(f"  ソース  : {BLENDER_EXT_DIR}")
    print(f"  出力先  : {ZIP_OUTPUT_PATH}")
    print("=" * 64)

    # ソースフォルダの存在確認
    if not os.path.isdir(BLENDER_EXT_DIR):
        print(f"[エラー] Blender_Extension フォルダが見つかりません: {BLENDER_EXT_DIR}")
        return False

    file_count = 0

    with zipfile.ZipFile(ZIP_OUTPUT_PATH, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(BLENDER_EXT_DIR):

            # __pycache__ フォルダを除外（in-place で dirs を変更することで
            # os.walk の再帰を防ぐ）
            dirs[:] = [d for d in dirs if d != '__pycache__']

            for file in files:
                # .pyc バイトコードファイルを除外
                if file.endswith('.pyc'):
                    continue

                full_path = os.path.join(root, file)

                # ZIP アーカイブ内の相対パス
                # BLENDER_EXT_DIR を基準にすることで、中身を直接ルートに配置する
                # (Blender Extension の仕様: blender_manifest.toml がルートに必須)
                archive_path = os.path.relpath(full_path, BLENDER_EXT_DIR)

                zf.write(full_path, archive_path)
                print(f"  + {archive_path}")
                file_count += 1

    print(f"\n✅ ZIP 生成完了 ({file_count} ファイル): {ZIP_OUTPUT_PATH}\n")
    return True


# =============================================================================
# 処理 2: Unity CLI によるパッケージエクスポート
# =============================================================================

def export_unity_package() -> bool:
    """
    Unity CLI を呼び出し、IsekaiSystem を .unitypackage 形式でエクスポートする。

    Unity 実行ファイルが存在しない場合は、実行コマンドをコンソールに表示して
    スキップする（エラーにはしない）。

    Returns:
        bool: 実行を試みた場合 True、スキップした場合 False。
    """
    print("=" * 64)
    print("[処理2] Unity CLI パッケージエクスポートを実行します...")
    print(f"  Unity EXE  : {UNITY_EXE_PATH}")
    print(f"  Project    : {PROJECT_PATH}")
    print(f"  出力ファイル: {UNITY_PACKAGE_NAME}")
    print("=" * 64)

    # --- Unity EXE の存在確認 ---
    if not os.path.isfile(UNITY_EXE_PATH):
        print("[スキップ] Unity 実行ファイルが見つかりませんでした。")
        print(f"  パスを確認してください: {UNITY_EXE_PATH}")
        print("\n以下のコマンドを手動で実行することでパッケージを生成できます:\n")

        # 参照用コマンドを表示
        cmd_display = " ".join([
            f'"{UNITY_EXE_PATH}"',
            "-quit",
            "-batchmode",
            f'-projectPath "{PROJECT_PATH}"',
            f'-exportPackage "{UNITY_EXPORT_PACKAGE_ASSET}"',
            f'"{UNITY_PACKAGE_NAME}"',
        ])
        print(f"  {cmd_display}\n")
        return False

    # --- Unity CLI コマンドの構築 ---
    command = [
        UNITY_EXE_PATH,
        "-quit",                          # 処理完了後に Unity を終了
        "-batchmode",                     # GUIなしのバッチモード実行
        "-projectPath", PROJECT_PATH,     # プロジェクトパス
        "-exportPackage",
        UNITY_EXPORT_PACKAGE_ASSET,       # エクスポートするアセットパス
        UNITY_PACKAGE_NAME,               # 出力ファイル名
    ]

    print("Unityをバッチモードで起動中（数分かかる場合があります）...")
    print(f"  コマンド: {' '.join(command)}\n")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300,  # 最大5分のタイムアウト
        )

        if result.returncode == 0:
            print(f"✅ Unity パッケージエクスポート完了: {UNITY_PACKAGE_NAME}")
        else:
            print(f"[警告] Unity プロセスがコード {result.returncode} で終了しました。")
            if result.stdout:
                print(f"  STDOUT (末尾500字): {result.stdout[-500:]}")
            if result.stderr:
                print(f"  STDERR (末尾500字): {result.stderr[-500:]}")

    except subprocess.TimeoutExpired:
        print("[警告] Unity プロセスがタイムアウトしました（5分）。")
        print("  手動での実行・確認をお勧めします。")
    except FileNotFoundError:
        print(f"[エラー] Unity 実行ファイルが実行できませんでした: {UNITY_EXE_PATH}")
    except Exception as e:
        # 予期せぬエラーはスキップしてビルド全体を継続する
        print(f"[警告] Unity コマンドの実行中にエラーが発生しました（スキップ）: {e}")

    return True


# =============================================================================
# 処理 3: 単一EXEパッケージビルド (PyInstaller)
# =============================================================================

def build_exe_package() -> bool:
    """
    生成されたBlender拡張機能とUnityパッケージをバックエンド用静的フォルダにコピーし、
    PyInstallerを使用してvaxis_launcher.pyを単一EXEファイル化する。
    """
    print("=" * 64)
    print("[処理3] VAXIS Local AI Engine の EXE 化を開始します...")
    print("=" * 64)

    static_dir = os.path.join(_ROOT, "SaaS_Backend", "static_assets")
    os.makedirs(static_dir, exist_ok=True)

    # 1. アセットのコピー
    print("  アセットを静的ディレクトリへコピー中...")
    if os.path.exists(ZIP_OUTPUT_PATH):
        shutil.copy2(ZIP_OUTPUT_PATH, os.path.join(static_dir, ZIP_OUTPUT_NAME))
    
    unity_pkg_path = os.path.join(_ROOT, UNITY_PACKAGE_NAME)
    if os.path.exists(unity_pkg_path):
        shutil.copy2(unity_pkg_path, os.path.join(static_dir, UNITY_PACKAGE_NAME))
    else:
        # 空のダミーファイルを作成しておき、エラーを防ぐ
        with open(os.path.join(static_dir, UNITY_PACKAGE_NAME), 'w', encoding='utf-8') as f:
            f.write("Unity package not built in this environment.")

    # 2. PyInstaller 実行
    launcher_script = os.path.join(_ROOT, "vaxis_launcher.py")
    
    # OSに応じたセパレータの設定
    sep = ";" if os.name == "nt" else ":"
    add_data_arg = f"{static_dir}{sep}static_assets"

    pyinstaller_cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--name", "VAXIS_Engine",
        "--add-data", add_data_arg,
        launcher_script
    ]

    print(f"  PyInstaller を実行中: {' '.join(pyinstaller_cmd)}\n")

    try:
        # shell=True on Windows may help if 'pyinstaller' is not found directly but in Scripts
        result = subprocess.run(
            pyinstaller_cmd,
            capture_output=True,
            text=True,
            timeout=600,
            shell=True if os.name == 'nt' else False
        )
        if result.returncode == 0:
            exe_path = os.path.join(_ROOT, "dist", "VAXIS_Engine.exe" if os.name == "nt" else "VAXIS_Engine")
            print(f"✅ EXE ビルド完了: {exe_path}")
            return True
        else:
            print(f"[エラー] PyInstaller プロセスがコード {result.returncode} で終了しました。")
            if result.stdout:
                print(f"  STDOUT: {result.stdout[-1000:]}")
            if result.stderr:
                print(f"  STDERR: {result.stderr[-1000:]}")
            return False
    except FileNotFoundError:
        print("[エラー] pyinstaller コマンドが見つかりません。 'pip install pyinstaller' を実行してください。")
        return False
    except Exception as e:
        print(f"[エラー] EXEビルド中に例外が発生しました: {e}")
        return False

# =============================================================================
# メイン処理
# =============================================================================

def main():
    """自動ビルドパイプラインのメインエントリーポイント。"""
    print("\n🏯 IsekaiPipeline — 自動ビルドスクリプト v1.0.0")
    print("   MobilisFrontier XR Project\n")

    success_ext   = build_blender_extension()
    success_unity = export_unity_package()
    success_exe   = build_exe_package()

    # --- 結果サマリー ---
    print("\n" + "=" * 64)
    print("📋 ビルド結果サマリー")
    print("=" * 64)
    print(f"  Blender Extension ZIP : {'✅ 成功' if success_ext   else '❌ 失敗'}")
    print(f"  Unity Package Export  : {'✅ 実行' if success_unity  else '⏭  スキップ（手動実行要）'}")
    print(f"  VAXIS Engine EXE Build: {'✅ 成功' if success_exe    else '❌ 失敗'}")
    print("=" * 64)

    if success_exe:
        print(f"\n📦 プロジェクトパッケージが完成しました。")
        print("   -> dist/VAXIS_Engine.exe （これをユーザーに配布してください）")
    elif success_ext:
        print(f"\n📦 Blender からインストールするファイル: {ZIP_OUTPUT_PATH}")
        print("   Blender > Edit > Preferences > Extensions > Install from Disk")

    print("\nお疲れ様でした。異世界へのデプロイ準備が整いました。🌟\n")


if __name__ == "__main__":
    main()
