import json
import urllib.request
import urllib.error

class VAXIS_ComfyBridge:
    """
    ComfyUI との通信を担当するブリッジクラス。
    クリーンアーキテクチャの Infrastructure 層として、HTTP 通信をカプセル化します。
    """
    
    def __init__(self, base_url="http://127.0.0.1:8188"):
        """
        初期化メソッド。
        
        Args:
            base_url (str): ComfyUI のベースURL（デフォルト: http://127.0.0.1:8188）
        """
        self.base_url = base_url.rstrip("/")
        self.prompt_endpoint = f"{self.base_url}/prompt"

    def post_prompt(self, workflow_json):
        """
        ComfyUI の /prompt エンドポイントに対し、生成リクエストを送信します。
        
        Args:
            workflow_json (dict): 送信するワークフローデータ (dict 形式)
            
        Returns:
            dict: 成功時のレスポンスデータ。
            tuple: (False, エラーメッセージ) 失敗時。
        """
        # JSON データをバイト列に変換
        data = json.dumps({"prompt": workflow_json}).encode('utf-8')
        
        # リクエストの構築
        req = urllib.request.Request(self.prompt_endpoint, data=data)
        req.add_header('Content-Type', 'application/json')
        
        try:
            # 通信の実行
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = response.read().decode('utf-8')
                return json.loads(res_body)
        
        except urllib.error.URLError as e:
            # 接続エラー、タイムアウトなどのハンドル
            error_msg = f"接続エラー: {e.reason}"
            print(f"[VAXIS Bridge Error] {error_msg}")
            return (False, error_msg)
            
        except Exception as e:
            # その他の予期せぬエラー
            error_msg = f"予期せぬエラーが発生しました: {str(e)}"
            print(f"[VAXIS Bridge Error] {error_msg}")
            return (False, error_msg)

# 著作者: VAXIS Development Team
