from google.adk.agents import Agent

from ._prompts import SYSTEM_PROMPT

root_agent = Agent(
    name="root_agent",
    instruction=SYSTEM_PROMPT,
    model="gemini-3-flash-preview",
    tools=[],
)
