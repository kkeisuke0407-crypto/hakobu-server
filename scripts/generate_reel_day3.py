#!/usr/bin/env python3
"""reel_day3.mp4 生成 — 「産後に言われてしんどかった言葉」"""
from reel_generator import generate

SLIDES = [
    (0.0, "産後、言われてしんどかった言葉。",         0.4),
    (3.0, "「育児って楽しいでしょ？」",               0.4),
    (5.5, "「自分の時間作ればいいじゃん」",           0.4),
    (8.0, "「旦那さん、協力的でいいね」",             0.4),
    (10.5, "全部、地獄でした。",                     0.3),
    (12.0, "共感したら保存してください。",            0.3),
]

generate(SLIDES, duration=14.0, output="reel_day3.mp4")
