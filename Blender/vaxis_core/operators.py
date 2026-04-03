import bpy
from .comfy_bridge import VAXIS_ComfyBridge

class VAXIS_OT_Generate(bpy.types.Operator):
    """
    ComfyUI への 生成リクエストを実行するオペレータークラス。
    ユーザーのアクション（ボタン押下）から、実際の処理フローを開始します。
    """
    
    # オペレーターの識別子と表示ラベル
    bl_idname = "vaxis.generate"
    bl_label = "Generate"
    bl_description = "ComfyUI へ プロンプトを送信し、生成プロセスを開始します。"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """
        オペレーターのメイン処理（実行時に呼び出されます）。
        
        Args:
            context (bpy.types.Context): Blender のコンテキスト。
            
        Returns:
            set: {'FINISHED'} (成功時) または {'CANCELLED'} (失敗時)。
        """
        # シーンに保存されたアドオン設定（プロパティ）を取得
        props = context.scene.vaxis_props
        comfy_url = props.comfy_url
        
        # ユーザー通知: 生成開始
        self.report({'INFO'}, f"Generartion 準備中... (URL: {comfy_url})")
        
        # ComfyUI ブリッジの初期化とリクエスト送信
        bridge = VAXIS_ComfyBridge(base_url=comfy_url)
        
        # プレースホルダープロンプト（実運用では動的に構築します）
        placeholder_prompt = {
            "3": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": { "ckpt_name": "v1-5-pruned-emaonly.ckpt" }
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": { "text": "masterpiece, best quality, 3D model style", "clip": ["3", 1] }
            }
        }
        
        # 通信の実行
        response = bridge.post_prompt(placeholder_prompt)
        
        # レスポンスの検証とフィードバック
        if isinstance(response, tuple) and response[0] is False:
            self.report({'ERROR'}, f"生成エラー: {response[1]}")
            return {'CANCELLED'}
        
        prompt_id = response.get("prompt_id", "不明")
        self.report({'INFO'}, f"生成リクエスト成功: ID = {prompt_id}")
        
        return {'FINISHED'}

# クラス登録
classes = (VAXIS_OT_Generate,)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

# 著作者: VAXIS Development Team
