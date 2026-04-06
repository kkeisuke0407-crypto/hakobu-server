#!/usr/bin/env python3
"""
Instagram Reel 動画生成スクリプト
出力: reel_day1.mp4 (1080x1920, 10秒, 縦型9:16)
PIL で直接描画 → ImageMagick 依存なし
"""

import os
import sys
import textwrap
import urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# --- MoviePy ---
try:
    from moviepy import ImageClip, CompositeVideoClip, ColorClip
except ImportError:
    os.system(f"{sys.executable} -m pip install moviepy pillow numpy")
    from moviepy import ImageClip, CompositeVideoClip, ColorClip

# --- 設定 ---
WIDTH, HEIGHT = 1080, 1920
DURATION = 10.0
BG_COLOR = (0, 0, 0)
TEXT_COLOR = (255, 255, 255)
FONT_SIZE = 60
MARGIN_X = 100          # 左右マージン
TEXT_MAX_W = WIDTH - MARGIN_X * 2   # 880px
OUTPUT = "reel_day1.mp4"

# テキスト構成: (開始秒, テキスト, フェード秒)
SLIDES = [
    (0.0,  "育児は年収1000万円じゃ足りない",             0.4),
    (3.0,  "生卵を1年間、割らずに抱えて生活できますか？",  0.4),
    (6.0,  "割ったら終わり。",                           0.3),
    (7.5,  "0歳の子って、いつ死ぬかわからない。",         0.3),
    (9.0,  "育児のつらさって、そういうこと。",            0.3),
]

ENDS = [SLIDES[i + 1][0] if i + 1 < len(SLIDES) else DURATION
        for i in range(len(SLIDES))]


# --- フォント準備 ---
def ensure_font():
    candidates = [
        "./NotoSansJP-Bold.otf",
        "./NotoSansJP-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/takao-gothic/TakaoGothic.ttf",
        "/usr/share/fonts/truetype/vlgothic/VL-Gothic-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            print(f"フォント: {path}")
            return path

    print("Noto Sans JP をダウンロード中...")
    url = ("https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/"
           "NotoSansCJKjp-Bold.otf")
    try:
        urllib.request.urlretrieve(url, "NotoSansJP-Bold.otf")
        return "NotoSansJP-Bold.otf"
    except Exception as e:
        print(f"ダウンロード失敗: {e}")
        return None


def wrap_text(text, font, max_width, draw):
    """文字列をmax_width内で折り返す（日本語対応）"""
    lines = []
    for paragraph in text.split("\n"):
        line = ""
        for char in paragraph:
            test = line + char
            bbox = draw.textbbox((0, 0), test, font=font)
            w = bbox[2] - bbox[0]
            if w > max_width and line:
                lines.append(line)
                line = char
            else:
                line = test
        if line:
            lines.append(line)
    return lines


def render_text_image(text, font, alpha=1.0):
    """テキストをPILで1080x1920の画像に描画して numpy 配列で返す"""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    lines = wrap_text(text, font, TEXT_MAX_W, draw)

    # 行の高さを計算
    line_height = draw.textbbox((0, 0), "あ", font=font)[3] + 16
    total_h = line_height * len(lines)

    # 垂直中央の開始y
    y_start = (HEIGHT - total_h) // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (WIDTH - w) // 2   # 水平中央
        y = y_start + i * line_height
        draw.text((x, y), line, font=font, fill=TEXT_COLOR)

    arr = np.array(img).astype("uint8")

    # フェード用にアルファ適用（RGBにスカラー乗算）
    if alpha < 1.0:
        arr = (arr * alpha).astype("uint8")

    return arr


def main():
    font_path = ensure_font()
    if font_path is None:
        print("エラー: 日本語フォントが見つかりません")
        sys.exit(1)

    font = ImageFont.truetype(font_path, FONT_SIZE)

    print(f"解像度: {WIDTH}x{HEIGHT}, 尺: {DURATION}秒, フォント: {FONT_SIZE}px")

    fps = 30
    total_frames = int(DURATION * fps)
    frames = []

    for frame_i in range(total_frames):
        t = frame_i / fps

        # この時刻に表示するスライドを特定
        current_slide = None
        for i, (start, text, fade) in enumerate(SLIDES):
            end = ENDS[i]
            if start <= t < end:
                elapsed = t - start
                alpha = min(elapsed / fade, 1.0) if fade > 0 else 1.0
                current_slide = (text, alpha)
                break

        if current_slide is None:
            # 黒フレーム
            frame = np.zeros((HEIGHT, WIDTH, 3), dtype="uint8")
        else:
            text, alpha = current_slide
            frame = render_text_image(text, font, alpha)

        frames.append(frame)

    print(f"フレーム生成完了: {len(frames)}枚")

    # numpy 配列の動画として書き出し
    from moviepy import VideoClip

    def make_frame(t):
        idx = min(int(t * fps), total_frames - 1)
        return frames[idx]

    clip = VideoClip(make_frame, duration=DURATION)

    print(f"書き出し中: {OUTPUT}")
    clip.write_videofile(
        OUTPUT,
        fps=fps,
        codec="libx264",
        audio=False,
        preset="medium",
        ffmpeg_params=["-crf", "18"],
    )
    print(f"\n完了: {OUTPUT}")


if __name__ == "__main__":
    main()
