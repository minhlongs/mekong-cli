/**
 * Service Worker - PWA Offline Support
 * F&B Container Café
 *
 * Strategies:
 * - Cache-First: CSS, JS, images, static assets
 * - Network-First: HTML pages (with cache fallback)
 * - Stale-While-Revalidate: API requests
 *
 * Enhanced with:
 * - Critical asset pre-caching
 * - Runtime caching for JS modules
 * - Better offline fallback
 */

const CACHE_NAME = 'fnb-cache-v3';
const STATIC_CACHE = 'fnb-static-v3';
const DYNAMIC_CACHE = 'fnb-dynamic-v3';

// Static assets to pre-cache (critical for app shell)
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/public/offline.html',
  '/manifest.json',
  '/public/images/favicon.svg',
  '/public/images/favicon-192x192.png',
  '/public/images/favicon-512x512.png',
  '/css/styles.min.css',
  '/js/script.js',
  '/js/api-client.js',
  '/js/order.js',
  '/js/config.js',
  '/js/navigation.js',
  '/js/hero.js',
  '/js/scroll-effects.js'
];

// Install event - cache critical assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker, caching critical assets...');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Opening static cache');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('[SW] All critical assets cached');
        self.skipWaiting();
      })
      .catch((err) => {
        console.error('[SW] Failed to cache some assets:', err);
      })
  );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name !== STATIC_CACHE && name !== DYNAMIC_CACHE)
            .map((name) => caches.delete(name))
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - strategy based on request type
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {return;}

  // Skip cross-origin requests (except for API)
  if (!url.origin.startsWith(self.location.origin)) {return;}

  // Determine strategy based on request type
  if (isStaticAsset(request)) {
    // Cache-First for CSS, JS, images
    event.respondWith(cacheFirst(request, STATIC_CACHE));
  } else if (isHtmlPage(request)) {
    // Network-First for HTML pages
    event.respondWith(networkFirst(request, DYNAMIC_CACHE));
  } else if (isApiRequest(request)) {
    // Stale-While-Revalidate for API
    event.respondWith(staleWhileRevalidate(request, DYNAMIC_CACHE));
  } else {
    // Default: Network-First
    event.respondWith(networkFirst(request, DYNAMIC_CACHE));
  }
});

// Helper functions to identify request types
function isStaticAsset(request) {
  const url = new URL(request.url);
  return (
    url.pathname.endsWith('.css') ||
    url.pathname.endsWith('.js') ||
    url.pathname.match(/\.(png|jpg|jpeg|gif|svg|webp|ico)$/i) ||
    url.pathname.startsWith('/css/') ||
    url.pathname.startsWith('/js/') ||
    url.pathname.startsWith('/assets/') ||
    url.pathname.startsWith('/images/') ||
    url.pathname.startsWith('/public/')
  );
}

function isHtmlPage(request) {
  const url = new URL(request.url);
  return (
    request.headers.get('accept')?.includes('text/html') ||
    url.pathname.endsWith('.html') ||
    url.pathname.endsWith('/') ||
    url.pathname === ''
  );
}

function isApiRequest(request) {
  const url = new URL(request.url);
  return (
    url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/v1/')
  );
}

// Cache-First Strategy: Best for static assets (CSS, JS, images)
async function cacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);

  try {
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
  } catch (error) {
    console.log('[SW] Cache-first cache match failed:', error);
  }

  // Fetch from network and cache
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    return new Response('Offline', {
      status: 503,
      statusText: 'Service Unavailable'
    });
  }
}

// Network-First Strategy: Best for HTML pages (always fresh when possible)
async function networkFirst(request, cacheName) {
  const cache = await caches.open(cacheName);

  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.log('[SW] Network failed, trying cache for:', request.url);

    // Network failed, try cache
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      console.log('[SW] Serving from cache:', request.url);
      return cachedResponse;
    }

    // Show offline page for navigation requests
    if (request.mode === 'navigate') {
      const offlinePage = await caches.match('/public/offline.html');
      if (offlinePage) {
        console.log('[SW] Serving offline page');
        return offlinePage;
      }
    }

    return new Response('Offline - No cached version available', {
      status: 503,
      statusText: 'Service Unavailable',
      headers: new Headers({
        'Content-Type': 'text/plain'
      })
    });
  }
}

// Stale-While-Revalidate Strategy: Best for API requests
async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);

  try {
    const cachedResponse = await cache.match(request);

    // Fetch in background to update cache
    const fetchPromise = fetch(request)
      .then((networkResponse) => {
        if (networkResponse.ok) {
          cache.put(request, networkResponse.clone());
        }
        return networkResponse;
      })
      .catch(() => null);

    // Return cached response immediately, or wait for network
    return cachedResponse || await fetchPromise || new Response('Offline', {
      status: 503,
      statusText: 'Service Unavailable'
    });
  } catch (error) {
    return new Response('Offline', {
      status: 503,
      statusText: 'Service Unavailable'
    });
  }
}

// Push notifications
self.addEventListener('push', (event) => {
  const options = {
    body: event.data?.text() || 'Đơn hàng của bạn đã sẵn sàng!',
    icon: '/public/images/favicon-192x192.png',
    badge: '/public/images/favicon-192x192.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      { action: 'view', title: 'Xem đơn hàng' },
      { action: 'close', title: 'Đóng' }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('F&B Container Café', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/?tab=orders')
    );
  }
});

// Background sync for orders
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-orders') {
    event.waitUntil(syncOrders());
  }
});

async function syncOrders() {
  // Sync pending orders when back online
  // Implementation would sync with backend
}
