#!/usr/bin/env python3
"""
Gemini API を使って Instagram リール用縦型画像を生成
出力: reel_day2.png (1080x1920)
"""

import os
import sys
import io
import subprocess

# --- 必要ライブラリの自動インストール ---
def install(package):
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-q", package]
    )

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("google-genai をインストール中...")
    install("google-genai")
    from google import genai
    from google.genai import types

try:
    from PIL import Image
except ImportError:
    install("pillow")
    from PIL import Image

# --- 設定 ---
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("エラー: 環境変数 GEMINI_API_KEY が設定されていません")
    print("  export GEMINI_API_KEY='your-api-key'")
    sys.exit(1)

MODEL  = "gemini-2.5-flash-preview-04-17"   # Gemini 2.5 Flash (image output)
FALLBACK_MODEL = "gemini-2.0-flash-preview-image-generation"
OUTPUT = "reel_day2.png"
TARGET_W, TARGET_H = 1080, 1920

PROMPT = """\
Create a vertical smartphone image (9:16 portrait aspect ratio).

Design requirements:
- Pure solid black background (#000000), no gradients, no textures
- White Japanese text only, bold weight, large font
- Text centered both horizontally and vertically on the canvas
- Generous line spacing between each line (about 1.8x)
- No decorations, borders, or background imagery — black and white only
- Minimal, dramatic, emotional Japanese typography aesthetic

Display the following lines exactly, each on its own line:
「手伝うね」って言った。
その夜も、
一人だった。
育児は「手伝う」ものじゃない。
あなたの子でしょ。
"""


def main():
    client = genai.Client(api_key=API_KEY)

    # モデルを順番に試す
    for model in [MODEL, FALLBACK_MODEL]:
        print(f"モデル: {model}")
        print("画像生成中...")
        try:
            response = client.models.generate_content(
                model=model,
                contents=PROMPT,
                config=types.GenerateContentConfig(
                    response_modalities=["image", "text"]
                ),
            )
            break  # 成功したらループを抜ける
        except Exception as e:
            print(f"  → 失敗 ({e.__class__.__name__}): {str(e)[:80]}")
            if model == FALLBACK_MODEL:
                print("全モデルで失敗しました")
                sys.exit(1)
            print("  → フォールバックモデルを試します...")

    # レスポンスから画像データを取得
    image_data = None
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            if part.inline_data.mime_type.startswith("image/"):
                image_data = part.inline_data.data
                break
        if hasattr(part, "text") and part.text:
            print(f"テキスト応答: {part.text[:100]}")

    if not image_data:
        print("エラー: 画像データが返ってきませんでした")
        sys.exit(1)

    # PIL で開く
    img = Image.open(io.BytesIO(image_data))
    print(f"生成サイズ: {img.width}x{img.height}")

    # 1080x1920 の黒キャンバスに中央配置でフィット
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), (0, 0, 0))
    img_copy = img.copy()
    img_copy.thumbnail((TARGET_W, TARGET_H), Image.LANCZOS)
    x = (TARGET_W - img_copy.width) // 2
    y = (TARGET_H - img_copy.height) // 2
    canvas.paste(img_copy, (x, y))
    canvas.save(OUTPUT, "PNG")

    print(f"保存完了: {OUTPUT} ({TARGET_W}x{TARGET_H})")


if __name__ == "__main__":
    main()
