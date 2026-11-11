from google.adk.agents import Agent        # ADK の Agent クラスを使う
from app import tools                      # 演習で作った関数たち（そのまま流用）
from app.agent import INSTRUCTIONS         # 演習の指示文（そのまま流用）

root_agent = Agent(
    model="gemini-3.5-flash-lite",         # 頭脳
    name="glossary_agent",                 # ADK ではエージェントに名前が必須
    instruction=INSTRUCTIONS,              # 指示
    tools=[tools.search_glossary,          # 道具を関数のまま並べるだけ
           tools.get_lecture_summary,
           tools.make_quiz],
)