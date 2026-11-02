"""第2回 宿題（発展）: 用語集から SFT 用の Q&A データ（JSONL）を作る。

使い方:
    uv run python scripts/make_sft_dataset.py > data/glossary_sft.jsonl
    uv run python scripts/make_sft_dataset.py --eval > data/glossary_eval.jsonl

できたファイルを Colab にアップロードし、LoRA 学習のデータとして使う。
質問の言い回しを増やす、別名でも質問を作る、検証用に一部を分ける、などを工夫してみよう。
"""

import json
import sys
from pathlib import Path

GLOSSARY = Path(__file__).resolve().parent.parent / "data" / "glossary.json"

TEMPLATES = [
    "「{term}」とは何ですか？",
    "{term}について簡単に説明してください。",
    "{term}の意味を教えてください。",
]

EVAL_TEMPLATE = "初めて学ぶ人にも分かるように「{term}」を説明してください。"

# 学習から除外する8用語
HELD_OUT_IDS = {
    "context-window", "rate-limit",
    "qlora", "overfitting",
    "agent-loop", "structured-output",
    "mcp-client", "mcp-transport",
}

# 意味が曖昧になりやすい別名
AMBIGUOUS_ALIASES = {
    "r", "rank", "FT", "env", "instructions",
    "agent", "prefix", "fetch", "transport",
    "429エラー", "指示文", "確認を挟む",
}

# 用語集にない評価用の5用語
EXTRA_EVAL = [
    ("ビームサーチ", "複数の候補列を保持して、確率の高い文章を探索する生成方法。"),
    ("ドロップアウト", "学習時に一部のユニットの出力をランダムに無効化して、過学習を抑える手法。"),
    ("勾配クリッピング", "大きすぎる勾配を制限し、学習を安定させる処理。"),
    ("混同行列", "分類の予測結果と正解の組み合わせごとの件数を整理した表。"),
    ("アテンション機構", "各要素の関連度に応じた重みで、情報を集約する仕組み。"),
]


def main() -> None:
    eval_mode = "--eval" in sys.argv[1:]
    terms = json.loads(GLOSSARY.read_text(encoding="utf-8"))["terms"]

    for t in terms:
        if eval_mode:
            questions = [
                EVAL_TEMPLATE.format(term=t["term"])
            ]
        else:
            if t["id"] in HELD_OUT_IDS:
                continue

            questions = [
                template.format(term=t["term"])
                for template in TEMPLATES
            ]

            # 別名でも質問を生成
            questions += [
                f"「{alias}」とは何ですか？"
                for alias in t.get("aliases", [])
                if alias not in AMBIGUOUS_ALIASES
            ]

        for question in questions:
            record = {
                "messages": [
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": t["definition"]},
                ]
            }

            if eval_mode:
                record["group"] = (
                    "B" if t["id"] in HELD_OUT_IDS else "A"
                )
                record["source"] = "glossary"
                record["term_id"] = t["id"]

            sys.stdout.write(json.dumps(record, ensure_ascii=False) + "\n")

    if eval_mode:
        for term, definition in EXTRA_EVAL:
            record = {
                "messages": [
                    {
                        "role": "user",
                        "content": EVAL_TEMPLATE.format(term=term)
                    },
                    {"role": "assistant", "content": definition},
                ],
                "group": "B",
                "source": "outside_glossary",
                "term_id": term,
            }
            sys.stdout.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()

