#!/usr/bin/env python3
"""
背景画像 + テキストオーバーレイ Instagram リール動画生成
background.png → 1080x1920 にリサイズ → テキストフェードイン
出力: reel_day3.mp4
"""

import os
import sys
import urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

try:
    from moviepy import VideoClip
except ImportError:
    os.system(f"{sys.executable} -m pip install moviepy pillow numpy")
    from moviepy import VideoClip

# --- 設定 ---
WIDTH, HEIGHT   = 1080, 1920
BG_IMAGE_PATH   = "background.png"
OUTPUT          = "reel_day3.mp4"
FONT_SIZE       = 70
MARGIN_X        = 100
TEXT_MAX_W      = WIDTH - MARGIN_X * 2   # 880px
LINE_SPACING    = 0.65
TEXT_COLOR      = (255, 255, 255)
SHADOW_COLOR    = (0, 0, 0)
SHADOW_OFFSET   = 3     # テキストシャドウのオフセット(px)
DARK_OVERLAY    = 0.45  # 背景を暗くするオーバーレイ濃度 (0.0〜1.0)
FPS             = 30

# スライド: (開始秒, テキスト, フェード秒)  ※空文字 = 空白
SLIDES = [
    (0.0,  "育休、取ってくれた。",             0.4),
    (2.0,  "ありがたかった。",                0.4),
    (4.0,  "でもその夜、夫が言った。",         0.4),
    (6.0,  "「今日、疲れた」",               0.3),
    (8.0,  "",                              0.0),   # 空白（沈黙）
    (9.0,  "私は何て言えばよかったんだろう。", 0.5),
]

DURATION = 12.5
ENDS = [SLIDES[i+1][0] if i+1 < len(SLIDES) else DURATION
        for i in range(len(SLIDES))]


# --- フォント ---
def ensure_font():
    candidates = [
        "./NotoSansJP-Bold.otf",
        "./NotoSansJP-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/takao-gothic/TakaoGothic.ttf",
        "/usr/share/fonts/truetype/vlgothic/VL-Gothic-Regular.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    print("Noto Sans JP をダウンロード中...")
    url = ("https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/"
           "NotoSansCJKjp-Bold.otf")
    urllib.request.urlretrieve(url, "NotoSansJP-Bold.otf")
    return "NotoSansJP-Bold.otf"


# --- 背景画像準備 ---
def load_background():
    """background.png を 1080x1920 にクロップ＋ダーク オーバーレイ"""
    if not os.path.exists(BG_IMAGE_PATH):
        print(f"警告: {BG_IMAGE_PATH} が見つかりません → 黒背景を使用")
        return Image.new("RGB", (WIDTH, HEIGHT), (10, 10, 20))

    img = Image.open(BG_IMAGE_PATH).convert("RGB")
    print(f"背景画像読み込み: {img.size}")

    # アスペクト比を保ちながら 1080x1920 にカバーリサイズ
    target_ratio = WIDTH / HEIGHT
    src_ratio    = img.width / img.height
    if src_ratio > target_ratio:
        # 横長 → 高さ基準でリサイズ
        new_h = HEIGHT
        new_w = int(img.width * HEIGHT / img.height)
    else:
        # 縦長 → 幅基準でリサイズ
        new_w = WIDTH
        new_h = int(img.height * WIDTH / img.width)

    img = img.resize((new_w, new_h), Image.LANCZOS)
    # 中央クロップ
    left = (new_w - WIDTH)  // 2
    top  = (new_h - HEIGHT) // 2
    img  = img.crop((left, top, left + WIDTH, top + HEIGHT))

    # 暗めのオーバーレイを重ねてテキストを読みやすくする
    overlay = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    img = Image.blend(img, overlay, DARK_OVERLAY)

    return img


def tw(text, font, draw):
    if not text:
        return 0
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0]


def wrap(text, font, max_w, draw):
    if not text:
        return []
    if tw(text, font, draw) <= max_w:
        return [text]
    PUNCT = "、。！？・"
    mid   = len(text) // 2
    best  = None
    for d in range(min(7, len(text) // 2)):
        for pos in [mid - d, mid + d]:
            if 1 <= pos < len(text) and text[pos - 1] in PUNCT:
                best = pos
                break
        if best:
            break
    if best:
        l1, l2 = text[:best], text[best:]
        if tw(l1, font, draw) <= max_w and tw(l2, font, draw) <= max_w:
            return [l1, l2]
    lines, ln = [], ""
    for ch in text:
        if tw(ln + ch, font, draw) > max_w and ln:
            lines.append(ln); ln = ch
        else:
            ln += ch
    if ln:
        lines.append(ln)
    return lines


def draw_text_with_shadow(draw, x, y, text, font, text_color, shadow_color, offset):
    """シャドウ付きテキストを描画"""
    draw.text((x + offset, y + offset), text, font=font, fill=shadow_color)
    draw.text((x, y), text, font=font, fill=text_color)


def render_frame(bg_base, text, font, alpha=1.0):
    """背景+テキストを合成して numpy 配列を返す"""
    img  = bg_base.copy()
    draw = ImageDraw.Draw(img)

    # 空テキストはそのまま返す
    if not text:
        arr = np.array(img).astype("uint8")
        if alpha < 1.0:
            # 暗くフェード
            black = np.zeros_like(arr)
            arr = (arr * alpha + black * (1 - alpha)).astype("uint8")
        return arr

    lines  = wrap(text, font, TEXT_MAX_W, draw)
    sb     = draw.textbbox((0, 0), "あ", font=font)
    char_h = sb[3] - sb[1]
    top_h  = sb[1]
    line_h = char_h + int(char_h * LINE_SPACING)
    total  = char_h + line_h * (len(lines) - 1)

    # テキストは画面下寄り（約65%の位置）
    y = int(HEIGHT * 0.65) - total // 2 - top_h

    for ln in lines:
        w = tw(ln, font, draw)
        x = (WIDTH - w) // 2
        draw_text_with_shadow(draw, x, y, ln, font,
                              TEXT_COLOR, SHADOW_COLOR, SHADOW_OFFSET)
        y += line_h

    arr = np.array(img).astype("uint8")

    # フェードイン：黒背景との合成
    if alpha < 1.0:
        bg_arr  = np.array(bg_base).astype("float32")
        text_arr = arr.astype("float32")
        arr = (bg_arr * (1 - alpha) + text_arr * alpha).astype("uint8")

    return arr


def main():
    font_path = ensure_font()
    font      = ImageFont.truetype(font_path, FONT_SIZE)
    bg_base   = load_background()

    total_frames = int(DURATION * FPS)
    frames = []

    for fi in range(total_frames):
        t     = fi / FPS
        frame = np.array(bg_base).astype("uint8")  # デフォルトは背景のみ

        for i, (start, text, fade) in enumerate(SLIDES):
            if start <= t < ENDS[i]:
                elapsed = t - start
                alpha   = min(elapsed / fade, 1.0) if fade > 0 else 1.0
                frame   = render_frame(bg_base, text, font, alpha)
                break

        frames.append(frame)

    print(f"フレーム生成: {total_frames}枚")

    def make_frame(t):
        return frames[min(int(t * FPS), total_frames - 1)]

    clip = VideoClip(make_frame, duration=DURATION)

    print(f"書き出し: {OUTPUT}")
    clip.write_videofile(
        OUTPUT, fps=FPS, codec="libx264",
        audio=False, preset="medium",
        ffmpeg_params=["-crf", "18"],
        logger=None,
    )
    print(f"完了: {OUTPUT}")


if __name__ == "__main__":
    main()
