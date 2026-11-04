"""第3回 宿題（発展a）: 同じエージェントを Google ADK で作り直した版。

Pydantic AI 版（app/agent.py）と同じ INSTRUCTIONS・同じ3ツールを持つ。
ツール関数は app/tools.py のものをそのまま渡す（ADK も docstring と型ヒントを
ツール定義として使うため、共有しても同じ説明文がモデルに見える）。

実行方法（リポジトリ直下で）:
    uv run --group adk adk run lectures/03/adk_agent   # CLI で対話
    uv run --group adk adk web lectures/03             # Web UI（トレース可視化）
"""

import sys
from pathlib import Path

from google.adk.agents import Agent

# リポジトリ直下を sys.path に足して app/tools.py を再利用する
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app import tools  # noqa: E402

INSTRUCTIONS = """\
あなたはAIエンジニアリング講座（AIE2026）の学習支援エージェントです。
- 用語や講座に固有のことを答える前に、必ず search_glossary で用語集を確認する。
- 回の内容を聞かれたら get_lecture_summary を使う。
- 確認問題を求められたら make_quiz を使い、答えはすぐに見せず問題だけを出す。
- 用語集に見つからないことは、推測で断定せず「用語集にはない」と伝える。
- 回答の最後に、関係する回（第N回）を示す。
- 宿題の答えそのものは書かず、考え方のヒントで導く。
"""

root_agent = Agent(
    model="gemini-3.5-flash-lite",
    name="learning_support_agent",
    description="AIE2026の講座用語・講義内容を答える学習支援エージェント",
    instruction=INSTRUCTIONS,
    tools=[tools.search_glossary, tools.get_lecture_summary, tools.make_quiz],
)
