// ハコぶファミリー公式サイト — 旧アプリ用 Service Worker の停止用スクリプト
//
// 以前このドメインで配信していた家族アプリ「ハコぶ」の Service Worker が
// 登録されたままの端末では、古いアプリ画面がキャッシュから表示され続けます。
// このスクリプトはそれを解除するためのもので、キャッシュを全削除し、
// 自身の登録を解除してから、開いているページを再読み込みします。

self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map(k => caches.delete(k)));
    await self.registration.unregister();
    const clients = await self.clients.matchAll({ type: 'window' });
    clients.forEach(client => client.navigate(client.url));
  })());
});

// 解除が完了するまでの間もキャッシュを使わず、常にネットワークから取得する
self.addEventListener('fetch', event => {
  event.respondWith(fetch(event.request));
});
