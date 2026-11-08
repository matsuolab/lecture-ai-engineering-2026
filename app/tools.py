"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
import random
from datetime import datetime
from functools import cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_RESULTS = 3
# 第3回 宿題（実装）: 学習の記録の保存先（.gitignore 済み）
LOG_DIR = Path(__file__).resolve().parent.parent / "learning_log"


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
    """指定した回の用語から 1つを選び、
    確認問題と答えを返す。
    「第2回の確認問題を出して」のように、
    復習用の問題を求められたときに使う。
    """
    # 1. load_glossary() から lecture が一致する用語を集める
    candidates = [e for e in load_glossary() if e["lecture"] == lecture]
    if not candidates:
        available = sorted({e["lecture"] for e in load_glossary()})
        return (
            f"第{lecture}回の用語は用語集にありません。"
            f"用語がある回: {', '.join(str(n) for n in available)}"
        )
    # 2. 1 つ選ぶ（random.choice）
    entry = random.choice(candidates)
    # 3. 問題と答えを文字列で返す（ json.dumps など）
    return json.dumps(
        {"question": f"「{entry['term']}」の意味は？", "answer": entry["definition"]},
        ensure_ascii=False,
    )


def save_learning_log(topic: str, note: str) -> str:
    """学習の記録を learning_log/ フォルダに Markdown で保存する。

    「今日学んだことを記録して」「この内容をメモに残して」のように、
    学習の記録を残すよう頼まれたときに使う。
    topic には記録の題（例: "LoRA"）、note には残す内容を入れる。
    ファイルに書き込む操作なので、実行の前に利用者の承認を得る。
    """
    LOG_DIR.mkdir(exist_ok=True)
    now = datetime.now()
    path = LOG_DIR / f"{now:%Y%m%d_%H%M%S}.md"
    n = 2
    while path.exists():  # 同じ秒に2回保存しても上書きしない
        path = LOG_DIR / f"{now:%Y%m%d_%H%M%S}_{n}.md"
        n += 1
    path.write_text(f"# {topic}\n\n- 日時: {now:%Y-%m-%d %H:%M}\n\n{note}\n", encoding="utf-8")
    return f"学習の記録を保存しました: learning_log/{path.name}"
