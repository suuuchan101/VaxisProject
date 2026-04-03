"""
VAXIS - 自動スカルプモジュール（完全ローカル・プロシージャル実装）

TripoSRで生成したメッシュにBlender内蔵プロシージャルテクスチャを重ねて
筋肉・皮膚質感などのサーフェス詳細を追加する。

ネットワーク不要・ダウンロード不要・即時実行。

テクスチャ構成:
    - MusgraveテクスチャA: 大きな筋肉の隆起（低周波）
    - MusgraveテクスチャB: 細かい皮膚の質感（高周波）
    → 2つのDisplaceモディファイアを重ねることで有機的な表面を表現
"""

import bpy

# 生物タイプごとの設定
_TYPE_CONFIG = {
    "HUMAN": {
        "subdivisions": 2,
        "muscle_strength": 0.03,
        "detail_strength": 0.008,
        "muscle_scale": 1.2,
        "detail_scale": 4.0,
    },
    "ANIMAL": {
        "subdivisions": 2,
        "muscle_strength": 0.05,
        "detail_strength": 0.012,
        "muscle_scale": 1.0,
        "detail_scale": 5.0,
    },
}
_DEFAULT_CONFIG = _TYPE_CONFIG["ANIMAL"]


def apply_muscle_detail(
    obj: bpy.types.Object,
    prompt: str,
    creature_type: str = "ANIMAL",
    status_callback=None,
) -> None:
    """
    メインスレッドから呼び出す。
    UV展開・Subdivision・プロシージャルDisplacementを適用する。

    Args:
        obj           : 対象メッシュオブジェクト
        prompt        : 元の生成プロンプト（将来の拡張用、現在は未使用）
        creature_type : "HUMAN" または "ANIMAL"
        status_callback: ステータス更新コールバック
    """
    def _cb(msg):
        print(f"[VAXIS Sculpt] {msg}")
        if status_callback:
            status_callback(msg)

    cfg = _TYPE_CONFIG.get(creature_type, _DEFAULT_CONFIG)

    # ----------------------------------------------------------
    # Step 1: Smart UV Project
    # ----------------------------------------------------------
    _cb("UV展開中...")
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')

    # ----------------------------------------------------------
    # Step 2: 既存VAXISモディファイアをクリア → Subdivision追加
    # ----------------------------------------------------------
    _cb("ポリゴンを細分化中...")
    for mod in list(obj.modifiers):
        if mod.name.startswith("VAXIS_"):
            obj.modifiers.remove(mod)

    subsurf = obj.modifiers.new(name="VAXIS_Subdiv", type='SUBSURF')
    subsurf.subdivision_type = 'CATMULL_CLARK'
    subsurf.levels = cfg["subdivisions"]
    subsurf.render_levels = cfg["subdivisions"]

    # ----------------------------------------------------------
    # Step 3: 筋肉隆起テクスチャ（Musgrave 低周波）
    # ----------------------------------------------------------
    _cb("筋肉ディスプレイスメントを構築中...")

    muscle_tex_name = f"VAXIS_Muscle_{obj.name}"
    if muscle_tex_name in bpy.data.textures:
        bpy.data.textures.remove(bpy.data.textures[muscle_tex_name])
    muscle_tex = bpy.data.textures.new(muscle_tex_name, type='MUSGRAVE')
    muscle_tex.musgrave_type = 'HYBRID_MULTIFRACTAL'
    muscle_tex.noise_scale = cfg["muscle_scale"]
    muscle_tex.noise_basis = 'ORIGINAL_PERLIN'
    muscle_tex.octaves = 4
    muscle_tex.dimension_max = 1.0
    muscle_tex.lacunarity = 2.0
    muscle_tex.gain = 1.0

    displace_muscle = obj.modifiers.new(name="VAXIS_Muscle", type='DISPLACE')
    displace_muscle.texture = muscle_tex
    displace_muscle.texture_coords = 'UV'
    displace_muscle.strength = cfg["muscle_strength"]
    displace_muscle.mid_level = 0.5

    # ----------------------------------------------------------
    # Step 4: 皮膚細部テクスチャ（Musgrave 高周波）
    # ----------------------------------------------------------
    _cb("皮膚質感ディスプレイスメントを構築中...")

    detail_tex_name = f"VAXIS_SkinDetail_{obj.name}"
    if detail_tex_name in bpy.data.textures:
        bpy.data.textures.remove(bpy.data.textures[detail_tex_name])
    detail_tex = bpy.data.textures.new(detail_tex_name, type='MUSGRAVE')
    detail_tex.musgrave_type = 'FBM'
    detail_tex.noise_scale = cfg["detail_scale"]
    detail_tex.noise_basis = 'ORIGINAL_PERLIN'
    detail_tex.octaves = 6
    detail_tex.dimension_max = 1.2

    displace_detail = obj.modifiers.new(name="VAXIS_SkinDetail", type='DISPLACE')
    displace_detail.texture = detail_tex
    displace_detail.texture_coords = 'UV'
    displace_detail.strength = cfg["detail_strength"]
    displace_detail.mid_level = 0.5

    # ----------------------------------------------------------
    # Step 5: モディファイア順序を整列 Subdiv→Muscle→SkinDetail
    # ----------------------------------------------------------
    _reorder_modifiers(obj)

    _cb("スカルプ完了！")


def _reorder_modifiers(obj: bpy.types.Object) -> None:
    """Subdiv → VAXIS_Muscle → VAXIS_SkinDetail の順に並べ替える。"""
    target_order = ["VAXIS_Subdiv", "VAXIS_Muscle", "VAXIS_SkinDetail"]
    for target_idx, mod_name in enumerate(target_order):
        names = [m.name for m in obj.modifiers]
        if mod_name not in names:
            continue
        current_idx = names.index(mod_name)
        if current_idx != target_idx:
            with bpy.context.temp_override(object=obj):
                bpy.ops.object.modifier_move_to_index(
                    modifier=mod_name, index=target_idx
                )
