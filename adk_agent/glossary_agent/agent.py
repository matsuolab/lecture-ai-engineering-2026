"""第3回 宿題（発展 a）: 演習と同じ指示とツールで、エージェントの組み立てだけを Google ADK で書き直す。

動かす（リポジトリの直下で。GEMINI_API_KEY をそのまま使う）:
    PYTHONPATH=. uv run --with google-adk adk run adk_agent/glossary_agent
    PYTHONPATH=. uv run --with google-adk adk web adk_agent   # ブラウザでツール呼び出しの流れを見る

Pydantic AI 版（app/agent.py）との違い:
- 指示は instruction=、ツールは tools=[関数] で渡す（Pydantic AI は instructions= と agent.tool_plain(関数)）
- モデルは Agent を作るときに名前で決める（Pydantic AI は実行時に run_sync(model=...) で渡す）
- 会話のループ・履歴・入力欄は adk run / adk web が受け持つ（Pydantic AI 版は自分で argparse を書いた）
"""

from google.adk.agents import Agent

from app import tools
from app.agent import INSTRUCTIONS
from app.config import MODEL  # 既定は gemini-3.5-flash-lite。AIE_MODEL で切り替えられるのも演習と同じ

root_agent = Agent(
    model=MODEL,
    name="glossary_agent",
    description="AIE2026 の用語集と各回の要点を使って質問に答える学習支援エージェント",
    instruction=INSTRUCTIONS,
    # 演習で使ったツール。docstring と型ヒントから、モデルに渡すツールの説明が作られる（Pydantic AI と同じ）
    # 承認付きの save_learning_log は対象外（宿題の範囲外）
    tools=[tools.search_glossary, tools.get_lecture_summary, tools.make_quiz],
)
