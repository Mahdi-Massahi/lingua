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
export const db = initializeFirestore(app, { experimentalForceLongPolling: true });

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
		const lastDate = new Date(profile.last_active_date);
		const diffDays = Math.floor((Date.now() - lastDate.getTime()) / (1000 * 60 * 60 * 24));
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
