#!/usr/bin/env python3
"""
Instagram Reel 動画生成スクリプト
出力: reel_day1.mp4 (1080x1920, 10秒, 縦型9:16)
"""

import os
import sys
import urllib.request

# --- 依存チェック ---
try:
    from moviepy.editor import (
        ColorClip, TextClip, CompositeVideoClip
    )
except ImportError:
    print("MoviePy が見つかりません。インストールします...")
    os.system(f"{sys.executable} -m pip install moviepy")
    from moviepy.editor import (
        ColorClip, TextClip, CompositeVideoClip
    )

# --- フォント準備 ---
FONT_PATH = "./NotoSansJP-Bold.ttf"
FONT_URL = (
    "https://github.com/notofonts/noto-cjk/raw/main/Sans/SubsetOTF/JP/"
    "NotoSansCJKjp-Bold.otf"
)

def ensure_font():
    if os.path.exists(FONT_PATH):
        return FONT_PATH
    # フォールバック: システムフォントを探す
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/usr/share/fonts/truetype/takao-gothic/TakaoGothic.ttf",
        "/usr/share/fonts/truetype/vlgothic/VL-Gothic-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            print(f"フォント使用: {path}")
            return path

    # NotoSansJP をダウンロード (Google Fonts CDN)
    print("Noto Sans JP をダウンロード中...")
    download_url = (
        "https://fonts.gstatic.com/s/notosansjp/v53/"
        "-F6jfjtqLzI2JPCgQBnw7HFyzSD-AsregP8VFBEj75s.woff2"
    )
    # woff2 は ImageMagick/PIL が直接使えないので ttf を探す別手段
    # GitHub releases から otf を取得
    alt_url = (
        "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/"
        "NotoSansCJKjp-Bold.otf"
    )
    try:
        urllib.request.urlretrieve(alt_url, "NotoSansJP-Bold.otf")
        return "NotoSansJP-Bold.otf"
    except Exception as e:
        print(f"フォントのダウンロードに失敗: {e}")
        print("ImageMagick のデフォルトフォントを使用します（文字化けする場合あり）")
        return None


# --- 設定 ---
WIDTH, HEIGHT = 1080, 1920
DURATION = 10.0
BG_COLOR = (0, 0, 0)      # 黒背景
TEXT_COLOR = "white"
OUTPUT = "reel_day1.mp4"

# テキスト構成: (開始秒, テキスト, フォントサイズ, フェード時間)
SLIDES = [
    (0.0,  "育児は年収1000万円じゃ\n足りない",              90, 0.5),
    (3.0,  "生卵を1年間、\n割らずに抱えて\n生活できますか？",   62, 0.5),
    (6.0,  "割ったら終わり。",                              80, 0.3),
    (7.5,  "0歳の子って、\nいつ死ぬかわからない。",            62, 0.3),
    (9.0,  "育児のつらさって、\nそういうこと。",              66, 0.3),
]

# 各スライドの表示終了秒（次のスライド開始 or 動画終了）
ENDS = [SLIDES[i + 1][0] if i + 1 < len(SLIDES) else DURATION
        for i in range(len(SLIDES))]


def make_text_clip(text, fontsize, font, start, end, fade_duration):
    """フェードイン付きテキストクリップを生成"""
    clip_duration = end - start
    tc = TextClip(
        text,
        fontsize=fontsize,
        font=font,
        color=TEXT_COLOR,
        align="center",
        method="caption",
        size=(WIDTH - 120, None),   # 左右60pxマージン
        kerning=2,
        interline=10,
    )
    tc = tc.set_position("center").set_start(start).set_duration(clip_duration)
    # フェードイン
    tc = tc.crossfadein(fade_duration)
    # フェードアウト（次テキストへの切り替えを滑らかに）
    if clip_duration > fade_duration * 2:
        tc = tc.crossfadeout(fade_duration * 0.5)
    return tc


def main():
    font = ensure_font()
    if font is None:
        font = "DejaVu-Sans-Bold"
        print(f"警告: 日本語フォントが見つかりません。'{font}' を使用します。")

    print(f"使用フォント: {font}")
    print(f"解像度: {WIDTH}x{HEIGHT}, 尺: {DURATION}秒")

    # 背景クリップ
    bg = ColorClip(size=(WIDTH, HEIGHT), color=BG_COLOR, duration=DURATION)

    # テキストクリップ一覧
    clips = [bg]
    for i, (start, text, fontsize, fade) in enumerate(SLIDES):
        end = ENDS[i]
        print(f"  [{start:.1f}s - {end:.1f}s] {text[:20].replace(chr(10), ' ')}...")
        tc = make_text_clip(text, fontsize, font, start, end, fade)
        clips.append(tc)

    # 合成
    final = CompositeVideoClip(clips, size=(WIDTH, HEIGHT))
    final = final.set_duration(DURATION)

    print(f"\n書き出し中: {OUTPUT}")
    final.write_videofile(
        OUTPUT,
        fps=30,
        codec="libx264",
        audio=False,
        preset="medium",
        ffmpeg_params=["-crf", "18"],
    )
    print(f"\n完了: {OUTPUT}")


if __name__ == "__main__":
    main()
