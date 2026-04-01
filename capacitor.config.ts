import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.hakobu.family',
  appName: 'ハコぶ',
  webDir: 'public',
  server: {
    // 開発時はローカルサーバーを使う場合はここにURLを設定
    // androidScheme: 'https',
  },
  plugins: {
    StatusBar: {
      style: 'dark',           // ステータスバー文字色を白に
      backgroundColor: '#1D3D5C',
    },
    Keyboard: {
      resize: 'body',          // キーボード表示時にbodyをリサイズ
      resizeOnFullScreen: true,
    },
    SplashScreen: {
      launchShowDuration: 0,   // スプラッシュはアプリ内で独自表示
    },
  },
  ios: {
    contentInset: 'always',    // safe-area-insetを常に適用
    allowsLinkPreview: false,
    scrollEnabled: false,      // ネイティブスクロールを無効（アプリ内スクロールを使用）
    backgroundColor: '#F5F0EB',
  },
};

export default config;
