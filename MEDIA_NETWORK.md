# ハコぶファミリー メディアネットワーク構成

`hakobu-family.com` を親サイト（メディア運営本体）とし、各テーマの専門メディアを
サブドメインで運営する構成にするためのメモ。

## 構成

```text
hakobu-family.com
├ /                … 家族アプリ「ハコぶ」（現状のまま）
├ /media/          … ハコぶファミリー公式サイト（運営者情報・運営メディア一覧）
│
├ hajimai.hakobu-family.com       … 墓じまいガイド
├ kaitori.hakobu-family.com       … 買取ガイド
├ taisyoku.hakobu-family.com      … 退職・働き方ガイド
└ unsou-shikin.hakobu-family.com  … 法人資金調達ガイド
```

## 公式サイトのページ構成（`public/media/`）

| ページ | ファイル | 内容 |
|---|---|---|
| トップ | `index.html` | コンセプト＋運営メディアカード一覧（JSON-LD 付き） |
| 運営メディア一覧 | `sites.html` | 各メディアのURL・テーマ・想定読者・状況 |
| メディアについて | `about.html` | 運営方針・なぜテーマ別に分けているか |
| 編集方針 | `editorial.html` | 情報源の扱い・費用の示し方・訂正方針 |
| 広告掲載方針 | `advertising.html` | アフィリエイト明示・掲載基準（ステマ規制対応） |
| 運営者情報 | `company.html` | 運営者・連絡先・運営サイト一覧 |
| プライバシーポリシー | `privacy.html` | Cookie・アクセス解析・広告配信・第三者提供 |
| お問い合わせ | `contact.html` | 問い合わせ窓口 |

共通スタイルは `public/media/style.css`。

## 残作業

### 1. 運営者情報の記入（必須）

`public/media/company.html` の `[ ]` 部分を実際の情報に差し替える。

- 運営者（屋号または氏名）
- 代表者
- 所在地
- 設立年月

同じ `[ ]` は `public/privacy.html` / `public/tokusho.html`（アプリ側）にも残っている。

### 2. メールアドレスの用意（必須）

公式サイトの窓口を `info@hakobu-family.com` としているため、
このアドレスを受信できる状態にする。

### 3. 各サブドメインのフッターに親サイトへのリンクを追加

各メディア側のフッターに以下を貼る（親 → 子 / 子 → 親 の相互リンクを成立させる）。

```html
<p style="text-align:center;font-size:13px;color:#5A7A99;margin-top:24px;">
  運営：<a href="https://hakobu-family.com/media/" style="color:#1D8F8A;font-weight:700;">ハコぶファミリー</a><br>
  <a href="https://hakobu-family.com/media/company.html" style="color:#5A7A99;">運営者情報</a> ｜
  <a href="https://hakobu-family.com/media/editorial.html" style="color:#5A7A99;">編集方針</a> ｜
  <a href="https://hakobu-family.com/media/advertising.html" style="color:#5A7A99;">広告掲載方針</a> ｜
  <a href="https://hakobu-family.com/media/privacy.html" style="color:#5A7A99;">プライバシーポリシー</a>
</p>
```

### 4. canonical / OGP の正規化

各サブドメインの `canonical` が自サイトの正しいURLを指しているか確認する。

### 5. セキュリティベンダーへの再審査申請

サイト整理後に、判定が付いているベンダーへ再スキャン・解除申請を行う。
（VirusTotal の各エンジン、Bitdefender など。判定は自動では消えない）

### 6. 新しいメディアを追加したとき

- `public/media/index.html` のカードを追加
- `public/media/sites.html` に詳細を追加
- `public/media/style.css` の変更は不要
- フッター（`public/media/*.html` の運営メディア欄）にも追加
- `public/sitemap.xml` は公式サイト分のみ管理

---

*2026-08 作成*
