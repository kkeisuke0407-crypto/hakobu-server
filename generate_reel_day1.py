#!/usr/bin/env python3
"""
Instagram Reel 動画生成スクリプト
出力: reel_day1.mp4 (1080x1920, 10秒, 縦型9:16)
PIL で直接描画 → ImageMagick 依存なし
BGM: bgm.mp3 があれば使用、なければ白ノイズを自動生成
"""

import os
import sys
import wave
import struct
import tempfile
import urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# --- MoviePy ---
try:
    from moviepy import VideoClip, AudioFileClip
    from moviepy.audio.fx import AudioLoop, MultiplyVolume
except ImportError:
    os.system(f"{sys.executable} -m pip install moviepy pillow numpy")
    from moviepy import VideoClip, AudioFileClip
    from moviepy.audio.fx import AudioLoop, MultiplyVolume

BGM_PATH = "bgm.mp3"
BGM_VOLUME = 0.25       # BGMの音量（0.0〜1.0）
NOISE_VOLUME = 0.04     # 白ノイズの音量（控えめ）

# --- 設定 ---
WIDTH, HEIGHT = 1080, 1920
DURATION = 10.0
BG_COLOR = (0, 0, 0)
TEXT_COLOR = (255, 255, 255)
FONT_SIZE = 72
MARGIN_X = 120          # 左右マージン
TEXT_MAX_W = WIDTH - MARGIN_X * 2   # 840px
LINE_SPACING = 0.55     # 行間 = 文字高の55%
OUTPUT = "reel_day1.mp4"

# テキスト構成: (開始秒, テキスト, フェード秒)
SLIDES = [
    (0.0,  "育児は年収1000万円",                          0.3),
    (2.0,  "それは間違ってる",                            0.3),
    (4.0,  "生卵を1年間、割らずに抱えて生活できますか？",  0.4),
    (6.0,  "割ったら終わり。",                            0.3),
    (7.5,  "2000万円あげるから\nやってみて",              0.3),
    (9.0,  "それが育児。",                                0.3),
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


def generate_white_noise(duration, sample_rate=44100):
    """白ノイズをWAVファイルとして生成し、パスを返す"""
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()

    n_samples = int(duration * sample_rate)
    noise = (np.random.randn(n_samples) * NOISE_VOLUME * 32767).astype(np.int16)

    with wave.open(tmp.name, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(noise.tobytes())

    print(f"白ノイズ生成: {duration:.1f}秒 / {sample_rate}Hz → {tmp.name}")
    return tmp.name


def prepare_audio(duration):
    """BGMを準備してMoviePy AudioClipを返す"""
    if os.path.exists(BGM_PATH):
        print(f"BGM読み込み: {BGM_PATH}")
        audio = AudioFileClip(BGM_PATH)
        volume = BGM_VOLUME
    else:
        print(f"bgm.mp3 が見つかりません → 白ノイズを自動生成します")
        noise_path = generate_white_noise(duration)
        audio = AudioFileClip(noise_path)
        volume = 1.0  # 白ノイズは生成時に音量調整済み

    # 動画より短い場合はループ
    if audio.duration < duration:
        audio = audio.with_effects([AudioLoop(duration=duration)])
    else:
        audio = audio.subclipped(0, duration)

    # 音量調整
    audio = audio.with_effects([MultiplyVolume(volume)])
    return audio


def text_width(t, font, draw):
    """文字列のピクセル幅を返す"""
    if not t:
        return 0
    bbox = draw.textbbox((0, 0), t, font=font)
    return bbox[2] - bbox[0]


def wrap_text(text, font, max_width, draw):
    """
    テキストを自然に折り返す（日本語句読点優先・行バランス重視）
    1. 1行に収まるならそのまま
    2. 句読点（、。！？）付近で均等分割を試みる
    3. それでも長い場合は文字単位で折り返し
    """
    # \n による手動改行を尊重
    paragraphs = text.split("\n")
    all_lines = []
    for para in paragraphs:
        all_lines.extend(_wrap_paragraph(para, font, max_width, draw))
    return all_lines


def _wrap_paragraph(text, font, max_width, draw):
    """1段落を折り返す"""
    if not text:
        return []

    # 1行に収まる
    if text_width(text, font, draw) <= max_width:
        return [text]

    # 句読点に近い中点で2分割を試みる
    mid = len(text) // 2
    PUNCTUATION = "、。！？・"

    # 中点から前後6文字以内の句読点を探す
    best = None
    for delta in range(min(7, len(text) // 2)):
        for pos in [mid - delta, mid + delta]:
            if 1 <= pos < len(text) and text[pos - 1] in PUNCTUATION:
                best = pos
                break
        if best:
            break

    # 句読点が見つかった → 2分割
    if best:
        l1 = text[:best]
        l2 = text[best:]
        w1 = text_width(l1, font, draw)
        w2 = text_width(l2, font, draw)
        if w1 <= max_width and w2 <= max_width:
            return [l1, l2]

    # 句読点がない or 分割後もはみ出す → 文字幅で均等分割
    # 全体幅から想定行数を算出し、均等ブレイクを試みる
    total_w = text_width(text, font, draw)
    n_lines = int(total_w / max_width) + 1
    target_chars = len(text) // n_lines

    lines = []
    while text:
        if text_width(text, font, draw) <= max_width:
            lines.append(text)
            break
        # target_chars 付近で区切る（句読点優先）
        cut = target_chars
        for delta in range(6):
            for pos in [cut + delta, cut - delta]:
                if 1 <= pos < len(text) and text[pos - 1] in PUNCTUATION:
                    cut = pos
                    break
            else:
                continue
            break
        # 最低でも1文字は確保し、max_width超えを防ぐ
        while cut < len(text) and text_width(text[:cut + 1], font, draw) <= max_width:
            cut += 1
        lines.append(text[:cut])
        text = text[cut:]

    return lines


def render_text_image(text, font, draw_ref, alpha=1.0):
    """テキストをPILで1080x1920の画像に描画して numpy 配列で返す"""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    lines = wrap_text(text, font, TEXT_MAX_W, draw)

    # 正確なフォントメトリクスで行高を算出
    sample_bbox = draw.textbbox((0, 0), "あ", font=font)
    char_h = sample_bbox[3] - sample_bbox[1]   # top〜bottomの実高さ
    top_offset = sample_bbox[1]                 # ベースラインからtopへのオフセット
    line_gap = int(char_h * LINE_SPACING)
    line_height = char_h + line_gap

    # 全体の高さ = 最初の文字高 + 残り行 × line_height
    total_h = char_h + line_height * (len(lines) - 1)

    # 垂直中央（top_offsetで微補正）
    y_start = (HEIGHT - total_h) // 2 - top_offset

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (WIDTH - w) // 2   # 水平中央
        y = y_start + i * line_height
        draw.text((x, y), line, font=font, fill=TEXT_COLOR)

    arr = np.array(img).astype("uint8")

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
            frame = np.zeros((HEIGHT, WIDTH, 3), dtype="uint8")
        else:
            text, alpha = current_slide
            frame = render_text_image(text, font, None, alpha)

        frames.append(frame)

    print(f"フレーム生成完了: {len(frames)}枚")

    def make_frame(t):
        idx = min(int(t * fps), total_frames - 1)
        return frames[idx]

    clip = VideoClip(make_frame, duration=DURATION)

    # BGM合成
    audio = prepare_audio(DURATION)
    clip = clip.with_audio(audio)

    print(f"書き出し中: {OUTPUT}")
    clip.write_videofile(
        OUTPUT,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        ffmpeg_params=["-crf", "18"],
    )
    print(f"\n完了: {OUTPUT}")


if __name__ == "__main__":
    main()
