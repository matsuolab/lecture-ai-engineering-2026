"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
import random
from datetime import UTC, datetime
from functools import cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LEARNING_LOG_DIR = Path(__file__).resolve().parent.parent / "learning_log"
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
    答える前に使うこと。query には調べたい用語を1つだけ入れる（例: "LoRA"）
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

def make_quize(lecture: int) -> str:
    """ 指定した回の用語から１つを選び、確認問題と答えを返す。

    「第２回の確認問題を出して」のように、復習用の問題を求められたときに使う。
    """
    lecture_terms = [term for term in load_glossary() if term["lecture"] == lecture]
    if not lecture_terms:
        return f"第{lecture}回の用語は用語集にありません。"

    term = random.choice(lecture_terms)
    return json.dumps(
        {
            "question": f"「{term['definition']}」に当てはまる用語は何でしょう？",
            "answer": term["term"],
        },
        ensure_ascii=False,
    )

def save_learning_log(content: str) -> str:
    """学習した内容を記録として保存する。

    ユーザーから学習記録の保存を明示的に頼まれたときに使う。
    content には保存する要点をそのまま入れる。
    """
    if not content.strip():
        return "保存する学習記録が空です。内容を指定してください。"

    filename = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ.md")
    log_path = LEARNING_LOG_DIR / filename
    LEARNING_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return f"学習記録を learning_log/{filename} に保存しました。"