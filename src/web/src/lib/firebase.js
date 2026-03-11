import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, onAuthStateChanged } from 'firebase/auth';
import {
	initializeFirestore,
	collection,
	doc,
	onSnapshot,
	setDoc,
	query,
	orderBy,
	limit
} from 'firebase/firestore';


// Reads VITE_* vars from web/.env (dev) or build-time env (production)
const firebaseConfig = {
	apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
	authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
	projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
	storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
	messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
	appId: import.meta.env.VITE_FIREBASE_APP_ID
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = initializeFirestore(app, { experimentalAutoDetectLongPolling: true });

const provider = new GoogleAuthProvider();

export async function signIn() {
	return signInWithPopup(auth, provider);
}

export function signOut() {
	return auth.signOut();
}

/**
 * Subscribe to auth state changes.
 * @param {(user: import('firebase/auth').User | null) => void} callback
 */
export function onAuth(callback) {
	return onAuthStateChanged(auth, callback);
}

/**
 * Subscribe to the vocabulary collection (real-time).
 * @param {(items: any[]) => void} callback
 */
export function subscribeVocabulary(callback) {
	const q = query(
		collection(db, 'vocabulary'),
		orderBy('created_at', 'desc'),
		limit(200)
	);
	return onSnapshot(q, (snapshot) => {
		const items = snapshot.docs.map((d) => ({ id: d.id, ...d.data() }));
		callback(items);
	});
}

/**
 * Subscribe to user profile (real-time).
 * @param {string} userId
 * @param {(profile: any) => void} callback
 */
export function subscribeProfile(userId, callback) {
	const docRef = doc(db, 'users', userId);
	return onSnapshot(docRef, (snapshot) => {
		callback(snapshot.exists() ? snapshot.data() : {});
	});
}

/**
 * Toggle star on a vocabulary item.
 * @param {string} vocabId
 * @param {boolean} currentStarred
 */
export async function toggleStar(vocabId, currentStarred) {
	const docRef = doc(db, 'vocabulary', vocabId);
	await setDoc(docRef, { starred: !currentStarred }, { merge: true });
}

/**
 * Fetch a quiz deck: 15 due words + 5 randomly sampled mastered words.
 * Uses a single orderBy query (no composite index required).
 * Falls back gracefully when all words have high scores.
 * @returns {Promise<{ due: any[], masteredSample: any[], error?: string }>}
 */
export async function fetchQuizQueue() {
	try {
		// No orderBy — avoids composite index requirements. Sort client-side instead.
		const q = query(collection(db, 'vocabulary'), limit(100));

		// Use onSnapshot (not getDocs) with a timeout guard.
		// If the connection silently fails (CORS / network), the timeout rejects so loading always ends.
		const snap = await new Promise((resolve, reject) => {
			const timer = setTimeout(() => { unsub(); reject(new Error('Timed out waiting for Firestore')); }, 8000);
			const unsub = onSnapshot(
				q,
				(snapshot) => { clearTimeout(timer); unsub(); resolve(snapshot); },
				(err) => { clearTimeout(timer); reject(err); }
			);
		});

		/** @type {Array<{ id: string, score?: number, [key: string]: any }>} */
		const all = snap.docs
			.map((/** @type {any} */ d) => ({ id: d.id, ...d.data() }))
			.sort((/** @type {any} */ a, /** @type {any} */ b) => (a.score || 0) - (b.score || 0));

		// Split by 0.8 threshold (clamped to handle agent-set scores > 1.0)
		const due = all.filter((i) => Math.min(1.0, i.score || 0) < 0.8);

		// Fallback: if all words have high scores (agent over-scored), use lowest 15 as practice
		const practicePool = due.length > 0 ? due.slice(0, 15) : all.slice(0, 15);
		const practiceIds = new Set(practicePool.map((i) => i.id));

		// Bonus 5: any reviewed word (review_count > 0) not already in the practice pool
		const reviewed = all.filter((i) => (i.review_count || 0) > 0 && !practiceIds.has(i.id));
		const masteredSample = [...reviewed].sort(() => Math.random() - 0.5).slice(0, 5);

		return { due: practicePool, masteredSample };
	} catch (err) {
		console.error('fetchQuizQueue error:', err);
		return { due: [], masteredSample: [], error: 'Failed to load vocabulary. Check your connection.' };
	}
}

/**
 * Update a vocabulary item's score after a quiz result.
 * @param {string} vocabId
 * @param {number} scoreDelta (+0.2 easy, +0.05 hard, -0.1 missed)
 * @param {{ score?: number, review_count?: number }} item current item data
 */
export async function updateVocabScore(vocabId, scoreDelta, item) {
	const docRef = doc(db, 'vocabulary', vocabId);
	await setDoc(docRef, {
		score: Math.max(0, Math.min(1.0, (item.score || 0) + scoreDelta)),
		review_count: (item.review_count || 0) + 1,
		last_review: new Date().toISOString()
	}, { merge: true });
}

/**
 * Save a session title for a user.
 * @param {string} userId
 * @param {string} sessionId
 * @param {string} title
 */
export async function setSessionTitle(userId, sessionId, title) {
	const docRef = doc(db, 'users', userId, 'sessionTitles', sessionId);
	await setDoc(docRef, { title });
}

/**
 * Subscribe to session titles for a user (real-time).
 * @param {string} userId
 * @param {(titles: Record<string, string>) => void} callback
 */
export function subscribeSessionTitles(userId, callback) {
	const colRef = collection(db, 'users', userId, 'sessionTitles');
	return onSnapshot(colRef, (snapshot) => {
		/** @type {Record<string, string>} */
		const map = {};
		snapshot.docs.forEach((d) => { map[d.id] = d.data().title; });
		callback(map);
	});
}

/**
 * Update activity streak in Firestore.
 * @param {string} userId
 * @param {any} profile
 */
export async function updateStreak(userId, profile) {
	const today = new Date().toISOString().split('T')[0];
	if (profile.last_active_date === today) return;

	let currentStreak = profile.current_streak || 0;
	const maxStreak = profile.max_streak || 0;

	if (profile.last_active_date) {
		const msPerDay = 24 * 60 * 60 * 1000;
		const todayMs = new Date(today + 'T00:00:00Z').getTime();
		const lastMs = new Date(profile.last_active_date + 'T00:00:00Z').getTime();
		const diffDays = Math.round((todayMs - lastMs) / msPerDay);
		currentStreak = diffDays === 1 ? currentStreak + 1 : 1;
	} else {
		currentStreak = 1;
	}

	const newMax = Math.max(currentStreak, maxStreak);
	const docRef = doc(db, 'users', userId);
	await setDoc(docRef, {
		last_active_date: today,
		current_streak: currentStreak,
		max_streak: newMax
	}, { merge: true });
}
