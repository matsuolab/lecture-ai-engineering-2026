"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
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
    検索結果には related（関連用語）も含まれる。用語同士の違いを答えるときは、
    related に挙がった用語の中から重要なものを1つ選び、その用語でもう一度
    このツールを呼んでから答えること。
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
    その回のねらい・要点を返す。用語がどの回で扱われるか分かったあと、
    その回の内容を踏まえて説明したいときにも使う。
    """
    path = DATA_DIR / "lectures" / f"{lecture:02d}.md"
    if not path.exists():
        available = sorted(p.stem for p in (DATA_DIR / "lectures").glob("*.md"))
        return f"第{lecture}回の要点はまだありません。用意されている回: {', '.join(available)}"
    return path.read_text(encoding="utf-8")


def make_quiz(lecture: int) -> str:
    """指定した回の用語から確認問題を1問作る。

    学習者が理解度を確認したいとき、復習の問題がほしいときに使う。
    指定した回（1始まりの整数）の用語から1つを選び、
    「この用語の意味は？」という問題と、その答えを返す。
    """
    terms = [e for e in load_glossary() if e["lecture"] == lecture]
    if not terms:
        return f"第{lecture}回の用語は用語集にありません。"
    entry = terms[0]
    return json.dumps(
        {"question": f"「{entry['term']}」の意味は？", "answer": entry["definition"]},
        ensure_ascii=False,
    )


LEARNING_LOG_DIR = Path(__file__).resolve().parent.parent / "learning_log"


def save_learning_log(text: str) -> str:
    """学習ログを保存する。

    学習者が学んだことを記録・保存したいと言ったときに使う。
    引数 text には、記録する内容を1文にまとめて渡す。
    保存先は learning_log フォルダの日付ごとのファイルで、1行ずつ追記する。
    このツールは利用者の承認が必要で、承認されたときだけ実際に保存する。
    """
    from datetime import date

    LEARNING_LOG_DIR.mkdir(exist_ok=True)
    log_file = LEARNING_LOG_DIR / f"{date.today().isoformat()}.md"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"- {text}\n")
    return f"学習ログを保存しました（{log_file.name}）。"
