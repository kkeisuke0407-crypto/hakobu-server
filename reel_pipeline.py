#!/usr/bin/env python3
"""
Reel Pipeline: YAML台本 → HTML → スクショ → MP4

使い方:
  python3 reel_pipeline.py <script.yaml>

YAMLフォーマット例:
  output: reel_XX_topic.mp4
  color: coral   # yellow(デフォルト) / coral / navy / green / purple
  slides:
    hook:
      marker: 知らないと損！
      main: "退去費用で\\n専門家に頼んだら"
      big_num: "15"
      big_unit: 万円〜
      sub: かかることがある（弁護士費用）
    problem:
      marker: 専門家費用の目安
      main: "頼む前に\\n知ってほしいこと"
      warn: "弁護士：着手金5〜15万円\\n成功報酬：回収額の15〜30%"
      sub: 請求5万円なら費用倒れになる
    solution:
      marker: 自分でできる！ただし
      main: "9割の人が\\n詰まる4つの壁"
      steps:
        - AIの操作方法がわからない
        - 契約書・請求書の読み方
        - 管理会社の返答への対処法
        - 保証会社・代位弁済への対処
      foot: この壁を越えれば費用ゼロで交渉できる
    cta:
      marker: 解決策は2つある
      main: "¥500か\\n¥5,000か"
      sub: "自分でやる→¥500\\n一緒に進む→¥5,000サポート付き"
      btn: ▶ プロフのリンクへ
"""

import io
import os
import sys
import numpy as np
from PIL import Image

try:
    import yaml
except ImportError:
    os.system(f"{sys.executable} -m pip install pyyaml")
    import yaml

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

# ── 設定 ──────────────────────────────────────────────────────
CHROME_PATH  = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
OUT_W, OUT_H = 1080, 1920
SLIDE_SEC    = 3.0
FPS          = 30
SCALE        = 3   # CSSの360×640px → 1080×1920px

# ── CSS（reel_5series.html と同一デザイン）────────────────────
CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Noto Sans JP', sans-serif; background: #fff; }

.slide {
  width: 360px; height: 640px; background: #fff;
  position: relative; overflow: hidden;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
}

/* ── 三角デコレーション ── */
.tri-tl {
  position: absolute; top: 0; left: 0;
  width: 0; height: 0; border-style: solid;
  border-width: 160px 160px 0 0;
  border-color: #FFE040 transparent transparent transparent;
}
.tri-br {
  position: absolute; bottom: 0; right: 0;
  width: 0; height: 0; border-style: solid;
  border-width: 0 0 160px 160px;
  border-color: transparent transparent #FFE040 transparent;
}

/* ── カラーバリエーション ── */
.slide.coral .tri-tl { border-color: #FF6B6B transparent transparent transparent; }
.slide.coral .tri-br { border-color: transparent transparent #FF6B6B transparent; }
.slide.coral .marker  { background: #FF6B6B; color: #fff; }
.slide.coral .step-num { background: #FF6B6B; }
.slide.coral .cta-btn  { background: #FF6B6B; color: #fff; }
.slide.coral .warn-box { border-left: 6px solid #FF6B6B; }
.slide.coral .warn-box p { color: #FF6B6B; }

.slide.navy .tri-tl { border-color: #1E3A5F transparent transparent transparent; }
.slide.navy .tri-br { border-color: transparent transparent #1E3A5F transparent; }
.slide.navy .marker  { background: #1E3A5F; color: #fff; }
.slide.navy .step-num { background: #1E3A5F; color: #FFE040; }
.slide.navy .cta-btn  { background: #1E3A5F; color: #FFE040; }
.slide.navy .warn-box { border-left: 6px solid #1E3A5F; }
.slide.navy .warn-box p { color: #1E3A5F; }

.slide.green .tri-tl { border-color: #2D8C4E transparent transparent transparent; }
.slide.green .tri-br { border-color: transparent transparent #2D8C4E transparent; }
.slide.green .marker  { background: #2D8C4E; color: #fff; }
.slide.green .step-num { background: #2D8C4E; }
.slide.green .cta-btn  { background: #2D8C4E; color: #fff; }
.slide.green .warn-box { border-left: 6px solid #2D8C4E; }
.slide.green .warn-box p { color: #2D8C4E; }

.slide.purple .tri-tl { border-color: #6B46C1 transparent transparent transparent; }
.slide.purple .tri-br { border-color: transparent transparent #6B46C1 transparent; }
.slide.purple .marker  { background: #6B46C1; color: #fff; }
.slide.purple .step-num { background: #6B46C1; }
.slide.purple .cta-btn  { background: #6B46C1; color: #fff; }
.slide.purple .warn-box { border-left: 6px solid #6B46C1; }
.slide.purple .warn-box p { color: #6B46C1; }

/* ── コンテンツ共通 ── */
.content { position: relative; z-index: 10; text-align: center; padding: 0 28px; width: 100%; }

.marker {
  display: inline-block; background: #FFE040;
  padding: 6px 18px; font-size: 19px; font-weight: 700;
  color: #1a1a1a; margin-bottom: 18px; border-radius: 3px;
}
.dots { font-size: 16px; color: #1a1a1a; letter-spacing: 4px; margin-bottom: 8px; display: block; }
.main-text { font-size: 30px; font-weight: 900; color: #1a1a1a; line-height: 1.3; margin-bottom: 20px; }

.big-num {
  font-size: 120px; font-weight: 900; line-height: 1; display: inline-block;
  background: linear-gradient(180deg, #ccc 0%, #888 45%, #444 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(3px 3px 0 rgba(0,0,0,0.12));
  letter-spacing: -4px;
}
.big-unit {
  font-size: 48px; font-weight: 900;
  background: linear-gradient(180deg, #bbb 0%, #777 45%, #444 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; vertical-align: bottom;
}

.warn-box {
  border-left: 6px solid #FFE040; background: #fafafa;
  border-radius: 0 8px 8px 0; padding: 14px 16px; margin: 14px 0; text-align: left;
}
.warn-box p { font-size: 22px; font-weight: 900; color: #B8860B; line-height: 1.4; }
.sub-text { font-size: 17px; font-weight: 700; color: #666; line-height: 1.6; margin-top: 10px; }

.step-list { text-align: left; width: 100%; margin-top: 14px; }
.step-item { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 14px; }
.step-num {
  background: #FFE040; color: #1a1a1a; font-size: 16px; font-weight: 900;
  min-width: 32px; height: 32px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.step-text { font-size: 20px; font-weight: 700; color: #1a1a1a; line-height: 1.4; padding-top: 4px; }
.step-foot { font-size: 15px; font-weight: 700; color: #999; margin-top: 10px; text-align: center; }

.cta-main { font-size: 40px; font-weight: 900; color: #1a1a1a; line-height: 1.25; margin-bottom: 14px; }
.cta-sub  { font-size: 17px; font-weight: 700; color: #555; line-height: 1.7; margin-bottom: 18px; }
.cta-btn  {
  display: inline-block; background: #1a1a1a; color: #FFE040;
  font-size: 18px; font-weight: 900; padding: 10px 28px; border-radius: 40px;
}
"""


# ── HTML生成ヘルパー ───────────────────────────────────────────

def nl2br(text):
    """\\n（文字列or実改行）→ <br>"""
    return str(text).replace('\\n', '<br>').replace('\n', '<br>')


def _slide_hook(s, color):
    return f"""
<div class="slide {color}">
  <div class="tri-tl"></div><div class="tri-br"></div>
  <div class="content">
    <div class="marker">{s['marker']}</div>
    <span class="dots">・・・</span>
    <div class="main-text">{nl2br(s['main'])}</div>
    <div>
      <span class="big-num">{s['big_num']}</span>
      <span class="big-unit">{s['big_unit']}</span>
    </div>
    <div class="sub-text">{nl2br(s['sub'])}</div>
  </div>
</div>"""


def _slide_problem(s, color):
    return f"""
<div class="slide {color}">
  <div class="tri-tl"></div><div class="tri-br"></div>
  <div class="content">
    <div class="marker">{s['marker']}</div>
    <div class="main-text">{nl2br(s['main'])}</div>
    <div class="warn-box"><p>{nl2br(s['warn'])}</p></div>
    <div class="sub-text">{nl2br(s['sub'])}</div>
  </div>
</div>"""


def _slide_solution(s, color):
    steps_html = ''.join(
        f'<div class="step-item">'
        f'<div class="step-num">{i+1}</div>'
        f'<div class="step-text">{step}</div>'
        f'</div>'
        for i, step in enumerate(s['steps'])
    )
    return f"""
<div class="slide {color}">
  <div class="tri-tl"></div><div class="tri-br"></div>
  <div class="content">
    <div class="marker">{s['marker']}</div>
    <div class="main-text">{nl2br(s['main'])}</div>
    <div class="step-list">{steps_html}</div>
    <div class="step-foot">{s['foot']}</div>
  </div>
</div>"""


def _slide_cta(s, color):
    return f"""
<div class="slide {color}">
  <div class="tri-tl"></div><div class="tri-br"></div>
  <div class="content">
    <div class="marker">{s['marker']}</div>
    <div class="cta-main">{nl2br(s['main'])}</div>
    <div class="cta-sub">{nl2br(s['sub'])}</div>
    <div class="cta-btn">{s['btn']}</div>
  </div>
</div>"""


def build_html(config):
    """YAMLコンフィグからHTMLを生成"""
    color  = config.get('color', '')
    slides = config['slides']
    body   = (
        _slide_hook(slides['hook'], color) +
        _slide_problem(slides['problem'], color) +
        _slide_solution(slides['solution'], color) +
        _slide_cta(slides['cta'], color)
    )
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@700;900&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
{body}
</body>
</html>"""


# ── スクショ ─────────────────────────────────────────────────

def screenshot_slides(html_content):
    """HTMLの .slide 要素を順にスクショ → numpy配列リスト"""
    arrays = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=CHROME_PATH,
            args=['--no-sandbox', '--disable-setuid-sandbox'],
        )
        page = browser.new_page(
            viewport={'width': 800, 'height': 4000},
            device_scale_factor=SCALE,
        )
        page.set_content(html_content, wait_until='domcontentloaded')
        try:
            page.wait_for_load_state('networkidle', timeout=8000)
        except Exception:
            page.wait_for_timeout(2000)

        slides = page.query_selector_all('.slide')
        print(f"  スライド検出: {len(slides)}枚")
        for i, slide in enumerate(slides):
            png = slide.screenshot()
            img = Image.open(io.BytesIO(png)).convert('RGB')
            if img.size != (OUT_W, OUT_H):
                img = img.resize((OUT_W, OUT_H), Image.LANCZOS)
            arrays.append(np.array(img).astype('uint8'))
            print(f"  [{i+1}/{len(slides)}] キャプチャ完了  {img.size}")
        browser.close()
    return arrays


# ── MP4生成 ──────────────────────────────────────────────────

def make_mp4(output, frames):
    duration = SLIDE_SEC * len(frames)

    def make_frame(t, _f=frames):
        return _f[min(int(t / SLIDE_SEC), len(_f) - 1)]

    clip = VideoClip(make_frame, duration=duration)
    clip.write_videofile(
        output, fps=FPS, codec='libx264',
        preset='medium', ffmpeg_params=['-crf', '18'],
        logger=None,
    )


# ── エントリーポイント ────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("使い方: python3 reel_pipeline.py <script.yaml>")
        sys.exit(1)

    yaml_path = sys.argv[1]
    if not os.path.exists(yaml_path):
        print(f"エラー: {yaml_path} が見つかりません")
        sys.exit(1)

    with open(yaml_path, encoding='utf-8') as f:
        config = yaml.safe_load(f)

    output   = config.get('output', 'reel_output.mp4')
    print(f"台本: {yaml_path}")
    print(f"出力: {output}\n")

    print("Step 1: HTML生成")
    html = build_html(config)
    html_path = output.replace('.mp4', '_preview.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  → {html_path}\n")

    print("Step 2: スクショ")
    frames = screenshot_slides(html)

    print(f"\nStep 3: MP4生成 ({len(frames)}枚 × {SLIDE_SEC}秒)")
    make_mp4(output, frames)
    size_kb = os.path.getsize(output) // 1024
    print(f"\n完了: {output}  ({size_kb} KB)")


if __name__ == '__main__':
    main()
