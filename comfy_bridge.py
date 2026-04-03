import json
import urllib.request
import urllib.error


class VAXIS_ComfyBridge:
    """
    ComfyUI との通信を担当するブリッジクラス。
    """

    def __init__(self, base_url="http://127.0.0.1:8188"):
        self.base_url = base_url.rstrip("/")
        self.prompt_endpoint = f"{self.base_url}/prompt"
        self.queue_endpoint  = f"{self.base_url}/queue"

    def ping(self) -> bool:
        """ComfyUI が起動しているか確認する。"""
        try:
            with urllib.request.urlopen(f"{self.base_url}/system_stats", timeout=3):
                return True
        except Exception:
            return False

    def post_prompt(self, workflow_json: dict):
        """
        ComfyUI の /prompt エンドポイントへ生成リクエストを送信する。

        Returns:
            dict : 成功時のレスポンス
            tuple: (False, エラーメッセージ) 失敗時
        """
        data = json.dumps({"prompt": workflow_json}).encode("utf-8")
        req  = urllib.request.Request(self.prompt_endpoint, data=data)
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as e:
            msg = f"ComfyUI 接続エラー: {e.reason}"
            print(f"[VAXIS ComfyBridge] {msg}")
            return (False, msg)
        except Exception as e:
            msg = f"予期せぬエラー: {e}"
            print(f"[VAXIS ComfyBridge] {msg}")
            return (False, msg)
