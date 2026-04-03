# ============================================================
# VAXIS アドオン - パイプライン抽象基底クラス
# ファイル: pipelines/base.py
#
# 責務: 全パイプラインが実装すべきインターフェースの定義
#
# Python の abc モジュールを使用して抽象基底クラスを定義し、
# 各具象パイプラインクラスに4つのメソッド実装を強制する。
#
# 設計パターン: Template Method パターン
#   - run() がパイプラインの実行フローを定義する公開API
#   - 各ステップ (_step_*) はサブクラスで実装するプライベートメソッド
#   - get_*() はUIへのメタデータ提供メソッド
# ============================================================

from abc import ABC, abstractmethod
import bpy


class BasePipeline(ABC):
    """
    全VAXISパイプラインの抽象基底クラス。

    Human / Animal / Environment / Props の各パイプラインは
    このクラスを継承し、すべての抽象メソッドを実装する必要がある。

    新しいパイプラインを追加する手順:
        1. このクラスを継承した新クラスを作成する
        2. 4つの抽象メソッドを実装する
        3. pipelines/__init__.py の PipelineRouter._REGISTRY に登録する
        4. panels.py の EnumProperty の items に同じキーを追加する
    """

    @abstractmethod
    def run(self, prompt: str, context: bpy.types.Context) -> None:
        """
        パイプラインの主処理を実行する。

        フェーズ1ではコンソールへの詳細ログ出力のみ。
        フェーズ2以降で実際のAI呼び出しと後処理に置き換える。

        Args:
            prompt: ユーザーが入力した生成プロンプト文字列
            context: Blenderの現在のコンテキスト（シーン・オブジェクトへのアクセス）
        """
        ...

    @abstractmethod
    def get_recommended_ai_model(self) -> str:
        """
        このパイプラインで推奨されるAIモデル名を返す。
        UIのステータスパネルやコンソールログに表示するために使用する。

        Returns:
            AIモデル名の文字列 (例: "SF3D (Stable Fast 3D)")
        """
        ...

    @abstractmethod
    def get_display_name(self) -> str:
        """
        UIに表示するパイプライン名を返す。
        Blenderのステータスバー通知に使用する。

        Returns:
            パイプライン表示名 (例: "Character: Human")
        """
        ...

    @abstractmethod
    def get_post_process_description(self) -> str:
        """
        このパイプラインが適用する後処理の説明文を返す。
        UIのGenerateControlsパネルに表示して、
        ユーザーに処理の内容をボタン押下前に告知する。

        Returns:
            後処理の説明文 (例: "Humanoid Rigging + ARKit Blendshapes (52種)")
        """
        ...
