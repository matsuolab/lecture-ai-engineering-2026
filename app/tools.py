"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
import random

from datetime import datetime   # 日時を扱う部品（ファイル名の日付用）
from pathlib import Path        # ファイルパスを扱う部品（learning_log/ フォルダ用）

from functools import cache


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_RESULTS = 3

LEARNING_LOG_DIR = Path(__file__).resolve().parent.parent / "learning_log"


@cache
def load_glossary() -> list[dict]:
    with open(DATA_DIR / "glossary.json", encoding="utf-8") as f:
        return json.load(f)["terms"]


def _normalize(text: str) -> str:
    return text.casefold().replace(" ", "").replace("　", "")


def _names(entry: dict) -> list[str]:
    return [_normalize(entry["term"]), _normalize(entry["id"])] + [
        _normalize(a) for a in entry["aliases"]
    ]


def search_glossary(query: str) -> str:
    """講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。

    AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
    答える前に使うこと。query には調べたい用語を1つだけ入れる（例: “LoRA”）。
    """
    q = _normalize(query)
    if not q:
        return "検索語が空です。調べたい用語を1つ指定してください。"
    glossary = load_glossary()

    exact = [e for e in glossary if q in _names(e)]
    # 「r」のような短い別名が何にでも当たらないよう、名前側が短いものは除く
    partial = [
        e for e in glossary
        if e not in exact and any(q in n or (len(n) >= 3 and n in q) for n in _names(e))
    ]
    in_definition = [
        e for e in glossary
        if e not in exact and e not in partial and q in _normalize(e["definition"])
    ]
    hits = (exact + partial + in_definition)[:MAX_RESULTS]

    if not hits:
        return f"用語集に「{query}」は見つかりませんでした。"
    return json.dumps(
        [
            {
                "term": e["term"],
                "lecture": e["lecture"],
                "definition": e["definition"],
                "related": e["related"],
            }
            for e in hits
        ],
        ensure_ascii=False,
    )


def get_lecture_summary(lecture: int) -> str:
    """指定した回（1始まりの整数）の講義の要点を返す。

    「第3回では何を学ぶ？」のように、回の内容や関係を聞かれたときに使う。
    """
    path = DATA_DIR / "lectures" / f"{lecture:02d}.md"
    if not path.exists():
        available = sorted(p.stem for p in (DATA_DIR / "lectures").glob("*.md"))
        return f"第{lecture}回の要点はまだありません。用意されている回: {', '.join(available)}"
    return path.read_text(encoding="utf-8")

def make_quiz(lecture: int) -> str:
    """指定した回の用語から1つを選び、確認問題と答えを返す。

    「第2回の確認問題を出して」のように、復習用の問題を求められたときに使う。
    lecture には回の番号（1始まりの整数）を入れる。
    """
    # 1. load_glossary() から lecture が一致する用語を集める
    terms = [e for e in load_glossary() if e["lecture"] == lecture]
    if not terms:
        return f"第{lecture}回の用語は用語集にありません。別の回を指定してください。"

    # 2. 1つ選ぶ
    entry = random.choice(terms)

    # 3. 問題と答えを文字列で返す
    return json.dumps(
        {
            "question": f"「{entry['term']}」の意味は？",
            "answer": entry["definition"],
            "lecture": entry["lecture"],
        },
        ensure_ascii=False,
    )

def save_learning_log(title: str, content: str) -> str:
    """学習の記録を learning_log/ フォルダに Markdown ファイルとして保存する。

    利用者が「記録して」「メモを保存して」「学習ログに残して」と頼んだときに使う。
    承認は呼び出し側のプログラムが自動で求めるので、ツールを呼ぶ前に利用者へ確認する必要はない。
    記録を頼まれたら、内容を組み立ててすぐにこのツールを呼ぶ。

    Args:
        title: 記録の見出し（例: "第3回 Pydantic AI のツール"）。
        content: 記録する本文。学んだこと・気づきを Markdown で書く。見出し行（# で始まる行）はツール側で title から付けるので、本文には含めない。

    Returns:
        保存したファイルのパス。
    """
    LEARNING_LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = LEARNING_LOG_DIR / f"{stamp}.md"
    path.write_text(f"# {title}\n\n{content}\n", encoding="utf-8")
    return f"保存しました: {path.relative_to(LEARNING_LOG_DIR.parent)}"