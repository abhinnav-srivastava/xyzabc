/**
 * Restore app name Service Worker
 * Provides offline functionality and caching for the PWA
 */

const CACHE_NAME = 'Restore app name-v1.0.4';
const STATIC_CACHE_NAME = 'Restore app name-static-v1.0.4';
const DYNAMIC_CACHE_NAME = 'Restore app name-dynamic-v1.0.4';

// Files to cache for offline functionality (paths must match actual static layout)
const STATIC_FILES = [
  '/',
  '/login',
  '/start',
  '/guidelines',
  '/summary',
  '/upload-patch',
  '/offline',
  '/static/vendor/bootstrap/css/bootstrap.min.css',
  '/static/vendor/bootstrap/js/bootstrap.bundle.min.js',
  '/static/vendor/bootstrap-icons/bootstrap-icons.css',
  '/static/vendor/bootstrap-icons/fonts/bootstrap-icons.woff2',
  '/static/css/styles.css',
  '/static/js/app.js',
  '/static/js/pwa.js',
  '/static/manifest.json',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
];

// API routes that should be cached
const API_ROUTES = [
  '/refresh',
  '/refresh-all',
  '/refresh-categories'
];

// Minimal HTML fallback when cache is empty (server down, first load)
function getOfflineFallbackResponse() {
  const html = '<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>App Unavailable</title></head><body style="font-family:sans-serif;max-width:480px;margin:2rem auto;padding:1rem;text-align:center"><h1>App Unavailable</h1><p>The app server is not reachable. Please ensure the app is running and try again.</p><p><button onclick="location.reload()" style="padding:0.5rem 1rem;cursor:pointer">Try Again</button> <button onclick="history.back()" style="padding:0.5rem 1rem;cursor:pointer">Go Back</button></p></body></html>';
  return new Response(html, {
    status: 503,
    statusText: 'Service Unavailable',
    headers: { 'Content-Type': 'text/html; charset=utf-8' }
  });
}

// Install event - cache static files
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker: Caching static files');
        return cache.addAll(STATIC_FILES);
      })
      .then(() => {
        console.log('Service Worker: Static files cached successfully');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('Service Worker: Failed to cache static files', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE_NAME && cacheName !== DYNAMIC_CACHE_NAME) {
              console.log('Service Worker: Deleting old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker: Activated successfully');
        return self.clients.claim();
      })
  );
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip external requests
  if (url.origin !== location.origin) {
    return;
  }
  
  // Don't intercept navigation (page) requests - let browser handle them directly.
  // SW interception was causing ERR_FAILED for routes like /start, /summary.
  if (request.mode === 'navigate') {
    return;
  }
  
  event.respondWith(
    caches.match(request)
      .then((cachedResponse) => {
        // Return cached version if available
        if (cachedResponse) {
          console.log('Service Worker: Serving from cache', request.url);
          return cachedResponse;
        }
        
        // Otherwise, fetch from network
        return fetch(request)
          .then((response) => {
            // Don't cache if not a valid response
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // Clone the response
            const responseToCache = response.clone();
            
            // Cache dynamic content
            if (shouldCacheRequest(request)) {
              caches.open(DYNAMIC_CACHE_NAME)
                .then((cache) => {
                  cache.put(request, responseToCache);
                });
            }
            
            return response;
          })
          .catch((error) => {
            console.log('Service Worker: Network request failed', request.url, error);
            
            if (request.mode === 'navigate') {
              return caches.match(new Request(url.origin + '/offline'))
                .then((r) => r || caches.match(new Request(url.origin + '/')))
                .then((r) => r || getOfflineFallbackResponse())
                .catch(() => getOfflineFallbackResponse());
            }
            return caches.match(request)
              .then((r) => r || getOfflineFallbackResponse())
              .catch(() => getOfflineFallbackResponse());
          });
      })
  );
});

// Background sync for offline form submissions
self.addEventListener('sync', (event) => {
  console.log('Service Worker: Background sync triggered', event.tag);
  
  if (event.tag === 'review-sync') {
    event.waitUntil(
      syncReviewData()
    );
  }
});

// Push notifications
self.addEventListener('push', (event) => {
  console.log('Service Worker: Push notification received');
  
  const options = {
    body: event.data ? event.data.text() : 'New notification from Restore app name',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Open App',
        icon: '/static/icons/icon-96x96.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/static/icons/icon-96x96.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('Restore app name', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  console.log('Service Worker: Notification clicked');
  
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Helper functions
function shouldCacheRequest(request) {
  const url = new URL(request.url);
  
  // Cache API routes
  if (API_ROUTES.some(route => url.pathname.startsWith(route))) {
    return true;
  }
  
  // Cache static assets
  if (url.pathname.startsWith('/static/')) {
    return true;
  }
  
  // Cache HTML pages
  if (request.mode === 'navigate') {
    return true;
  }
  
  return false;
}

async function syncReviewData() {
  try {
    // Get stored review data from IndexedDB
    const reviewData = await getStoredReviewData();
    
    if (reviewData && reviewData.length > 0) {
      // Send data to server
      const response = await fetch('/api/sync-reviews', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(reviewData)
      });
      
      if (response.ok) {
        console.log('Service Worker: Review data synced successfully');
        // Clear stored data
        await clearStoredReviewData();
      } else {
        console.error('Service Worker: Failed to sync review data');
      }
    }
  } catch (error) {
    console.error('Service Worker: Error syncing review data', error);
  }
}

async function getStoredReviewData() {
  // This would integrate with IndexedDB to get stored review data
  // For now, return empty array
  return [];
}

async function clearStoredReviewData() {
  // This would clear stored review data from IndexedDB
  console.log('Service Worker: Clearing stored review data');
}

// Message handler for communication with main thread
self.addEventListener('message', (event) => {
  console.log('Service Worker: Message received', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: CACHE_NAME });
  }
});

console.log('Service Worker: Loaded successfully');