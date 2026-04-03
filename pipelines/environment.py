# ============================================================
# VAXIS アドオン - Environment パイプライン
# ファイル: pipelines/environment.py
#
# 責務: 環境空間（360度HDRI / 地形 / Skybox）の生成後処理
#
# 対応する generation_type: "ENVIRONMENT"
#
# フェーズ1: コンソール出力のみ（ダミー実装）
# フェーズ2以降の実装予定:
#   - 360度パノラマ画像 (等正距円筒図法 4096x2048px) のAI生成
#   - bpy.context.scene.world へのノード自動接続（World Node Setup）
#   - Geometry Nodes を使用したプロップ自動スキャタリング
#     （「荒廃した都市」などのプロンプトから瓦礫・建材を自動配置）
# ============================================================

import bpy
from .base import BasePipeline


class EnvironmentPipeline(BasePipeline):
    """
    環境空間生成パイプライン。

    AIで360度HDRIパノラマを生成し、BlenderのWorld Nodeに
    自動接続することで、シーン全体の背景・照明を一括設定する。
    さらに Geometry Nodes と連携してプロップの自動スキャタリングを行い、
    プロンプトで指定した情景を自動的に空間として構築する。
    """

    def run(self, prompt: str, context: bpy.types.Context) -> None:
        """
        環境空間生成パイプラインを実行する。

        フェーズ1: 実行予定の処理ステップをコンソールに詳細出力する。
        フェーズ2: 各ステップを実際の API 呼び出し・Blender操作に置き換える。
        """
        print("=" * 60)
        print("[VAXIS] Environment Pipeline 起動")
        print(f"  使用AIモデル   : {self.get_recommended_ai_model()}")
        print(f"  受信プロンプト : '{prompt}'")
        print()

        # 3Dメッシュ生成（ミニチュアジオラマとして）
        self._step_ai_generate(prompt, context)

        print(f"  後処理 : {self.get_post_process_description()}")
        print("[VAXIS] Environment Pipeline 起動完了（生成はバックグラウンドで継続）")
        print("=" * 60)

    def get_recommended_ai_model(self) -> str:
        return "Panorama360-XL (Equirectangular HDRI Generator)"

    def get_display_name(self) -> str:
        return "Environment (360° HDRI + Scattering)"

    def get_post_process_description(self) -> str:
        return "World Node 自動接続 + Geometry Nodes スキャタリング"

    # ----------------------------------------------------------
    # 内部: 各処理ステップ（フェーズ2で本番コードに置き換える）
    # ----------------------------------------------------------

    def _step_ai_generate(self, prompt: str, context: bpy.types.Context) -> None:
        """日本語対応プロンプトからミニチュアジオラマとして3D生成する。"""
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
            pipeline_type="ENVIRONMENT",
            apply_sculpt=False,
            status_callback=_set_status,
        )

    def _step_generate_panorama(self, prompt: str) -> None:
        """
        [フェーズ2で置換] 360度パノラマ（等正距円筒図法）画像のAI生成。

        生成画像の仕様:
            - 投影方式: 等正距円筒図法 (Equirectangular)
            - 解像度  : 最低 4096x2048px (アスペクト比 2:1)
            - ファイル形式: EXR (32bit float HDR) または JPEG (8bit SDR)

        実装予定:
            image_data = panorama_client.generate(prompt=prompt, resolution=(4096, 2048))
            hdri_path = image_data.save_to_temp()  # Blenderの一時ディレクトリに保存
        """
        print(f"  [STEP 1] パノラマ生成 (placeholder): '{prompt}'")
        print(f"           → 等正距円筒図法 4096x2048px HDRI 生成予定")
        print(f"           → AIモデル: Panorama360-XL (フェーズ2で統合)")

    def _step_apply_world_node(self, context: bpy.types.Context) -> None:
        """
        [フェーズ2で置換] 生成したHDRIをBlenderのWorld Nodeに自動接続する。

        実装予定コード（参考実装）:
            world = bpy.data.worlds.new("VAXIS_Generated_World")
            world.use_nodes = True
            nodes = world.node_tree.nodes
            links = world.node_tree.links

            # 既存ノードをクリア
            nodes.clear()

            # Environment Texture ノードを追加
            env_node = nodes.new("ShaderNodeTexEnvironment")
            env_node.image = bpy.data.images.load(hdri_path)

            # Background ノードと Output ノードを接続
            bg_node  = nodes.new("ShaderNodeBackground")
            out_node = nodes.new("ShaderNodeOutputWorld")
            links.new(env_node.outputs["Color"], bg_node.inputs["Color"])
            links.new(bg_node.outputs["Background"], out_node.inputs["Surface"])

            # シーンのワールドとして設定
            context.scene.world = world
        """
        print("  [STEP 2] World Node 適用 (placeholder)")
        print("           → bpy.context.scene.world へのEnvironment Textureノード自動接続予定")
        print("           → 照明・背景の一括セットアップが完了予定")

    def _step_scatter_props(self, context: bpy.types.Context) -> None:
        """
        [フェーズ2で置換] Geometry Nodes を使ったプロップ自動スキャタリング。

        「荒廃した部屋」「森の中の遺跡」などのプロンプトから
        対応する3Dモデル（瓦礫・樹木・岩等）をSF3Dで生成し、
        Geometry Nodesのポイントスキャタリングで自然なランダム配置を実現する。

        実装予定:
            scatter_context = GeometryNodesScatterBuilder(context)
            scatter_context.set_density(prompt_density_estimate(prompt))
            scatter_context.set_objects(generated_prop_objects)
            scatter_context.build_node_graph()  # Geometry Nodesグラフを自動構築
        """
        print("  [STEP 3] Prop Scattering (placeholder)")
        print("           → Geometry Nodes ベースのランダムスキャタリング設定予定")
        print("           → プロンプト解析による密度・配置ルールの自動推定予定")
