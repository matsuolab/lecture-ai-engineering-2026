from google.adk.agents import Agent
from app.tools import search_glossary, get_lecture_summary, make_quize
from app.agent import INSTRUCTIONS
root_agent = Agent(
    model="gemini-3.5-flash-lite",
    name="glossary_agent",
    instruction=INSTRUCTIONS,
    tools=[search_glossary, get_lecture_summary, make_quize], # 演習で使ったツール
)