"""
VAXIS - Shap-E テキスト→3Dメッシュ 生成モジュール

初回実行時にモデル重みを自動ダウンロード（約300MB）。
生成したメッシュを .obj としてテンポラリフォルダに保存し、
Blender へインポートするパスを返す。
"""

import os
import sys
import tempfile

# Blender 5.1 (Windows) のsite-packagesをモジュール読み込み時に追加
_SP = r"C:\5.1\python\Lib\site-packages"
if os.path.isdir(_SP) and _SP not in sys.path:
    sys.path.insert(0, _SP)


def _ensure_site_packages():
    """念のため再確認（モジュールレベルで既に追加済み）。"""
    if os.path.isdir(_SP) and _SP not in sys.path:
        sys.path.insert(0, _SP)


def generate(prompt: str, output_dir: str = None) -> str:
    """
    テキストプロンプトから3Dメッシュを生成し、.objファイルのパスを返す。

    Args:
        prompt   : 英語のテキストプロンプト
        output_dir: 出力先ディレクトリ（省略時はtempフォルダ）

    Returns:
        生成した .obj ファイルの絶対パス
    """
    _ensure_site_packages()

    import torch
    from shap_e.diffusion.sample import sample_latents
    from shap_e.diffusion.gaussian_diffusion import diffusion_from_config
    from shap_e.models.download import load_model, load_config
    from shap_e.util.notebooks import decode_latent_mesh

    print(f"[VAXIS Shap-E] 生成開始: '{prompt}'")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[VAXIS Shap-E] 使用デバイス: {device}")

    # キャッシュを専用フォルダに保存
    cache_dir = r"C:\vaxis_models"
    os.makedirs(cache_dir, exist_ok=True)

    print("[VAXIS Shap-E] モデルを読み込み中...")
    xm        = load_model("transmitter", device=device, cache_dir=cache_dir)
    model     = load_model("text300M",    device=device, cache_dir=cache_dir)
    diffusion = diffusion_from_config(load_config("diffusion"))

    print("[VAXIS Shap-E] 推論中（CPUなので数分かかります）...")
    latents = sample_latents(
        batch_size=1,
        model=model,
        diffusion=diffusion,
        guidance_scale=15.0,
        model_kwargs=dict(texts=[prompt]),
        progress=True,
        clip_denoised=True,
        use_fp16=True,  # GPU使用時はfp16で高速化
        use_karras=True,
        karras_steps=32,
        sigma_min=1e-3,
        sigma_max=160,
        s_churn=0,
    )

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="vaxis_shape_")

    output_path = os.path.join(output_dir, "generated.obj")

    print(f"[VAXIS Shap-E] メッシュをエクスポート中: {output_path}")
    t = decode_latent_mesh(xm, latents[0]).tri_mesh()
    with open(output_path, "w") as f:
        t.write_obj(f)

    print(f"[VAXIS Shap-E] 完了: {output_path}")
    return output_path
