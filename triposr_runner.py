"""
VAXIS - TripoSR 画像→3Dメッシュ 生成モジュール

TripoSR (Stability AI) を使って単一画像から高品質な3Dメッシュを生成する。
テキスト→画像は SDXL-Turbo (ローカル) で生成する。
初回実行時にモデル重みを自動ダウンロード（TripoSR: 約1.5GB）。
"""

import os
import sys
import tempfile

# Blender 5.1 site-packages
_SP = r"C:\5.1\python\Lib\site-packages"
if os.path.isdir(_SP) and _SP not in sys.path:
    sys.path.insert(0, _SP)

# TripoSRリポジトリをパスに追加
_TRIPOSR = r"C:\TripoSR"
if os.path.isdir(_TRIPOSR) and _TRIPOSR not in sys.path:
    sys.path.insert(0, _TRIPOSR)


def generate_from_image(image_path: str, output_dir: str = None, status_callback=None) -> str:
    """
    画像ファイルから3Dメッシュを生成し、.objファイルのパスを返す。

    Args:
        image_path: 入力画像のパス
        output_dir: 出力先ディレクトリ（省略時はtempフォルダ）

    Returns:
        生成した .obj ファイルの絶対パス
    """
    import torch
    import numpy as np
    import rembg
    from PIL import Image

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="vaxis_triposr_")
    os.makedirs(output_dir, exist_ok=True)

    def _cb(msg):
        if status_callback:
            status_callback(msg)

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"[VAXIS TripoSR] 使用デバイス: {device}")

    cache_dir = r"C:\vaxis_models\triposr"
    os.makedirs(cache_dir, exist_ok=True)
    os.environ["HF_HOME"] = cache_dir

    from tsr.system import TSR
    from tsr.utils import remove_background, resize_foreground

    _cb("TripoSRモデルを読み込み中... (初回は約1.5GBダウンロード)")
    model = TSR.from_pretrained(
        "stabilityai/TripoSR",
        config_name="config.yaml",
        weight_name="model.ckpt",
    )
    model.renderer.set_chunk_size(8192)
    model.to(device)

    _cb("背景を除去中...")
    rembg_session = rembg.new_session()
    image = remove_background(Image.open(image_path), rembg_session)
    image = resize_foreground(image, 0.85)
    img_array = np.array(image).astype(np.float32) / 255.0
    img_array = img_array[:, :, :3] * img_array[:, :, 3:4] + (1 - img_array[:, :, 3:4]) * 0.5
    image = Image.fromarray((img_array * 255.0).astype(np.uint8))

    _cb("3D推論中... (GPU)")
    with torch.no_grad():
        scene_codes = model([image], device=device)

    _cb("メッシュを抽出中...")
    meshes = model.extract_mesh(scene_codes, True, resolution=384)

    output_path = os.path.join(output_dir, "generated.obj")
    meshes[0].export(output_path)
    print(f"[VAXIS TripoSR] 完了: {output_path}")
    return output_path


def generate(prompt: str, output_dir: str = None, status_callback=None) -> str:
    """
    テキストプロンプトから3Dメッシュを生成し、.objファイルのパスを返す。
    テキスト→画像 (SDXL-Turbo / ローカル) → 3D (TripoSR) の2段階処理。

    Args:
        prompt   : 英語テキストプロンプト
        output_dir: 出力先ディレクトリ（省略時はtempフォルダ）

    Returns:
        生成した .obj ファイルの絶対パス
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="vaxis_triposr_")
    os.makedirs(output_dir, exist_ok=True)

    print(f"[VAXIS TripoSR] 生成開始: '{prompt}'")

    def _cb(msg):
        if status_callback:
            status_callback(msg)

    # Step 1: テキスト → 参照画像 (SDXL-Turbo ローカル)
    # プロンプト補正はgenerate_utils側で実施済みのためここでは追加しない
    from . import image_gen_local
    img_path = os.path.join(output_dir, "reference.png")
    image_gen_local.generate(
        prompt=prompt,
        output_path=img_path,
        status_callback=_cb,
    )

    # Step 2: 参照画像 → 3Dメッシュ (TripoSR)
    return generate_from_image(img_path, output_dir, status_callback=status_callback)
