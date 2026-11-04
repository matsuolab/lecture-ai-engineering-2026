"""第3回 宿題（発展 a）: 第3回と同じ学習支援エージェントを Google ADK で作り直したもの。

Pydantic AI 版（app/agent.py）との比較が目的。ツール関数は app/tools.py のものを
そのまま再利用する（「docstring + 型ヒントがツール定義になる」点はどちらのフレームワークも同じ）。

実行（リポジトリのルートで。app を import するため PYTHONPATH=. が必要）:
    PYTHONPATH=. adk web lectures/03/work/adk        # ブラウザ UI（http://localhost:8000）
    PYTHONPATH=. adk run lectures/03/work/adk/learning_agent   # ターミナルで対話

API キー: ADK は agent の親フォルダから上に向かって .env を探して自動ロードする
（google/adk/cli/utils/envs.py の load_dotenv_for_agent）。GOOGLE_API_KEY を読む。
"""
from google.adk.agents import Agent

from app import tools

MODEL = "gemini-3.5-flash-lite"

# Pydantic AI 版 app/agent.py の INSTRUCTIONS と同じ文字列
INSTRUCTIONS = """\
あなたはAIエンジニアリング講座（AIE2026）の学習支援エージェントです。
- 用語や講座に固有のことを答える前に、必ず search_glossary で用語集を確認する。
- 回の内容を聞かれたら get_lecture_summary を使う。
- 用語集に見つからないことは、推測で断定せず「用語集にはない」と伝える。
- 回答の最後に、関係する回（第N回）を示す。
- 宿題の答えそのものは書かず、考え方のヒントで導く。
"""

root_agent = Agent(
    name="learning_agent",
    model=MODEL,
    description="AIE2026 の学習支援エージェント（用語集検索・講義要約・確認クイズ）",
    instruction=INSTRUCTIONS,
    tools=[tools.search_glossary, tools.get_lecture_summary, tools.make_quiz],
)
