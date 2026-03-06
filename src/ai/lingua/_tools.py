import logging
import time
from datetime import datetime
from google.cloud import firestore

logger = logging.getLogger(__name__)

db = firestore.Client(project="lingua-489020")
VOCAB_COLLECTION = "vocabulary"
USERS_COLLECTION = "users"
DEFAULT_USER_ID = "default_user"


def add_to_vocabulary(
    session_id: str,
    text: str,
    translation: str,
    context: str,
    category: str,
):
    """
    Saves a new phrase/sentence to the user's vocabulary for future review.

    Args:
        session_id: The conversation session ID.
        text: The text in the target language (e.g., Dutch).
        translation: The English translation.
        context: The surrounding conversation or situation.
        category: A tag like 'formal', 'informal', 'business', 'greeting'.
    """
    now = datetime.now().isoformat()
    reference = {"session_id": session_id, "timestamp": time.time()}

    doc_data = {
        "text": text,
        "translation": translation,
        "context": context,
        "category": category,
        "language": "dutch",
        "score": 0.0,
        "review_count": 0,
        "starred": False,
        "created_at": now,
        "last_review": now,
        "references": [reference],
    }

    db.collection(VOCAB_COLLECTION).add(doc_data)
    return f"Saved '{text}' to vocabulary."


def review_vocabulary(topic: str = ""):
    """
    Searches for vocabulary related to a topic to review.

    Args:
        topic: The topic to search for (e.g., 'food', 'greeting').
    """
    query = db.collection(VOCAB_COLLECTION)

    if topic and topic.strip():
        # Filter by category if it matches, otherwise return recent items
        category_results = (
            query.where("category", "==", topic.strip().lower())
            .limit(5)
            .get()
        )
        if category_results:
            docs = category_results
        else:
            # Fallback: get recent vocabulary items
            docs = query.order_by("created_at", direction=firestore.Query.DESCENDING).limit(5).get()
    else:
        docs = query.order_by("created_at", direction=firestore.Query.DESCENDING).limit(5).get()

    if not docs:
        return "No vocabulary found for this topic."

    response = "Here are some phrases to review:\n"
    for doc in docs:
        data = doc.to_dict()
        response += f"- {data['text']} ({data.get('translation', 'N/A')})\n"
    return response


def find_vocab_by_text(text: str):
    """Find a vocabulary document by exact text match (case-insensitive)."""
    docs = (
        db.collection(VOCAB_COLLECTION)
        .where("text", "==", text)
        .limit(1)
        .get()
    )
    if docs:
        return docs[0]

    # Try lowercase match
    docs = (
        db.collection(VOCAB_COLLECTION)
        .where("text", "==", text.lower())
        .limit(1)
        .get()
    )
    return docs[0] if docs else None


def update_word_mastery(text: str, was_correct: bool = True):
    """
    Updates the usage statistics for a phrase.
    Increments review count and adjusts score based on correctness.

    Args:
        text: The phrase used.
        was_correct: Whether the user used the phrase correctly.
    """
    doc = find_vocab_by_text(text)
    if not doc:
        return f"Phrase '{text}' not found."

    data = doc.to_dict()
    current_score = data.get("score", 0.0)
    new_score = current_score + 0.1 if was_correct else max(0.0, current_score - 0.1)

    doc.reference.update({
        "score": new_score,
        "review_count": data.get("review_count", 0) + 1,
        "last_review": datetime.now().isoformat(),
    })

    status = "correctly" if was_correct else "incorrectly"
    return f"Updated stats for '{data['text']}'. Used {status}."


def update_user_info(key: str, value: str):
    """
    Updates the user's profile information.

    Args:
        key: The attribute to update (e.g., 'name', 'level', 'topic_interest').
        value: The value to set.
    """
    doc_ref = db.collection(USERS_COLLECTION).document(DEFAULT_USER_ID)
    doc_ref.set({key: value}, merge=True)
    return f"Updated profile: {key} = {value}"


def get_user_info():
    """Retrieves the user's profile."""
    doc = db.collection(USERS_COLLECTION).document(DEFAULT_USER_ID).get()
    if doc.exists:
        return str(doc.to_dict())
    return "No profile data found."
