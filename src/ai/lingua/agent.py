import logging
import re
from datetime import datetime

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.load_memory_tool import LoadMemoryTool
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
import pytz

from ._prompts import SYSTEM_PROMPT
from ._tools import (
    add_to_vocabulary,
    find_vocab_by_text,
    review_vocabulary,
    update_user_info,
    get_user_info,
    update_word_mastery,
)

logger = logging.getLogger(__name__)


def update_current_datetime(callback_context: CallbackContext) -> None:
    tz = pytz.timezone("Europe/Berlin")
    now = datetime.now(tz)
    formatted_time = now.strftime("%Y-%m-%d (%B) %H:%M:%S %Z%z")
    timestamp = int(now.timestamp())
    result = f"{formatted_time} (timestamp: {timestamp})"
    callback_context.state["current_datetime"] = result


async def check_and_save_vocab(callback_context: CallbackContext) -> None:
    """
    Scans the agent's response for bolded vocabulary, checks if it exists,
    and adds it if it's new. Also persists session to Memory Bank.
    """
    text = callback_context.session.events[-1].content.parts[-1].text

    # Find bolded words with translation: **word** (translation)
    matches = re.findall(r"\*\*(.*?)\*\*\s*\((.*?)\)", text)
    if matches:
        logger.info("Found %d vocabulary matches in response", len(matches))

        for word, translation in matches:
            word = word.strip(" .,!?;:")
            translation = translation.strip()

            if not word:
                continue

            existing = find_vocab_by_text(word)
            if existing:
                continue

            session_id = callback_context.session.id
            try:
                add_to_vocabulary(
                    session_id,
                    word,
                    translation=translation,
                    context=text[:200],
                    category="auto-saved",
                )
                logger.info("Auto-saved vocab: %s", word)
            except Exception as e:
                logger.error("Error saving vocab '%s': %s", word, e)

    # Persist session to Memory Bank for long-term user memory
    try:
        await callback_context.add_session_to_memory()
    except Exception as e:
        logger.warning("Failed to persist to Memory Bank: %s", e)


root_agent = Agent(
    name="root_agent",
    instruction=SYSTEM_PROMPT,
    model="gemini-2.5-flash",
    before_agent_callback=update_current_datetime,
    after_agent_callback=check_and_save_vocab,
    tools=[
        review_vocabulary,
        update_user_info,
        get_user_info,
        update_word_mastery,
        PreloadMemoryTool(),
        LoadMemoryTool(),
    ],
    output_key="output",
)
