@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM ============================================================
REM  VAXIS Installer - Windows ランチャー v0.3.0
REM
REM  優先順位:
REM   1. システム Python (pythonw.exe でコンソール非表示)
REM   2. Blender に同梱されている Python (Blender 起動不要)
REM ============================================================

set "INSTALLER=%~dp0installer.py"
set "PYTHON_EXE="

REM ── 1. Python Launcher (py.exe) ────────────────────────────
for /f "delims=" %%i in ('py -3 -c "import sys,os; p=os.path.join(os.path.dirname(sys.executable),'pythonw.exe'); print(p if os.path.exists(p) else sys.executable)" 2^>nul') do (
    if not defined PYTHON_EXE if exist "%%i" set "PYTHON_EXE=%%i"
)

REM ── 2. PATH の pythonw.exe ─────────────────────────────────
if not defined PYTHON_EXE (
    for /f "delims=" %%i in ('where pythonw 2^>nul') do (
        if not defined PYTHON_EXE set "PYTHON_EXE=%%i"
    )
)

REM ── 3. PATH の python.exe → pythonw.exe に変換 ────────────
if not defined PYTHON_EXE (
    for /f "delims=" %%i in ('where python 2^>nul') do (
        if not defined PYTHON_EXE (
            set "_PY=%%i"
            set "_PYW=!_PY:python.exe=pythonw.exe!"
            if exist "!_PYW!" (
                set "PYTHON_EXE=!_PYW!"
            ) else (
                set "PYTHON_EXE=%%i"
            )
        )
    )
)

REM ── 4. Blender 同梱 Python を検索（システムPython がない場合）──
if not defined PYTHON_EXE (
    echo [情報] システム Python が見つかりません。Blender 同梱 Python を検索中...
    for /f "delims=" %%i in ('dir /s /b "C:\Program Files\Blender Foundation\python.exe" 2^>nul') do (
        REM \bin\ を含むパスのみ採用（Blenderの同梱Pythonは bin フォルダ内にある）
        echo %%i | findstr /i "\\bin\\" >nul
        if !errorlevel! equ 0 (
            if not defined PYTHON_EXE set "PYTHON_EXE=%%i"
        )
    )
)

REM ── 5. Program Files (x86) も検索 ─────────────────────────
if not defined PYTHON_EXE (
    for /f "delims=" %%i in ('dir /s /b "C:\Program Files (x86)\Blender Foundation\python.exe" 2^>nul') do (
        echo %%i | findstr /i "\\bin\\" >nul
        if !errorlevel! equ 0 (
            if not defined PYTHON_EXE set "PYTHON_EXE=%%i"
        )
    )
)

REM ── Python が見つからない場合 ──────────────────────────────
if not defined PYTHON_EXE (
    echo.
    echo  [エラー] Python が見つかりませんでした。
    echo.
    echo  以下のいずれかを実行してください:
    echo    A) https://www.python.org からシステム Python をインストール
    echo       (インストール時に「Add Python to PATH」にチェック)
    echo    B) Blender 5.1 をインストール後に再試行
    echo.
    pause
    exit /b 1
)

echo [OK] Python: !PYTHON_EXE!
echo.

REM ── インストーラー GUI を起動 ──────────────────────────────
REM   "start /b" でバックグラウンド起動し、このコンソール画面を閉じる
start "" "!PYTHON_EXE!" "!INSTALLER!"
exit /b 0
