import argparse
import asyncio
from pydantic_ai import Agent
from app import tools

INSTRUCTIONS = """\
あなたはAIエンジニアリング講座 (AIE2026) の学習支援エージェントです。
- 用語や講座に固有のことを答える前に、必ず search_glossary で用語集を確認する。
- 回の内容を聞かれたら get_lecture_summary を使う。
- 用語集に見つからないことは、推測で断定せず「用語集にはない」と伝える。
- 回答の最後に、関係する回 (第N回) を示す。
- 宿題の答えそのものは書かず、考え方のヒントで導く。
"""

agent = Agent(instructions=INSTRUCTIONS)

agent.tool_plain(tools.search_glossary)
agent.tool_plain(tools.get_lecture_summary)
agent.tool_plain(tools.make_quiz)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="?", default="第3回の確認問題を1問出して")
    parser.add_argument("--list-tools", action="store_true", help="登録されたツールの一覧を表示")
    parser.add_argument("--trace", action="store_true", help="トレースを有効化")
    args = parser.parse_args()

    if args.list_tools:
        print("Registered tools:", list(agent._function_toolset.tools.keys()))
        exit(0)

    async def main():
        result = await agent.run(args.prompt)
        print(result.data)

    asyncio.run(main())
# from pydantic_ai import Agent
# from app import tools

# INSTRUCTIONS = """\
# あなたはAIエンジニアリング講座 (AIE2026) の学習支援エージェントです。
# - 用語や講座に固有のことを答える前に、必ず search_glossary で用語集を確認する。
# - 回の内容を聞かれたら get_lecture_summary を使う。
# - 用語集に見つからないことは、推測で断定せず「用語集にはない」と伝える。
# - 回答の最後に、関係する回 (第N回) を示す。
# - 宿題の答えそのものは書かず、考え方のヒントで導く。
# """

# # モデルは実行時に渡す (テストではAPIを呼ばない TestModel に差し替えるため)
# agent = Agent(instructions=INSTRUCTIONS)

# agent.tool_plain(tools.search_glossary)
# agent.tool_plain(tools.get_lecture_summary)
# agent.tool_plain(tools.make_quiz)