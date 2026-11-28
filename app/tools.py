"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
import random
from datetime import datetime
from functools import cache
from pathlib import Path

from app.config import api_error_message

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LOG_DIR = DATA_DIR.parent / "learning_log"
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
    """講座の用語集から、指定した回（1始まりの整数）の確認問題を1問作り、問題と答えを返す。

    「第2回の確認問題を出して」「第3回のクイズを作って」のように、回を指定して
    確認問題やクイズを求められたときに使う。lecture には回の番号だけを入れる（例: 2）。
    返り値に error があるときは、問題は作れていない。その内容をユーザーに伝え、
    available_lectures の中から回を選び直すよう案内する。
    """
    terms = load_glossary()
    available = sorted({e["lecture"] for e in terms})
    if lecture not in available:
        if lecture < 1:
            reason = f"第{lecture}回という回はありません。回は1から始まる整数で指定してください。"
        elif lecture > max(available):
            reason = f"第{lecture}回は、用語集にある範囲（第{min(available)}〜{max(available)}回）を超えています。"
        else:
            reason = f"第{lecture}回の用語は、用語集にまだ登録されていません。"
        return json.dumps(
            {"error": reason, "available_lectures": available,
             "hint": "available_lectures のどれかの回を指定して、もう一度呼んでください。"},
            ensure_ascii=False)
    entry = random.choice([e for e in terms if e["lecture"] == lecture])
    return json.dumps(
        {"lecture": lecture, "question": f"「{entry['term']}」の意味は？", "answer": entry["definition"]},
        ensure_ascii=False)


def save_learning_log(content: str) -> str:
    """学習の記録を learning_log/ フォルダにMarkdownファイルとして保存する。

    「今日学んだことを記録して」「この内容をメモに残して」のように、
    学習の記録の保存を求められたときに使う。content には保存する本文を入れる。
    """
    if not content.strip():
        return "保存する内容が空です。"
    LOG_DIR.mkdir(exist_ok=True)
    path = LOG_DIR / f"{datetime.now():%Y%m%d-%H%M%S}.md"
    path.write_text(content, encoding="utf-8")
    return f"学習の記録を保存しました: learning_log/{path.name}"

def search_materials(query: str) -> str:
    """第1〜3回の本講義資料を検索し、関連ページの本文・タイトル・ページ番号を返す。

    queryに調べたい内容を指定する。
    """
    from google.genai.errors import APIError
    import sqlite3
    from app.retrieval import search

    try:
        return json.dumps({"results": search(query)}, ensure_ascii=False)
    except (ValueError, FileNotFoundError, sqlite3.Error) as e:
        return json.dumps({"error": str(e), "results": []}, ensure_ascii=False)
    except APIError as e:
        return json.dumps({"error": api_error_message(e.code), "results": []}, ensure_ascii=False)


def browse_tree(node_id: str | None = None) -> str:
    """目次とページの先頭文を返す。ページIDを指定すると全文を返す。

    最初はnode_idを省略する。続いて返されたIDを指定して目次をたどる。
    """
    from app.retrieval import browse_tree as browse

    try:
        return json.dumps(browse(node_id), ensure_ascii=False)
    except (ValueError, OSError) as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def search_graph(query: str) -> str:
    """資料を検索し、前後ページ・共通用語をたどって関連ページの本文と引用情報を返す。

    queryに調べたい内容を指定する。
    """
    import sqlite3
    from google.genai.errors import APIError
    from app.retrieval import search_graph as search

    try:
        return json.dumps(search(query), ensure_ascii=False)
    except (ValueError, OSError, sqlite3.Error) as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except APIError as e:
        return json.dumps({"error": api_error_message(e.code)}, ensure_ascii=False)
