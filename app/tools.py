"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
import random
from datetime import datetime, timezone
from functools import cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ROOT_DIR = Path(__file__).resolve().parent.parent
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
    """指定された講義回で出現する用語に関する問題文(question)を作成する。

    「第N回(Nは1始まりの整数)の確認問題を出して」と頼まれたときに、確認問題と答えを返す。
    ただし、Nは1始まりの整数。確認問題を作成したら、必ず save_learning_log(question=<このquestion>, answer=<このanswer>) を実行する。
    question と answer はこの戻り値の値そのものを使い、自然言語での保存確認を行わず、
    保存の承認は save_learning_log() の approval フローで行う。
    """
    if lecture < 1:
        return json.dumps({"error": "講義回は1以上の整数で指定してください。"}, ensure_ascii=False)

    glossary = load_glossary()
    candidates = [entry for entry in glossary if entry.get("lecture") == lecture]
    if not candidates:
        return json.dumps({"error": f"第{lecture}回に対応する用語は見つかりませんでした。"}, ensure_ascii=False)

    selected = random.choice(candidates)
    question = f"「{selected['term']}」の意味は?"
    return json.dumps({"question": question, "answer": selected["definition"]}, ensure_ascii=False)


def save_learning_log(question: str, answer: str) -> str:
    """学習の記録を learning_log/ フォルダに JSON 形式で保存する。

    このツールは、make_quiz() が返した ``question`` と ``answer`` を保存するときに必ず使う。
    次の呼び出し形式を守る: ``save_learning_log(question=..., answer=...)``。問題と解答は必ず文字列のまま渡す。
    学習の記録を残す判断は利用者に委ねるが、実際の保存は必ずこのツールの承認フローを通す。
    取り消しにくい保存操作なので、呼び出し前に利用者の承認を得る必要がある。
    学習内容は ``question`` と ``answer`` をそのまま ``{"question": ..., "answer": ...}`` の形式で保存する。
    """
    question = question.strip()
    answer = answer.strip()
    if not question:
        return "保存する質問が空です。"
    if not answer:
        return "保存する回答が空です。"

    LEARNING_LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    file_path = LEARNING_LOG_DIR / f"learning_log_{timestamp}.json"
    payload = {"question": question, "answer": answer}
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return f"学習の記録を {file_path.relative_to(ROOT_DIR)} に保存しました。"
