#!/usr/bin/env python3
"""
Instagram リール用縦型画像生成（PIL版）
出力: reel_day2.png (1080x1920)
"""

import os
import sys
import urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# --- 設定 ---
WIDTH, HEIGHT = 1080, 1920
BG_COLOR      = (0, 0, 0)
TEXT_COLOR    = (255, 255, 255)
FONT_SIZE     = 72
MARGIN_X      = 130
TEXT_MAX_W    = WIDTH - MARGIN_X * 2   # 820px
LINE_SPACING  = 0.65    # 行間 = 文字高の65%（reel_day1より広め）
SLIDE_GAP     = 1.0     # スライド間の余白倍率（行間 × この値）
OUTPUT        = "reel_day2.png"

# テキスト（/ で区切りを表す → 描画時に間隔を広げる）
LINES = [
    ("「手伝うね」って言った。", False),
    ("その夜も、",               False),
    ("一人だった。",             False),
    ("---",                      True),   # 区切り（空行）
    ("育児は「手伝う」ものじゃない。", False),
    ("あなたの子でしょ。",        False),
]

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
            return path
    print("Noto Sans JP をダウンロード中...")
    url = ("https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/"
           "NotoSansCJKjp-Bold.otf")
    urllib.request.urlretrieve(url, "NotoSansJP-Bold.otf")
    return "NotoSansJP-Bold.otf"


def text_width(t, font, draw):
    if not t:
        return 0
    bbox = draw.textbbox((0, 0), t, font=font)
    return bbox[2] - bbox[0]


def wrap_line(text, font, max_width, draw):
    """1行を max_width 内で折り返す（句読点優先・バランス重視）"""
    if text_width(text, font, draw) <= max_width:
        return [text]

    mid = len(text) // 2
    PUNCT = "、。！？・"
    best = None
    for delta in range(min(7, len(text) // 2)):
        for pos in [mid - delta, mid + delta]:
            if 1 <= pos < len(text) and text[pos - 1] in PUNCT:
                best = pos
                break
        if best:
            break

    if best:
        l1, l2 = text[:best], text[best:]
        if text_width(l1, font, draw) <= max_width and text_width(l2, font, draw) <= max_width:
            return [l1, l2]

    # 文字単位フォールバック
    result, line = [], ""
    for char in text:
        if text_width(line + char, font, draw) > max_width and line:
            result.append(line)
            line = char
        else:
            line += char
    if line:
        result.append(line)
    return result


def main():
    font_path = ensure_font()
    font = ImageFont.truetype(font_path, FONT_SIZE)
    print(f"フォント: {font_path}, サイズ: {FONT_SIZE}px")

    img  = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # フォントメトリクス
    sample_bbox = draw.textbbox((0, 0), "あ", font=font)
    char_h   = sample_bbox[3] - sample_bbox[1]
    top_off  = sample_bbox[1]
    line_h   = char_h + int(char_h * LINE_SPACING)
    gap_h    = int(line_h * SLIDE_GAP)  # セクション間の追加余白

    # 描画アイテムリストを構築
    # (text_line, is_gap)
    items = []
    for text, is_separator in LINES:
        if is_separator:
            items.append(("", True))   # 空行（余白）
        else:
            for sub in wrap_line(text, font, TEXT_MAX_W, draw):
                items.append((sub, False))

    # 全体の高さを計算
    total_h = 0
    for i, (text, is_gap) in enumerate(items):
        if is_gap:
            total_h += gap_h
        else:
            total_h += char_h
            if i < len(items) - 1 and not items[i + 1][1]:  # 次が空行でなければ行間追加
                total_h += int(char_h * LINE_SPACING)

    # 垂直中央の開始 y
    y = (HEIGHT - total_h) // 2 - top_off

    # 描画
    for i, (text, is_gap) in enumerate(items):
        if is_gap:
            y += gap_h
            continue

        w = text_width(text, font, draw)
        x = (WIDTH - w) // 2
        draw.text((x, y), text, font=font, fill=TEXT_COLOR)
        y += char_h

        # 次の行との間隔
        if i < len(items) - 1:
            next_is_gap = items[i + 1][1]
            if not next_is_gap:
                y += int(char_h * LINE_SPACING)

    img.save(OUTPUT, "PNG")
    print(f"保存完了: {OUTPUT} ({WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    main()
