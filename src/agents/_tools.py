import json
import time
from google.adk.tools.tool_context import ToolContext
from .memory.vector_store import VectorStore
from .memory.user_store import UserStore

# Initialize singletons
vector_store = VectorStore()
user_store = UserStore()


def add_to_vocabulary(
    tool_context: ToolContext, text: str, translation: str, context: str, category: str
):
    """
    Saves a new phrase/sentence to the user's vocabulary for future review.

    Args:
        tool_context: The tool context (provided by system).
        text: The text in the target language (e.g., Dutch).
        translation: The English translation.
        context: The surrounding conversation or situation.
        category: A tag like 'formal', 'informal', 'business', 'greeting'.
    """
    session_id = None
    if getattr(tool_context, "session", None):
        session_id = getattr(tool_context.session, "id", None)

    # Store reference
    reference = {"session_id": session_id, "timestamp": time.time()}

    vector_store.add_phrase(text, translation, context, category, reference=reference)
    return f"Saved '{text}' to vocabulary."


def review_vocabulary(topic: str = ""):
    """
    Searches for vocabulary related to a topic to review.

    Args:
        topic: The topic to search for (e.g., 'food', 'greeting').
    """
    if not topic or not topic.strip():
        # Fallback to a generic term if topic is missing to avoid embedding errors
        topic = "common phrases"

    results = vector_store.search_phrases(topic, n_results=3)
    if not results:
        return "No vocabulary found for this topic."

    response = "Here are some phrases to review:\n"
    for item in results:
        meta = item["metadata"]
        response += f"- {item['text']} ({meta.get('translation', 'N/A')})\n"
    return response


def check_vocabulary(text: str):
    """
    Checks if a phrase already exists in the vocabulary.

    Args:
        text: The phrase to check.
    """
    results = vector_store.search_phrases(text, n_results=1)
    if results and results[0]["distance"] < 0.1:
        return f"Found similar phrase: '{results[0]['text']}' (Translation: {results[0]['metadata'].get('translation')})"
    return "Phrase not found."


def update_word_mastery(text: str, was_correct: bool = True):
    """
    Updates the usage statistics for a phrase.
    Increments review count and adjusts score based on correctness.

    Args:
        text: The phrase used.
        was_correct: Whether the user used the phrase correctly.
    """
    # Find the phrase first
    results = vector_store.search_phrases(text, n_results=1)
    if results and results[0]["distance"] < 0.1:
        item = results[0]
        current_score = item["metadata"].get("score", 0.0)

        # Adjust score
        if was_correct:
            new_score = current_score + 0.1
        else:
            # Penalize slightly or keep same?
            # "adjust the score if it was used properly and right"
            # Let's subtract a bit, but floor at 0.
            new_score = max(0.0, current_score - 0.1)

        vector_store.update_review_stats(item["id"], score=new_score)
        status = "correctly" if was_correct else "incorrectly"
        return f"Updated stats for '{item['text']}'. Used {status}."
    else:
        return f"Phrase '{text}' not found."


def update_user_info(key: str, value: str):
    """
    Updates the user's profile information.

    Args:
        key: The attribute to update (e.g., 'name', 'level', 'topic_interest').
        value: The value to set.
    """
    user_store.update_profile(key, value)
    return f"Updated profile: {key} = {value}"


def get_user_info():
    """Retrieves the user's profile."""
    return str(user_store.get_profile())
