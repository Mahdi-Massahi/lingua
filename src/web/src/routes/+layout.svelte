<script>
	import '../app.css';
	import { onMount } from 'svelte';
	import { onAuth, signIn, signOut } from '$lib/firebase.js';
	import { page } from '$app/state';
	import { ui } from '$lib/ui.svelte.js';

	let { children } = $props();
	let user = $state(null);
	let loading = $state(true);

	onMount(() => {
		return onAuth((u) => {
			user = u;
			loading = false;
		});
	});

	function isActive(path) {
		return page.url.pathname === path;
	}
</script>

{#if loading}
	<div class="flex h-full items-center justify-center">
		<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-500"></div>
	</div>
{:else if !user}
	<div class="flex h-screen items-center justify-center flex-col gap-6">
		<h1 class="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-violet-400 to-purple-400">
			Lingua
		</h1>
		<p class="text-gray-400">AI-powered language tutor</p>
		<button
			onclick={signIn}
			class="bg-gradient-to-r from-violet-600 to-indigo-600 text-white px-6 py-3 rounded-xl hover:from-violet-500 hover:to-indigo-500 transition-all shadow-lg shadow-violet-500/20 font-medium"
		>
			Sign in with Google
		</button>
	</div>
{:else}
	<nav class="bg-gray-900/80 backdrop-blur-md border-b border-white/5 sticky top-0 z-50 pwa-nav pwa-safe-x">
		<div class="container mx-auto px-2 sm:px-4 py-2 sm:py-3 flex justify-between items-center">
			<div class="flex items-center gap-1">
				{#if isActive('/chat')}
					<button onclick={() => ui.sidebarOpen = true} class="md:hidden text-gray-400 hover:text-white p-1.5 rounded-lg" aria-label="Open sessions">
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
						</svg>
					</button>
				{/if}
				<h1 class="text-lg sm:text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-violet-400 to-purple-400">
					Lingua
				</h1>
			</div>
			<div class="flex items-center gap-2 sm:gap-4">
				<div class="space-x-1 bg-gray-800/50 p-1 rounded-lg border border-white/5">
					<a
						href="/"
						class="px-3 sm:px-4 py-1.5 rounded-md text-xs sm:text-sm font-medium transition-all {isActive('/') ? 'bg-violet-600 text-white shadow-lg shadow-violet-500/20' : 'text-gray-400 hover:text-white'}"
					>Dashboard</a>
					<a
						href="/chat"
						class="px-3 sm:px-4 py-1.5 rounded-md text-xs sm:text-sm font-medium transition-all {isActive('/chat') ? 'bg-violet-600 text-white shadow-lg shadow-violet-500/20' : 'text-gray-400 hover:text-white'}"
					>Chat</a>
					<a
						href="/quiz"
						class="px-3 sm:px-4 py-1.5 rounded-md text-xs sm:text-sm font-medium transition-all {isActive('/quiz') ? 'bg-violet-600 text-white shadow-lg shadow-violet-500/20' : 'text-gray-400 hover:text-white'}"
					>Quiz</a>
				</div>
				<button onclick={signOut} class="text-xs text-gray-500 hover:text-gray-300 transition-colors hidden sm:block">
					Sign out
				</button>
			</div>
		</div>
	</nav>
	{@render children()}
{/if}
