# Firebase セットアップガイド（iOS アプリ向け）

iOSアプリでGoogleログイン・Appleログイン（ママパパ連携）を動かすための設定手順です。

---

## 1. Firebase Console での設定

### 1-1. 承認済みドメインの追加

Firebase Console → Authentication → Settings → 承認済みドメイン

以下を追加：
```
hakobu-app
localhost
hakobu-family.com
```

> `hakobu-app` が Capacitor の WebView から Firebase Auth リダイレクト後に戻ってくるホスト名です。
> （capacitor.config.ts の `server.hostname` と一致させること）

### 1-2. Google ログインの有効化

Firebase Console → Authentication → Sign-in method → Google → 有効にする

- プロジェクトのサポートメール を設定する

### 1-3. Apple ログインの有効化

Firebase Console → Authentication → Sign-in method → Apple → 有効にする

- Apple Developer Program での設定が必要（後述）

---

## 2. iOS（Xcode）での設定

### 2-1. GoogleService-Info.plist の追加

1. Firebase Console → プロジェクトの設定 → iOS アプリ → `GoogleService-Info.plist` をダウンロード
2. Xcode でプロジェクトルートに追加（Copy if needed にチェック）

### 2-2. URL スキームの登録（Google ログイン用）

`GoogleService-Info.plist` を開き `REVERSED_CLIENT_ID` の値をコピー。

例：`com.googleusercontent.apps.123456789-abcdefg`

Xcode → ターゲット → Info → URL Types → `+` ボタン → URL Schemes に貼り付け

### 2-3. Sign In with Apple の設定

Xcode → ターゲット → Signing & Capabilities → `+` → Sign In with Apple を追加

Apple Developer Console で：
- Identifiers → App ID → `com.hakobu.family` → Sign In with Apple を有効化
- Keys → Sign In with Apple 用のキーを生成
- そのキー ID と Team ID を Firebase Console の Apple プロバイダー設定に入力

---

## 3. アプリ内 Firebase 設定（初回起動時）

アプリ起動 → Firebase 未設定時は設定ダイアログが表示されます。

Firebase Console → プロジェクトの設定 → マイアプリ → ウェブアプリ → SDK 設定 から以下を取得：

| 項目 | 例 |
|---|---|
| API Key | `AIzaSy...` |
| Auth Domain | `your-app.firebaseapp.com` |
| Database URL | `https://your-app-default-rtdb.asia-southeast1.firebasedatabase.app` |
| Project ID | `your-app` |
| Storage Bucket | `your-app.appspot.com` |
| Messaging Sender ID | `123456789` |
| App ID | `1:123456789:web:abcdef` |

---

## 4. Realtime Database のルール設定

Firebase Console → Realtime Database → ルール

```json
{
  "rules": {
    "families": {
      "$familyId": {
        ".read": "auth != null",
        ".write": "auth != null"
      }
    }
  }
}
```

---

## 5. 動作確認フロー

```
iOS アプリ起動
  → Firebase 設定ダイアログで上記設定を入力
  → 「接続する」
  → スプラッシュ画面で「Googleでログイン」タップ
  → Safari/Google 認証画面が開く
  → 認証後アプリに自動で戻ってくる（capacitor://hakobu-app）
  → ホーム画面へ遷移
  → 「招待コード」でパパ/ママが同じ Family Room に入る
  → タスク・家事がリアルタイム同期される
```
