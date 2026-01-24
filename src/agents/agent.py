from datetime import datetime
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents import Agent
from dotenv import load_dotenv
import pytz

from ._prompts import SYSTEM_PROMPT
from ._tools import (
    add_to_vocabulary,
    review_vocabulary,
    update_user_info,
    get_user_info,
    check_vocabulary,
    increment_review_count,
)

load_dotenv()


def update_current_datetime(callback_context: CallbackContext) -> None:
    tz = pytz.timezone("Europe/Berlin")  # Handles CET/CEST automatically
    now = datetime.now(tz)
    formatted_time = now.strftime("%Y-%m-%d (%B) %H:%M:%S %Z%z")
    timestamp = int(now.timestamp())
    result = f"{formatted_time} (timestamp: {timestamp})"
    callback_context.state["current_datetime"] = result


root_agent = Agent(
    name="root_agent",
    instruction=SYSTEM_PROMPT,
    model="gemini-3-flash-preview",
    before_agent_callback=update_current_datetime,
    tools=[
        add_to_vocabulary,
        review_vocabulary,
        update_user_info,
        get_user_info,
        check_vocabulary,
        increment_review_count,
    ],
)
