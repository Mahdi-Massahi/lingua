import { json } from '@sveltejs/kit';
import { getSession } from '$lib/agentEngine.js';

export async function GET({ url }) {
	const sessionId = url.searchParams.get('sessionId');
	const userId = url.searchParams.get('userId');
	if (!sessionId || !userId) return json({ success: false, error: 'Session ID and User ID required' }, { status: 400 });

	try {
		const session = await getSession(String(sessionId), String(userId));
		return json({ success: true, session });
	} catch (err) {
		console.error('Error getting session:', err);
		return json({ success: false, error: err instanceof Error ? err.message : 'Failed to get session' }, { status: 500 });
	}
}
