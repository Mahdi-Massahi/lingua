<script>
	import { onMount, tick } from 'svelte';
	import { enhance } from '$app/forms';
	import { auth, updateStreak, subscribeProfile } from '$lib/firebase.js';
	import { speak } from '$lib/speech.js';
	import { marked } from 'marked';

	let sessions = $state([]);
	let currentSessionId = $state(null);
	let messages = $state([]);
	let inputMessage = $state('');
	let loading = $state(false);
	let loadingSessions = $state(false);
	let sessionsError = $state(null);
	let chatContainer = $state(null);
	let profile = $state({});

	const userId = auth.currentUser?.uid || 'default_user';

	onMount(() => {
		loadSessions();
		const unsub = subscribeProfile(userId, (p) => { profile = p; });
		return unsub;
	});

	async function scrollToBottom() {
		await tick();
		if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
	}

	async function loadSessions() {
		loadingSessions = true;
		sessionsError = null;
		try {
			const res = await fetch(`/chat/sessions?userId=${encodeURIComponent(userId)}`);
			const data = await res.json();
			if (data.success) {
				sessions = data.sessions || [];
			} else {
				sessionsError = data.error || 'Failed to load sessions';
			}
		} catch (err) {
			console.error('Error loading sessions:', err);
			sessionsError = 'Failed to load sessions';
		}
		loadingSessions = false;
	}

	async function loadSession(sessionId) {
		currentSessionId = sessionId;
		messages = [];

		try {
			const res = await fetch(`/chat/session?sessionId=${encodeURIComponent(sessionId)}&userId=${encodeURIComponent(userId)}`);
			const data = await res.json();

			if (data?.success && data.session) {
				const events = data.session.events || [];
				const merged = [];
				let current = null;

				for (const event of events) {
					if (!event.content?.parts) continue;
					const role = event.content.role;
					const text = event.content.parts.map((p) => p.text || '').join('');
					if (!text) continue;

					if (current && current.role === role) {
						current.text += text;
					} else {
						if (current) merged.push(current);
						current = { role, text };
					}
				}
				if (current) merged.push(current);
				messages = merged;
			} else if (!data?.success) {
				messages = [{ role: 'model', text: `Failed to load session: ${data?.error ?? 'unknown error'}` }];
			}
		} catch (err) {
			console.error('Error loading session:', err);
			messages = [{ role: 'model', text: `Failed to load session: ${err instanceof Error ? err.message : String(err)}` }];
		}
		scrollToBottom();
	}

	function createNewSession() {
		currentSessionId = null;
		messages = [];
	}

	function renderMarkdown(text) {
		return marked.parse(text || '');
	}

	async function handleEnhance({ formData, cancel }) {
		const message = formData.get('message')?.toString().trim();
		if (!message || loading) { cancel(); return; }

		messages = [...messages, { role: 'user', text: message }];
		inputMessage = '';
		loading = true;
		scrollToBottom();

		await updateStreak(userId, profile);

		return async ({ result: serverResult }) => {
			loading = false;
			const data = serverResult?.type === 'success' ? serverResult.data : null;

			if (data?.success) {
				messages = [...messages, { role: 'model', text: data.botResponse }];
				if (data.sessionId && data.sessionId !== currentSessionId) {
					currentSessionId = data.sessionId;
					loadSessions();
				}
			} else {
				messages = [...messages, { role: 'model', text: 'Error communicating with agent.' }];
			}
			scrollToBottom();
		};
	}

	function addPronunciationButtons(html) {
		// Add play buttons to bold words in rendered HTML
		return html.replace(/<strong>(.*?)<\/strong>/g, (_, word) => {
			return `<strong>${word}</strong><button class="inline-flex items-center justify-center ml-1 text-violet-400 hover:text-white bg-violet-500/10 hover:bg-violet-500 rounded p-0.5 transition-colors align-middle pronunciation-btn" data-word="${word.replace(/"/g, '&quot;')}"><svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" /></svg></button>`;
		});
	}

	function handleChatClick(e) {
		const btn = e.target.closest('.pronunciation-btn');
		if (btn) {
			e.preventDefault();
			speak(btn.dataset.word);
		}
	}
</script>

<main class="flex-1 flex min-h-0" style="height: calc(100vh - 57px);">
	<!-- Sidebar -->
	<div class="w-80 bg-gray-900 border-r border-white/5 flex flex-col min-h-0">
		<div class="p-4 border-b border-white/5">
			<button onclick={createNewSession} class="w-full bg-gradient-to-r from-violet-600 to-indigo-600 text-white px-4 py-3 rounded-xl hover:from-violet-500 hover:to-indigo-500 transition-all shadow-lg shadow-violet-500/20 font-medium flex items-center justify-center gap-2">
				<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
					<path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
				</svg>
				New Chat
			</button>
		</div>
		<div class="flex-1 overflow-y-auto p-3 space-y-2">
			{#if loadingSessions}
				<div class="text-center text-gray-500 text-sm mt-8">Loading sessions...</div>
			{:else if sessionsError}
				<div class="text-center text-red-400 text-sm mt-8 px-4">
					{sessionsError}
					<button onclick={loadSessions} class="block mt-2 mx-auto text-violet-400 hover:text-violet-300 underline text-xs">Retry</button>
				</div>
			{:else if sessions.length === 0}
				<div class="text-center text-gray-500 text-sm mt-8">No session history.</div>
			{:else}
				{#each sessions as session}
					<button
						onclick={() => loadSession(session.id)}
						class="w-full text-left px-4 py-3 rounded-xl transition-all mb-2 flex flex-col gap-1 border border-transparent hover:bg-gray-800 hover:border-white/5 {currentSessionId === session.id ? 'bg-gray-800 border-violet-500/30 shadow-md' : ''}"
					>
						<div class="truncate text-gray-200 font-medium {currentSessionId === session.id ? 'text-violet-300' : ''}">
							Session {String(session.id ?? '').substring(0, 8)}...
						</div>
						<div class="text-xs text-gray-500">
							{session.last_update_time ? new Date(session.last_update_time * 1000).toLocaleDateString() : ''}
						</div>
					</button>
				{/each}
			{/if}
		</div>
	</div>

	<!-- Chat Area -->
	<div class="flex-1 flex flex-col bg-gray-950 relative min-h-0">
		<!-- Background Glow -->
		<div class="absolute inset-0 overflow-hidden pointer-events-none">
			<div class="absolute -top-[20%] -right-[10%] w-[500px] h-[500px] rounded-full bg-violet-900/10 blur-3xl"></div>
			<div class="absolute top-[20%] -left-[10%] w-[400px] h-[400px] rounded-full bg-indigo-900/10 blur-3xl"></div>
		</div>

		<!-- Messages -->
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div bind:this={chatContainer} onclick={handleChatClick} class="flex-1 overflow-y-auto p-6 space-y-6 z-10">
			{#if messages.length === 0 && !loading}
				<div class="flex h-full items-center justify-center text-gray-500 flex-col">
					<div class="p-6 rounded-full bg-gray-900/50 border border-white/5 mb-4">
						<svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-violet-500/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
						</svg>
					</div>
					<p class="font-medium">Select a session or start a new chat</p>
				</div>
			{/if}

			{#each messages as msg}
				<div class="flex {msg.role === 'user' ? 'justify-end' : 'justify-start'}">
					{#if msg.role === 'user'}
						<div class="bg-gradient-to-br from-violet-600 to-indigo-600 text-white rounded-2xl rounded-tr-none p-4 max-w-[85%] text-sm shadow-lg shadow-violet-900/20">
							{msg.text}
						</div>
					{:else}
						<div class="bg-gray-800 text-gray-200 border border-white/5 rounded-2xl rounded-tl-none p-5 max-w-[85%] text-sm shadow-xl markdown-body">
							{@html addPronunciationButtons(renderMarkdown(msg.text))}
						</div>
					{/if}
				</div>
			{/each}

			{#if loading}
				<div class="flex justify-start animate-pulse">
					<div class="bg-gray-800 text-gray-400 rounded-2xl rounded-tl-none p-4 text-sm border border-white/5 flex gap-1">
						<span class="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce"></span>
						<span class="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" style="animation-delay: 0.2s"></span>
						<span class="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" style="animation-delay: 0.4s"></span>
					</div>
				</div>
			{/if}
		</div>

		<!-- Input -->
		<div class="p-6 border-t border-white/5 bg-gray-900/50 backdrop-blur-sm z-10">
			<form
				method="POST"
				action="/chat?/sendMessage"
				use:enhance={handleEnhance}
				class="flex gap-3 max-w-4xl mx-auto"
			>
				<input type="hidden" name="userId" value={userId} />
				{#if currentSessionId}
					<input type="hidden" name="sessionId" value={currentSessionId} />
				{/if}
				<input
					type="text"
					name="message"
					bind:value={inputMessage}
					class="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-5 py-3.5 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 shadow-sm text-white placeholder-gray-500"
					placeholder="Type a message..."
					autocomplete="off"
					disabled={loading}
				/>
				<button type="submit" class="bg-violet-600 text-white px-6 py-2 rounded-xl hover:bg-violet-500 transition-colors font-medium shadow-lg shadow-violet-500/20" disabled={loading}>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
						<path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
					</svg>
				</button>
			</form>
		</div>
	</div>
</main>
