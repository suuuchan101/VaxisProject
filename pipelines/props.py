# ============================================================
# VAXIS アドオン - Props パイプライン
# ファイル: pipelines/props.py
#
# 責務: 静的オブジェクト（武器・家具・建材・小物等）の生成後処理
#
# 対応する generation_type: "PROPS"
#
# フェーズ1: コンソール出力のみ（ダミー実装）
# フェーズ2以降の実装予定:
#   - SF3D Static Mode による高精度メッシュ生成
#   - AI によるPBRマテリアル（Albedo / Roughness / Metallic / Normal）自動生成
#   - LOD (Level of Detail) LOD0-3 の自動生成
#     （ゲームエンジン: UE5 / Unity 向けの段階的ポリゴン削減）
# ============================================================

import bpy
from .base import BasePipeline


class PropsPipeline(BasePipeline):
    """
    静的プロップ（小道具）生成パイプライン。

    武器、家具、建築部材などの静的オブジェクトを生成する。
    キャラクターとは異なりリギングは不要だが、
    ゲームエンジンへの組み込みを考慮した PBR マテリアルと
    LOD の自動生成が主な後処理となる。
    """

    def run(self, prompt: str, context: bpy.types.Context) -> None:
        """
        プロップ生成パイプラインを実行する。

        フェーズ1: 実行予定の処理ステップをコンソールに詳細出力する。
        フェーズ2: SF3D API 呼び出しと後処理の本番実装に置き換える。
        """
        print("=" * 60)
        print("[VAXIS] Props Pipeline 起動")
        print(f"  使用AIモデル   : {self.get_recommended_ai_model()}")
        print(f"  受信プロンプト : '{prompt}'")
        print()

        # 3Dメッシュ生成
        self._step_ai_generate(prompt, context)

        print(f"  後処理 : {self.get_post_process_description()}")
        print("[VAXIS] Props Pipeline 起動完了（生成はバックグラウンドで継続）")
        print("=" * 60)

    def get_recommended_ai_model(self) -> str:
        return "SF3D (Stable Fast 3D) - Static Mode"

    def get_display_name(self) -> str:
        return "Props (Static Object)"

    def get_post_process_description(self) -> str:
        return "PBRマテリアル自動生成 + LOD0-3 自動生成"

    # ----------------------------------------------------------
    # 内部: 各処理ステップ（フェーズ2で本番コードに置き換える）
    # ----------------------------------------------------------

    def _step_ai_generate(self, prompt: str, context: bpy.types.Context) -> None:
        """日本語対応プロンプトからプロップを3D生成する。"""
        from ..translator import translate_to_english
        from .. import generate_utils

        english_prompt = translate_to_english(prompt)
        print(f"  [STEP 1] 生成開始（バックグラウンド）: '{english_prompt}'")

        def _set_status(msg: str):
            print(f"  [STEP 1] {msg}")
            def _update():
                try:
                    bpy.context.scene.vaxis_props.generation_status = msg
                    for area in bpy.context.screen.areas:
                        area.tag_redraw()
                except Exception:
                    pass
                return None
            bpy.app.timers.register(_update, first_interval=0.0)

        generate_utils.generate_and_import(
            prompt=english_prompt,
            pipeline_type="PROPS",
            apply_sculpt=False,
            status_callback=_set_status,
        )

    def _step_ai_generate_placeholder(self, prompt: str) -> None:
        """
        [フェーズ2で置換] SF3D Static Mode による静的メッシュ生成。

        キャラクターパイプラインと異なり "Static Mode" を指定することで、
        リギングを前提としない高精細なサーフェスメッシュを生成する。

        実装予定:
            response = sf3d_client.generate(prompt=prompt, mode="static_prop")
            mesh = response.get_mesh_data()
            bpy.ops.import_mesh.from_data(mesh)
        """
        print(f"  [STEP 1] 静的メッシュ生成 (placeholder): '{prompt}'")
        print(f"           → SF3D Static Mode での高精度メッシュ生成予定")

    def _step_apply_pbr_material(self) -> None:
        """
        [フェーズ2で置換] PBR 物理ベースレンダリングマテリアルの自動生成・適用。

        生成するテクスチャマップ:
            - Albedo (Base Color) : ベースカラーテクスチャ
            - Roughness           : 粗さマップ（鏡面反射の制御）
            - Metallic            : 金属度マップ
            - Normal              : 法線マップ（表面の凹凸情報）
            - Ambient Occlusion   : 環境光遮蔽マップ（オプション）

        実装予定:
            pbr_maps = material_ai.generate_pbr(mesh_object, resolution=2048)
            blender_material_builder.apply(mesh_object, pbr_maps)
        """
        print("  [STEP 2] PBR マテリアル (placeholder)")
        print("           → Albedo / Roughness / Metallic / Normal 各マップ自動生成予定")
        print("           → テクスチャ解像度: 2048x2048px (設定変更可)")

    def _step_generate_lod(self) -> None:
        """
        [フェーズ2で置換] Level of Detail メッシュの自動生成。

        ゲームエンジン（UE5 / Unity）向けのLOD0-3を自動生成し、
        ポリゴン数を段階的に削減したメッシュのコレクションを作成する。
        Blenderの Decimate モディファイアを活用する予定。

        LOD段階の定義:
            LOD0: オリジナル解像度（最高品質）
            LOD1: 50%削減（中距離表示用）
            LOD2: 75%削減（遠距離表示用）
            LOD3: 90%削減（最遠距離表示用）

        実装予定:
            lod_builder = LODGenerator(source_mesh=active_object)
            lod_builder.generate([1.0, 0.5, 0.25, 0.1])
            lod_builder.create_collection("VAXIS_LOD_Collection")
        """
        print("  [STEP 3] LOD 生成 (placeholder)")
        print("           → LOD0(100%) / LOD1(50%) / LOD2(25%) / LOD3(10%)")
        print("           → Blender Decimate モディファイアによる自動削減予定")
