"""第3回 宿題（基礎）: INSTRUCTIONS とツールの docstring を 1 か所ずつ変え、同じ質問で比べる。

使い方（リポジトリの直下で。app を読み込むので -m で実行する。GEMINI_API_KEY が必要）:
    uv run python -m scripts.compare_prompts                 # 全パターン × 全質問（LLM を 15 回前後呼ぶ）
    uv run python -m scripts.compare_prompts --only base no_search_rule
    uv run python -m scripts.compare_prompts --out lectures/03/compare_result.md

app/ のファイルは書き換えない。パターンごとにエージェントを組み立て直し、
指示（instructions）と search_glossary の説明文（description）だけを差し替える。
各実行で、呼ばれたツールと引数（--trace と同じ情報）、LLM の呼び出し回数、回答を表示する。
"""

import argparse
import inspect
import sys
import time

from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ToolCallPart

from app import tools
from app.agent import INSTRUCTIONS, build_model
from app.config import MODEL

SEARCH_RULE = "- 用語や講座に固有のことを答える前に、必ず search_glossary で用語集を確認する。\n"
SEARCH_DOC = inspect.cleandoc(tools.search_glossary.__doc__)
assert SEARCH_RULE in INSTRUCTIONS, "INSTRUCTIONS の検索の行が見つかりません。SEARCH_RULE を合わせてください"
assert "1つだけ" in SEARCH_DOC, "search_glossary の docstring が想定と違います"

# パターン名: (説明, instructions, search_glossary の説明文)。base 以外は 1 か所だけ変える
VARIANTS = {
    "base": ("元のまま", INSTRUCTIONS, SEARCH_DOC),
    "no_search_rule": (
        "INSTRUCTIONS から「必ず search_glossary で用語集を確認する」の行を消す",
        INSTRUCTIONS.replace(SEARCH_RULE, ""),
        SEARCH_DOC,
    ),
    "doc_bulk": (
        "docstring の「用語を1つだけ入れる」を「まとめて入れる」に変える",
        INSTRUCTIONS,
        SEARCH_DOC.replace("1つだけ", "まとめて").replace('（例: "LoRA"）', '（例: "LoRA QLoRA"）'),
    ),
}

QUESTIONS = [
    "LoRAとQLoRAの違いは？",                                  # 用語が 2 つ: 検索の回数と引数を見る
    "AIE2026の講座で使う「lecNN-start タグ」とは何ですか？",  # 講座固有の語: 検索せずに答えると作り話になりやすい
]


def build_agent(instructions: str, search_doc: str) -> Agent:
    target = Agent(instructions=instructions)
    target.tool_plain(description=search_doc)(tools.search_glossary)
    target.tool_plain(tools.get_lecture_summary)
    target.tool_plain(tools.make_quiz)
    return target


def run_once(target: Agent, question: str, model, wait: int):
    for attempt in range(2):
        try:
            return target.run_sync(question, model=model)
        except ModelHTTPError as e:
            if e.status_code == 429 and attempt == 0:
                print(f"  レート制限（429）。{wait} 秒待って 1 回だけ再実行します", file=sys.stderr)
                time.sleep(wait)
                continue
            raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", nargs="+", choices=list(VARIANTS), help="比べるパターン（既定: 全部）")
    parser.add_argument("--sleep", type=int, default=5, help="実行の間に待つ秒数（無料枠のレート制限対策）")
    parser.add_argument("--out", help="結果を Markdown で保存するファイル")
    args = parser.parse_args()

    model = build_model()
    lines = [f"# 第3回 宿題（基礎）比較結果\n\nモデル: `{MODEL}`\n"]
    for name in args.only or list(VARIANTS):
        label, instructions, search_doc = VARIANTS[name]
        target = build_agent(instructions, search_doc)
        lines.append(f"## {name}: {label}\n")
        for question in QUESTIONS:
            result = run_once(target, question, model, wait=60)
            calls = [p for m in result.all_messages() for p in m.parts if isinstance(p, ToolCallPart)]
            lines.append(f"### {question}\n")
            lines.append(f"- ツール呼び出し {len(calls)} 回 / LLM 呼び出し（requests）{result.usage.requests} 回")
            lines += [f"  - `{c.tool_name}({c.args})`" for c in calls] or ["  - （ツールを呼ばずに回答）"]
            lines.append(f"\n回答:\n\n> " + result.output.strip().replace("\n", "\n> ") + "\n")
            print(f"[{name}] {question} -> ツール {len(calls)} 回 / requests {result.usage.requests} 回")
            time.sleep(args.sleep)

    text = "\n".join(lines)
    print("\n" + text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"\n保存しました: {args.out}")


if __name__ == "__main__":
    main()
