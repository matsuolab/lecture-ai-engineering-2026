"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import re
from datetime import datetime
from zoneinfo import ZoneInfo
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
    """指定した会の用語から一つを選び、確認問題と答えを返す。
    「第二回の確認問題を出して」のように言われた時に使う。
    """
    # 1. load_glossary()からlectureが一致する用語集を集める
    terms = [term for term in load_glossary() if term["lecture"] == lecture]
    if not terms:
        return f"第{lecture}回の用語は用語集にありません。"

    # 2. 一つ選ぶ(random.choice)
    term = random.choice(terms)

    # 3. 問題と答えを文字列で返す(json.dumps　など)
    return json.dumps(
        {
            "question": f"「{term['term']}」とは何ですか？",
            "answer": term["definition"],
        },
        ensure_ascii=False,
    )

def save_learning_log(filename: str, content: str) -> str:
    """利用者の学びや気づきを learning_log/ に Markdown で保存する。

    利用者が「学んだ」「わかった」「覚えておいて」など、学習した内容を伝えてきたときに使う。
    保存前に利用者の承認が入る。

    Args:
        filename: トピックを表す短い名前。例: "ツール"。日付と .md は自動で付くので書かない。
        content: Markdown 本文。学んだこと・関係する回を箇条書きでまとめる。
    """

    log_dir = Path("learning_log")
    log_dir.mkdir(exist_ok=True)

    # 日付はモデルに推測させず、コード側で今日の日付を付ける
    # （モデルが日付を付けてきても一度取り除いてから付け直す）
    topic = re.sub(r"^\d{4}-\d{2}-\d{2}_?", "", filename)
    today = datetime.now(ZoneInfo("Asia/Tokyo")).date().isoformat()  # 日本時間の日付
    filename = f"{today}_{topic}"

    # 拡張子がなければ .md を付ける
    if not filename.endswith(".md"):
        filename += ".md"

    save_path = log_dir / filename
    save_path.write_text(content, encoding="utf-8")

    return f"学習記録を {save_path} に保存しました。"
