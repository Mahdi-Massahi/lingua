from google.adk.agents import Agent
from dotenv import load_dotenv

from ._prompts import SYSTEM_PROMPT
from ._tools import (
    add_to_vocabulary,
    review_vocabulary,
    speak_text,
    update_user_info,
    get_user_info,
    check_vocabulary,
    increment_review_count,
)

load_dotenv()

root_agent = Agent(
    name="root_agent",
    instruction=SYSTEM_PROMPT,
    model="gemini-3-flash-preview",
    tools=[
        add_to_vocabulary,
        review_vocabulary,
        speak_text,
        update_user_info,
        get_user_info,
        check_vocabulary,
        increment_review_count,
    ],
)
