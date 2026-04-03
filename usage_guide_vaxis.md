# VAXIS (万能3D生成エンジン) アドオン導入ガイド

本ガイドでは、作成した Blender 4.2 用アドオンの導入方法と基本的な使用方法を説明します。

## 1. アドオンのパッケージング
現在のディレクトリ内の以下の 3 ファイルを一つの ZIP ファイル（例: `vaxis_addon.zip`）にまとめてください。
- `__init__.py`
- `comfy_bridge.py`
- `operators.py`

> [!NOTE]
> ファイルを直接 Blender の `scripts/addons` フォルダに `vaxis` という名前のフォルダを作成して配置することでも動作します。

## 2. インストール手順
1. **Blender を起動** します。
2. **Edit > Preferences > Add-ons** を開きます。
3. 右上の `Install...` ボタンをクリックし、作成した `vaxis_addon.zip` を選択します。
4. 一覧に表示される **VAXIS Core** のチェックボックスをオンにして有効化します。

## 3. 使用方法
1. **3D Viewport** （編集画面）の右側にあるサイドバー（通常は `N` キーで開閉）を展開します。
2. **VAXIS Core** というタブが表示されていることを確認します。
3. **ComfyUI 接続設定** セクションで、ComfyUI が起動している URL (デフォルト: `http://127.0.0.1:8188`) を入力します。
4. **Generate** ボタンを押すと、ComfyUI へのリクエストが送信されます。

## 4. 開発・デバッグ
- コンソールログは、Blender の `Window > Toggle System Console` (Windowsの場合) で確認できます。
- 通信エラーが発生した場合は、ComfyUI が正しく起動しており、APIへのアクセスが許可されているか確認してください。

---
**著作者:** VAXIS Development Team
