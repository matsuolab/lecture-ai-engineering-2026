"""第3回 発展(a): 演習のエージェントを Google の ADK で組み立て直したもの。

指示（INSTRUCTIONS）とツールは app/ のものをそのまま使い、エージェントを組み立てる部分だけを ADK で書く。

使い方（リポジトリの直下で）:
    PYTHONPATH=. uv run --with google-adk adk run adk_agent/glossary_agent
"""

from google.adk.agents import Agent

from app import tools
from app.agent import INSTRUCTIONS
from app.config import MODEL

# ADK は、関数の名前・docstring・型ヒントから、モデルに渡すツールの説明を自動で作る
root_agent = Agent(
    model=MODEL,
    name="glossary_agent",
    instruction=INSTRUCTIONS,
    tools=[tools.search_glossary, tools.get_lecture_summary, tools.make_quiz],
)
