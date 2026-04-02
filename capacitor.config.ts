import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.hakobu.family',
  appName: 'ハコぶ',
  webDir: 'public',
  server: {
    // FirebaseのsignInWithRedirectがcapacitor://localhostに戻ってこれるよう
    // hostname を設定する（Firebase Console の承認済みドメインに追加要）
    hostname: 'hakobu-app',
    androidScheme: 'https',
    // iosScheme はデフォルト 'ionic' → 'capacitor' に変更不要
    // Firebase Console → Authentication → 承認済みドメインに
    //   hakobu-app  を追加すること（セットアップガイド参照）
  },
  plugins: {
    StatusBar: {
      style: 'dark',
      backgroundColor: '#1D3D5C',
    },
    Keyboard: {
      resize: 'body',
      resizeOnFullScreen: true,
    },
    SplashScreen: {
      launchShowDuration: 0,
    },
    // @capacitor/app: URLスキームによるディープリンク処理
    App: {
      // Firebase Auth のリダイレクト後に appUrlOpen イベントが発火する
    },
  },
  ios: {
    contentInset: 'always',
    allowsLinkPreview: false,
    scrollEnabled: false,
    backgroundColor: '#F5F0EB',
    // カスタムURLスキーム（Xcode で Info.plist に追加が必要）
    // Firebase Console から GoogleService-Info.plist をダウンロードし
    // REVERSED_CLIENT_ID の値を URLスキームとして Info.plist に登録する
  },
};

export default config;
