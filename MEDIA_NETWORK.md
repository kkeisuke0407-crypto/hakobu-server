# ハコぶファミリー メディアネットワーク構成

`hakobu-family.com` を親サイト（メディア運営本体）とし、各テーマの専門メディアを
サブドメインで運営する構成にするためのメモ。

## 構成

```text
hakobu-family.com
└ ハコぶファミリー公式サイト（メディア運営本体）
   ├ hajimai.hakobu-family.com       … 墓じまいガイド
   ├ kaitori.hakobu-family.com       … 買取ガイド
   ├ taisyoku.hakobu-family.com      … 退職・働き方ガイド
   └ unsou-shikin.hakobu-family.com  … 法人資金調達ガイド
```

家族アプリ「ハコぶ」は 2026-08 にこのドメインから削除した（`public/` 配下のアプリ
一式・PWA マニフェストを削除。コードは git 履歴に残っている）。

## 公式サイトのページ構成（`public/`）

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

共通スタイルは `public/style.css`。GitHub Actions で `public/` を GitHub Pages へデプロイしている。

## 残作業

### 1. 運営者情報

`public/company.html` に掲載しているのは以下。

- 運営者（屋号）… HAKOBU MEDIA
- 連絡先 … hakobu.app@gmail.com

代表者・所在地・設立年月は掲載しない方針（2026-08 決定）。
ASP や広告主から求められた場合は、その都度追記して対応する。

### 2. 各サブドメインのフッターに親サイトへのリンクを追加

各メディア側のフッターに以下を貼る（親 → 子 / 子 → 親 の相互リンクを成立させる）。

```html
<p style="text-align:center;font-size:13px;color:#5A7A99;margin-top:24px;">
  運営：<a href="https://hakobu-family.com/" style="color:#1D8F8A;font-weight:700;">ハコぶファミリー</a><br>
  <a href="https://hakobu-family.com/company.html" style="color:#5A7A99;">運営者情報</a> ｜
  <a href="https://hakobu-family.com/editorial.html" style="color:#5A7A99;">編集方針</a> ｜
  <a href="https://hakobu-family.com/advertising.html" style="color:#5A7A99;">広告掲載方針</a> ｜
  <a href="https://hakobu-family.com/privacy.html" style="color:#5A7A99;">プライバシーポリシー</a>
</p>
```

### 3. canonical / OGP の正規化

各サブドメインの `canonical` が自サイトの正しいURLを指しているか確認する。

### 4. セキュリティベンダーへの再審査申請

サイト整理後に、判定が付いているベンダーへ再スキャン・解除申請を行う。
（VirusTotal の各エンジン、Bitdefender など。判定は自動では消えない）

### 5. アプリ削除の残り（要判断）

サイトからは削除済み。リポジトリ側には以下が残っている。

- `capacitor.config.ts`（iOS ラッパー設定）
- `package.json` の `@capacitor/*` 依存と `cap:*` スクリプト
- `hakobu_dashboard.html` / `hakobu_spec.html` / `FIREBASE_SETUP.md`（アプリの仕様ドキュメント）

いずれも GitHub Pages には配信されないため公開サイトには影響しない。
アプリを完全に畳むなら削除、`hakobu.app` で再開する可能性を残すならそのままでよい。

### 6. 下層ページのプルダウン（`sites.html`）

各メディアの下層ページ（サブディレクトリ）を折りたたみで見せる用のスタイルを
`public/style.css` に用意済み（`.pages`）。`sites.html` の各メディアカードの
`</div>` 直前に以下を入れると、そのメディアの掲載ページ一覧になる。

```html
    <details class="pages">
      <summary>掲載ページ（N件）</summary>
      <div class="pages-body">
        <ul>
          <li><a href="https://kaitori.hakobu-family.com/tokei/">時計買取ガイド
            <span class="path">kaitori.hakobu-family.com/tokei/</span></a></li>
        </ul>
      </div>
    </details>
```

※ 下層ページの実URLが未確認のため、中身はまだ入れていない。

### 7. 新しいメディアを追加したとき

- `public/index.html` のカードを追加
- `public/sites.html` に詳細を追加
- `public/style.css` の変更は不要
- フッター（`public/*.html` の運営メディア欄）にも追加
- `public/sitemap.xml` に URL を追加

---

*2026-08 作成*
