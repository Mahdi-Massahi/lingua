/**
 * ADK agent client — two modes:
 *
 *   ADK_BACKEND=local          → talks to `adk web` on localhost (default)
 *   ADK_BACKEND=agent_engine   → talks to Vertex AI Agent Engine REST API
 */

import { env } from '$env/dynamic/private';

const ADK_BACKEND = env.ADK_BACKEND || 'local';

// ── Local / Cloud Run config ─────────────────────────────────────────────────
const ADK_URL = env.ADK_URL || 'http://localhost:8080';
const ADK_APP_NAME = env.ADK_APP_NAME || 'lingua';

// ── Agent Engine config ──────────────────────────────────────────────────────
const GCP_PROJECT = env.GOOGLE_CLOUD_PROJECT || '';
const GCP_LOCATION = env.GOOGLE_CLOUD_LOCATION || 'europe-west4';
const REASONING_ENGINE_ID = env.REASONING_ENGINE_ID || '';

function isAgentEngine() {
	return ADK_BACKEND === 'agent_engine';
}

// ── Agent Engine helpers (ADC-based auth) ────────────────────────────────────

/** @type {any} */
let authClient = null;

async function getAccessToken() {
	if (!authClient) {
		const { GoogleAuth } = await import('google-auth-library');
		const auth = new GoogleAuth({
			scopes: ['https://www.googleapis.com/auth/cloud-platform']
		});
		authClient = await auth.getClient();
	}
	const { token } = await authClient.getAccessToken();
	return token;
}

function engineBaseUrl() {
	return `https://${GCP_LOCATION}-aiplatform.googleapis.com/v1/projects/${GCP_PROJECT}/locations/${GCP_LOCATION}/reasoningEngines/${REASONING_ENGINE_ID}`;
}

/**
 * @param {string} classMethod
 * @param {Record<string, any>} input
 */
async function queryEngine(classMethod, input) {
	const token = await getAccessToken();
	const res = await fetch(`${engineBaseUrl()}:query`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({ class_method: classMethod, input })
	});
	if (!res.ok) {
		const err = await res.text();
		throw new Error(`Agent Engine ${classMethod} failed (${res.status}): ${err}`);
	}
	return (await res.json()).output;
}

// ── Local / Cloud Run helpers ────────────────────────────────────────────────

/**
 * @param {string} path
 * @param {RequestInit} [init]
 */
async function adkFetch(path, init) {
	const response = await fetch(`${ADK_URL}${path}`, init);
	if (!response.ok) {
		const errorText = await response.text();
		throw new Error(`ADK ${path} failed (${response.status}): ${errorText}`);
	}
	return response;
}

// ── Shared ───────────────────────────────────────────────────────────────────

/**
 * Collect model text from an SSE event stream.
 * @param {string} sseText
 */
function extractTextFromSSE(sseText) {
	let result = '';
	for (const line of sseText.split('\n')) {
		const trimmed = line.trim();
		if (!trimmed) continue;
		const data = trimmed.startsWith('data: ') ? trimmed.substring(6).trim() : trimmed;
		if (!data || data === '[DONE]') continue;
		try {
			const parsed = JSON.parse(data);
			const parts = parsed.content?.parts;
			if (parts) {
				for (const part of parts) {
					if (part.text) result += part.text;
				}
			} else if (typeof parsed.content === 'string') {
				result += parsed.content;
			}
		} catch {
			// skip unparseable SSE lines
		}
	}
	return result;
}

// ── Public API ───────────────────────────────────────────────────────────────

/** @param {string} userId */
export async function createSession(userId) {
	if (isAgentEngine()) {
		const output = await queryEngine('create_session', { user_id: userId });
		return String(output.id);
	}
	const res = await adkFetch(`/apps/${ADK_APP_NAME}/users/${userId}/sessions`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({})
	});
	return String((await res.json()).id);
}

/** @param {string} userId */
export async function listSessions(userId) {
	if (isAgentEngine()) {
		const result = await queryEngine('list_sessions', { user_id: userId });
		// Agent Engine may return { sessions: [...] } or a flat array
		if (Array.isArray(result)) return result;
		if (result?.sessions && Array.isArray(result.sessions)) return result.sessions;
		return [];
	}
	const res = await adkFetch(`/apps/${ADK_APP_NAME}/users/${userId}/sessions`);
	return await res.json();
}

/**
 * @param {string} sessionId
 * @param {string} userId
 */
export async function getSession(sessionId, userId) {
	if (isAgentEngine()) {
		const result = await queryEngine('get_session', { session_id: sessionId, user_id: userId });
		// Agent Engine may return { session: {...} } or the session object directly
		if (result?.session) return result.session;
		return result;
	}
	const res = await adkFetch(`/apps/${ADK_APP_NAME}/users/${userId}/sessions/${sessionId}`);
	return await res.json();
}

/**
 * @param {string} sessionId
 * @param {string} userId
 */
export async function deleteSession(sessionId, userId) {
	if (isAgentEngine()) {
		return await queryEngine('delete_session', { session_id: sessionId, user_id: userId });
	}
	await adkFetch(`/apps/${ADK_APP_NAME}/users/${userId}/sessions/${sessionId}`, {
		method: 'DELETE'
	});
}

/**
 * @param {string} userId
 * @param {string} sessionId
 * @param {string} message
 */
export async function sendMessage(userId, sessionId, message) {
	if (isAgentEngine()) {
		const token = await getAccessToken();
		const res = await fetch(`${engineBaseUrl()}:streamQuery`, {
			method: 'POST',
			headers: {
				Authorization: `Bearer ${token}`,
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				class_method: 'stream_query',
				input: { user_id: userId, session_id: sessionId, message }
			})
		});
		if (!res.ok) {
			const err = await res.text();
			throw new Error(`Stream query failed (${res.status}): ${err}`);
		}
		return extractTextFromSSE(await res.text()) || 'No response received from agent';
	}

	const res = await adkFetch('/run_sse', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({
			app_name: ADK_APP_NAME,
			user_id: userId,
			session_id: sessionId,
			new_message: { role: 'user', parts: [{ text: message }] },
			streaming: false
		})
	});
	return extractTextFromSSE(await res.text()) || 'No response received from agent';
}
