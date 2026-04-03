# ============================================================
# VAXIS アドオン - Operator モジュール
# ファイル: operators.py
# バージョン: 0.2.0 (Universal Reality Forge 対応)
#
# 責務: ビジネスロジックの実装（PipelineRouter への委譲）
#
# v0.2.0 変更点:
#   - VAXIS_OT_GenerateCreature → VAXIS_OT_Generate にリネーム
#   - bl_idname: "vaxis.generate_creature" → "vaxis.generate"
#   - execute() 内でパイプラインを直接実装するのではなく、
#     PipelineRouter に generation_type を渡して委譲する設計に変更。
#     これにより Operator は「ルーティング責務」のみを持つ。
#
# アーキテクチャノート:
#   - Operator は「何のパイプラインを呼ぶか」だけを知っている
#   - 「パイプラインが何をするか」は pipelines/ の各クラスが知っている
#   - この分離により、新パイプライン追加時に Operator を変更不要
# ============================================================

import bpy
import sys
from .pipelines import PipelineRouter


# ============================================================
# オペレーター: 万能3D生成 (フェーズ1 - パイプライン委譲実装)
# ============================================================

class VAXIS_OT_Generate(bpy.types.Operator):
    """
    万能3D生成オペレーター（Universal Reality Forge）。

    UIパネルから generation_type と generation_prompt を受け取り、
    PipelineRouter を通じて適切なパイプラインに処理を委譲する。

    このクラス自身はルーティング責務のみを持ち、
    具体的な生成ロジックや後処理は各パイプラインクラスが担当する。

    フェーズ1 実装:
        各パイプラインのコンソール出力（詳細ログ）のみ

    フェーズ2 以降:
        各パイプラインが実際の AI API 呼び出しと後処理を実行する
    """

    # --- Blender オペレーターの必須メタデータ ---
    bl_idname = "vaxis.generate"          # v0.2.0: vaxis.generate_creature から変更
    bl_label = "Generate"
    bl_description = (
        "選択された生成タイプのパイプラインを実行します。\n"
        "(フェーズ1: 各パイプラインのコンソールへの詳細ログ出力のみ)"
    )
    # アンドゥ（Ctrl+Z）履歴に登録するオプション
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        """
        オペレーターの主処理。UIの「⚡ Generate」ボタン押下時に呼ばれる。

        処理フロー:
            1. シーンプロパティから generation_type と generation_prompt を取得
            2. PipelineRouter から対応するパイプラインインスタンスを取得
            3. パイプラインの run() メソッドを呼び出す
            4. Blender ステータスバーに完了通知を表示

        Args:
            context: Blenderの現在のコンテキスト

        Returns:
            {"FINISHED"}: 処理が正常に完了したことをBlenderに通知するセット
            {"CANCELLED"}: 不明な generation_type でパイプラインの取得に失敗した場合
        """
        props = context.scene.vaxis_props
        generation_type = props.generation_type
        use_image = props.use_image_input
        image_path = props.input_image_path.strip()
        prompt = props.generation_prompt

        # 画像入力モード: パイプラインを経由せず直接TripoSRに渡す
        if use_image and image_path:
            import os
            if not os.path.isfile(image_path):
                self.report({"ERROR"}, f"画像ファイルが見つかりません: {image_path}")
                return {"CANCELLED"}

            from . import generate_utils

            def _set_status(msg):
                def _update():
                    try:
                        context.scene.vaxis_props.generation_status = msg
                        for area in context.screen.areas:
                            area.tag_redraw()
                    except Exception:
                        pass
                    return None
                import bpy as _bpy
                _bpy.app.timers.register(_update, first_interval=0.0)

            generate_utils.generate_from_image_path(
                image_path=image_path,
                pipeline_type=generation_type,
                apply_sculpt=(generation_type in ("HUMAN", "ANIMAL")),
                status_callback=_set_status,
            )
            self.report({"INFO"}, f"[VAXIS] 画像から3D生成開始: {os.path.basename(image_path)}")
            return {"FINISHED"}

        # テキストプロンプトモード: 従来のパイプライン経由
        try:
            pipeline = PipelineRouter.get_pipeline(generation_type)
        except KeyError as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}

        pipeline.run(prompt=prompt, context=context)
        self.report({"INFO"}, f"[VAXIS] {pipeline.get_display_name()} パイプライン実行: '{prompt}'")
        return {"FINISHED"}


# ============================================================
# オペレーター: アドオンリロード
# ============================================================

class VAXIS_OT_Reload(bpy.types.Operator):
    bl_idname = "vaxis.reload"
    bl_label = "Reload VAXIS"
    bl_description = "VAXISアドオンをリロードします"
    bl_options = {"REGISTER"}

    def execute(self, context):
        def _do_reload():
            mods = [k for k in sys.modules if k.startswith("vaxis")]
            for m in mods:
                del sys.modules[m]
            bpy.ops.preferences.addon_disable(module="vaxis")
            bpy.ops.preferences.addon_enable(module="vaxis")
            print("[VAXIS] リロード完了")
            return None
        bpy.app.timers.register(_do_reload, first_interval=0.1)
        self.report({"INFO"}, "VAXIS リロード中...")
        return {"FINISHED"}


# ============================================================
# 登録対象のオペレータークラス一覧
# 新しいオペレーターを追加した場合は、このリストに追記する。
# ============================================================

_CLASSES: list[type] = [
    VAXIS_OT_Generate,
    VAXIS_OT_Reload,
]


def register() -> None:
    """このモジュール内の全オペレータークラスをBlenderに登録する。"""
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """このモジュール内の全オペレータークラスをBlenderから登録解除する。"""
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
