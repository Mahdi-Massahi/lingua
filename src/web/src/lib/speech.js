/**
 * Speak text using the browser's SpeechSynthesis API.
 * @param {string} text
 * @param {string} lang - BCP 47 language tag (default: 'nl-NL')
 */
export function speak(text, lang = 'nl-NL') {
	if (!('speechSynthesis' in window)) return;

	const utterance = new SpeechSynthesisUtterance(text);
	utterance.lang = lang;
	utterance.rate = 0.9;

	// Try to find a Dutch voice
	const voices = speechSynthesis.getVoices();
	const dutchVoice = voices.find((v) => v.lang.startsWith('nl'));
	if (dutchVoice) utterance.voice = dutchVoice;

	speechSynthesis.speak(utterance);
}
