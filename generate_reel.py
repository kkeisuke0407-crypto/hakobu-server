#!/usr/bin/env python3
"""
Instagram リール自動生成パイプライン

使い方:
  1. script.txt に台本を書く
  2. export GEMINI_API_KEY=your_key
  3. python3 generate_reel.py [--skip-bg]

script.txt フォーマット（1行1スライド）:
  開始秒|テキスト|フェード秒
  開始秒|テキスト          ← フェードはデフォルト0.4秒
  開始秒|               ← 空テキスト（沈黙）
  # コメント行

オプション:
  --skip-bg   背景画像を再生成せず既存の reel_background.png を使う
"""

import os
import sys
import io
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

# ============================================================
# 設定
# ============================================================
WIDTH, HEIGHT  = 1080, 1920
SCRIPT_FILE    = "script.txt"
BG_IMAGE_PATH  = "backgrounds/reel_background.png"
REELS_DIR      = "reels"
FONT_SIZE      = 70
MARGIN_X       = 100
TEXT_MAX_W     = WIDTH - MARGIN_X * 2   # 880px
LINE_SPACING   = 0.65
TEXT_COLOR     = (255, 255, 255)
SHADOW_COLOR   = (0,   0,   0)
SHADOW_OFFSET  = 3
DARK_OVERLAY   = 0.40    # 背景暗化（0=そのまま / 1=真っ黒）
FPS            = 30
TAIL_PADDING   = 2.0     # 最終スライド後の余白（秒）
DEFAULT_FADE   = 0.4     # フェード秒のデフォルト
BGM_PATH       = "bgm.mp3"
BGM_VOLUME     = 0.25
NOISE_VOLUME   = 0.04
WATERMARK_SIZE = 110     # 右下の黒塗りサイズ（px）


# ============================================================
# 台本パース
# ============================================================
def parse_script(path):
    slides = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) < 2:
                continue
            start = float(parts[0].strip())
            text  = parts[1].strip().replace("\\n", "\n")
            fade  = float(parts[2].strip()) if len(parts) >= 3 else DEFAULT_FADE
            slides.append((start, text, fade))
    return slides


# ============================================================
# Gemini 画像生成プロンプト自動生成
# ============================================================
def build_image_prompt(slides):
    texts   = [t for _, t, _ in slides if t]
    content = "、".join(texts)
    return (
        "Vertical Instagram reel background photo, 9:16 aspect ratio. "
        "Cinematic, moody, atmospheric. "
        f"Theme: {content}. "
        "No text overlay, no watermarks, no faces. "
        "Soft bokeh, dramatic lighting, professional photography."
    )


# ============================================================
# Hugging Face FLUX で背景画像生成（無料）
# ============================================================
def generate_background_hf(prompt, hf_token, out_path):
    import urllib.request
    import json

    print("Hugging Face FLUX.1-schnell で背景画像を生成中...")
    print(f"プロンプト: {prompt[:90]}...")

    models = [
        "black-forest-labs/FLUX.1-schnell",
        "stabilityai/stable-diffusion-xl-base-1.0",
    ]

    for model in models:
        url     = f"https://api-inference.huggingface.co/models/{model}"
        payload = json.dumps({
            "inputs": prompt,
            "parameters": {"width": 576, "height": 1024},
        }).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {hf_token}",
                "Content-Type":  "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read()
            img = Image.open(io.BytesIO(raw)).convert("RGB")
            img.save(out_path)
            print(f"背景画像保存: {out_path} ({img.size})")
            return True
        except Exception as e:
            print(f"{model} 失敗: {e}")

    return False


# ============================================================
# Gemini API で背景画像生成（有料プラン向け）
# ============================================================
def generate_background(prompt, api_key, out_path):
    print("Gemini APIで背景画像を生成中...")
    print(f"プロンプト: {prompt[:90]}...")

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        os.system(f"{sys.executable} -m pip install google-genai")
        from google import genai
        from google.genai import types

    client = genai.Client(api_key=api_key)

    import base64

    # 利用可能なモデルを確認して画像生成対応モデルを探す
    imagen_model  = None
    flash_model   = None
    try:
        for m in client.models.list():
            name = m.name.split("/")[-1]
            if "imagen" in name and imagen_model is None:
                imagen_model = name
            if "flash" in name and "image" in name and flash_model is None:
                flash_model = name
        print(f"[モデル検索] imagen={imagen_model}, flash={flash_model}")
    except Exception as e:
        print(f"[モデル一覧取得失敗] {e}")

    # --- Imagen 3 で生成（最高品質） ---
    imagen_candidates = list(dict.fromkeys(filter(None, [
        imagen_model,
        "imagen-3.0-generate-002",
        "imagen-3.0-fast-generate-001",
    ])))
    for m in imagen_candidates:
        try:
            resp = client.models.generate_images(
                model=m,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="9:16",
                    person_generation="DONT_ALLOW",
                ),
            )
            img_bytes = resp.generated_images[0].image.image_bytes
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            img.save(out_path)
            print(f"背景画像保存: {out_path} ({img.size})")
            return True
        except Exception as e:
            print(f"{m} 失敗: {e}")

    # --- フォールバック: Gemini Flash 画像生成 ---
    flash_candidates = list(dict.fromkeys(filter(None, [
        flash_model,
        "gemini-2.0-flash-exp-image-generation",
        "gemini-2.0-flash-preview-image-generation",
        "gemini-2.0-flash-exp",
    ])))
    for flash_model in flash_candidates:
        try:
            resp = client.models.generate_content(
                model=flash_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            ),
        )
            for part in resp.candidates[0].content.parts:
                if part.inline_data:
                    raw = part.inline_data.data
                    if isinstance(raw, str):
                        raw = base64.b64decode(raw)
                    img = Image.open(io.BytesIO(raw)).convert("RGB")
                    img.save(out_path)
                    print(f"背景画像保存: {out_path} ({img.size})")
                    return True
            print(f"{flash_model}: 画像パートなし")
        except Exception as e:
            print(f"{flash_model} 失敗: {e}")

    return False


# ============================================================
# ウォーターマーク除去（右下を黒塗り）
# ============================================================
def remove_watermark(image_path):
    img  = Image.open(image_path).convert("RGB")
    w, h = img.size
    draw = ImageDraw.Draw(img)
    draw.rectangle([(w - WATERMARK_SIZE, h - WATERMARK_SIZE), (w, h)], fill=(0, 0, 0))
    img.save(image_path)
    print(f"ウォーターマーク除去: 右下 {WATERMARK_SIZE}x{WATERMARK_SIZE}px 黒塗り")


# ============================================================
# 背景リサイズ＋暗化
# ============================================================
def load_background(image_path):
    img = Image.open(image_path).convert("RGB")
    print(f"背景読み込み: {img.size}")

    # カバーリサイズ
    tr = WIDTH / HEIGHT
    sr = img.width / img.height
    if sr > tr:
        nw, nh = int(img.width * HEIGHT / img.height), HEIGHT
    else:
        nw, nh = WIDTH, int(img.height * WIDTH / img.width)
    img  = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - WIDTH)  // 2
    top  = (nh - HEIGHT) // 2
    img  = img.crop((left, top, left + WIDTH, top + HEIGHT))

    # 暗化オーバーレイ
    overlay = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    img = Image.blend(img, overlay, DARK_OVERLAY)
    return img


# ============================================================
# フォント
# ============================================================
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


# ============================================================
# テキスト描画
# ============================================================
def tw(text, font, draw):
    if not text:
        return 0
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0]


def wrap(text, font, max_w, draw):
    lines = []
    for para in text.split("\n"):
        lines.extend(_wrap_para(para, font, max_w, draw))
    return lines


def _wrap_para(text, font, max_w, draw):
    if not text:
        return []
    if tw(text, font, draw) <= max_w:
        return [text]
    PUNCT = "、。！？・"
    mid, best = len(text) // 2, None
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


def render_frame(bg_base, text, font, alpha=1.0):
    img  = bg_base.copy()
    draw = ImageDraw.Draw(img)

    if not text:
        arr = np.array(img).astype("uint8")
        if alpha < 1.0:
            arr = (arr * alpha).astype("uint8")
        return arr

    lines  = wrap(text, font, TEXT_MAX_W, draw)
    sb     = draw.textbbox((0, 0), "あ", font=font)
    char_h = sb[3] - sb[1]
    top_h  = sb[1]
    line_h = char_h + int(char_h * LINE_SPACING)
    total  = char_h + line_h * (len(lines) - 1)
    y      = int(HEIGHT * 0.62) - total // 2 - top_h

    for ln in lines:
        w = tw(ln, font, draw)
        x = (WIDTH - w) // 2
        draw.text((x + SHADOW_OFFSET, y + SHADOW_OFFSET), ln, font=font, fill=SHADOW_COLOR)
        draw.text((x, y), ln, font=font, fill=TEXT_COLOR)
        y += line_h

    arr = np.array(img).astype("uint8")
    if alpha < 1.0:
        bg_f   = np.array(bg_base).astype("float32")
        txt_f  = arr.astype("float32")
        arr    = (bg_f * (1 - alpha) + txt_f * alpha).astype("uint8")
    return arr


# ============================================================
# オーディオ
# ============================================================
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
    audio = (audio.with_effects([AudioLoop(duration=duration)])
             if audio.duration < duration else audio.subclipped(0, duration))
    return audio.with_effects([MultiplyVolume(vol)])


# ============================================================
# メイン
# ============================================================
def main():
    skip_bg  = "--skip-bg" in sys.argv
    hf_token = os.environ.get("HF_TOKEN")
    api_key  = os.environ.get("GEMINI_API_KEY")

    if not skip_bg and not hf_token and not api_key:
        print("エラー: HF_TOKEN または GEMINI_API_KEY が必要です")
        print("  export HF_TOKEN=your_huggingface_token   ← 無料")
        print("  export GEMINI_API_KEY=your_key           ← 有料プラン向け")
        print("  既存の背景を使う場合は --skip-bg を指定してください")
        sys.exit(1)

    # 台本読み込み
    if not os.path.exists(SCRIPT_FILE):
        print(f"エラー: {SCRIPT_FILE} が見つかりません")
        sys.exit(1)
    slides = parse_script(SCRIPT_FILE)
    if not slides:
        print("エラー: スクリプトが空です")
        sys.exit(1)
    print(f"スライド数: {len(slides)}")

    duration = slides[-1][0] + TAIL_PADDING
    print(f"動画尺: {duration:.1f}秒")

    # 出力ファイル名: reels/YYYYMMDD_HHMMss.mp4
    from datetime import datetime
    os.makedirs(REELS_DIR, exist_ok=True)
    os.makedirs("backgrounds", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT = os.path.join(REELS_DIR, f"reel_{timestamp}.mp4")

    ends = [slides[i + 1][0] if i + 1 < len(slides) else duration
            for i in range(len(slides))]

    # ── 1. 背景画像生成 ──
    if skip_bg and os.path.exists(BG_IMAGE_PATH):
        print(f"既存の背景を使用: {BG_IMAGE_PATH}")
    else:
        prompt = build_image_prompt(slides)
        ok = False
        if hf_token:
            ok = generate_background_hf(prompt, hf_token, BG_IMAGE_PATH)
        if not ok and api_key:
            ok = generate_background(prompt, api_key, BG_IMAGE_PATH)
        if not ok:
            print("警告: 画像生成失敗 → 黒背景で続行")
            Image.new("RGB", (WIDTH, HEIGHT), (10, 10, 20)).save(BG_IMAGE_PATH)

    # ── 2. ウォーターマーク除去 ──
    # ── 3. 背景読み込み ──
    bg_base = load_background(BG_IMAGE_PATH)

    # ── 4. フレーム生成 ──
    font_path    = ensure_font()
    font         = ImageFont.truetype(font_path, FONT_SIZE)
    total_frames = int(duration * FPS)
    frames       = []

    for fi in range(total_frames):
        t     = fi / FPS
        frame = np.array(bg_base).astype("uint8")
        for i, (start, text, fade) in enumerate(slides):
            if start <= t < ends[i]:
                elapsed = t - start
                alpha   = min(elapsed / fade, 1.0) if fade > 0 else 1.0
                frame   = render_frame(bg_base, text, font, alpha)
                break
        frames.append(frame)

    print(f"フレーム生成: {total_frames}枚")

    def make_frame(t):
        return frames[min(int(t * FPS), total_frames - 1)]

    # ── 5. 動画書き出し ──
    clip  = VideoClip(make_frame, duration=duration)
    audio = prepare_audio(duration)
    clip  = clip.with_audio(audio)

    print(f"書き出し: {OUTPUT}")
    clip.write_videofile(
        OUTPUT, fps=FPS, codec="libx264", audio_codec="aac",
        preset="medium", ffmpeg_params=["-crf", "18"],
        logger=None,
    )
    print(f"\n完了: {OUTPUT}")


# ============================================================
# 退去費用リール生成
# ============================================================

def _hex_rgb(hex_str):
    """#RRGGBB → (R, G, B)"""
    h = hex_str.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _ctr_x(text, font, draw, canvas_w=None):
    """テキストを水平中央配置するときのx座標を返す"""
    canvas_w = canvas_w or WIDTH
    bb = draw.textbbox((0, 0), text, font=font)
    return (canvas_w - (bb[2] - bb[0])) // 2


def _slide1_chintai(fp):
    """スライド1: フック（#111111）"""
    BG     = _hex_rgb("#111111")
    RED    = _hex_rgb("#E03030")
    WHITE  = (255, 255, 255)
    YELLOW = (255, 230, 0)

    img  = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    f_tag   = ImageFont.truetype(fp, 46)
    f_main  = ImageFont.truetype(fp, 108)
    f_large = ImageFont.truetype(fp, 170)
    f_med   = ImageFont.truetype(fp, 64)
    f_arrow = ImageFont.truetype(fp, 90)

    # タグ「知らないと損」赤背景白文字
    tag = "知らないと損"
    tb  = draw.textbbox((0, 0), tag, font=f_tag)
    pw, ph = 50, 22
    rw = (tb[2] - tb[0]) + pw * 2
    rh = (tb[3] - tb[1]) + ph * 2
    rx = (WIDTH - rw) // 2
    ry = 230
    draw.rectangle([rx, ry, rx + rw, ry + rh], fill=RED)
    draw.text((rx + pw, ry + ph - tb[1]), tag, font=f_tag, fill=WHITE)

    # 「246,488円」白・大・取り消し線（赤）
    price = "246,488円"
    pb  = draw.textbbox((0, 0), price, font=f_main)
    pw2 = pb[2] - pb[0]
    ph2 = pb[3] - pb[1]
    px2 = (WIDTH - pw2) // 2
    py2 = 490
    draw.text((px2, py2 - pb[1]), price, font=f_main, fill=WHITE)
    sy = py2 + ph2 // 2
    draw.line([(px2, sy), (px2 + pw2, sy)], fill=RED, width=9)

    # 矢印 ↓ 赤
    ab = draw.textbbox((0, 0), "↓", font=f_arrow)
    draw.text((_ctr_x("↓", f_arrow, draw), 680 - ab[1]), "↓", font=f_arrow, fill=RED)

    # 「0円」黄色・大
    zb = draw.textbbox((0, 0), "0円", font=f_large)
    draw.text((_ctr_x("0円", f_large, draw), 840 - zb[1]), "0円", font=f_large, fill=YELLOW)

    # 「+46,950円返金」白・中
    refund = "+46,950円返金"
    rb = draw.textbbox((0, 0), refund, font=f_med)
    draw.text((_ctr_x(refund, f_med, draw), 1090 - rb[1]), refund, font=f_med, fill=WHITE)

    return np.array(img).astype("uint8")


def _slide2_chintai(fp):
    """スライド2: 問題提起（#0D1B3E）"""
    BG          = _hex_rgb("#0D1B3E")
    WHITE       = (255, 255, 255)
    LIGHT_WHITE = (190, 205, 225)
    YELLOW      = (255, 230, 0)

    img  = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    f_small = ImageFont.truetype(fp, 44)
    f_main  = ImageFont.truetype(fp, 88)
    f_box   = ImageFont.truetype(fp, 44)

    # 「あなたは大丈夫？」薄白小
    top = "あなたは大丈夫？"
    tb  = draw.textbbox((0, 0), top, font=f_small)
    draw.text((_ctr_x(top, f_small, draw), 220 - tb[1]), top, font=f_small, fill=LIGHT_WHITE)

    # メイン2行: 「そのまま払ったら」白 / 「負けです」黄
    line1, line2 = "そのまま払ったら", "負けです"
    l1b  = draw.textbbox((0, 0), line1, font=f_main)
    l2b  = draw.textbbox((0, 0), line2, font=f_main)
    lh   = l1b[3] - l1b[1]
    base = 540
    draw.text((_ctr_x(line1, f_main, draw), base - l1b[1]), line1, font=f_main, fill=WHITE)
    draw.text((_ctr_x(line2, f_main, draw), base + lh + int(lh * 0.22) - l2b[1]), line2, font=f_main, fill=YELLOW)

    # 黄枠ボックス
    box_lines = ["知らないと言われた額を", "そのまま払うだけ"]
    sb   = draw.textbbox((0, 0), "あ", font=f_box)
    b_ch = sb[3] - sb[1]
    b_lh = int(b_ch * 1.45)
    bws  = []
    for bl in box_lines:
        bb = draw.textbbox((0, 0), bl, font=f_box)
        bws.append(bb[2] - bb[0])
    bcw  = max(bws)
    bch  = b_ch + b_lh * (len(box_lines) - 1)
    bpx, bpy = 55, 32
    bx   = (WIDTH - bcw - bpx * 2) // 2
    by_  = 980
    draw.rectangle([bx, by_, bx + bcw + bpx * 2, by_ + bch + bpy * 2], outline=YELLOW, width=4)
    ty = by_ + bpy
    for bl in box_lines:
        bb  = draw.textbbox((0, 0), bl, font=f_box)
        bw_ = bb[2] - bb[0]
        bxo = bx + bpx + (bcw - bw_) // 2
        draw.text((bxo, ty - bb[1]), bl, font=f_box, fill=YELLOW)
        ty += b_lh

    return np.array(img).astype("uint8")


def _slide3_chintai(fp):
    """スライド3: 解決（#FFFFFF）"""
    BG    = (255, 255, 255)
    BLACK = (20, 20, 20)
    RED   = _hex_rgb("#E03030")
    GRAY  = (110, 110, 110)
    WHITE = (255, 255, 255)

    img  = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    f_small  = ImageFont.truetype(fp, 44)
    f_main   = ImageFont.truetype(fp, 80)
    f_step   = ImageFont.truetype(fp, 44)
    f_badge  = ImageFont.truetype(fp, 38)
    f_bottom = ImageFont.truetype(fp, 46)

    # 「やることは1つだけ」グレー小
    top = "やることは1つだけ"
    tb  = draw.textbbox((0, 0), top, font=f_small)
    draw.text((_ctr_x(top, f_small, draw), 200 - tb[1]), top, font=f_small, fill=GRAY)

    # メイン「サインする前にこれだけやれ」黒大（2行）
    ml1, ml2 = "サインする前に", "これだけやれ"
    m1b = draw.textbbox((0, 0), ml1, font=f_main)
    m2b = draw.textbbox((0, 0), ml2, font=f_main)
    mh  = m1b[3] - m1b[1]
    my  = 360
    draw.text((_ctr_x(ml1, f_main, draw), my - m1b[1]), ml1, font=f_main, fill=BLACK)
    draw.text((_ctr_x(ml2, f_main, draw), my + mh + int(mh * 0.18) - m2b[1]), ml2, font=f_main, fill=BLACK)

    # ステップ3つ（赤番号バッジ＋黒テキスト）
    steps = [
        "請求書を受け取っても即サインしない",
        "管理会社に異議を伝える",
        "ガイドラインを根拠に交渉",
    ]
    BR     = 32
    LM     = 72
    step_y = 650
    sp     = 225

    s_sb  = draw.textbbox((0, 0), "あ", font=f_step)
    s_ch  = s_sb[3] - s_sb[1]
    s_lh  = int(s_ch * 1.3)

    for i, stext in enumerate(steps):
        bcx = LM + BR
        bcy = step_y + BR
        draw.ellipse([bcx - BR, bcy - BR, bcx + BR, bcy + BR], fill=RED)
        num = str(i + 1)
        nb  = draw.textbbox((0, 0), num, font=f_badge)
        draw.text(
            (bcx - (nb[0] + nb[2]) // 2, bcy - (nb[1] + nb[3]) // 2),
            num, font=f_badge, fill=WHITE
        )

        tx    = LM + BR * 2 + 28
        max_w = WIDTH - tx - 50
        lines = wrap(stext, f_step, max_w, draw)
        ty    = step_y + max(0, (BR * 2 - s_ch) // 2)
        for line in lines:
            lb = draw.textbbox((0, 0), line, font=f_step)
            draw.text((tx, ty - lb[1]), line, font=f_step, fill=BLACK)
            ty += s_lh

        step_y += sp

    # 「難しい知識ゼロでOK」赤小
    bot = "難しい知識ゼロでOK"
    bb  = draw.textbbox((0, 0), bot, font=f_bottom)
    draw.text((_ctr_x(bot, f_bottom, draw), 1400 - bb[1]), bot, font=f_bottom, fill=RED)

    return np.array(img).astype("uint8")


def _slide4_chintai(fp):
    """スライド4: CTA（#C72020）"""
    BG      = _hex_rgb("#C72020")
    WHITE   = (255, 255, 255)
    RED_TXT = _hex_rgb("#C72020")

    img  = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    f_small = ImageFont.truetype(fp, 48)
    f_main  = ImageFont.truetype(fp, 112)
    f_sub   = ImageFont.truetype(fp, 52)
    f_btn   = ImageFont.truetype(fp, 56)
    f_arrow = ImageFont.truetype(fp, 86)

    # 「交渉文テンプレ込み」白小
    top = "交渉文テンプレ込み"
    tb  = draw.textbbox((0, 0), top, font=f_small)
    draw.text((_ctr_x(top, f_small, draw), 280 - tb[1]), top, font=f_small, fill=WHITE)

    # 「全部まとめました」白大
    main = "全部まとめました"
    mb   = draw.textbbox((0, 0), main, font=f_main)
    draw.text((_ctr_x(main, f_main, draw), 490 - mb[1]), main, font=f_main, fill=WHITE)

    # 「そのまま使える文章も公開中」白小
    sub = "そのまま使える文章も公開中"
    sb  = draw.textbbox((0, 0), sub, font=f_sub)
    draw.text((_ctr_x(sub, f_sub, draw), 740 - sb[1]), sub, font=f_sub, fill=WHITE)

    # ボタン「▶ プロフのリンクへ」白背景赤文字角丸
    btn  = "▶ プロフのリンクへ"
    bb   = draw.textbbox((0, 0), btn, font=f_btn)
    btw  = bb[2] - bb[0]
    bth  = bb[3] - bb[1]
    bpx, bpy = 64, 30
    bw   = btw + bpx * 2
    bh   = bth + bpy * 2
    bx   = (WIDTH - bw) // 2
    by_  = 880
    draw.rounded_rectangle([bx, by_, bx + bw, by_ + bh], radius=bh // 2, fill=WHITE)
    draw.text((bx + bpx, by_ + bpy - bb[1]), btn, font=f_btn, fill=RED_TXT)

    # ↓ 半透明白（RGBAオーバーレイ合成）
    ab      = draw.textbbox((0, 0), "↓", font=f_arrow)
    ax      = _ctr_x("↓", f_arrow, draw)
    ay      = 1100
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    od      = ImageDraw.Draw(overlay)
    od.text((ax, ay - ab[1]), "↓", font=f_arrow, fill=(255, 255, 255, 160))
    img     = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    return np.array(img).astype("uint8")


def generate_chintai_reel():
    """退去費用リール: 4スライド × 3秒 → reel_chintai.mp4"""
    OUTPUT      = "reel_chintai.mp4"
    SLIDE_SEC   = 5.0
    TOTAL_SEC   = SLIDE_SEC * 4
    CHINTAI_FPS = 30

    font_path = ensure_font()
    print(f"フォント: {font_path}")

    print("スライド描画中...")
    slides = [
        _slide1_chintai(font_path),
        _slide2_chintai(font_path),
        _slide3_chintai(font_path),
        _slide4_chintai(font_path),
    ]
    print("スライド4枚 完了")

    def make_frame(t):
        idx = min(int(t / SLIDE_SEC), len(slides) - 1)
        return slides[idx]

    print(f"動画書き出し: {OUTPUT}  ({TOTAL_SEC:.0f}秒 / {CHINTAI_FPS}fps)")
    clip = VideoClip(make_frame, duration=TOTAL_SEC)
    clip.write_videofile(
        OUTPUT,
        fps=CHINTAI_FPS,
        codec="libx264",
        preset="medium",
        ffmpeg_params=["-crf", "18"],
        logger=None,
    )
    print(f"\n完了: {OUTPUT}")


if __name__ == "__main__":
    if "--chintai" in sys.argv:
        generate_chintai_reel()
    else:
        main()
