"""第2回 宿題（発展）: 用語集を検索する仕組みを、LoRA 学習と同じ 30 問・同じ基準で評価する。

使い方:
    uv run python lectures/02/advanced/glossary_search.py

検索は 2 段階で、LLM は使わない。
    1. 質問に用語名か別名が含まれていれば、最も長く一致した語の定義を返す
    2. 無ければ文字 2-gram の一致度（IDF で重み付け）で定義を探し、しきい値未満なら「記載なし」を返す
"""

import json
import math
import re
import time
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

HERE = Path(__file__).resolve().parent
GLOSSARY = HERE.parents[2] / "data" / "glossary.json"
EVAL = HERE / "glossary_eval.json"
OUTPUT = HERE / "eval_search.json"

THRESHOLD = 0.5  # 評価結果を見る前に決めた値。他の値の結果は感度分析として併記する
SENSITIVITY = [0.3, 0.4, 0.5, 0.6, 0.7]
NOT_FOUND = "この用語集には記載がありません。"


def bigrams(text: str) -> set[str]:
    chars = re.sub(r"[\s、。？！?!「」『』（）()・:：]", "", text.lower())
    return {chars[i : i + 2] for i in range(len(chars) - 1)}


def contains_name(question: str, name: str) -> bool:
    # 英数字の語は語の途中で一致させない（別名の r が RAG に、LoRA が QLoRA に一致するのを防ぐ）
    pattern = re.escape(name.lower())
    if name[0].isascii() and name[0].isalnum():
        pattern = r"(?<![a-z0-9])" + pattern
    if name[-1].isascii() and name[-1].isalnum():
        pattern += r"(?![a-z0-9])"
    return re.search(pattern, question.lower()) is not None


class GlossarySearch:
    def __init__(self, terms: list[dict]):
        self.terms = terms
        self.names = []
        for t in terms:
            base = re.sub(r"（.*?）", "", t["term"])  # 「LLM（大規模言語モデル）」は「LLM」でも引けるようにする
            for name in {t["term"], base, *t["aliases"]}:
                self.names.append((name, t))
        self.docs = [bigrams(" ".join([t["term"], *t["aliases"], t["definition"]])) for t in terms]
        df = Counter(gram for doc in self.docs for gram in doc)
        self.idf = {gram: math.log((len(terms) + 1) / (count + 1)) + 1 for gram, count in df.items()}

    def by_name(self, question: str) -> dict | None:
        hits = [(name, t) for name, t in self.names if contains_name(question, name)]
        return max(hits, key=lambda hit: len(hit[0]))[1] if hits else None

    def by_similarity(self, question: str) -> tuple[dict, float]:
        grams = bigrams(question)
        # 用語集に無い 2-gram にも重みを与え、質問の大半が用語集に無いときに一致度が下がるようにする
        weight = {gram: self.idf.get(gram, math.log(len(self.terms) + 1) + 1) for gram in grams}
        total = sum(weight.values()) or 1.0
        scores = [sum(weight[g] for g in grams & doc) / total for doc in self.docs]
        best = max(range(len(scores)), key=scores.__getitem__)
        return self.terms[best], scores[best]

    def search(self, question: str, threshold: float = THRESHOLD) -> dict:
        term = self.by_name(question)
        if term:
            return {"answer": term["definition"], "matched_term": term["term"], "method": "name", "score": 1.0}
        term, score = self.by_similarity(question)
        if score >= threshold:
            return {"answer": term["definition"], "matched_term": term["term"], "method": "similarity", "score": round(score, 3)}
        return {"answer": NOT_FOUND, "matched_term": None, "method": "not_found", "score": round(score, 3)}


def score(q: dict, raw: str, refusal_markers: list[str], definitions: dict[str, str]) -> dict:
    """lora_glossary_tuning.ipynb の score と同じ基準で採点する"""
    refused = any(marker in raw for marker in refusal_markers)
    if q["type"] == "unknown":
        return {"ok": refused, "refused": refused, "similarity": None}
    ok = all(word in raw for word in q["must_include"]) and not refused
    return {"ok": ok, "refused": refused, "similarity": round(SequenceMatcher(None, raw, definitions[q["term"]], autojunk=False).ratio(), 3)}


def rate(rows: list[dict]) -> float:
    return round(sum(r["ok"] for r in rows) / len(rows), 3)


def evaluate(engine: GlossarySearch, questions: list[dict], markers: list[str], threshold: float) -> tuple[dict, list[dict]]:
    definitions = {t["term"]: t["definition"] for t in engine.terms}
    rows = []
    t0 = time.perf_counter()
    for q in questions:
        hit = engine.search(q["question"], threshold)
        rows.append({"type": q["type"], "term": q["term"], "question": q["question"], "raw": hit["answer"],
                     "matched_term": hit["matched_term"], "method": hit["method"], "search_score": hit["score"],
                     **score(q, hit["answer"], markers, definitions)})
    seconds = time.perf_counter() - t0
    by_type = {t: [r for r in rows if r["type"] == t] for t in ("known", "paraphrase", "unknown")}
    answerable = by_type["known"] + by_type["paraphrase"]
    summary = {"label": f"search_t{threshold}", "n": len(rows), "all_rate": rate(rows),
               "known_rate": rate(by_type["known"]), "paraphrase_rate": rate(by_type["paraphrase"]), "unknown_rate": rate(by_type["unknown"]),
               "refused_on_answerable": round(sum(r["refused"] for r in answerable) / len(answerable), 3),
               "mean_similarity": round(sum(r["similarity"] for r in answerable) / len(answerable), 3),
               "seconds_per_question": round(seconds / len(rows), 6)}
    return summary, rows


def main() -> None:
    terms = json.loads(GLOSSARY.read_text(encoding="utf-8"))["terms"]
    eval_data = json.loads(EVAL.read_text(encoding="utf-8"))
    questions, markers = eval_data["questions"], eval_data["refusal_markers"]
    engine = GlossarySearch(terms)

    sensitivity = [evaluate(engine, questions, markers, t)[0] for t in SENSITIVITY]
    summary, rows = evaluate(engine, questions, markers, THRESHOLD)
    OUTPUT.write_text(json.dumps({"summary": summary, "sensitivity": sensitivity, "rows": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False))
    for s in sensitivity:
        print(s["label"], {k: s[k] for k in ("all_rate", "known_rate", "paraphrase_rate", "unknown_rate")})
    for r in rows:
        print(r["type"][:3], "○" if r["ok"] else "×", r["method"], r["search_score"], r["question"], "=>", r["matched_term"])


if __name__ == "__main__":
    main()
