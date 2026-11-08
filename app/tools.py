"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""
import random
import json
from functools import cache
from pathlib import Path
import datetime
from urllib.parse import quote
from pydantic_ai import ModelRetry
from typing import Literal


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
    """指定した回の用語から１つを選び、講義内容に基づき、簡単なクイズを作る。
    返すのは JSON 文字列で、1つの問題を表すオブジェクトの配列。
    各問題オブジェクトには "question"（文字列）と "choices"（文字列の配列）、    "answer"（正解の選択肢のインデックス）が含まれる。
    例: [{"question": "LoRAの意味は？", "choices": ["低ランク適応", "大規模言語モデル", "強化学習"], "answer": 0}]
    """

    #用語集をロード
    all_items = load_glossary()
    #全てのアイテムを取得
    # all_items = glossary.get("terms", [])
    # 指定された回の用語を抽出
    terms_in_lecture = []
    for entry in all_items:
        if entry.get("lecture") == lecture:
            terms_in_lecture.append(entry)
    
    if not terms_in_lecture:
        return json.dumps({"error": f"第{lecture}回の用語が見つかりませんでした。"})

    # 1つ選ぶ
    selected = random.choice(terms_in_lecture)
    
    # 問題と答えを生成
    result = {
        "question": f"「{selected['term']}」の意味は？",
        "answer": selected['definition']
    }
    return json.dumps(result)

# 1. 保存用ディレクトリの定義
LOG_DIR = Path("learning_logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 2. 安全なファイル保存用の内部関数
def _save_log_to_file(log_data: dict) -> str:
    """
    内部用関数。指定されたディレクトリにのみ書き込みを許可する。
    """
    lecture_num = log_data["lecture"]
    today = datetime.datetime.now().strftime("%Y%m%d")
    term = log_data["term"]
    term_filename = quote(term, safe="")
    filename = f"lecture_{lecture_num:02d}_term_{term_filename}_{today}.json"

    log_dir = LOG_DIR.resolve()
    file_path = (log_dir / filename).resolve()

    if not file_path.is_relative_to(log_dir):
        raise ValueError("ログ保存先が許可されたディレクトリの外です。")

    log_dir.mkdir(parents=True, exist_ok=True)
    
    # セキュリティチェック：LOG_DIR 配下か確認
    if not str(file_path).startswith(str(LOG_DIR.resolve())):
        return "エラー：安全のため、指定されたディレクトリ以外への保存は拒否されました。"

    # 書き込み処理
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    return f"ログを保存しました：{log_data['term']} (理解度: {log_data['understanding']})"

# 3. 学習ログ保存ツール

def save_learning_log(
    lecture: int,
    term: str,
    understanding: Literal["high", "medium", "low"],
    next_action: str,
) -> str:
    """確認済みの講義回、用語、理解度、次のアクションを保存する。"""

    if lecture < 1:
        raise ModelRetry("講義回は1以上の整数を指定してください。")
    if not term.strip():
        raise ModelRetry("用語を入力してください。")
    if understanding not in {"high", "medium", "low"}:
        raise ModelRetry("理解度は high / medium / low のいずれかを指定してください。")
    if not next_action.strip():
        raise ModelRetry("次のアクションを入力してください。")

    return _save_log_to_file({
        "lecture": lecture,
        "term": term.strip(),
        "understanding": understanding,
        "next_action": next_action.strip(),
    })


# 4. 復習用ツール

def get_pending_topics() -> str:
    """
    過去の学習ログから、まだ理解が不十分（low）な項目を抽出します。
    次の学習の指針として使います。
    """
    pending_items = []
    
    # 指定したディレクトリ内のjsonファイルをすべて走査
    if LOG_DIR.exists():
        for file_path in LOG_DIR.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("understanding") == "low":
                        pending_items.append(data.get("term"))
            except Exception:
                continue
    
    if not pending_items:
        return "すべての項目をマスターしました！新しい内容に進みましょう。"
    
    return f"まだ復習が必要な項目は以下です: {', '.join(set(pending_items))}"