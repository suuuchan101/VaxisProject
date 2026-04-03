"""
VAXIS Universal Reality Forge - インストーラー GUI
ファイル: installer.py  v0.3.0

変更点 (v0.3.0):
  - Blender を「起動」せずに Python を検出する方式に変更
  - Blender のインストールディレクトリから直接 python.exe を検索
  - アドオンフォルダも OS の規則に従い計算で決定（Blender 実行不要）
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import os
import sys
import shutil
import glob
import platform
from datetime import datetime

# ============================================================
# 定数
# ============================================================
APP_TITLE  = "VAXIS Installer"
APP_W, APP_H = 700, 580
ADDON_DIR  = os.path.dirname(os.path.abspath(__file__))
ADDON_NAME = os.path.basename(ADDON_DIR)   # "vaxis"
PACKAGES   = ["requests", "Pillow", "numpy", "tqdm"]

EXCLUDE = frozenset({
    "install.bat", "Install_Windows.bat", "Install_macOS.command",
    "setup_helper.py", "installer.py", "requirements.txt",
    "__pycache__", ".git", ".gitignore", "vaxis.zip",
})

_SYS = platform.system()
FONT_UI   = ("Segoe UI", 10)        if _SYS == "Windows" else ("Helvetica Neue", 11)
FONT_BOLD = ("Segoe UI", 11, "bold") if _SYS == "Windows" else ("Helvetica Neue", 12, "bold")
FONT_HEAD = ("Segoe UI", 15, "bold") if _SYS == "Windows" else ("Helvetica Neue", 16, "bold")
FONT_MONO = ("Consolas",  9)        if _SYS == "Windows" else ("Monaco", 10)

C = {
    "bg":      "#1e1e2e", "panel":   "#313244", "border":  "#45475a",
    "fg":      "#cdd6f4", "sub":     "#a6adc8", "accent":  "#89b4fa",
    "success": "#a6e3a1", "warning": "#f9e2af", "danger":  "#f38ba8",
}


# ============================================================
# Blender 検出・パス計算ユーティリティ
# ============================================================

def find_blender() -> str:
    """OS に合わせて blender 実行ファイルを自動検索する。"""
    found = shutil.which("blender")
    if found:
        return found

    if _SYS == "Windows":
        for base in ("C:/Program Files", "C:/Program Files (x86)"):
            for exe in glob.glob(f"{base}/Blender Foundation/Blender */blender.exe"):
                return exe
        steam = "C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe"
        if os.path.exists(steam):
            return steam

    elif _SYS == "Darwin":
        for candidate in [
            "/Applications/Blender.app/Contents/MacOS/Blender",
            os.path.expanduser("~/Applications/Blender.app/Contents/MacOS/Blender"),
        ]:
            if os.path.exists(candidate):
                return candidate
    return ""


def find_blender_python(blender_exe: str) -> str:
    """
    Blender の実行ファイルパスから、同梱の Python 実行ファイルを
    ファイルシステム上で直接検索する。Blender を起動しない。

    Blender のディレクトリ構造:
      Windows: <blender_dir>/<version>/python/bin/python.exe
      macOS  : Blender.app/Contents/Resources/<version>/python/bin/python3.x
    """
    if _SYS == "Windows":
        blender_dir = os.path.dirname(blender_exe)
        patterns = [
            os.path.join(blender_dir, "*", "python", "bin", "python.exe"),
        ]
    elif _SYS == "Darwin":
        # Blender.app/Contents/MacOS/Blender → Resources/
        resources = os.path.join(
            os.path.dirname(os.path.dirname(blender_exe)), "Resources"
        )
        patterns = [
            os.path.join(resources, "*", "python", "bin", "python3.*"),
            os.path.join(resources, "*", "python", "bin", "python3"),
        ]
    else:
        return ""

    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        if matches:
            return matches[-1]   # バージョンが新しい方を優先
    return ""


def get_blender_version(blender_exe: str) -> str:
    """
    Blender のインストールディレクトリ内のバージョンフォルダ名を取得する。
    例: "5.1"  (Blender の python ディレクトリが存在するフォルダ名)
    """
    if _SYS == "Windows":
        blender_dir = os.path.dirname(blender_exe)
        search_root = blender_dir
    elif _SYS == "Darwin":
        search_root = os.path.join(
            os.path.dirname(os.path.dirname(blender_exe)), "Resources"
        )
    else:
        return ""

    if not os.path.isdir(search_root):
        return ""

    for item in sorted(os.listdir(search_root), reverse=True):
        candidate = os.path.join(search_root, item, "python")
        if os.path.isdir(candidate):
            return item   # 例: "5.1"
    return ""


def get_addons_dir(blender_version: str) -> str:
    """
    Blender のユーザーアドオンディレクトリを OS の規則に従い計算する。
    Blender を起動せずに決定できる。

    Windows : %APPDATA%\\Blender Foundation\\Blender\\<ver>\\scripts\\addons
    macOS   : ~/Library/Application Support/Blender/<ver>/scripts/addons
    """
    if not blender_version:
        return ""

    if _SYS == "Windows":
        appdata = os.environ.get("APPDATA", "")
        return os.path.join(
            appdata, "Blender Foundation", "Blender",
            blender_version, "scripts", "addons"
        )
    elif _SYS == "Darwin":
        return os.path.expanduser(
            f"~/Library/Application Support/Blender/{blender_version}/scripts/addons"
        )
    return ""


# ============================================================
# メインウィンドウ
# ============================================================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.resizable(False, False)
        self.configure(bg=C["bg"])

        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{APP_W}x{APP_H}+{(sw-APP_W)//2}+{(sh-APP_H)//2}")

        self._build()
        self.after(400, self._auto_detect)

    # ── UI 構築 ──────────────────────────────────────────────
    def _build(self):
        pad = dict(padx=24)

        # ヘッダー
        hdr = tk.Frame(self, bg=C["bg"])
        hdr.pack(fill="x", **pad, pady=(18, 4))
        tk.Label(hdr, text="⚡  VAXIS", font=FONT_HEAD,
                 bg=C["bg"], fg=C["accent"]).pack(side="left")
        tk.Label(hdr, text="  Universal Reality Forge — Installer v0.3.0",
                 font=FONT_UI, bg=C["bg"], fg=C["sub"]).pack(side="left", pady=(5, 0))

        self._sep()

        # Blender パス
        bf = tk.Frame(self, bg=C["bg"])
        bf.pack(fill="x", **pad, pady=6)
        tk.Label(bf, text="Blender 実行ファイル", font=FONT_UI,
                 bg=C["bg"], fg=C["fg"]).pack(anchor="w")

        row = tk.Frame(bf, bg=C["bg"])
        row.pack(fill="x", pady=(4, 0))
        self._blender_var = tk.StringVar()
        tk.Entry(row, textvariable=self._blender_var,
                 bg=C["panel"], fg=C["fg"], insertbackground=C["fg"],
                 relief="flat", font=FONT_MONO,
                 highlightthickness=1, highlightbackground=C["border"]
                 ).pack(side="left", fill="x", expand=True, ipady=6)
        tk.Button(row, text=" 参照... ", font=FONT_UI,
                  bg=C["panel"], fg=C["fg"], relief="flat",
                  activebackground=C["border"], cursor="hand2",
                  command=self._browse).pack(side="left", padx=(8, 0), ipady=4)

        # 検出情報ラベル
        self._detect_lbl = tk.Label(bf, text="", font=FONT_UI,
                                    bg=C["bg"], fg=C["sub"])
        self._detect_lbl.pack(anchor="w", pady=(2, 0))

        # オプション
        of = tk.Frame(self, bg=C["bg"])
        of.pack(fill="x", **pad, pady=4)
        self._opt_pkg  = tk.BooleanVar(value=True)
        self._opt_copy = tk.BooleanVar(value=True)
        for var, label in [
            (self._opt_pkg,  "依存パッケージをインストール  (requests / Pillow / numpy / tqdm)"),
            (self._opt_copy, "VAXIS アドオンを Blender へコピー"),
        ]:
            tk.Checkbutton(of, text=label, variable=var, font=FONT_UI,
                           bg=C["bg"], fg=C["fg"], selectcolor=C["panel"],
                           activebackground=C["bg"], activeforeground=C["accent"]
                           ).pack(anchor="w", pady=1)

        self._sep()

        # ログ
        lf = tk.Frame(self, bg=C["bg"])
        lf.pack(fill="both", expand=True, **pad)
        tk.Label(lf, text="ログ", font=FONT_UI,
                 bg=C["bg"], fg=C["sub"]).pack(anchor="w", pady=(0, 4))
        self._log_box = tk.Text(
            lf, height=10, wrap="word", state="disabled",
            bg=C["panel"], fg=C["fg"], insertbackground=C["fg"],
            font=FONT_MONO, relief="flat",
            highlightthickness=1, highlightbackground=C["border"],
        )
        self._log_box.pack(fill="both", expand=True)
        for tag, color in [("ok", C["success"]), ("err", C["danger"]),
                           ("info", C["accent"]), ("ts", C["border"])]:
            self._log_box.tag_config(tag, foreground=color)

        # プログレスバー
        pf = tk.Frame(self, bg=C["bg"])
        pf.pack(fill="x", **pad, pady=8)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("V.Horizontal.TProgressbar",
                        troughcolor=C["panel"], background=C["accent"],
                        bordercolor=C["bg"], lightcolor=C["accent"], darkcolor=C["accent"])
        self._prog_var = tk.DoubleVar()
        ttk.Progressbar(pf, variable=self._prog_var, maximum=100,
                        style="V.Horizontal.TProgressbar").pack(fill="x")
        self._status_lbl = tk.Label(pf, text="準備完了", font=FONT_UI,
                                    bg=C["bg"], fg=C["sub"])
        self._status_lbl.pack(anchor="w", pady=(4, 0))

        # インストールボタン
        bf2 = tk.Frame(self, bg=C["bg"])
        bf2.pack(fill="x", **pad, pady=(0, 20))
        self._btn = tk.Button(
            bf2, text="⚡  インストール開始", font=FONT_BOLD,
            bg=C["accent"], fg=C["bg"], relief="flat",
            activebackground="#74c7ec", cursor="hand2",
            command=self._start, pady=10,
        )
        self._btn.pack(fill="x")

    def _sep(self):
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", padx=20, pady=6)

    # ── 操作 ────────────────────────────────────────────────
    def _auto_detect(self):
        path = find_blender()
        if path:
            self._blender_var.set(path)
            self._update_detect_info(path)
            self._log("Blender を自動検出しました", "ok")
            self._log(f"  {path}", "info")
        else:
            self._log("Blender が自動検出できませんでした。パスを手動入力してください。", "err")

    def _update_detect_info(self, blender_exe: str):
        """Blenderパスから Python とアドオンディレクトリを確認してラベル表示。"""
        ver = get_blender_version(blender_exe)
        py  = find_blender_python(blender_exe)
        ads = get_addons_dir(ver)

        parts = []
        if ver:
            parts.append(f"バージョン: {ver}")
        if py:
            parts.append(f"Python: {os.path.basename(py)}")
        if ads:
            parts.append(f"アドオン先: .../{ver}/scripts/addons")

        if parts:
            self._detect_lbl.configure(text="  " + "   |   ".join(parts), fg=C["sub"])
        else:
            self._detect_lbl.configure(text="  ⚠ Blender の Python が見つかりません", fg=C["warning"])

    def _browse(self):
        ft = [("blender", "blender.exe"), ("All", "*.*")] if _SYS == "Windows" else [("All", "*")]
        p = filedialog.askopenfilename(title="Blender を選択", filetypes=ft)
        if p:
            self._blender_var.set(p)
            self._update_detect_info(p)

    def _log(self, msg: str, tag: str = ""):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_box.configure(state="normal")
        self._log_box.insert("end", f"[{ts}] ", "ts")
        self._log_box.insert("end", msg + "\n", tag)
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _status(self, text: str, pct: float):
        self._status_lbl.configure(text=text)
        self._prog_var.set(pct)
        self.update_idletasks()

    def _start(self):
        blender = self._blender_var.get().strip()
        if not blender or not os.path.exists(blender):
            messagebox.showerror("エラー", "有効な Blender のパスを指定してください。")
            return
        self._btn.configure(state="disabled")
        threading.Thread(target=self._worker, args=(blender,), daemon=True).start()

    # ── バックグラウンド処理（Blender 起動不要） ────────────
    def _worker(self, blender_exe: str):
        try:
            self.after(0, lambda: self._log("インストールを開始します...", "info"))

            # ── Blender の Python を直接検索 ──
            self.after(0, lambda: self._status("Blender の Python を検索中...", 5))
            python = find_blender_python(blender_exe)
            if not python:
                raise RuntimeError(
                    "Blender の Python が見つかりませんでした。\n"
                    "Blender 5.1 が正しくインストールされているか確認してください。"
                )
            self.after(0, lambda: self._log(f"Blender Python: {python}", "ok"))

            # ── pip アップグレード ──
            self.after(0, lambda: self._status("pip をアップグレード中...", 10))
            subprocess.run([python, "-m", "pip", "install", "--upgrade", "pip"],
                           capture_output=True)
            self.after(0, lambda: self._log("pip アップグレード完了", "ok"))

            # ── パッケージインストール ──
            if self._opt_pkg.get():
                for i, pkg in enumerate(PACKAGES):
                    pct = 15 + (i / len(PACKAGES)) * 50
                    self.after(0, lambda p=pkg, v=pct: (
                        self._log(f"インストール中: {p}", "info"),
                        self._status(f"{p} をインストール中...", v),
                    ))
                    r = subprocess.run(
                        [python, "-m", "pip", "install", pkg, "--upgrade"],
                        capture_output=True, text=True, encoding="utf-8"
                    )
                    tag  = "ok"  if r.returncode == 0 else "err"
                    mark = "✓" if r.returncode == 0 else "✗"
                    self.after(0, lambda p=pkg, t=tag, m=mark:
                               self._log(f"  {m} {p}", t))

            # ── アドオンコピー ──
            if self._opt_copy.get():
                self.after(0, lambda: self._status("アドオンフォルダを特定中...", 70))

                ver = get_blender_version(blender_exe)
                addons_dir = get_addons_dir(ver)

                if not addons_dir:
                    raise RuntimeError(
                        f"アドオンフォルダを特定できませんでした。\n"
                        f"(Blender バージョン: '{ver}')"
                    )

                dst = os.path.join(addons_dir, ADDON_NAME)
                self.after(0, lambda d=dst: self._log(f"コピー先: {d}", "info"))
                self.after(0, lambda: self._status("アドオンをコピー中...", 80))

                os.makedirs(addons_dir, exist_ok=True)
                if os.path.exists(dst):
                    shutil.rmtree(dst)

                shutil.copytree(
                    ADDON_DIR, dst,
                    ignore=lambda s, n: {x for x in n if x in EXCLUDE}
                )
                self.after(0, lambda: self._log("アドオンコピー完了", "ok"))

            # ── 完了 ──
            self.after(0, lambda: self._status("インストール完了！", 100))
            self.after(0, lambda: self._log("", ""))
            self.after(0, lambda: self._log("✅ インストールが完了しました！", "ok"))
            self.after(0, lambda: self._log(
                "Blender を起動 → Edit > Preferences > Add-ons → 「VAXIS Core」を有効化", "info"))
            self.after(0, lambda: messagebox.showinfo(
                "完了",
                "インストール完了！\n\nBlender を起動し\n"
                "Edit > Preferences > Add-ons で\n「VAXIS Core」を有効化してください。"))

        except Exception as e:
            self.after(0, lambda: self._log(f"エラー: {e}", "err"))
            self.after(0, lambda: messagebox.showerror("エラー", str(e)))
        finally:
            self.after(0, lambda: self._btn.configure(state="normal"))


if __name__ == "__main__":
    App().mainloop()
