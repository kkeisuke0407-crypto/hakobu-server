# ikuji_no_real プロジェクト設定

## プロジェクト概要
ゆか（@ikuji_no_real）のInstagramリール自動生成パイプライン。
働くママ向けテキストリールを毎日21時に投稿する。

---

## 台本生成のルール（必須）

台本を作成するときは **必ず `RESEARCH.md` を参照すること。**

参照する項目：
- セクション2：バズる冒頭フック
- セクション3：テキストリールの構成パターン
- セクション4：ゆかのキャラクター設定
- セクション5：台本フォーマット

### 台本生成の手順
1. ユーザーからテーマ or 「今日の台本作って」と言われたら RESEARCH.md を参照
2. フック種別（質問型/告白型/ギャップ型）を選択またはユーザーに確認
3. ゆかのトーン・キャラクターに合わせて台本を生成
4. script.txt に直接書き込む
5. 使用するハッシュタグも RESEARCH.md セクション6から選んで hashtags.txt に書き込む

---

## 毎日の運用フロー

```
1. 「今日のリール作って」or「〇〇テーマで台本作って」
       ↓ Claude Code が RESEARCH.md 参照して
       ↓ script.txt・hashtags.txt に書き込む
       ↓ Gemini用の背景画像プロンプトを出力する

2. ユーザーがGeminiに指示文を貼って画像を生成
       ↓ GitHubの claude/sns-content に画像をアップロード
       ↓ 「入れました」と報告

3. Claude Code が画像を pull して動画を生成
       ↓ reels/reel_YYYYMMDD_HHMMss.mp4 に保存
       ↓ push

4. reels/ から動画をDL → Instagram投稿（21時）
```

---

## ファイル構成

```
hakobu-server/
├── generate_reel.py       ← メイン動画生成スクリプト
├── script.txt             ← 今日の台本（Claude Codeが書き込む）
├── hashtags.txt           ← 今日のハッシュタグ（Claude Codeが書き込む）
├── RESEARCH.md            ← リサーチ資料（台本生成時に必ず参照）
├── CLAUDE.md              ← このファイル
├── NotoSansJP-Bold.otf    ← フォント
├── bgm.mp3                ← BGM（任意）
├── reels/                 ← 完成動画（自動日付命名）
├── backgrounds/           ← 背景画像置き場
└── scripts/               ← 旧スクリプトアーカイブ
```

---

## 実行コマンド

```bash
# 通常（既存script.txtを使う）
python3 generate_reel.py --skip-script

# 背景も流用する場合
python3 generate_reel.py --skip-script --skip-bg

# 環境変数（画像自動生成したい場合）
export HF_TOKEN=hf_xxx        # Hugging Face（無料）
export GEMINI_API_KEY=xxx     # Gemini Imagen（有料・高品質）
```

---

## 注意事項

- ゆかのトーンを絶対に外さない（RESEARCH.md セクション4参照）
- 「頑張ろう！」「大丈夫！」系の押しつけ応援は禁止
- 台本は短文・体言止め・余白を大事に
- 1スライド2〜12文字程度
- 動画尺は15〜25秒に収める
