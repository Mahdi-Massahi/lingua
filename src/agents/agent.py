from datetime import datetime
import re
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext
from google.adk.agents import Agent
from dotenv import load_dotenv
import pytz

from ._prompts import SYSTEM_PROMPT
from ._tools import (
    add_to_vocabulary,
    review_vocabulary,
    update_user_info,
    get_user_info,
    update_word_mastery,
    vector_store,
)

load_dotenv()


def update_current_datetime(callback_context: CallbackContext) -> None:
    tz = pytz.timezone("Europe/Berlin")  # Handles CET/CEST automatically
    now = datetime.now(tz)
    formatted_time = now.strftime("%Y-%m-%d (%B) %H:%M:%S %Z%z")
    timestamp = int(now.timestamp())
    result = f"{formatted_time} (timestamp: {timestamp})"
    callback_context.state["current_datetime"] = result


def check_and_save_vocab(callback_context: CallbackContext) -> None:
    """
    Scans the agent's response for bolded vocabulary, checks if it exists,
    and adds it if it's new.
    """
    # Attempt to get the last agent response
    text = callback_context.session.events[-1].content.parts[-1].text

    # Find bolded words with translation: **word** (translation)
    matches = re.findall(r"\*\*(.*?)\*\*\s*\((.*?)\)", text)
    if not matches:
        return

    print("matches", matches)

    for word, translation in matches:
        word = word.strip(" .,!?;:")
        translation = translation.strip()

        if not word:
            continue

        # Exact match check
        results = vector_store.search_phrases(word, n_results=1)
        exists = False
        if results:
            if results[0]["text"].lower() == word.lower():
                exists = True

        if not exists:
            # Construct ToolContext
            session_id = callback_context.session.id

            class MockSession:
                def __init__(self, sid):
                    self.id = sid

            # Add to vocab with extracted metadata
            try:
                add_to_vocabulary(
                    session_id,
                    word,
                    translation=translation,
                    context=text[:200],  # Use part of response as context
                    category="auto-saved",
                )
                print(f"Automatically saved new vocab: {word}")

            except Exception as e:
                print(f"Error saving vocab '{word}': {e}")


root_agent = Agent(
    name="root_agent",
    instruction=SYSTEM_PROMPT,
    model="gemini-3-flash-preview",
    before_agent_callback=update_current_datetime,
    after_agent_callback=check_and_save_vocab,
    tools=[
        review_vocabulary,
        update_user_info,
        get_user_info,
        update_word_mastery,
    ],
    output_key="output",
)
