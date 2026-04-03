"""
VAXIS - Tripo3D API ランナー

Tripo3D API (https://platform.tripo3d.ai) を使って
テキスト・画像から高品質な3Dメッシュを生成する。

無料枠: 毎月一定クレジット（登録のみで使用可）
品質  : 現在最高水準のtext/image→3Dモデル
"""

import os
import sys
import time
import json
import tempfile
import urllib.request
import urllib.error

_SP = r"C:\5.1\python\Lib\site-packages"
if os.path.isdir(_SP) and _SP not in sys.path:
    sys.path.insert(0, _SP)

_BASE_URL = "https://platform.tripo3d.ai/v2/openapi"


def _request(method: str, path: str, api_key: str, body: dict = None, timeout: int = 30):
    """Tripo3D APIへのHTTPリクエスト共通処理。"""
    url = f"{_BASE_URL}{path}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _poll_task(task_id: str, api_key: str, status_callback=None, poll_interval: int = 3) -> dict:
    """タスクが完了するまでポーリングし、結果を返す。"""
    def _cb(msg):
        if status_callback:
            status_callback(msg)

    while True:
        result = _request("GET", f"/task/{task_id}", api_key)
        status = result["data"]["status"]

        if status == "success":
            return result["data"]
        elif status == "failed":
            raise RuntimeError(f"Tripo3D タスク失敗: {result}")
        elif status in ("queued", "running"):
            progress = result["data"].get("progress", 0)
            _cb(f"生成中... {progress}%")
            time.sleep(poll_interval)
        else:
            time.sleep(poll_interval)


def _download_model(url: str, output_path: str) -> str:
    """モデルファイルをダウンロードして保存する。"""
    req = urllib.request.Request(url, headers={"User-Agent": "VAXIS/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        with open(output_path, "wb") as f:
            f.write(resp.read())
    return output_path


def generate_from_text(
    prompt: str,
    api_key: str,
    output_dir: str = None,
    status_callback=None,
) -> str:
    """
    テキストプロンプトから3Dメッシュを生成し、.glbファイルのパスを返す。

    Args:
        prompt    : 英語テキストプロンプト
        api_key   : Tripo3D APIキー
        output_dir: 出力先ディレクトリ
        status_callback: ステータス更新コールバック

    Returns:
        生成した .glb ファイルの絶対パス
    """
    def _cb(msg):
        print(f"[VAXIS Tripo3D] {msg}")
        if status_callback:
            status_callback(msg)

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="vaxis_tripo3d_")
    os.makedirs(output_dir, exist_ok=True)

    _cb(f"テキスト→3D タスクを送信中...")
    resp = _request("POST", "/task", api_key, {
        "type": "text_to_model",
        "prompt": prompt,
        "model_version": "v2.5-20250123",
    })

    if resp.get("code") != 0:
        raise RuntimeError(f"タスク作成失敗: {resp}")

    task_id = resp["data"]["task_id"]
    _cb(f"タスクID: {task_id} / 生成中...")

    result = _poll_task(task_id, api_key, status_callback=_cb)

    model_url = result["output"]["model"]
    out_path = os.path.join(output_dir, "generated.glb")
    _cb("モデルをダウンロード中...")
    _download_model(model_url, out_path)
    _cb(f"完了: {out_path}")
    return out_path


def generate_from_image(
    image_path: str,
    api_key: str,
    output_dir: str = None,
    status_callback=None,
) -> str:
    """
    画像ファイルから3Dメッシュを生成し、.glbファイルのパスを返す。

    Args:
        image_path: 入力画像のパス（PNG/JPG）
        api_key   : Tripo3D APIキー
        output_dir: 出力先ディレクトリ
        status_callback: ステータス更新コールバック

    Returns:
        生成した .glb ファイルの絶対パス
    """
    import base64

    def _cb(msg):
        print(f"[VAXIS Tripo3D] {msg}")
        if status_callback:
            status_callback(msg)

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="vaxis_tripo3d_")
    os.makedirs(output_dir, exist_ok=True)

    # 画像をBase64エンコードして送信
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    ext = os.path.splitext(image_path)[1].lower().lstrip(".")
    mime = "image/png" if ext == "png" else "image/jpeg"

    _cb("画像→3D タスクを送信中...")
    resp = _request("POST", "/task", api_key, {
        "type": "image_to_model",
        "file": {
            "type": mime,
            "file": img_b64,
        },
        "model_version": "v2.5-20250123",
    })

    if resp.get("code") != 0:
        raise RuntimeError(f"タスク作成失敗: {resp}")

    task_id = resp["data"]["task_id"]
    _cb(f"タスクID: {task_id} / 生成中...")

    result = _poll_task(task_id, api_key, status_callback=_cb)

    model_url = result["output"]["model"]
    out_path = os.path.join(output_dir, "generated.glb")
    _cb("モデルをダウンロード中...")
    _download_model(model_url, out_path)
    _cb(f"完了: {out_path}")
    return out_path
