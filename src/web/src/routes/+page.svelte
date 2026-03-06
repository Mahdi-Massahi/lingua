<script>
	import { onMount } from 'svelte';
	import { auth, subscribeVocabulary, subscribeProfile, toggleStar } from '$lib/firebase.js';
	import { speak } from '$lib/speech.js';

	let vocabulary = $state([]);
	let profile = $state({});
	let searchQuery = $state('');
	let debounceTimer;

	onMount(() => {
		const unsubVocab = subscribeVocabulary((items) => {
			vocabulary = items;
		});

		const userId = auth.currentUser?.uid || 'default_user';
		const unsubProfile = subscribeProfile(userId, (p) => {
			profile = p;
		});

		return () => {
			unsubVocab();
			unsubProfile();
		};
	});

	function filteredVocab() {
		if (!searchQuery.trim()) return vocabulary;
		const q = searchQuery.toLowerCase();
		return vocabulary.filter(
			(item) =>
				item.text?.toLowerCase().includes(q) ||
				item.translation?.toLowerCase().includes(q) ||
				item.category?.toLowerCase().includes(q)
		);
	}

	function timeAgo(dateString) {
		if (!dateString) return '';
		const diffDays = Math.floor((Date.now() - new Date(dateString).getTime()) / (1000 * 60 * 60 * 24));
		if (diffDays <= 0) return 'Today';
		if (diffDays === 1) return 'Yesterday';
		return `${diffDays} days ago`;
	}

	async function handleToggleStar(id, currentStarred) {
		await toggleStar(id, currentStarred);
	}
</script>

<main class="container mx-auto px-3 sm:px-4 py-6 sm:py-8 flex-1 overflow-y-auto">
	<header class="mb-6 sm:mb-8">
		<h2 class="text-2xl sm:text-3xl font-bold text-white mb-2">Welcome Back</h2>
		<p class="text-gray-400 text-sm sm:text-base">Track your language learning progress</p>
	</header>

	<!-- Activity Streak -->
	<section class="bg-gray-900 border border-white/5 rounded-2xl p-4 sm:p-6 mb-6 sm:mb-8 shiny-border shadow-xl">
		<h2 class="text-xl font-semibold mb-4 text-violet-300">Activity</h2>
		<div class="flex gap-2">
			<div class="bg-gray-800/50 p-2 rounded-lg border border-white/5 shiny-border relative overflow-hidden">
				<span class="block text-[9px] font-bold text-gray-500 uppercase tracking-wider mb-0.5">Streak</span>
				<span class="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-red-500">🔥 {profile.current_streak || 0}</span>
			</div>
			<div class="bg-gray-800/50 p-2 rounded-lg border border-white/5 relative overflow-hidden">
				<span class="block text-[9px] font-bold text-gray-500 uppercase tracking-wider mb-0.5">Max</span>
				<span class="text-lg text-gray-100 font-bold">⚡ {profile.max_streak || 0}</span>
			</div>
		</div>
	</section>

	<!-- Vocabulary -->
	<section class="bg-gray-900 border border-white/5 rounded-2xl p-4 sm:p-6 shiny-border shadow-xl">
		<div class="flex flex-col sm:flex-row justify-between sm:items-center gap-3 sm:gap-0 mb-4 sm:mb-6">
			<h2 class="text-xl font-semibold text-violet-300">Vocabulary List</h2>
			<div class="relative w-full sm:w-64">
				<input
					type="text"
					placeholder="Search vocabulary..."
					bind:value={searchQuery}
					class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 pl-10 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-all text-sm text-white placeholder-gray-500"
				/>
				<svg class="w-4 h-4 absolute left-3 top-3 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
				</svg>
			</div>
		</div>

		<div class="overflow-x-auto rounded-lg border border-white/5">
			<table class="min-w-full table-auto text-left">
				<thead class="bg-gray-800/50 text-gray-400 text-xs uppercase tracking-wider font-semibold">
					<tr>
						<th class="px-3 sm:px-6 py-3 sm:py-4">Phrase</th>
						<th class="px-3 sm:px-6 py-3 sm:py-4">Translation</th>
						<th class="px-6 py-4 hidden sm:table-cell">Category</th>
						<th class="px-6 py-4 hidden sm:table-cell">Added</th>
						<th class="px-6 py-4 hidden sm:table-cell">Stats</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-white/5 text-sm">
					{#each filteredVocab() as item (item.id)}
						<tr class="hover:bg-white/5 transition-colors group">
							<td class="px-3 sm:px-6 py-3 sm:py-4 font-medium text-gray-100">
								<div class="flex items-center gap-2 sm:gap-3">
									<button onclick={() => speak(item.text)} class="text-violet-400 hover:text-white hover:bg-violet-600 p-1.5 rounded-full transition-all shrink-0" title="Play">
										<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
											<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" />
										</svg>
									</button>
									<button
										onclick={() => handleToggleStar(item.id, item.starred)}
										class="{item.starred ? 'text-yellow-400' : 'text-gray-600 group-hover:text-gray-400'} p-1.5 rounded-lg hover:bg-white/10 transition-colors shrink-0"
									>
										<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
											<path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
										</svg>
									</button>
									<span class="text-sm sm:text-base">{item.text}</span>
								</div>
							</td>
							<td class="px-3 sm:px-6 py-3 sm:py-4 text-gray-300 text-sm">{item.translation || '-'}</td>
							<td class="px-6 py-4 hidden sm:table-cell">
								<span class="px-2 py-1 rounded bg-gray-800 border border-gray-700 text-xs text-gray-300">{item.category || 'General'}</span>
							</td>
							<td class="px-6 py-4 text-gray-400 text-sm hidden sm:table-cell">
								<div>{item.created_at ? new Date(item.created_at).toLocaleDateString() : '-'}</div>
								<div class="text-xs text-gray-600">{timeAgo(item.created_at)}</div>
							</td>
							<td class="px-6 py-4 text-sm text-gray-500 hidden sm:table-cell">
								Reviews: <span class="text-gray-300">{item.review_count || 0}</span>
							</td>
						</tr>
					{:else}
						<tr>
							<td colspan="5" class="px-3 sm:px-6 py-6 sm:py-8 text-center text-gray-500 italic text-sm">
								{searchQuery ? 'No matches found.' : 'No vocabulary found yet. Start chatting to learn!'}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</section>
</main>
