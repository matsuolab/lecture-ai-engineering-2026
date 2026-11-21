"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
import random
import sys
from datetime import datetime
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


def make_quiz(lecture: int) -> str:
    """指定した回（1始まりの整数）の用語集から確認問題を1問作り、問題と答えを返す。

    「第2回の確認問題を出して」「第3回の復習クイズをやりたい」のように、
    出題を頼まれたときに使う。返った question を利用者に出題し、answer は
    利用者が答えたあとの採点・解説に使う（先に見せない）。
    """
    terms = [e for e in load_glossary() if e["lecture"] == lecture]
    if not terms:
        available = sorted({e["lecture"] for e in load_glossary()})
        return f"第{lecture}回の用語は用語集にありません。用意されている回: {', '.join(map(str, available))}"
    entry = random.choice(terms)
    return json.dumps(
        {"question": f"「{entry['term']}」の意味は？", "answer": entry["definition"]},
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


# ================ ここから【自分の宿題(第3回)】: 学習記録ツール ================
LEARNING_LOG_DIR = DATA_DIR.parent / "learning_log"


def save_learning_log(title: str, content: str) -> str:
    """学習の記録（今日学んだこと・つまずき・次にやること）を learning_log/ にファイルとして保存する。

    利用者が「今日の学習を記録して」「ログに残して」と頼んだときだけ使う。
    保存は取り消しにくいので、実行前に必ず利用者の承認が入る。
    title は短い題名、content は Markdown の本文。
    """
    if not title.strip() or not content.strip():
        return "title と content の両方が必要です。保存しませんでした。"
    LEARNING_LOG_DIR.mkdir(exist_ok=True)
    # ファイル名は時刻から作る（title をそのまま使うと ../ や記号でフォルダの外に書ける）
    path = LEARNING_LOG_DIR / f"{datetime.now():%Y%m%d-%H%M%S-%f}.md"
    path.write_text(f"# {title.strip()}\n\n{content.strip()}\n", encoding="utf-8")
    return f"保存しました: learning_log/{path.name}"
# ================ ここまで【自分の宿題(第3回)】 ================


# ================ ここから【講座側(第5回)】: 資料検索・目次・グラフ検索ツール ================
def search_materials(query: str) -> str:
    """第1〜3回の本講義資料を検索し、関連ページの本文・タイトル・ページ番号を返す。

    queryに調べたい内容を指定する。
    """
    from google.genai.errors import APIError
    import sqlite3
    from app.retrieval import search_with_neighbors as search

    try:
        results = search(query)
        # 【第5回宿題】モデルへ実際に渡したページを記録する（*は前後ページ）。traceでは本文が見えないため。
        print("[retrieved] " + ", ".join(
            f"{r['lecture']}-p{r['page']}" + ("*" if r.get("role") == "neighbor" else "") for r in results
        ), file=sys.stderr)
        return json.dumps({"results": results}, ensure_ascii=False)
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
# ================ ここまで【講座側(第5回)】 ================
