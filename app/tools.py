"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
import random
from functools import cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_RESULTS = 3


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


# 変更後（実験用）

def search_glossary(query: str) -> str:
    """講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。

    AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
    答える前に使うこと。query には調べたい用語を1つだけ入れる（例: "LoRA"）。
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
    """指定した回の用語から1つ選び、確認問題と答えを返す。
    「第2回の確認問題を出して」のように、復習用の問題を求められたときに使う。
    """
    # 1. 用語集データをロードする
    glossary = load_glossary()

    # 2. 指定された回（lecture）に一致する用語を抽出する
    filtered_items = [
        item for item in glossary if item.get("lecture") == lecture
    ]

    # 指定された回の用語が見つからない場合の処理
    if not filtered_items:
        return json.dumps(
            {
                "error": f"第{lecture}回の用語が見つかりませんでした。"
            },
            ensure_ascii=False,
        )

    # 3. 対象の用語からランダムに1つ選択する
    selected_item = random.choice(filtered_items)

    # 4. 問題と答えの形式を作成してJSON文字列で返す
    quiz_data = {
        "question": f"「{selected_item['term']}」の意味は？",
        "answer": selected_item["definition"],
    }

    return json.dumps(quiz_data, ensure_ascii=False)

import os

def save_learning_log(content: str, filename: str = "log.txt") -> str:
    """学習記録を learning_log ディレクトリ内のファイルに保存する。

    ユーザーから学習内容の記録や保存を求められたときに使う。
    content には保存する本文、filename には保存先のファイル名を指定する。
    """
    os.makedirs("learning_log", exist_ok=True)
    filepath = os.path.join("learning_log", filename)
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(content + "\n---\n")
    return f"学習記録を {filepath} に保存しました。"