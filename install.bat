@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title VAXIS Setup Installer

cls
echo.
echo  ====================================================
echo   VAXIS - Universal Reality Forge
echo   セットアップ インストーラー v0.2.0
echo  ====================================================
echo.
echo  このスクリプトは以下を自動実行します:
echo    1. Blender の自動検出
echo    2. 依存パッケージのインストール
echo       (requests / Pillow / numpy / tqdm)
echo    3. VAXIS アドオンを Blender へコピー
echo.
echo  準備ができたら何かキーを押してください...
pause >nul

echo.
echo  ====================================================
echo  [1/3] Blender を検出中...
echo  ====================================================
set "BLENDER_EXE="

REM --- 方法1: PATH に blender が通っている場合 ---
for /f "delims=" %%i in ('where blender 2^>nul') do (
    if not defined BLENDER_EXE set "BLENDER_EXE=%%i"
)

REM --- 方法2: Program Files 内のインストールをバージョン問わず検索 ---
if not defined BLENDER_EXE (
    for /d %%d in ("C:\Program Files\Blender Foundation\Blender *") do (
        if exist "%%d\blender.exe" set "BLENDER_EXE=%%d\blender.exe"
    )
)

REM --- 方法3: Program Files (x86) も検索 ---
if not defined BLENDER_EXE (
    for /d %%d in ("C:\Program Files (x86)\Blender Foundation\Blender *") do (
        if exist "%%d\blender.exe" set "BLENDER_EXE=%%d\blender.exe"
    )
)

REM --- 方法4: Steam 版 Blender ---
if not defined BLENDER_EXE (
    set "STEAM_PATH=C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe"
    if exist "!STEAM_PATH!" set "BLENDER_EXE=!STEAM_PATH!"
)

REM --- 自動検出失敗時: 手動入力 ---
if not defined BLENDER_EXE (
    echo.
    echo  [警告] Blender が自動検出できませんでした。
    echo.
    echo  blender.exe のフルパスを入力してください:
    echo  例: C:\Program Files\Blender Foundation\Blender 5.1\blender.exe
    echo.
    set /p "BLENDER_EXE=  >> "
    echo.
)

REM --- パスの存在確認 ---
if not exist "!BLENDER_EXE!" (
    echo.
    echo  [エラー] blender.exe が見つかりません:
    echo           !BLENDER_EXE!
    echo.
    echo  Blender が正しくインストールされているか確認してください。
    goto :ERROR
)

echo.
echo   検出OK: !BLENDER_EXE!

echo.
echo  ====================================================
echo  [2-3/3] パッケージインストール & アドオン設置中...
echo          (初回は数分かかります。閉じないでください)
echo  ====================================================
echo.

REM setup_helper.py をBlenderのPython環境で実行する
REM %~dp0 = このバッチファイルが置かれているディレクトリ (末尾に\付き)
"!BLENDER_EXE!" --background --python "%~dp0setup_helper.py"

if !errorlevel! neq 0 (
    echo.
    echo  [エラー] セットアップが失敗しました (code: !errorlevel!)
    echo.
    echo  以下を試してください:
    echo    - このスクリプトを「管理者として実行」する
    echo    - Blender のバージョンが 5.1 以上であることを確認する
    goto :ERROR
)

echo.
echo  ====================================================
echo   インストール完了！
echo.
echo   次のステップ:
echo    1. Blender を起動する
echo    2. Edit ^> Preferences ^> Add-ons を開く
echo    3. 「VAXIS Core」を検索して有効化する
echo    4. Nキー ^> 「VAXIS Core」タブで動作を確認する
echo  ====================================================
echo.
pause
exit /b 0

:ERROR
echo.
pause
exit /b 1
