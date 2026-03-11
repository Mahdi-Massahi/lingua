<script>
	import { onMount } from 'svelte';
	import { fetchQuizQueue, updateVocabScore } from '$lib/firebase.js';
	import { speak } from '$lib/speech.js';

	/** @type {any[]} */
	let due = $state([]);
	/** @type {any[]} */
	let masteredSample = $state([]);
	let index = $state(0);
	/** @type {'idle' | 'front' | 'back'} */
	let phase = $state('idle');
	let grading = $state(false);
	let loading = $state(false);
	let fetchError = $state('');

	// Deck: starred due first → non-starred due → mastered review cards
	let sortedQueue = $derived([
		...due.filter((i) => i.starred),
		...due.filter((i) => !i.starred),
		...masteredSample
	]);

	let currentCard = $derived(sortedQueue[index] ?? null);
	let isReviewCard = $derived(currentCard ? Math.min(1.0, currentCard.score || 0) >= 0.8 : false);

	async function loadQueue() {
		loading = true;
		fetchError = '';
		const result = await fetchQuizQueue();
		due = result.due;
		masteredSample = result.masteredSample;
		if (result.error) fetchError = result.error;
		loading = false;
	}

	onMount(loadQueue);

	async function startQuiz() {
		await loadQueue();
		if (!fetchError) {
			index = 0;
			phase = 'front';
		}
	}

	function showAnswer() {
		phase = 'back';
	}

	async function grade(delta) {
		if (!currentCard || grading) return;
		grading = true;
		await updateVocabScore(currentCard.id, delta, currentCard);
		grading = false;
		index += 1;
		if (index >= sortedQueue.length) {
			phase = 'idle';
			index = 0;
		} else {
			phase = 'front';
		}
	}

	function masteryPercent(score) {
		return Math.round(Math.min(1.0, score || 0) * 100);
	}
</script>

<main class="flex-1 flex flex-col items-center justify-start bg-gray-950 p-4 md:p-8 relative min-h-0 overflow-y-auto pwa-bottom-bar pwa-safe-x">
	<!-- Background glow -->
	<div class="absolute inset-0 overflow-hidden pointer-events-none">
		<div class="absolute -top-[20%] -right-[10%] w-[500px] h-[500px] rounded-full bg-violet-900/10 blur-3xl"></div>
		<div class="absolute top-[20%] -left-[10%] w-[400px] h-[400px] rounded-full bg-indigo-900/10 blur-3xl"></div>
	</div>

	<div class="w-full max-w-lg z-10">
		<h2 class="text-2xl md:text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-violet-400 to-purple-400 mb-6 text-center">
			Vocabulary Quiz
		</h2>

		{#if loading}
			<div class="flex justify-center mt-16">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-500"></div>
			</div>

		{:else if fetchError}
			<div class="bg-red-900/20 border border-red-800/30 text-red-400 rounded-2xl p-6 text-center text-sm">
				{fetchError}
				<button onclick={loadQueue} class="block mt-3 mx-auto text-violet-400 hover:text-violet-300 underline text-xs">Retry</button>
			</div>

		{:else if phase === 'idle'}
			<!-- Idle / summary screen -->
			<div class="bg-gray-900 border border-white/5 rounded-2xl p-5 sm:p-8 text-center shadow-xl">
				<div class="flex justify-center gap-8 mb-6">
					<div>
						<div class="text-4xl font-bold text-violet-400">{due.length}</div>
						<div class="text-xs text-gray-500 mt-1">due for review</div>
					</div>
					<div class="w-px bg-white/5"></div>
					<div>
						<div class="text-4xl font-bold text-emerald-400">{masteredSample.length}</div>
						<div class="text-xs text-gray-500 mt-1">reviewed (bonus)</div>
					</div>
				</div>
				<div class="text-sm text-gray-500 mb-6">
					{sortedQueue.length === 0
						? 'No vocabulary yet. Chat with the AI to build your word list!'
						: `${sortedQueue.length} cards total`}
				</div>
				<button
					onclick={startQuiz}
					disabled={sortedQueue.length === 0}
					class="bg-gradient-to-r from-violet-600 to-indigo-600 text-white px-8 py-3 rounded-xl hover:from-violet-500 hover:to-indigo-500 transition-all shadow-lg shadow-violet-500/20 font-medium disabled:opacity-40 disabled:cursor-not-allowed"
				>
					Start Review
				</button>
			</div>

		{:else if currentCard}
			<!-- Progress bar -->
			<div class="flex items-center gap-3 mb-4">
				<div class="flex-1 bg-gray-800 rounded-full h-1.5">
					<div
						class="h-1.5 rounded-full transition-all duration-300 {isReviewCard ? 'bg-emerald-500' : 'bg-violet-500'}"
						style="width: {Math.round((index / sortedQueue.length) * 100)}%"
					></div>
				</div>
				<span class="text-xs text-gray-500 shrink-0">{index + 1} / {sortedQueue.length}</span>
			</div>

			<!-- Flashcard -->
			<div class="bg-gray-900 border border-white/5 rounded-2xl shadow-xl overflow-hidden">
				<!-- Card front: Dutch word -->
				<div class="p-5 md:p-8 text-center border-b border-white/5">
					<div class="flex items-center justify-center gap-2 mb-2">
						{#if currentCard.starred}
							<span class="text-yellow-400">★</span>
						{/if}
						{#if isReviewCard}
							<span class="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full">Mastered · refreshing</span>
						{:else}
							<span class="text-xs text-gray-500 uppercase tracking-widest">Dutch</span>
						{/if}
					</div>
					<div class="text-3xl md:text-4xl font-bold text-white mt-2 mb-4">{currentCard.text}</div>
					<button
						onclick={() => speak(currentCard.text)}
						class="inline-flex items-center gap-2 text-violet-400 hover:text-violet-300 bg-violet-500/10 hover:bg-violet-500/20 px-3 py-1.5 rounded-lg text-sm transition-colors"
					>
						<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" />
						</svg>
						Pronounce
					</button>
					<!-- Mastery bar -->
					<div class="mt-4 flex items-center justify-center gap-2">
						<div class="w-24 bg-gray-800 rounded-full h-1">
							<div
								class="h-1 rounded-full transition-all {masteryPercent(currentCard.score) >= 80 ? 'bg-emerald-500' : masteryPercent(currentCard.score) >= 40 ? 'bg-yellow-500' : 'bg-red-500'}"
								style="width: {masteryPercent(currentCard.score)}%"
							></div>
						</div>
						<span class="text-xs text-gray-500">{masteryPercent(currentCard.score)}% mastery</span>
					</div>
				</div>

				{#if phase === 'front'}
					<div class="p-6 text-center">
						<button
							onclick={showAnswer}
							class="bg-gray-800 hover:bg-gray-700 border border-white/5 text-gray-200 px-8 py-3 rounded-xl transition-colors font-medium"
						>
							Show Answer
						</button>
					</div>
				{:else}
					<!-- Card back: translation + context + grade buttons -->
					<div class="p-6">
						<div class="text-center mb-4">
							<div class="text-xs uppercase tracking-widest text-gray-500 mb-1">Translation</div>
							<div class="text-xl font-semibold text-gray-100">{currentCard.translation}</div>
						</div>

						{#if currentCard.context}
							<div class="bg-gray-800/50 border border-white/5 rounded-xl p-3 mb-5 text-xs text-gray-400 italic leading-relaxed">
								"{currentCard.context.slice(0, 200)}{currentCard.context.length > 200 ? '…' : ''}"
							</div>
						{/if}

						<div class="text-xs text-gray-500 text-center mb-3">How did you do?</div>
						<div class="grid grid-cols-3 gap-2">
							<button
								onclick={() => grade(-0.1)}
								disabled={grading}
								class="flex flex-col items-center gap-1 bg-red-900/20 hover:bg-red-900/40 border border-red-800/30 text-red-400 hover:text-red-300 px-3 py-3 rounded-xl transition-colors disabled:opacity-50"
							>
								<span class="text-lg">✗</span>
								<span class="text-xs font-medium">Missed</span>
								<span class="text-xs text-red-600">−10%</span>
							</button>
							<button
								onclick={() => grade(0.05)}
								disabled={grading}
								class="flex flex-col items-center gap-1 bg-yellow-900/20 hover:bg-yellow-900/40 border border-yellow-800/30 text-yellow-400 hover:text-yellow-300 px-3 py-3 rounded-xl transition-colors disabled:opacity-50"
							>
								<span class="text-lg">~</span>
								<span class="text-xs font-medium">Hard</span>
								<span class="text-xs text-yellow-600">+5%</span>
							</button>
							<button
								onclick={() => grade(0.2)}
								disabled={grading}
								class="flex flex-col items-center gap-1 bg-green-900/20 hover:bg-green-900/40 border border-green-800/30 text-green-400 hover:text-green-300 px-3 py-3 rounded-xl transition-colors disabled:opacity-50"
							>
								<span class="text-lg">✓</span>
								<span class="text-xs font-medium">Easy</span>
								<span class="text-xs text-green-600">+20%</span>
							</button>
						</div>
					</div>
				{/if}
			</div>

			<div class="text-center mt-4">
				<button
					onclick={() => { phase = 'idle'; index = 0; }}
					class="text-xs text-gray-600 hover:text-gray-400 transition-colors"
				>
					End session
				</button>
			</div>
		{/if}
	</div>
</main>
