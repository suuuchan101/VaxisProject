# ============================================================
# VAXIS アドオン - Panel (UI) モジュール
# ファイル: panels.py
# バージョン: 0.2.0 (Universal Reality Forge 対応)
#
# 責務: UIの描画とプロパティの定義
# 3DビューポートのNパネル（サイドバー）に表示する「VAXIS Core」
# タブのUI要素をすべてここで定義します。
#
# アーキテクチャノート:
#   - 各クラスは bpy.types.Panel を継承する
#   - bl_idname は "VAXIS_PT_<パネル名>" の形式で命名する
#   - UIの描画ロジック（draw()）にビジネスロジックを含めない
#   - ビジネスロジックは operators.py のオペレーターに完全委譲する
#
# パネル構成 (Nパネル > VAXIS Core タブ):
#   1. VAXIS_PT_MainPanel          : 親パネル（タブのルート）
#   2. VAXIS_PT_AIEngineStatus     : AIエンジンの状態表示
#   3. VAXIS_PT_PromptInput        : 生成タイプ選択 + プロンプト入力
#   4. VAXIS_PT_GenerateControls   : パイプライン情報 + 生成ボタン
# ============================================================

import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty
from bpy.types import PropertyGroup


# ============================================================
# UI定数: generation_type ごとの動的テキスト定義
# パネルの draw() 内で直接文字列を書くことを避け、
# 定数として定義することで変更箇所を一元管理する。
# ============================================================

# 各生成タイプに対応するプロンプト入力例（ヒントテキスト）
_PROMPT_HINTS: dict[str, str] = {
    "HUMAN":       "例: young elf warrior with silver armor and glowing blue eyes",
    "ANIMAL":      "例: bioluminescent deep-sea creature with six tentacle-legs",
    "ENVIRONMENT": "例: abandoned cyberpunk alley at night with neon rain",
    "PROPS":       "例: ancient rusted sword with glowing arcane runes",
    "CONCEPT":     "例: 怒り / chaos / the weight of loneliness / 重力の歪み",
}

# 各生成タイプの後処理内容の要約（GenerateControlsパネルに表示）
# pipelines/ の各クラスの get_post_process_description() と内容を合わせる。
_POST_PROCESS_LABELS: dict[str, str] = {
    "HUMAN":       "Humanoid Rigging (Rigify/UE) + ARKit Blendshapes (52種)",
    "ANIMAL":      "Creature Skeleton + Bone Mapping",
    "ENVIRONMENT": "ミニチュアジオラマ生成 (TripoSR)",
    "PROPS":       "プロップメッシュ生成 (TripoSR)",
    "CONCEPT":     "抽象概念の3D具現化 (SDXL-Turbo + TripoSR)",
}


# ============================================================
# プロパティグループ: シーン全体で共有するVAXISの設定値
# ============================================================

class VAXIS_SceneProperties(PropertyGroup):
    """
    VAXISアドオンが使用するシーンレベルのプロパティをまとめたグループ。

    bpy.types.Scene.vaxis_props としてシーンに紐付けられ、
    Blenderファイルを保存・読み込みしてもデータが保持される。

    v0.2.0 変更点:
        - generation_type (EnumProperty) を新規追加
        - creature_prompt を汎用的な generation_prompt にリネーム
    """

    generation_type: EnumProperty(
        name="生成対象",
        description="生成する3Dオブジェクトのタイプを選択します",
        items=[
            (
                "HUMAN",
                "Human",
                "VRChatアバターやゲームNPCなどHumanoidキャラクターを生成します\n"
                "後処理: Rigify/UEマネキン対応リギング + ARKit準拠52種Blendshapes",
                "ARMATURE_DATA",
                0,
            ),
            (
                "ANIMAL",
                "Animal",
                "四足歩行や異形のクリーチャー・モンスターを生成します\n"
                "後処理: 独自Creature骨格テンプレート + ボーンマッピング",
                "OUTLINER_OB_ARMATURE",
                1,
            ),
            (
                "ENVIRONMENT",
                "Environment",
                "360度HDRIや地形などの空間・背景を生成します\n"
                "後処理: World Node自動接続 + Geometry Nodesスキャタリング",
                "WORLD",
                2,
            ),
            (
                "PROPS",
                "Props",
                "武器・家具・小物など静的オブジェクトを生成します\n"
                "後処理: PBRマテリアル自動生成 + LOD0-3自動生成",
                "OBJECT_DATA",
                3,
            ),
            (
                "CONCEPT",
                "Concept / Abstract",
                "感情・概念・現象など抽象的なアイデアを3Dオブジェクトとして具現化します\n"
                "例: 怒り、重力、時間の歪み、混沌",
                "OUTLINER_OB_POINTCLOUD",
                4,
            ),
        ],
        default="ANIMAL",
    )

    generation_prompt: StringProperty(
        name="Prompt",
        description=(
            "生成したいオブジェクトの特徴や雰囲気をテキストで入力します。\n"
            "生成タイプを選択すると、対応するプロンプト例がヒントとして表示されます。"
        ),
        default="",
        maxlen=512,
    )

    generation_status: StringProperty(
        name="Status",
        description="生成処理の現在の状態",
        default="",
    )

    use_image_input: BoolProperty(
        name="画像から生成",
        description="テキストプロンプトの代わりに画像ファイルを参照画像として使用する",
        default=False,
    )

    input_image_path: StringProperty(
        name="参照画像",
        description="3D生成のベースとなる画像ファイルのパス（PNG/JPG）",
        default="",
        subtype='FILE_PATH',
    )

    tripo3d_api_key: StringProperty(
        name="Tripo3D APIキー",
        description="Tripo3D APIキー (https://platform.tripo3d.ai で無料取得)",
        default="",
        subtype='PASSWORD',
    )


# ============================================================
# パネル1: メイン（ルート）パネル
# タブそのものを定義するクラス。このパネルがNパネルへの入口となる。
# ============================================================

class VAXIS_PT_MainPanel(bpy.types.Panel):
    """
    VAXISのメインパネル。
    NパネルのタブID「VAXIS Core」をここで定義する。
    このクラス自体はヘッダー行のみ描画し、
    実際のコンテンツは子パネルクラスが担当する。
    """

    bl_idname = "VAXIS_PT_MainPanel"
    bl_label = "VAXIS Core"              # Nパネルのタブ名（サイドバーに表示）
    bl_space_type = "VIEW_3D"            # 表示するエディタの種類: 3Dビューポート
    bl_region_type = "UI"                # Nパネル（サイドバー）に表示
    bl_category = "VAXIS Core"           # Nパネルのタブに表示されるカテゴリ名

    def draw(self, context: bpy.types.Context) -> None:
        """
        メインパネルのヘッダー部分を描画する。
        v0.2.0: コンセプト更新に合わせてラベルを変更。
        """
        layout = self.layout
        row = layout.row()
        # SCENE_DATA アイコン: 「世界の構築」のコンセプトを表現
        row.label(text="VAXIS - Universal Reality Forge", icon="SCENE_DATA")


# ============================================================
# パネル2: AIエンジンステータス
# ローカルAIの稼働状況をユーザーに通知するパネル。
# ============================================================

class VAXIS_PT_AIEngineStatus(bpy.types.Panel):
    """
    AIエンジンの現在状態を表示するサブパネル。

    v0.2.0 変更点:
        - Character/Props 向け SF3D に加え、
          Environment 向けの Panorama360-XL のステータスを追加。

    フェーズ2以降では、各AIサービスへの接続状態を
    ポーリングして動的に表示する実装に置き換える。
    """

    bl_idname = "VAXIS_PT_AIEngineStatus"
    bl_label = "AI Engine Status"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VAXIS Core"
    bl_parent_id = "VAXIS_PT_MainPanel"
    bl_options = {"DEFAULT_CLOSED"}      # デフォルトでは折りたたまれた状態

    def draw(self, context: bpy.types.Context) -> None:
        """AIエンジンの状態インジケーターを描画する。"""
        layout = self.layout
        props = context.scene.vaxis_props

        # --- Tripo3D API ---
        box = layout.box()
        has_key = bool(props.tripo3d_api_key.strip())
        icon = "CHECKMARK" if has_key else "ERROR"
        box.label(text="Tripo3D API (推奨・高品質):", icon=icon)
        box.prop(props, "tripo3d_api_key", text="APIキー")
        if not has_key:
            row = box.row()
            row.scale_y = 0.7
            row.label(text="platform.tripo3d.ai で無料取得", icon="URL")

        layout.separator()

        # --- ローカルエンジン (フォールバック) ---
        box2 = layout.box()
        box2.label(text="ローカル (フォールバック):", icon="DESKTOP")
        box2.label(text="  SDXL-Turbo + TripoSR", icon="MEMORY")


# ============================================================
# パネル3: プロンプト入力
# v0.2.0: 生成タイプ選択ドロップダウンを追加
# ============================================================

class VAXIS_PT_PromptInput(bpy.types.Panel):
    """
    生成タイプ選択ドロップダウンと、生成プロンプト入力フォームのパネル。

    generation_type の選択に連動してヒントテキストが動的に変わり、
    ユーザーがタイプに合ったプロンプトを書く助けになる。

    入力値はBlenderシーンに保存されるため、
    ファイルを再度開いても入力内容が保持される。
    """

    bl_idname = "VAXIS_PT_PromptInput"
    bl_label = "Prompt Input"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VAXIS Core"
    bl_parent_id = "VAXIS_PT_MainPanel"

    def draw(self, context: bpy.types.Context) -> None:
        """生成タイプドロップダウンとプロンプト入力フィールドを描画する。"""
        layout = self.layout
        props = context.scene.vaxis_props

        # --- 生成対象タイプ選択ドロップダウン ---
        col = layout.column(align=True)
        col.label(text="生成対象タイプ:", icon="PROPERTIES")
        # text="" にするとプロパティ名ラベルが非表示になりコンパクトになる
        col.prop(props, "generation_type", text="")

        layout.separator()

        # --- 入力モード切り替え ---
        layout.prop(props, "use_image_input", icon="IMAGE_DATA")

        if props.use_image_input:
            # --- 画像入力モード ---
            col = layout.column(align=True)
            col.label(text="参照画像:", icon="IMAGE_DATA")
            col.prop(props, "input_image_path", text="")
            if not props.input_image_path:
                col.label(text="PNG / JPG を選択してください", icon="INFO")
        else:
            # --- テキストプロンプト入力エリア ---
            col = layout.column(align=True)
            col.label(text="生成プロンプト:", icon="GREASEPENCIL")
            col.prop(props, "generation_prompt", text="")

            hint_text = _PROMPT_HINTS.get(props.generation_type, "")
            if hint_text:
                hint_col = layout.column()
                hint_col.scale_y = 0.75
                hint_col.label(text=hint_text, icon="INFO")


# ============================================================
# パネル4: 生成コントロール
# v0.2.0: パイプライン情報の事前告知ボックスを追加
# ============================================================

class VAXIS_PT_GenerateControls(bpy.types.Panel):
    """
    3D生成を実行するボタンと、適用されるパイプライン情報を表示するパネル。

    UIのボタンとビジネスロジックは完全に分離されており、
    ボタンは operator (VAXIS_OT_Generate) を呼び出すだけ。
    実際のパイプライン選択・実行は operators.py → pipelines/ が担当する。

    v0.2.0 追加:
        - 適用パイプラインと後処理の内容をボタン押下前にユーザーに告知する
          「適用パイプライン情報」ボックスを追加。
    """

    bl_idname = "VAXIS_PT_GenerateControls"
    bl_label = "Generate Controls"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VAXIS Core"
    bl_parent_id = "VAXIS_PT_MainPanel"

    def draw(self, context: bpy.types.Context) -> None:
        """パイプライン情報ボックスと生成ボタンを描画する。"""
        layout = self.layout
        props = context.scene.vaxis_props

        gen_type = props.generation_type
        use_image = props.use_image_input
        is_ready = (
            bool(props.input_image_path.strip()) if use_image
            else bool(props.generation_prompt.strip())
        )

        # --- 適用パイプライン情報ボックス ---
        info_box = layout.box()
        info_box.label(text="適用パイプライン:", icon="NODETREE")
        post_process = _POST_PROCESS_LABELS.get(gen_type, "不明")
        mode_label = "画像→3D (TripoSR)" if use_image else f"テキスト→3D: {post_process}"
        info_box.label(text=f"  → {mode_label}")

        layout.separator()

        # --- バリデーション ---
        if not is_ready:
            warn_box = layout.box()
            msg = "画像を選択してください" if use_image else "プロンプトを入力してください"
            warn_box.label(text=msg, icon="ERROR")

        # --- メイン生成ボタン ---
        col = layout.column(align=True)
        row = col.row()
        row.scale_y = 2.0
        row.enabled = is_ready
        row.operator(
            "vaxis.generate",
            text="⚡ Generate",
            icon="PLAY",
        )

        # --- 生成ステータス表示 ---
        if props.generation_status:
            layout.separator()
            status_box = layout.box()
            status_box.label(text=props.generation_status, icon="SORTTIME")

        # --- フェーズ情報 ---
        layout.separator()
        info_col = layout.column()
        info_col.scale_y = 0.75
        info_col.label(text="フェーズ1: パイプライン検証モード", icon="SETTINGS")

        # --- リロードボタン ---
        layout.separator()
        layout.operator("vaxis.reload", text="🔄 Reload VAXIS", icon="FILE_REFRESH")


# ============================================================
# 登録対象クラス一覧
# 登録順序に注意:
#   1. PropertyGroup を先に登録してシーンに紐付ける
#   2. 親パネルを子パネルより先に登録する
# ============================================================

_CLASSES: list[type] = [
    VAXIS_SceneProperties,
    VAXIS_PT_MainPanel,
    VAXIS_PT_AIEngineStatus,
    VAXIS_PT_PromptInput,
    VAXIS_PT_GenerateControls,
]


def register() -> None:
    """
    このモジュール内の全クラスをBlenderに登録し、
    シーンプロパティを bpy.types.Scene に紐付ける。
    """
    for cls in _CLASSES:
        bpy.utils.register_class(cls)

    # scene.vaxis_props で全プロパティにアクセスできるようになる
    bpy.types.Scene.vaxis_props = bpy.props.PointerProperty(
        type=VAXIS_SceneProperties,
        name="VAXIS Properties",
        description="VAXISアドオンが使用するシーンレベルのプロパティ",
    )


def unregister() -> None:
    """
    このモジュール内の全クラスのBlender登録を解除し、
    シーンプロパティの紐付けを削除する。
    """
    del bpy.types.Scene.vaxis_props

    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
