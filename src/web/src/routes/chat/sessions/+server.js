import { json } from '@sveltejs/kit';
import { listSessions } from '$lib/agentEngine.js';

export async function GET({ url }) {
	const userId = url.searchParams.get('userId');
	if (!userId) return json({ success: false, error: 'User ID required' }, { status: 400 });

	try {
		const sessions = await listSessions(String(userId));
		return json({ success: true, sessions: sessions || [] });
	} catch (err) {
		console.error('Error listing sessions:', err);
		return json({ success: false, error: 'Failed to list sessions' }, { status: 500 });
	}
}
