// ハコぶ Service Worker — オフラインキャッシュ
const CACHE = 'hakobu-v3';

// キャッシュするアセット（アプリシェル）
const PRECACHE = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png',
  'https://fonts.googleapis.com/css2?family=Nunito:ital,wght@0,400;0,600;0,700;0,800;0,900;1,800&family=Noto+Sans+JP:wght@400;500;700;900&display=swap',
  'https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css',
];

// インストール時にアプリシェルをキャッシュ
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(cache =>
      cache.addAll(PRECACHE.filter(url => !url.startsWith('https://fonts')))
    ).then(() => self.skipWaiting())
  );
});

// 古いキャッシュを削除
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// フェッチ戦略:
// - /api/* → ネットワーク優先（オフライン時はエラー）
// - Firebase / Anthropic → ネットワークのみ
// - その他 → キャッシュ優先、なければネットワーク
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // APIリクエストはキャッシュしない
  if(url.pathname.startsWith('/api/') ||
     url.hostname.includes('firebaseio.com') ||
     url.hostname.includes('googleapis.com') ||
     url.hostname.includes('anthropic.com')) {
    e.respondWith(fetch(e.request).catch(() =>
      new Response(JSON.stringify({ error: 'オフラインです' }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      })
    ));
    return;
  }

  // アプリシェル: キャッシュ優先
  e.respondWith(
    caches.match(e.request).then(cached => {
      if(cached) return cached;
      return fetch(e.request).then(res => {
        // 成功したレスポンスをキャッシュに追加
        if(res.ok && e.request.method === 'GET') {
          const clone = res.clone();
          caches.open(CACHE).then(cache => cache.put(e.request, clone));
        }
        return res;
      }).catch(() => {
        // HTMLリクエストにはindex.htmlをフォールバック
        if(e.request.destination === 'document') {
          return caches.match('/index.html');
        }
      });
    })
  );
});
