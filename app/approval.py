"""承認が必要なツールを対話的に実行する CLI。"""

import argparse
import asyncio

from pydantic_ai import Agent, DeferredToolRequests
from pydantic_ai.exceptions import ModelHTTPError

from app.agent import agent, build_model
from app.config import MODEL, api_error_message
print("approval.py が読み込まれました")

async def run_approval_cli(
    user_input: str,
    target: Agent | None = None,
    model=None,
) -> object:
    """承認待ちのツールを確認しながらエージェントを再開する。"""
    target = target or agent
    model = model or build_model()
    result = await target.run(user_input, model=model)
    history = result.all_messages()

    while isinstance(result.output, DeferredToolRequests):
        approvals: dict[str, bool] = {}

        for approval in result.output.approvals:
            print(f"ツール {approval.tool_name} を実行します。")
            print(f"引数: {approval.args}")

            answer = input("保存してよいですか？ [y/N]: ").strip().lower()
            approvals[approval.tool_call_id] = answer in ("y", "yes")

        deferred_results = result.output.build_results(approvals=approvals)
        result = await target.run(
            model=model,
            message_history=history,
            deferred_tool_results=deferred_results,
        )
        history = result.all_messages()

    return result.output


async def async_main() -> None:
    parser = argparse.ArgumentParser(
        description="承認機構付きの学習支援エージェントに質問する"
    )
    parser.add_argument("question", nargs="?", help="エージェントへの質問")
    args = parser.parse_args()

    if not args.question:
        parser.error("質問を指定してください")

    print(f"[model] {MODEL}")
    try:
        output = await run_approval_cli(args.question)
    except ModelHTTPError as e:
        print(api_error_message(e.status_code, str(e.body)[:200]))
        raise SystemExit(1) from e

    print(output)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
