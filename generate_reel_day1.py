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
    from moviepy import ColorClip, TextClip, CompositeVideoClip
except ImportError:
    print("MoviePy が見つかりません。インストールします...")
    os.system(f"{sys.executable} -m pip install moviepy")
    from moviepy import ColorClip, TextClip, CompositeVideoClip

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

TEXT_WIDTH = WIDTH - 200   # 左右100pxマージン
FONT_SIZE = 60             # 統一フォントサイズ

# テキスト構成: (開始秒, テキスト, フェード時間)
SLIDES = [
    (0.0,  "育児は年収1000万円じゃ足りない",              0.5),
    (3.0,  "生卵を1年間、割らずに抱えて生活できますか？",   0.5),
    (6.0,  "割ったら終わり。",                            0.3),
    (7.5,  "0歳の子って、いつ死ぬかわからない。",          0.3),
    (9.0,  "育児のつらさって、そういうこと。",             0.3),
]

# 各スライドの表示終了秒（次のスライド開始 or 動画終了）
ENDS = [SLIDES[i + 1][0] if i + 1 < len(SLIDES) else DURATION
        for i in range(len(SLIDES))]

from moviepy.video.fx import CrossFadeIn


def make_text_clip(text, font, start, end, fade_duration):
    """フェードイン付きテキストクリップを生成 (MoviePy 2.x API)"""
    clip_duration = end - start
    tc = TextClip(
        font=font,
        text=text,
        font_size=FONT_SIZE,
        color=TEXT_COLOR,
        text_align="center",
        method="caption",       # 自動折り返し
        size=(TEXT_WIDTH, None),
        interline=14,
        duration=clip_duration,
    )
    # 画面中央に配置（x, y ともにセンタリング）
    x = (WIDTH - tc.w) // 2
    y = (HEIGHT - tc.h) // 2
    tc = tc.with_position((x, y)).with_start(start)
    tc = tc.with_effects([CrossFadeIn(fade_duration)])
    return tc


def main():
    font = ensure_font()
    if font is None:
        font = "DejaVu-Sans-Bold"
        print(f"警告: 日本語フォントが見つかりません。'{font}' を使用します。")

    print(f"使用フォント: {font}")
    print(f"解像度: {WIDTH}x{HEIGHT}, 尺: {DURATION}秒")
    print(f"テキスト幅: {TEXT_WIDTH}px, フォントサイズ: {FONT_SIZE}px")

    # 背景クリップ（サイズ明示）
    bg = ColorClip(size=(WIDTH, HEIGHT), color=BG_COLOR, duration=DURATION)

    # テキストクリップ一覧
    clips = [bg]
    for i, (start, text, fade) in enumerate(SLIDES):
        end = ENDS[i]
        print(f"  [{start:.1f}s - {end:.1f}s] {text[:20]}...")
        tc = make_text_clip(text, font, start, end, fade)
        clips.append(tc)

    # 合成
    final = CompositeVideoClip(clips, size=(WIDTH, HEIGHT))
    final = final.with_duration(DURATION)

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
