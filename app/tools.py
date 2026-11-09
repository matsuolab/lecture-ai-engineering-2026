"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
import random
from datetime import datetime
from functools import cache
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
# 第3回 宿題（実装）: 学習の記録の保存先（.gitignore 済み。テストでは一時フォルダに差し替える）
LEARNING_LOG_DIR = ROOT_DIR / "learning_log"
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
    """指定した回（1始まりの整数）で扱う用語から1つを選び、確認問題と答えを返す。

    「第2回の内容から確認問題を出して」「クイズを出して」のように、
    学習の確認のための問題を求められたときに使う。
    返す JSON の answer は、利用者が答えたあとに示す（問題と同時に答えを見せない）。
    """
    candidates = [e for e in load_glossary() if e["lecture"] == lecture]
    if not candidates:
        available = sorted({e["lecture"] for e in load_glossary()})
        return f"第{lecture}回の用語は用語集にありません。用語がある回: {', '.join(map(str, available))}"
    entry = random.choice(candidates)
    return json.dumps(
        {
            "lecture": lecture,
            "term": entry["term"],
            "question": f"「{entry['term']}」の意味は？",
            "answer": entry["definition"],
        },
        ensure_ascii=False,
    )


def save_learning_log(title: str, content: str) -> str:
    """学習の記録を learning_log/ フォルダに Markdown で保存する（その日のファイルに追記する）。

    利用者が「今日学んだことを記録して」「メモを残して」のように、
    学習の記録を保存するよう明示的に頼んだときだけ使う。
    title には記録の見出し（例: "LoRA と QLoRA の違い"）、
    content には残す内容を、利用者の言葉をなるべく生かして入れる。
    保存はファイルへの書き込みなので、実行の前に利用者の承認を求める。
    """
    title = title.strip().replace("\n", " ")
    content = content.strip()
    if not title or not content:
        return "title と content の両方を指定してください。"
    now = datetime.now()
    LEARNING_LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LEARNING_LOG_DIR / f"{now:%Y-%m-%d}.md"
    is_new = not path.exists()
    with open(path, "a", encoding="utf-8") as f:
        if is_new:
            f.write(f"# 学習の記録 {now:%Y-%m-%d}\n")
        f.write(f"\n## {now:%H:%M} {title}\n\n{content}\n")
    return f"保存しました: {LEARNING_LOG_DIR.name}/{path.name}"
