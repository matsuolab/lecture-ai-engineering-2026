"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
import random
from functools import cache
from pathlib import Path

from app.config import api_error_message

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


# ---------------------------------------------------------------- 第6回 宿題（実装）
COURSE_LECTURES = range(1, 14)  # この講座は第1〜13回
MAX_QUIZ_COUNT = 5


class QuizArgumentError(ValueError):
    """make_quiz の引数が範囲外のときのエラー。メッセージは、そのままモデルが読む文にする。"""


def quiz_lectures() -> dict[int, int]:
    """用語集にある回と、その回の用語の数。"""
    counts: dict[int, int] = {}
    for entry in load_glossary():
        counts[entry["lecture"]] = counts.get(entry["lecture"], 0) + 1
    return dict(sorted(counts.items()))


def build_quiz(lecture: int, count: int = 1, rng: random.Random | None = None) -> dict:
    """用語集から、指定した回の用語を count 個選んで問題にする。範囲外なら QuizArgumentError。

    どこが範囲外か・次に何を指定すればよいかが、メッセージだけで分かるようにする。
    """
    available = quiz_lectures()
    choices = "、".join(f"第{n}回（{c}語）" for n, c in available.items())
    if lecture not in COURSE_LECTURES:
        raise QuizArgumentError(
            f"第{lecture}回はこの講座にありません。この講座は第1〜13回です。"
            f"クイズを作れる回: {choices}。")
    if lecture not in available:
        raise QuizArgumentError(
            f"第{lecture}回の用語はまだ用語集にありません。クイズを作れる回: {choices}。")
    if not 1 <= count <= MAX_QUIZ_COUNT:
        raise QuizArgumentError(
            f"問題数 count は1〜{MAX_QUIZ_COUNT}で指定してください（指定された値: {count}）。"
            f"第{lecture}回の用語は{available[lecture]}語あります。")
    terms = [e for e in load_glossary() if e["lecture"] == lecture]
    picked = (rng or random).sample(terms, min(count, len(terms)))
    return {
        "lecture": lecture,
        "quizzes": [{"question": f"「{e['term']}」の意味は？", "answer": e["definition"]} for e in picked],
    }


def make_quiz(lecture: int, count: int = 1) -> str:
    """講座の用語集から、指定した回（1始まりの整数）の確認問題を作り、問題と答えを返す。

    「第2回のクイズを出して」「第3回の確認問題を3問」のように頼まれたときに使う。
    count は問題数（1〜5、省略時は1）。答えはすぐに見せず、まず問題だけを出題すること。
    引数が範囲外のときは、作れる回や指定できる値を説明する文を返す。
    """
    try:
        return json.dumps(build_quiz(lecture, count), ensure_ascii=False)
    except QuizArgumentError as e:
        return f"クイズを作れません: {e}"


def get_lecture_summary(lecture: int) -> str:
    """指定した回（1始まりの整数）の講義の要点を返す。

    「第3回では何を学ぶ？」のように、回の内容や関係を聞かれたときに使う。
    """
    path = DATA_DIR / "lectures" / f"{lecture:02d}.md"
    if not path.exists():
        available = sorted(p.stem for p in (DATA_DIR / "lectures").glob("*.md"))
        return f"第{lecture}回の要点はまだありません。用意されている回: {', '.join(available)}"
    return path.read_text(encoding="utf-8")



LEARNING_LOG_DIR = Path(__file__).resolve().parent.parent / "learning_log"


def save_learning_log(title: str, content: str) -> str:
    """学習メモを learning_log に保存する。ユーザーが保存を求めた場合に使う。

    Args:
        title: 学習メモの見出し。
        content: 保存する学習内容。
    """
    from datetime import datetime, timezone
    from uuid import uuid4

    if not title.strip() or not content.strip():
        raise ValueError("タイトルと本文は空にできません")
    LEARNING_LOG_DIR.mkdir(parents=True, exist_ok=True)
    # モデルにパスを指定させない。既存ファイルも上書きしない。
    name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex + ".md"
    path = LEARNING_LOG_DIR / name
    with path.open("x", encoding="utf-8") as f:
        f.write(f"# {title.strip()}\n\n{content.strip()}\n")
    return f"保存しました: learning_log/{name}"


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


def search_materials_with_neighbors(query: str) -> str:
    """第1〜3回の本講義資料を検索し、関連ページの本文・タイトル・ページ番号を返す。

    queryに調べたい内容を指定する。
    role が hit のページは検索で見つかったページ、neighbor のページはその前後のページ。
    """
    from google.genai.errors import APIError
    import sqlite3
    from app.retrieval import search_with_neighbors

    try:
        return json.dumps({"results": search_with_neighbors(query)}, ensure_ascii=False)
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
