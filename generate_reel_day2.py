#!/usr/bin/env python3
"""reel_day2.mp4 生成"""
from reel_generator import generate

SLIDES = [
    (0.0, "「手伝うね」って言った。",          0.4),
    (2.5, "その夜も、",                       0.3),
    (4.5, "一人だった。",                     0.3),
    (6.5, "育児は「手伝う」ものじゃない。",     0.4),
    (9.0, "あなたの子でしょ。",               0.3),
]

generate(SLIDES, duration=11.0, output="reel_day2.mp4")
