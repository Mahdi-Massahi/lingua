import { error } from '@sveltejs/kit';
import {
	createSession,
	listSessions,
	getSession,
	deleteSession,
	sendMessage
} from '$lib/agentEngine.js';

/** @type {import('./$types').PageServerLoad} */
export async function load() {
	return {};
}

/** @type {import('./$types').Actions} */
export const actions = {
	sendMessage: async ({ request }) => {
		const formData = await request.formData();
		const message = formData.get('message');
		let userId = formData.get('userId');
		let sessionId = formData.get('sessionId');

		if (!message) throw error(400, 'Message is required');
		if (!userId) userId = 'default_user';

		try {
			const isNewSession = !sessionId;
			if (isNewSession) {
				sessionId = await createSession(String(userId));
				if (!sessionId) throw new Error('Failed to create session');
			}

			const botResponse = await sendMessage(
				String(userId),
				String(sessionId),
				String(message)
			);

			return {
				success: true,
				botResponse,
				userId: String(userId),
				sessionId: String(sessionId),
				timestamp: new Date().toISOString()
			};
		} catch (err) {
			console.error('Error in sendMessage:', err);
			return { success: false, error: 'Failed to get response from agent' };
		}
	},

	listSessions: async ({ request }) => {
		const formData = await request.formData();
		const userId = formData.get('userId');
		if (!userId) return { success: false, error: 'User ID required' };

		try {
			const sessions = await listSessions(String(userId));
			return { success: true, sessions };
		} catch (err) {
			console.error('Error listing sessions:', err);
			return { success: false, error: 'Failed to list sessions' };
		}
	},

	getSession: async ({ request }) => {
		const formData = await request.formData();
		const sessionId = formData.get('sessionId');
		const userId = formData.get('userId');
		if (!sessionId || !userId) return { success: false, error: 'Session ID and User ID required' };

		try {
			const session = await getSession(String(sessionId), String(userId));
			return { success: true, session };
		} catch (err) {
			console.error('Error getting session:', err);
			return { success: false, error: err instanceof Error ? err.message : 'Failed to get session' };
		}
	},

	deleteSession: async ({ request }) => {
		const formData = await request.formData();
		const sessionId = formData.get('sessionId');
		const userId = formData.get('userId');
		if (!sessionId || !userId) return { success: false, error: 'Session ID and User ID required' };

		try {
			await deleteSession(String(sessionId), String(userId));
			return { success: true };
		} catch (err) {
			console.error('Error deleting session:', err);
			return { success: false, error: 'Failed to delete session' };
		}
	}
};
