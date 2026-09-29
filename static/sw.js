// 간단한 서비스 워커 (PWA 설치 요건 충족 및 기본 캐싱)
const CACHE_NAME = "tech-comparator-v1";

self.addEventListener("install", (e) => {
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(clients.claim());
});

self.addEventListener("fetch", (e) => {
  // 네트워크 우선 통신 (실시간 검색 및 AI 결과 수신을 위해 네트워크 우선 사용)
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
