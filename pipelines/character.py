# ============================================================
# VAXIS アドオン - Character パイプライン
# ファイル: pipelines/character.py
#
# 責務: Human / Animal（キャラクター系）の生成後処理
#
# 対応する generation_type:
#   - "HUMAN"  : VRChatアバター / UEマネキン / Rigify対応 Humanoidリギング
#                + ARKit準拠52種 Blendshapes 自動生成
#   - "ANIMAL" : 四足歩行・怪物等の独自骨格リギング + ボーンマッピング
#
# 設計判断:
#   Human と Animal はコアの AI 呼び出し・メッシュインポートロジックを共有し、
#   リギングの型と Blendshapes の有無のみが異なる。
#   別クラスにすると共通コードの重複が生じるため、
#   subtype パラメータで分岐する単一クラス設計を採用した。
#
# フェーズ1: コンソール出力のみ（ダミー実装）
# フェーズ2: SF3D API + Rigify / 独自骨格テンプレートの本番統合
# ============================================================

import bpy
from .base import BasePipeline


class CharacterPipeline(BasePipeline):
    """
    キャラクター系オブジェクト生成パイプライン。

    Human と Animal の両タイプを subtype パラメータで分岐させる
    単一クラス設計。フェーズ1ではコンソールへの詳細ログ出力のみ。
    """

    def __init__(self, subtype: str) -> None:
        """
        パイプラインを初期化する。

        Args:
            subtype: "HUMAN" または "ANIMAL" を指定する。
                     それ以外の値を渡すと ValueError を送出する。
        """
        if subtype not in ("HUMAN", "ANIMAL", "CONCEPT"):
            raise ValueError(
                f"[VAXIS] CharacterPipeline の不正な subtype: '{subtype}'. "
                f"'HUMAN', 'ANIMAL', 'CONCEPT' のいずれかを指定してください。"
            )
        self.subtype = subtype

    # ----------------------------------------------------------
    # BasePipeline 抽象メソッドの実装
    # ----------------------------------------------------------

    def run(self, prompt: str, context: bpy.types.Context) -> None:
        """
        キャラクター生成パイプラインを実行する。

        フェーズ1: 実行予定の処理ステップをコンソールに詳細出力する。
        フェーズ2: 各ステップを実際の API 呼び出しに置き換える。
        """
        print("=" * 60)
        print(f"[VAXIS] Character Pipeline 起動 (subtype={self.subtype})")
        print(f"  使用AIモデル   : {self.get_recommended_ai_model()}")
        print(f"  受信プロンプト : '{prompt}'")
        print()

        # ステップ1: AIによる3Dモデル生成（フェーズ2でSF3D呼び出しに置換）
        self._step_ai_generate(prompt)

        # ステップ2: タイプ別リギング（フェーズ2でRigify/独自骨格統合）
        self._step_rigging()

        # ステップ3: Human の場合のみ ARKit Blendshapes を生成
        if self.subtype == "HUMAN":
            self._step_generate_blendshapes()

        print(f"  後処理 : {self.get_post_process_description()}")
        print("[VAXIS] Character Pipeline 完了シミュレーション")
        print("=" * 60)

    def get_recommended_ai_model(self) -> str:
        return "SF3D (Stable Fast 3D)"

    def get_display_name(self) -> str:
        if self.subtype == "HUMAN":
            return "Character: Human"
        return "Character: Animal / Creature"

    def get_post_process_description(self) -> str:
        if self.subtype == "HUMAN":
            return "Humanoid Rigging (Rigify / UE Mannequin) + ARKit Blendshapes (52種)"
        return "Custom Creature Skeleton + Bone Mapping"

    # ----------------------------------------------------------
    # 内部: 各処理ステップ（フェーズ2で本番コードに置き換える）
    # ----------------------------------------------------------

    def _step_ai_generate(self, prompt: str) -> None:
        """日本語対応プロンプトをTripoSRで非同期生成 → Blenderにインポートする。"""
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
            pipeline_type=self.subtype,
            apply_sculpt=True,
            status_callback=_set_status,
        )

    def _step_rigging(self) -> None:
        """
        [フェーズ2で置換] タイプに応じたリギングの適用。

        HUMAN  : Rigify Humanoidボーン or UEマネキン互換スケルトン自動適用
        ANIMAL : 四足歩行/異形Creatureボーンテンプレートの自動フィッティング
        """
        if self.subtype == "HUMAN":
            print("  [STEP 2] リギング (placeholder): Rigify Humanoid ボーン適用予定")
            print("           → UE Mannequin 互換スケルトンへの自動変換も予定")
        else:
            print("  [STEP 2] リギング (placeholder): Creature 独自骨格テンプレート適用予定")
            print("           → 四足歩行/異形ボーンマッピング自動処理予定")

    def _step_generate_blendshapes(self) -> None:
        """
        [フェーズ2で置換] ARKit準拠52種 Blendshapes の自動生成。

        Human タイプのみ実行し、Animal タイプには適用しない。
        VTuberソフトウェア（VTube Studio等）および VRChat の
        フルフェイストラッキングに即座に対応できる形式で生成する。

        実装予定:
            blendshape_generator.apply_arkit_52(active_object)
            → eyeBlinkLeft, mouthOpen, jawOpen, ... 52個のシェイプキーを生成
        """
        print("  [STEP 3] Blendshapes (placeholder): ARKit 52種 自動生成予定")
        print("           → VTuber / VRChat フルトラッキング完全対応形式で出力予定")
