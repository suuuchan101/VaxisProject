import bpy
from . import comfy_bridge
from . import operators

# Blender アドオン登録情報の定義
bl_info = {
    "name": "VAXIS Core",
    "author": "VAXIS Development Team",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > VAXIS Core",
    "description": "Universal Reality Forge - 最小構成 (ComfyUI連携版)",
    "category": "3D View",
}

class VAXIS_AddonProperties(bpy.types.PropertyGroup):
    """
    アドオン全体で共有するプロパティを管理するクラス。
    ユーザー設定（ComfyUI URL 等）をシーン単位で永続化します。
    """
    comfy_url: bpy.props.StringProperty(
        name="ComfyUI URL",
        description="ComfyUI API のエンドポイント URL (デフォルト: http://127.0.0.1:8188)",
        default="http://127.0.0.1:8188",
    )

class VAXIS_PT_MainPanel(bpy.types.Panel):
    """VAXISのメインパネルを定義するクラス"""
    bl_idname = "VAXIS_PT_MainPanel"
    bl_label = "VAXIS Core"
    bl_space_type = "VIEW_3D"   # 3Dビューポートに表示
    bl_region_type = "UI"       # サイドバー（Nパネル）に配置
    bl_category = "VAXIS Core"  # タブ名

    def draw(self, context):
        """UIの描画ロジック"""
        layout = self.layout
        props = context.scene.vaxis_props
        
        # ユーザー提供のラベル
        layout.label(text="VAXIS System Ready.", icon='CHECKMARK')
        layout.separator()
        
        # UI セクション: 接続設定
        box = layout.box()
        box.label(text="ComfyUI Connections", icon='URL')
        box.prop(props, "comfy_url", text="")
        
        # UI セクション: 生成実行
        col = layout.column(align=True)
        col.scale_y = 1.6
        col.operator("vaxis.generate", text="Generate", icon='PLAY')

# 登録対象のクラス
classes = (
    VAXIS_AddonProperties,
    VAXIS_PT_MainPanel,
)

def register():
    """アドオン有効化時に呼ばれる登録処理"""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # オペレーターの登録（別ファイル）
    operators.register()
    
    # PropertyGroup を Scene インスタンスに関連付け
    bpy.types.Scene.vaxis_props = bpy.props.PointerProperty(type=VAXIS_AddonProperties)
    
    print(f"[VAXIS] {bl_info['name']} v{bl_info['version']} を正常に読み込みました。")

def unregister():
    """アドオン無効化時に呼ばれる解除処理"""
    # オペレーターの解除
    operators.unregister()
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    del bpy.types.Scene.vaxis_props
    
    print(f"[VAXIS] {bl_info['name']} を解除しました。")

if __name__ == "__main__":
    register()

# 著作者: VAXIS Development Team
