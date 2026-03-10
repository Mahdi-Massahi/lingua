/// <reference types="@sveltejs/kit" />
import { build, files, version } from '$service-worker';

const CACHE_NAME = `lingua-cache-${version}`;
const ASSETS = [...build, ...files];

self.addEventListener('install', (event) => {
	event.waitUntil(
		caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
	);
});

self.addEventListener('activate', (event) => {
	event.waitUntil(
		caches.keys().then((keys) =>
			Promise.all(
				keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
			)
		)
	);
});

self.addEventListener('fetch', (event) => {
	if (event.request.method !== 'GET') return;

	const url = new URL(event.request.url);

	// Skip cross-origin requests (Firebase, Google APIs, etc.)
	if (url.origin !== self.location.origin) return;

	// Skip API routes
	if (
		url.pathname.startsWith('/chat/session') ||
		url.pathname.startsWith('/chat/sessions') ||
		url.pathname.startsWith('/tts')
	) {
		return;
	}

	event.respondWith(
		caches.match(event.request).then((cached) => {
			if (cached) return cached;

			return fetch(event.request)
				.then((response) => {
					if (!response || response.status !== 200) return response;

					const responseClone = response.clone();
					caches.open(CACHE_NAME).then((cache) => {
						cache.put(event.request, responseClone);
					});

					return response;
				})
				.catch(() => {
					if (event.request.mode === 'navigate') {
						return caches.match('/') || new Response('Offline', {
							status: 503,
							headers: { 'Content-Type': 'text/plain' }
						});
					}
					return new Response('Offline', { status: 503 });
				});
		})
	);
});
