import zipfile
import os

def build_package():
    """
    Blender/vaxis_core 配下のファイルをまとめ、
    Blender 5.1 Extension 形式の ZIP パッケージを生成します。
    """
    package_name = "IsekaiAssetStudio_v1.1.0.zip"
    source_dir = os.path.join("Blender", "vaxis_core")

    print(f"--- Packaging {package_name} ---")

    if not os.path.exists(source_dir):
        print(f"Error: {source_dir} が見つかりません。")
        return

    # ZIP ファイルの作成
    with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                # dummy.txt などの不要なファイルは除外
                if file == "dummy.txt":
                    continue

                full_path = os.path.join(root, file)
                # ZIP内では vaxis_core フォルダ直下の構造にする
                arcname = os.path.relpath(full_path, source_dir)
                zipf.write(full_path, arcname)
                print(f"  Added: {arcname}")

    print(f"\n成功: {package_name} が生成されました。")

if __name__ == "__main__":
    build_package()
