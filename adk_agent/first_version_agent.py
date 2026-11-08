"""第3回 発展(a): 同じエージェントを Google ADK で組み直した版。

Pydantic AI 版（app/agent.py）と INSTRUCTIONS・ツールはまったく同じものを使い、
違うのは「エージェントを組み立てる部分」だけ。
実行: uv run adk run adk_agent / uv run adk web
"""

import os
import sys
from pathlib import Path

# 元の道具（app/tools.py）を借りられるよう、リポジトリの場所を Python に教える
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ADK は GOOGLE_API_KEY を見るので、講座で使う GEMINI_API_KEY を渡しておく
if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from app import tools
from app.agent import INSTRUCTIONS
from app.config import MODEL

# 保存ツールは ADK でも確認つきにする（付け方はフレームワークで違う）
try:
    save_tool = FunctionTool(func=tools.save_learning_log, require_confirmation=True)
except TypeError:
    save_tool = tools.save_learning_log

root_agent = Agent(
    name="learning_agent_adk",
    model=MODEL,
    description="AIE2026の学習支援エージェント（Google ADK版）",
    instruction=INSTRUCTIONS,
    tools=[
        tools.search_glossary,
        tools.get_lecture_summary,
        tools.make_quiz,
        save_tool,
    ],
)
