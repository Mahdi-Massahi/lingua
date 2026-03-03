import textToSpeech from '@google-cloud/text-to-speech';

const client = new textToSpeech.TextToSpeechClient();

/** @type {import('@sveltejs/kit').RequestHandler} */
export async function GET({ url }) {
	const text = url.searchParams.get('text');
	if (!text) return new Response('Missing text parameter', { status: 400 });

	try {
		const [response] = await client.synthesizeSpeech({
			input: { text },
			voice: { languageCode: 'nl-NL', name: 'nl-NL-Wavenet-B' },
			audioConfig: { audioEncoding: 'MP3', speakingRate: 0.9 }
		});

		return new Response(response.audioContent, {
			headers: {
				'Content-Type': 'audio/mpeg',
				'Cache-Control': 'public, max-age=86400'
			}
		});
	} catch (err) {
		console.error('TTS error:', err);
		return new Response('TTS failed', { status: 500 });
	}
}
