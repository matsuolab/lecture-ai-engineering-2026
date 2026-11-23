"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
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


def get_lecture_summary(lecture: int) -> str:
    """指定した回（1始まりの整数）の講義の要点を返す。

    「第3回では何を学ぶ？」のように、回の内容や関係を聞かれたときに使う。
    """
    path = DATA_DIR / "lectures" / f"{lecture:02d}.md"
    if not path.exists():
        available = sorted(p.stem for p in (DATA_DIR / "lectures").glob("*.md"))
        return f"第{lecture}回の要点はまだありません。用意されている回: {', '.join(available)}"
    return path.read_text(encoding="utf-8")


def search_materials(query: str) -> str:
    """第1〜3回の本講義資料を検索し、該当ページと前後ページの本文等を返す。

    queryに調べたい内容を指定する。
    """
    from google.genai.errors import APIError
    import sqlite3
    from app.retrieval import load_pages, search

    try:
        hits = search(query)
        if not hits:
            return json.dumps({"results": []}, ensure_ascii=False)
        pages = load_pages()
        page_indices = {page["page_id"]: i for i, page in enumerate(pages)}
        hit_ids = {hit["page_id"] for hit in hits}
        results, included = [], set()

        for hit in hits:
            page_id = hit["page_id"]
            if page_id not in included:
                results.append({**hit, "context": "match"})
                included.add(page_id)

            index = page_indices.get(page_id)
            if index is None:
                continue
            for neighbor_index, context in (
                (index - 1, "previous"),
                (index + 1, "next"),
            ):
                if not 0 <= neighbor_index < len(pages):
                    continue
                neighbor = pages[neighbor_index]
                if neighbor["document_id"] != pages[index]["document_id"]:
                    continue
                neighbor_id = neighbor["page_id"]
                if neighbor_id in included or neighbor_id in hit_ids:
                    continue
                results.append({**neighbor, "context": context})
                included.add(neighbor_id)

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
