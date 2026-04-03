"""
VAXIS - 日本語→英語 自動翻訳ユーティリティ

外部ライブラリ不要。MyMemory 無料 API（APIキー不要）を使用。
日本語が含まれる場合のみ翻訳し、それ以外はそのまま返す。
"""

import re
import json
import urllib.request
import urllib.parse


def _contains_japanese(text: str) -> bool:
    """ひらがな・カタカナ・漢字のいずれかが含まれるか判定する。"""
    return bool(re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', text))


def translate_to_english(text: str) -> str:
    """
    テキストを英語に翻訳して返す。
    日本語が含まれない場合はそのまま返す。
    翻訳に失敗した場合も元のテキストを返す。
    """
    if not _contains_japanese(text):
        return text

    try:
        params = urllib.parse.urlencode({"q": text, "langpair": "ja|en"})
        url = f"https://api.mymemory.translated.net/get?{params}"

        req = urllib.request.Request(url, headers={"User-Agent": "VAXIS/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        translated = data["responseData"]["translatedText"]
        print(f"[VAXIS Translator] '{text}' → '{translated}'")
        return translated

    except Exception as e:
        print(f"[VAXIS Translator] 翻訳失敗（元のプロンプトを使用）: {e}")
        return text
