"""
VAXIS - ローカル画像生成モジュール

SDXL-Turbo (Stability AI) を使ってテキストから参照画像をローカル生成する。
初回実行時にモデル重みを自動ダウンロード（約6.5GB）。
以降はキャッシュから即時読み込み。

RTX 4070 Ti で約2秒/枚（4ステップ・fp16）。
"""

import os
import sys

# Blender 5.1 site-packages
_SP = r"C:\5.1\python\Lib\site-packages"
if os.path.isdir(_SP) and _SP not in sys.path:
    sys.path.insert(0, _SP)

# モデルキャッシュ先
_CACHE_DIR = r"C:\vaxis_models\sdxl_turbo"

# ロード済みパイプラインをモジュールレベルでキャッシュ（Blenderセッション中は再利用）
_pipeline = None


def _get_pipeline():
    """SDXL-Turboパイプラインを返す（初回のみロード）。"""
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    import torch
    from diffusers import AutoPipelineForText2Image

    os.makedirs(_CACHE_DIR, exist_ok=True)
    print("[VAXIS ImageGen] SDXL-Turboを読み込み中 (初回は約6.5GBダウンロード)...")

    _pipeline = AutoPipelineForText2Image.from_pretrained(
        "stabilityai/sdxl-turbo",
        torch_dtype=torch.float16,
        variant="fp16",
        cache_dir=_CACHE_DIR,
    )
    _pipeline.to("cuda")
    print("[VAXIS ImageGen] SDXL-Turbo 読み込み完了")
    return _pipeline


def generate(
    prompt: str,
    output_path: str,
    width: int = 512,
    height: int = 512,
    steps: int = 4,
    status_callback=None,
) -> str:
    """
    テキストプロンプトから画像を生成し、ファイルに保存する。

    Args:
        prompt       : 英語テキストプロンプト
        output_path  : 保存先ファイルパス（.png）
        width/height : 出力解像度（SDXL-Turboは512推奨）
        steps        : 推論ステップ数（4で十分、増やすと遅くなる）
        status_callback: ステータス更新コールバック

    Returns:
        保存したファイルのパス
    """
    def _cb(msg):
        print(f"[VAXIS ImageGen] {msg}")
        if status_callback:
            status_callback(msg)

    import torch

    _cb("SDXL-Turboを準備中...")
    pipe = _get_pipeline()

    _cb(f"画像を生成中... ({steps}ステップ / GPU)")
    with torch.no_grad():
        result = pipe(
            prompt=prompt,
            num_inference_steps=steps,
            guidance_scale=0.0,   # Turboはguidance_scale=0が最適
            width=width,
            height=height,
        )

    image = result.images[0]
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    image.save(output_path)
    _cb(f"画像を保存: {output_path}")
    return output_path
