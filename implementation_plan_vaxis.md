# VAXIS (万能3D生成エンジン) Blender 4.2 アドオン実装計画

この計画では、Blender 4.2 用の VAXIS アドオンを構築します。
クリーンアーキテクチャに基づき、各ファイルの役割を明確に分離し、保守性と拡張性を高めます。

## 1. ファイル構成
- `comfy_bridge.py`: 外部通信を担当（Infrastructure層）
- `operators.py`: ユーザーの操作を処理（Application/Presentation層）
- `__init__.py`: アドオンの登録とUI定義（Presentation/Registry層）

## 2. 各コンポーネントの詳細

### 2.1 comfy_bridge.py (通信クラス)
- `VAXIS_ComfyBridge` クラスを実装。
- `urllib.request` を使用し、ComfyUI の `/prompt` エンドポイントへ JSON データを送信。
- タイムアウト処理やエラーハンドリング（接続不可、404エラーなど）を適切に行い、上位層へ例外または結果を返却。

### 2.2 operators.py (Blenderオペレーター)
- `VAXIS_OT_Generate` (bpy.types.Operator) を実装。
- `execute` メソッド内で `comfy_bridge.py` を呼び出し、生成リクエストを実行。
- `self.report({'INFO', 'ERROR'}, "メッセージ")` を用いて、ユーザーへフィードバック。

### 2.3 __init__.py (登録・UI)
- `bl_info` の定義（著作者: VAXIS Development Team）。
- `VAXIS_AddonProperties` (bpy.types.PropertyGroup): ComfyUI URL などの設定を保持。
- `VAXIS_PT_MainPanel` (bpy.types.Panel): 3Dビューポートの Nパネル（タブ名「VAXIS Core」）を描画。
- クラスの自動登録・解除ロジック。

## 3. コーディング規約
- 言語: 日本語コメント、英語変数名、スネークケース。
- 品質: 型ヒントの活用（可能な限り）、冗長なロジックの排除。
- 著作者名: 「VAXIS Development Team」

## 4. 実行手順
1. `comfy_bridge.py` の作成
2. `operators.py` の作成
3. `__init__.py` の作成
4. 最終的な整合性確認
