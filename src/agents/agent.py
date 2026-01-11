from google.adk.agents import Agent
from dotenv import load_dotenv

from ._prompts import SYSTEM_PROMPT

load_dotenv()

root_agent = Agent(
    name="root_agent",
    instruction=SYSTEM_PROMPT,
    model="gemini-3-flash-preview",
    tools=[],
)
