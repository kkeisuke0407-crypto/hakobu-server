#!/usr/bin/env python3
"""
Instagram Reel 動画生成（汎用版）
PIL描画 + MoviePy合成
使い方: python3 reel_generator.py <config_file.py>
"""

import os
import sys
import wave
import tempfile
import urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    from moviepy import VideoClip, AudioFileClip
    from moviepy.audio.fx import AudioLoop, MultiplyVolume
except ImportError:
    os.system(f"{sys.executable} -m pip install moviepy pillow numpy")
    from moviepy import VideoClip, AudioFileClip
    from moviepy.audio.fx import AudioLoop, MultiplyVolume

# --- デフォルト設定 ---
WIDTH, HEIGHT = 1080, 1920
BG_COLOR      = (0, 0, 0)
TEXT_COLOR    = (255, 255, 255)
FONT_SIZE     = 72
MARGIN_X      = 130
LINE_SPACING  = 0.60
BGM_PATH      = "bgm.mp3"
BGM_VOLUME    = 0.25
NOISE_VOLUME  = 0.04
FPS           = 30


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


def text_width(t, font, draw):
    if not t:
        return 0
    b = draw.textbbox((0, 0), t, font=font)
    return b[2] - b[0]


def wrap_text(text, font, max_width, draw):
    """句読点優先・バランス重視の折り返し"""
    results = []
    for para in text.split("\n"):
        results.extend(_wrap_para(para, font, max_width, draw))
    return results


def _wrap_para(text, font, max_width, draw):
    if not text:
        return []
    if text_width(text, font, draw) <= max_width:
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
        if text_width(l1, font, draw) <= max_width and text_width(l2, font, draw) <= max_width:
            return [l1, l2]

    lines, line = [], ""
    for ch in text:
        if text_width(line + ch, font, draw) > max_width and line:
            lines.append(line)
            line = ch
        else:
            line += ch
    if line:
        lines.append(line)
    return lines


def render_frame(text, font, draw_ref, alpha=1.0):
    """1フレームをPILで描画してnumpy配列を返す"""
    img  = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    max_w  = WIDTH - MARGIN_X * 2
    lines  = wrap_text(text, font, max_w, draw)

    sb     = draw.textbbox((0, 0), "あ", font=font)
    char_h = sb[3] - sb[1]
    top_h  = sb[1]
    line_h = char_h + int(char_h * LINE_SPACING)
    total  = char_h + line_h * (len(lines) - 1)

    y = (HEIGHT - total) // 2 - top_h
    for ln in lines:
        w = text_width(ln, font, draw)
        x = (WIDTH - w) // 2
        draw.text((x, y), ln, font=font, fill=TEXT_COLOR)
        y += line_h

    arr = np.array(img).astype("uint8")
    if alpha < 1.0:
        arr = (arr * alpha).astype("uint8")
    return arr


def make_noise(duration, sr=44100):
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    n   = int(duration * sr)
    buf = (np.random.randn(n) * NOISE_VOLUME * 32767).astype(np.int16)
    with wave.open(tmp.name, "w") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr)
        f.writeframes(buf.tobytes())
    return tmp.name


def prepare_audio(duration):
    if os.path.exists(BGM_PATH):
        print(f"BGM: {BGM_PATH}")
        audio, vol = AudioFileClip(BGM_PATH), BGM_VOLUME
    else:
        print("白ノイズを生成します")
        audio, vol = AudioFileClip(make_noise(duration)), 1.0

    audio = audio.with_effects([AudioLoop(duration=duration)]) \
            if audio.duration < duration else audio.subclipped(0, duration)
    return audio.with_effects([MultiplyVolume(vol)])


def generate(slides, duration, output, font_size=None):
    """
    slides  : [(start_sec, text, fade_sec), ...]
    duration: 動画の長さ（秒）
    output  : 出力ファイル名
    """
    font_path = ensure_font()
    fs   = font_size or FONT_SIZE
    font = ImageFont.truetype(font_path, fs)

    ends = [slides[i+1][0] if i+1 < len(slides) else duration
            for i in range(len(slides))]

    total_frames = int(duration * FPS)
    frames = []
    for fi in range(total_frames):
        t    = fi / FPS
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype="uint8")
        for i, (start, text, fade) in enumerate(slides):
            if start <= t < ends[i]:
                elapsed = t - start
                alpha   = min(elapsed / fade, 1.0) if fade > 0 else 1.0
                frame   = render_frame(text, font, None, alpha)
                break
        frames.append(frame)

    print(f"フレーム生成: {total_frames}枚")

    def make_frame(t):
        return frames[min(int(t * FPS), total_frames - 1)]

    clip  = VideoClip(make_frame, duration=duration)
    audio = prepare_audio(duration)
    clip  = clip.with_audio(audio)

    print(f"書き出し: {output}")
    clip.write_videofile(
        output, fps=FPS, codec="libx264", audio_codec="aac",
        preset="medium", ffmpeg_params=["-crf", "18"],
        logger=None,
    )
    print(f"完了: {output}")
