"""ADK 版エージェントのツール呼び出しを確認するスクリプト（app/agent.py の --trace の ADK 相当）。

使い方（リポジトリのルートで。app と learning_agent を import するため PYTHONPATH が必要）:
    PYTHONPATH=.:lectures/03/work/adk python lectures/03/work/adk_trace.py "LoRAとQLoRAの違いは？"

adk web / adk run の裏でも同じ Runner が動いており、開発 UI はこのイベントストリームを
可視化している。ここではそのうちツール呼び出しと使用トークンを表示する。
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

# adk CLI 経由で実行しない場合の保険として、リポジトリのルートの .env を読む
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

from google.adk.runners import InMemoryRunner
from google.genai import types

from learning_agent.agent import MODEL, root_agent


async def main(question: str) -> None:
    print(f"[model] {MODEL}")
    runner = InMemoryRunner(agent=root_agent, app_name="aie2026")
    await runner.session_service.create_session(
        app_name="aie2026", user_id="local", session_id="trace"
    )
    content = types.Content(role="user", parts=[types.Part(text=question)])

    final_text = ""
    usage = None
    async for event in runner.run_async(
        user_id="local", session_id="trace", new_message=content
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if getattr(part, "function_call", None) is not None:
                    fc = part.function_call
                    print(f"[tool call]   {fc.name}({dict(fc.args)})")
                elif getattr(part, "function_response", None) is not None:
                    fr = part.function_response
                    print(f"[tool return] {fr.name} -> {str(fr.response)[:120]}")
                elif part.text:
                    final_text = part.text
        if getattr(event, "usage_metadata", None):
            usage = event.usage_metadata

    print(f"\n{final_text}")
    if usage:
        print(
            f"[usage] prompt={usage.prompt_token_count}, "
            f"output={usage.candidates_token_count}, total={usage.total_token_count}"
        )


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "LoRAとQLoRAの違いは？"))
