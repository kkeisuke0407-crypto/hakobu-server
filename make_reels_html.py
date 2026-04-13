#!/usr/bin/env python3
"""
reel_5series.html の各スライド(.slide)をPlaywrightでスクショし、
MoviePyで5本のInstagram Reels MP4を生成する。

出力:
  reel_01_taishokuhi.mp4
  reel_02_shikikin.mp4
  reel_03_chukaitesuryo.mp4
  reel_04_kasaihoken.mp4
  reel_05_hikkoshi.mp4
"""

import os
import sys
import numpy as np
from PIL import Image

try:
    from moviepy import VideoClip
except ImportError:
    os.system(f"{sys.executable} -m pip install moviepy")
    from moviepy import VideoClip

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    os.system(f"{sys.executable} -m pip install playwright")
    from playwright.sync_api import sync_playwright

# ── 設定 ─────────────────────────────────────────────────
CHROME_PATH   = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
HTML_FILE     = os.path.abspath("reel_5series.html")
CAPTURE_DIR   = "slide_captures"
OUT_W, OUT_H  = 1080, 1920   # 出力解像度
SLIDE_SEC     = 5.0
FPS           = 30
# CSS上のスライドサイズ: 360×640px → deviceScaleFactor=3 で 1080×1920px
SCALE_FACTOR  = 3

REELS = [
    ("reel_01_taishokuhi.mp4",     0,  4),
    ("reel_02_shikikin.mp4",       4,  8),
    ("reel_03_chukaitesuryo.mp4",  8, 12),
    ("reel_04_kasaihoken.mp4",    12, 16),
    ("reel_05_hikkoshi.mp4",      16, 20),
]


def screenshot_slides():
    """全スライドをPNGとしてキャプチャし、numpy配列のリストを返す"""
    os.makedirs(CAPTURE_DIR, exist_ok=True)
    slide_arrays = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=CHROME_PATH,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        page = browser.new_page(
            viewport={"width": 1800, "height": 4000},
            device_scale_factor=SCALE_FACTOR,
        )
        html_content = open(HTML_FILE, encoding="utf-8").read()
        page.set_content(html_content, wait_until="domcontentloaded")
        # Google Fontsの読み込みを待つ（外部通信不可の場合はフォールバック）
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            page.wait_for_timeout(2000)

        slides = page.query_selector_all(".slide")
        total = len(slides)
        print(f"スライド検出: {total}枚")

        for i, slide in enumerate(slides):
            path = os.path.join(CAPTURE_DIR, f"slide_{i:02d}.png")
            slide.screenshot(path=path)

            img = Image.open(path).convert("RGB")
            # サイズ確認・リサイズ（念のため）
            if img.size != (OUT_W, OUT_H):
                img = img.resize((OUT_W, OUT_H), Image.LANCZOS)
                img.save(path)

            slide_arrays.append(np.array(img).astype("uint8"))
            print(f"  [{i+1:02d}/{total}] {path}  {img.size}")

        browser.close()

    return slide_arrays


def make_reel(out_path, frames):
    """frames(4枚のnumpy配列)から1本のMP4を生成"""
    duration = SLIDE_SEC * len(frames)

    def make_frame(t, _f=frames):
        idx = min(int(t / SLIDE_SEC), len(_f) - 1)
        return _f[idx]

    clip = VideoClip(make_frame, duration=duration)
    clip.write_videofile(
        out_path,
        fps=FPS,
        codec="libx264",
        preset="medium",
        ffmpeg_params=["-crf", "18"],
        logger=None,
    )


def main():
    if not os.path.exists(HTML_FILE):
        print(f"エラー: {HTML_FILE} が見つかりません")
        sys.exit(1)

    print("=" * 50)
    print("Step 1: スライドキャプチャ")
    print("=" * 50)
    slide_arrays = screenshot_slides()

    if len(slide_arrays) < 20:
        print(f"警告: スライドが{len(slide_arrays)}枚しか取得できませんでした（期待: 20枚）")

    print()
    print("=" * 50)
    print("Step 2: MP4生成")
    print("=" * 50)
    for out_name, start, end in REELS:
        frames = slide_arrays[start:end]
        if not frames:
            print(f"スキップ: {out_name}（スライドなし）")
            continue
        print(f"\n書き出し: {out_name}  ({len(frames)}枚 × {SLIDE_SEC}秒 = {len(frames)*SLIDE_SEC:.0f}秒)")
        make_reel(out_name, frames)
        size_kb = os.path.getsize(out_name) // 1024
        print(f"完了: {out_name}  ({size_kb} KB)")

    print()
    print("=" * 50)
    print("全完了")
    for out_name, _, _ in REELS:
        if os.path.exists(out_name):
            print(f"  ✓ {out_name}  ({os.path.getsize(out_name)//1024} KB)")
    print("=" * 50)


if __name__ == "__main__":
    main()
