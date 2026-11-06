from google.adk.agents import Agent
from app import tools
from app.agent import INSTRUCTIONS

root_agent = Agent(
    model="gemini-3.5-flash-lite",
    name="glossary_agent",
    instruction=INSTRUCTIONS,
    tools=[tools.get_lecture_summary, tools.make_quiz,
           tools.search_glossary, tools.save_learning_log],
)
