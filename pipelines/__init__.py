# ============================================================
# VAXIS アドオン - Pipeline パッケージ 公開API + PipelineRouter
# ファイル: pipelines/__init__.py
#
# 責務: パイプラインのレジストリ管理とルーティング
#
# generation_type の文字列から適切なパイプラインインスタンスを
# 返す PipelineRouter クラスを定義する。
#
# 設計パターン: Registry Pattern（レジストリパターン）
#   - _REGISTRY 辞書でキー（文字列）→インスタンスのマッピングを管理
#   - 各パイプラインインスタンスはステートレス（状態を持たない）なため
#     シングルトン的に使い回し可能設計
#   - 新しい generation_type を追加する際は _REGISTRY のみ更新すればよい
# ============================================================

from .base import BasePipeline
from .character import CharacterPipeline
from .environment import EnvironmentPipeline
from .props import PropsPipeline

# パブリックAPI: このパッケージから外部にエクスポートするシンボル
__all__: list[str] = [
    "BasePipeline",
    "CharacterPipeline",
    "EnvironmentPipeline",
    "PropsPipeline",
    "PipelineRouter",
]


class PipelineRouter:
    """
    generation_type の文字列から対応するパイプラインを取得するルーター。

    operators.py の VAXIS_OT_Generate.execute() から呼び出され、
    UIで選択されたタイプに基づき適切なパイプラインを動的に選択する。

    新しい generation_type を追加する手順（3ファイルの変更が必要）:
        1. pipelines/ に新しいパイプラインクラスを作成する
        2. _REGISTRY に新エントリを追加する（このファイル）
        3. panels.py の VAXIS_SceneProperties.generation_type の
           items リストに同じキーを追加する
    """

    # ----------------------------------------------------------
    # パイプラインレジストリ
    # generation_type キー（大文字文字列）→ パイプラインインスタンス
    # ----------------------------------------------------------
    _REGISTRY: dict[str, BasePipeline] = {
        "HUMAN":       CharacterPipeline(subtype="HUMAN"),
        "ANIMAL":      CharacterPipeline(subtype="ANIMAL"),
        "ENVIRONMENT": EnvironmentPipeline(),
        "PROPS":       PropsPipeline(),
        "CONCEPT":     CharacterPipeline(subtype="CONCEPT"),
    }

    @classmethod
    def get_pipeline(cls, generation_type: str) -> BasePipeline:
        """
        generation_type に対応するパイプラインインスタンスを返す。

        Args:
            generation_type: panels.py の EnumProperty で選択された文字列
                             ("HUMAN" | "ANIMAL" | "ENVIRONMENT" | "PROPS")

        Returns:
            BasePipeline のサブクラスインスタンス

        Raises:
            KeyError: 未知の generation_type が渡された場合
                      （EnumProperty の items と _REGISTRY が不整合な場合に発生）
        """
        if generation_type not in cls._REGISTRY:
            raise KeyError(
                f"[VAXIS] 未知の generation_type: '{generation_type}'. "
                f"有効な値: {list(cls._REGISTRY.keys())}"
            )
        return cls._REGISTRY[generation_type]

    @classmethod
    def get_all_types(cls) -> list[str]:
        """登録されている全 generation_type のキーリストを返す。"""
        return list(cls._REGISTRY.keys())

    @classmethod
    def get_all_display_names(cls) -> dict[str, str]:
        """
        全 generation_type と対応する表示名の辞書を返す。
        デバッグやUI診断に使用する。
        """
        return {k: v.get_display_name() for k, v in cls._REGISTRY.items()}
