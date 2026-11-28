import argparse
import asyncio
import json
from pathlib import Path
from textwrap import shorten

from fastmcp import Client

CONFIG_PATH = Path(__file__).resolve().parents[1] / ".mcp.json"
SEARCH_TOOL_NAMES = {"search_documentation", "aws___search_documentation"}


def print_search_results(text: str) -> None:
    try:
        hits = json.loads(text)["content"]["result"]
    except (json.JSONDecodeError, KeyError, TypeError):
        print(text)
        return

    if not hits:
        print("検索結果はありませんでした。")
        return

    for index, hit in enumerate(hits, start=1):
        excerpt = shorten(hit["context"], width=220, placeholder="…")
        print(f"\n{index}. {hit['title']}")
        print(f"   URL: {hit['url']}")
        print(f"   抜粋: {excerpt}")


async def search(query: str) -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    url = config["mcpServers"]["aws"]["url"]

    async with Client(url) as client:
        tools = await client.list_tools()
        search_tool = next(
            (tool for tool in tools if tool.name in SEARCH_TOOL_NAMES),
            None,
        )
        if search_tool is None:
            raise RuntimeError("AWS MCPのドキュメント検索ツールが見つかりません。")

        result = await client.call_tool(
            search_tool.name,
            {"search_phrase": query, "limit": 2},
        )

    for item in result.content:
        if item.type == "text":
            print_search_results(item.text)


def main() -> None:
    parser = argparse.ArgumentParser(description="AWSの公式ドキュメントを検索")
    parser.add_argument("query", nargs="?", default="Amazon S3 bucket versioning")
    args = parser.parse_args()
    asyncio.run(search(args.query))


if __name__ == "__main__":
    main()