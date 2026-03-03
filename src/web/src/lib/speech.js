/**
 * Speak text using Google Cloud Text-to-Speech via the /tts endpoint.
 * Falls back to the browser SpeechSynthesis API if the request fails.
 * @param {string} text
 */
export async function speak(text) {
	try {
		const res = await fetch(`/tts?text=${encodeURIComponent(text)}`);
		if (!res.ok) throw new Error('TTS request failed');
		const blob = await res.blob();
		const url = URL.createObjectURL(blob);
		const audio = new Audio(url);
		audio.addEventListener('ended', () => URL.revokeObjectURL(url));
		audio.play();
	} catch {
		// Fallback to browser TTS
		if (!('speechSynthesis' in window)) return;
		const utterance = new SpeechSynthesisUtterance(text);
		utterance.lang = 'nl-NL';
		utterance.rate = 0.9;
		const voices = speechSynthesis.getVoices();
		const dutchVoice = voices.find((v) => v.lang.startsWith('nl'));
		if (dutchVoice) utterance.voice = dutchVoice;
		speechSynthesis.speak(utterance);
	}
}
