"""第3回 発展(a): app/agent.py と同じエージェントを Google ADK で書き直したもの。

依存固定（uv.lock）を崩さないよう google-adk は一時的に追加して動かす:
    cd lectures/03/advanced && PYTHONPATH=../../.. uv run --frozen --with google-adk adk web
"""

from google.adk.agents import Agent

from app import tools
from app.agent import INSTRUCTIONS
from app.config import MODEL

root_agent = Agent(
    name="aie_learning_agent",
    model=MODEL,
    instruction=INSTRUCTIONS,
    tools=[tools.search_glossary, tools.get_lecture_summary, tools.make_quiz],
)
