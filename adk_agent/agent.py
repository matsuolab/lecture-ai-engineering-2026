"""Google ADK版の学習支援エージェント。

起動:
    uv run --extra adk adk web adk_agent
"""

import os

from google.adk.agents import Agent

from app import tools
from app.config import MODEL
from app.prompts import INSTRUCTIONS

if "GOOGLE_API_KEY" not in os.environ and "GEMINI_API_KEY" in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

root_agent = Agent(
    name="aie_learning_agent",
    model=MODEL,
    description="AIE2026の学習支援エージェント",
    instruction=INSTRUCTIONS,
    tools=[tools.search_glossary, tools.get_lecture_summary, tools.make_quiz],
)