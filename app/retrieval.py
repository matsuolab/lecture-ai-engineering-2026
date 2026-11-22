"""第5回: ページ単位のベクトル検索。"""

import argparse
import json
import math
import re
import sqlite3
from contextlib import contextmanager
from collections import defaultdict, deque
from pathlib import Path

from google import genai
from google.genai import types
from pydantic_ai.exceptions import ModelHTTPError
import sqlite_vec

from app.config import (
    EMBEDDING_DIMENSIONS, EMBEDDING_MAX_TOKENS, EMBEDDING_MODEL,
    RAG_DB, RAG_DOCUMENT_IDS, RAG_SOURCE, RAG_TOP_K, RAG_TREE, get_api_key,
    RAG_GRAPH, GRAPH_START_K, GRAPH_HOPS, GRAPH_MAX_RESULTS,
    GRAPH_ADAPTIVE_MIN_RELEVANCE,
)


def get_all_materials() -> str:
    """全資料を、講義・章・ページの情報付きで1つの文字列にまとめる。"""
    documents = json.loads(RAG_SOURCE.read_text(encoding="utf-8"))
    return "\n\n".join(
        f"資料: {document['id']} / {document['title']}\n"
        f"章: {section['section']}\n"
        f"ページ: PDF p.{page['page']} / {page['title']}\n{page['content']}"
        for document in documents
        for section in document["content"]
        for page in section["content"]
    )

def load_pages(source: Path = RAG_SOURCE) -> list[dict]:
    """資料→章→ページのJSONを、対象資料のページ一覧に変換する。"""
    documents = json.loads(source.read_text(encoding="utf-8"))
    pages = []
    for document in documents:
        if document["id"] not in RAG_DOCUMENT_IDS:
            continue
        for section in document["content"]:
            for page in section["content"]:
                pages.append({"page_id": page["id"], "document_id": document["id"],
                              "lecture": int(document["id"][3:5]), "document_title": document["title"],
                              "section": section["section"], "title": page["title"],
                              "page": page["page"], "content": page["content"]})
    return pages


def browse_tree(node_id: str | None = None) -> dict:
    """直下のページは先頭文、指定したページ自身は全文を返す。"""
    tree = json.loads(RAG_TREE.read_text(encoding="utf-8"))
    tree["children"] = [node for node in tree["children"] if node["id"] in RAG_DOCUMENT_IDS]
    node_id = node_id or tree["id"]
    pages = {page["page_id"]: page for page in load_pages(RAG_SOURCE)}

    def describe(node, full=False):
        info = {key: node[key] for key in ("id", "kind", "title")}
        if node["kind"] == "page":
            info.update({key: value for key, value in pages[node["id"]].items() if key != "page_id"})
            if not full:
                info["content"] = re.split(r"(?<=[。！？])|\n", info["content"].strip(), maxsplit=1)[0]
        return info

    remaining = [tree]
    while remaining:
        node = remaining.pop()
        if node["id"] == node_id:
            return {
                "node": describe(node, full=True),
                "children": [describe(child) for child in node.get("children", [])],
            }
        remaining.extend(node.get("children", []))
    raise ValueError("対象の目次ノードが見つかりません。")


def read_page(page_id: str) -> dict:
    """第1〜3回の本講義から、指定した1ページの本文と引用情報を返す。"""
    for page in load_pages(RAG_SOURCE):
        if page["page_id"] == page_id:
            return page
    raise ValueError("対象のページが見つかりません。")


def normalized_vector(values: list[float]) -> list[float]:
    """ベクトルの長さを1に揃える。"""
    norm = math.hypot(*values)
    if norm == 0:
        raise ValueError("埋め込みがゼロベクトルです。")
    return [value / norm for value in values]


def embed_text(text: str, task_type: str) -> list[float]:
    """Geminiで文章を埋め込む。入力上限を超えた場合は切り捨てず停止する。"""
    with genai.Client(api_key=get_api_key()) as client:
        count = client.models.count_tokens(model=EMBEDDING_MODEL, contents=text).total_tokens
        if count is None or count > EMBEDDING_MAX_TOKENS:
            raise ValueError(f"埋め込み入力が上限を超えるか計測不能です: {count} tokens。")
        response = client.models.embed_content(
            model=EMBEDDING_MODEL, contents=text,
            config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=EMBEDDING_DIMENSIONS),
        )
    embedding = response.embeddings[0]
    if embedding.statistics and embedding.statistics.truncated:
        raise ValueError("埋め込みAPIが本文を切り捨てました。")
    return normalized_vector(embedding.values)


@contextmanager
def open_index(path: Path):
    """既存の検索DBを読み取り専用で開き、終了時に閉じる。"""
    if not path.is_file():
        raise FileNotFoundError("検索DBがありません。")
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        db.row_factory = sqlite3.Row
        db.enable_load_extension(True)
        sqlite_vec.load(db)
        db.enable_load_extension(False)
        yield db
    finally:
        db.close()


def search(query: str) -> list[dict]:
    """質問を埋め込み、近いページを最大RAG_TOP_K件返す。"""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("検索語が空です。")
    with open_index(RAG_DB) as db:
        vector = embed_text(query.strip(), "RETRIEVAL_QUERY")
        rows = db.execute("""
            SELECT page_id, document_id, lecture, document_title, section, title, page, content,
                   vec_distance_cosine(embedding, ?) AS distance
            FROM chunks ORDER BY distance, page_id LIMIT ?
        """, (sqlite_vec.serialize_float32(vector), RAG_TOP_K))
        return [dict(row) for row in rows]


def search_graph(query: str) -> dict:
    """ベクトル検索を入口に、前後ページと共通用語で候補を広げる。"""
    pages = {page["page_id"]: page for page in load_pages(RAG_SOURCE)}
    graph = json.loads(RAG_GRAPH.read_text(encoding="utf-8"))
    nodes = {node["id"]: node for node in graph["nodes"]
             if node["kind"] == "term" or node["id"] in pages}
    adjacent = defaultdict(set)
    for edge in graph["edges"]:
        a, b = edge["source"], edge["target"]
        if edge["relation"] in ("next_page", "mentions") and a in nodes and b in nodes:
            adjacent[a].add(b)
            adjacent[b].add(a)

    seeds = [hit for hit in search(query) if hit["page_id"] in pages][:min(GRAPH_START_K, GRAPH_MAX_RESULTS)]
    seed_ids = {seed["page_id"] for seed in seeds}
    results, candidates = [], {}
    for rank, seed in enumerate(seeds):
        root = seed["page_id"]
        results.append({**pages[root], "distance": seed["distance"], "hops": 0,
                        "path": [{"id": root, "title": pages[root]["title"]}]})
        queue = deque([(root, [root])])
        visited = {root}
        while queue:
            current, path = queue.popleft()
            if len(path) - 1 >= GRAPH_HOPS:
                continue
            # 同じ深さなら、接続先が少ない用語からたどる。
            neighbors = sorted(adjacent[current], key=lambda n: (len(adjacent[n]), n))
            for neighbor in neighbors:
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                route = path + [neighbor]
                queue.append((neighbor, route))
                if neighbor not in pages or neighbor in seed_ids:
                    continue
                frequency = max((len(adjacent[n]) for n in route if nodes[n]["kind"] == "term"), default=0)
                priority = (len(route) - 1, frequency, rank, neighbor)
                candidate = {**pages[neighbor], "hops": len(route) - 1,
                             "path": [{"id": n, "title": nodes[n]["title"]} for n in route]}
                if neighbor not in candidates or priority < candidates[neighbor][0]:
                    candidates[neighbor] = (priority, candidate)
    expanded = [candidate for _, candidate in sorted(candidates.values())]
    return {"seeds": results, "expanded": expanded[:max(0, GRAPH_MAX_RESULTS - len(results))],
            "max_hops": GRAPH_HOPS}


_LATIN_TOKEN_RE = re.compile(r"[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*", re.IGNORECASE)
_JAPANESE_RUN_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff々ー]+")
_NEGATION_RE = re.compile(
    r"(?:ない|ません|なかった|ませんでした|ぬ|なく)|\b(?:not|never|without)\b",
    re.IGNORECASE,
)
_NEGATION_MATCH_THRESHOLD = 0.5
_ADDITION_CUES = ("加え", "追加", "さらに", "増や", "足す", "加算")
_ADDITION_FEATURE = "concept:addition"
_QUESTION_STOP_FEATURES = {
    "は何", "何を", "何で", "どう", "とは", "です", "ます", "ますか", "すか",
    "しま", "えま", "加え", "する", "しな", "ます。", "です。", "を教", "教え",
}


def _text_features(text: str) -> set[str]:
    folded = text.casefold()
    features = set(_LATIN_TOKEN_RE.findall(folded))
    normalized = re.sub(r"\s+", "", folded)
    for run in _JAPANESE_RUN_RE.findall(normalized):
        features.update(run[index:index + 2] for index in range(len(run) - 1))
    if any(cue in normalized for cue in _ADDITION_CUES):
        features.add(_ADDITION_FEATURE)
    return features - _QUESTION_STOP_FEATURES


def _question_aspects(query: str) -> list[str]:
    return [aspect.strip() for aspect in re.split(r"(?<=[。！？!?])|[;；\n]+", query) if aspect.strip()]


def _evidence_sentences(content: str) -> list[str]:
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[。！？!?])|[\r\n]+", content)]
    return [sentence for sentence in sentences if sentence]


def _relevance_score(query: str, page: dict) -> float:
    query_features = _text_features(query)
    page_features = _text_features(" ".join((page["title"], page["section"], page["content"])))
    if not query_features:
        return 0.0
    return len(query_features & page_features) / len(query_features)


def _coverage_report(aspects: list[str], pages: list[dict]) -> dict:
    reports = []
    for aspect in aspects:
        aspect_features = _text_features(aspect)
        aspect_entities = {token.casefold() for token in _LATIN_TOKEN_RE.findall(aspect)}
        covered_features, covered_entities = set(), set()
        evidence = []
        negation_ambiguous = False
        for page in pages:
            candidates = []
            for sentence in _evidence_sentences(page["content"]):
                sentence_features = _text_features(sentence)
                sentence_entities = {token.casefold() for token in _LATIN_TOKEN_RE.findall(sentence)}
                matched_features = aspect_features & sentence_features
                matched_entities = aspect_entities & sentence_entities
                if not matched_features and not matched_entities:
                    continue
                match_score = (
                    len(matched_features) / len(aspect_features)
                    if aspect_features else float(bool(matched_entities))
                )
                ambiguous_negation = (
                    bool(_NEGATION_RE.search(sentence))
                    and match_score >= _NEGATION_MATCH_THRESHOLD
                )
                if ambiguous_negation:
                    negation_ambiguous = True
                else:
                    covered_features.update(matched_features)
                    covered_entities.update(matched_entities)
                candidates.append({
                    "page_id": page["page_id"],
                    "document_id": page["document_id"],
                    "lecture": page["lecture"],
                    "page": page["page"],
                    "title": page["title"],
                    "quote": sentence[:400],
                    "score": round(match_score, 3),
                    "matched_terms": sorted(matched_entities | matched_features),
                    "status": "ambiguous_negation" if ambiguous_negation else "lexical_match",
                })
            for status in ("lexical_match", "ambiguous_negation"):
                matching = [candidate for candidate in candidates if candidate["status"] == status]
                if matching:
                    evidence.append(max(matching, key=lambda item: (item["score"], len(item["quote"]))))

        feature_score = (
            len(covered_features) / len(aspect_features)
            if aspect_features else 1.0
        )
        missing_features = sorted(aspect_features - covered_features)
        missing_entities = sorted(aspect_entities - covered_entities)
        entities_covered = not missing_entities
        threshold = 0.4 if aspect_features else 1.0
        sufficient = entities_covered and feature_score >= threshold and bool(evidence) and not negation_ambiguous
        uncertainty_reasons = []
        if negation_ambiguous:
            uncertainty_reasons.append("negation_overlap")
        if missing_entities:
            uncertainty_reasons.append("missing_entities")
        if feature_score < threshold:
            uncertainty_reasons.append("feature_coverage_below_threshold")
        if not evidence:
            uncertainty_reasons.append("no_matching_evidence")
        reports.append({
            "aspect": aspect,
            "sufficient": sufficient,
            "status": "heuristic_sufficient" if sufficient else "uncertain",
            "uncertainty_reasons": uncertainty_reasons,
            "score": round(feature_score, 3),
            "matched_terms": sorted(covered_entities | covered_features),
            "missing_terms": sorted(set(missing_features + missing_entities)),
            "evidence": sorted(evidence, key=lambda item: (-item["score"], item["page_id"])),
        })
    sufficient = bool(reports) and all(item["sufficient"] for item in reports)
    return {
        "sufficient": sufficient,
        "status": "heuristic_sufficient" if sufficient else "uncertain",
        "aspects": reports,
    }


def search_graph_adaptive(query: str, question: str | None = None) -> dict:
    """Progressively retrieve relevant pages until lexical evidence coverage is sufficient or a limit is met.

    Coverage is an explainable heuristic, not a guarantee of entailment or correctness.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("検索語が空です。")
    coverage_question = question.strip() if isinstance(question, str) and question.strip() else query.strip()

    pages = {page["page_id"]: page for page in load_pages(RAG_SOURCE)}
    aspects = _question_aspects(coverage_question)
    hits = [hit for hit in search(query.strip())[:RAG_TOP_K] if hit["page_id"] in pages]
    results, trace = [], []
    seen = set()
    coverage = _coverage_report(aspects, results)

    def add_page(page_id: str, source: str, hops: int, path: list[str], hit: dict | None = None) -> None:
        page = pages[page_id]
        relevance = _relevance_score(coverage_question, page)
        result = {
            **page,
            "source": source,
            "relevance": round(relevance, 3),
            "hops": hops,
            "path": [{"id": node_id, "title": graph_nodes[node_id]["title"]} for node_id in path],
        }
        if hit and "distance" in hit:
            result["distance"] = hit["distance"]
        seen.add(page_id)
        results.append(result)
        trace.append({
            "event": "page_added",
            "page_id": page_id,
            "source": source,
            "hops": hops,
            "relevance": result["relevance"],
            "path": path,
        })

    graph_data = json.loads(RAG_GRAPH.read_text(encoding="utf-8"))
    graph_nodes = {
        node["id"]: node for node in graph_data["nodes"]
        if node["kind"] == "term" or node["id"] in pages
    }
    adjacent = defaultdict(set)
    for edge in graph_data["edges"]:
        source, target = edge["source"], edge["target"]
        if edge["relation"] in ("next_page", "mentions") and source in graph_nodes and target in graph_nodes:
            adjacent[source].add(target)
            adjacent[target].add(source)

    def check_coverage() -> bool:
        nonlocal coverage
        coverage = _coverage_report(aspects, results)
        trace.append({
            "event": "coverage_check",
            "sufficient": coverage["sufficient"],
            "missing_aspects": [
                {
                    "aspect": item["aspect"],
                    "status": item["status"],
                    "reasons": item["uncertainty_reasons"],
                }
                for item in coverage["aspects"] if not item["sufficient"]
            ],
        })
        return coverage["sufficient"]

    stop_reason = "no_vector_hits"
    if hits and GRAPH_MAX_RESULTS > 0:
        first = hits[0]
        add_page(first["page_id"], "vector_seed", 0, [first["page_id"]], first)
        check_coverage()
        stop_reason = "no_candidates"

        for hit in hits[1:]:
            if coverage["sufficient"]:
                stop_reason = "evidence_sufficient"
                break
            if len(results) >= GRAPH_MAX_RESULTS:
                stop_reason = "max_results"
                break
            if hit["page_id"] in seen:
                continue
            add_page(hit["page_id"], "vector_seed", 0, [hit["page_id"]], hit)
            check_coverage()
            stop_reason = "no_candidates"
        else:
            if coverage["sufficient"]:
                stop_reason = "evidence_sufficient"

        if not coverage["sufficient"] and len(results) < GRAPH_MAX_RESULTS:
            graph_candidates = {}
            rejected_candidate_ids = set()
            evaluated_candidate_ids = set()
            roots = [(page["page_id"], page["document_id"]) for page in results]
            for root_rank, (root_id, root_document_id) in enumerate(roots):
                queue = deque([(root_id, [root_id])])
                visited = {root_id}
                while queue:
                    current, path = queue.popleft()
                    hops = len(path) - 1
                    if hops >= GRAPH_HOPS:
                        continue
                    for neighbor in sorted(adjacent[current]):
                        if neighbor in visited:
                            continue
                        if neighbor in pages and pages[neighbor]["document_id"] != root_document_id:
                            continue
                        visited.add(neighbor)
                        route = path + [neighbor]
                        queue.append((neighbor, route))
                        if neighbor not in pages or neighbor in seen:
                            continue
                        evaluated_candidate_ids.add(neighbor)
                        relevance = _relevance_score(coverage_question, pages[neighbor])
                        if relevance < GRAPH_ADAPTIVE_MIN_RELEVANCE:
                            if neighbor not in rejected_candidate_ids:
                                rejected_candidate_ids.add(neighbor)
                                trace.append({
                                    "event": "candidate_rejected",
                                    "page_id": neighbor,
                                    "reason": "low_relevance",
                                    "relevance": round(relevance, 3),
                                })
                            continue
                        candidate = {
                            "page_id": neighbor,
                            "hops": len(route) - 1,
                            "path": route,
                            "relevance": relevance,
                            "root_rank": root_rank,
                        }
                        priority = (-relevance, candidate["hops"], root_rank, neighbor)
                        if neighbor not in graph_candidates or priority < graph_candidates[neighbor][0]:
                            graph_candidates[neighbor] = (priority, candidate)

            trace.append({
                "event": "candidate_summary",
                "unique_pages": len(evaluated_candidate_ids),
                "rejected_pages": len(rejected_candidate_ids),
                "eligible_pages": len(graph_candidates),
            })
            for _, candidate in sorted(graph_candidates.values(), key=lambda item: item[0]):
                if coverage["sufficient"]:
                    stop_reason = "evidence_sufficient"
                    break
                if len(results) >= GRAPH_MAX_RESULTS:
                    stop_reason = "max_results"
                    break
                add_page(candidate["page_id"], "graph", candidate["hops"], candidate["path"])
                check_coverage()
            else:
                stop_reason = "evidence_sufficient" if coverage["sufficient"] else "no_candidates"

        if len(results) >= GRAPH_MAX_RESULTS and not coverage["sufficient"]:
            stop_reason = "max_results"
        elif coverage["sufficient"]:
            stop_reason = "evidence_sufficient"

    trace.append({"event": "stopped", "reason": stop_reason})
    response = {
        "results": results,
        "coverage": coverage,
        "stop_reason": stop_reason,
        "max_hops": GRAPH_HOPS,
        "max_results": GRAPH_MAX_RESULTS,
        "trace": trace,
        "page_count": len(results),
        "context_chars": sum(len(page["content"]) for page in results),
    }
    response["tool_result_chars"] = len(json.dumps(response, ensure_ascii=False))
    return response



def run_full_context(agent, question: str, model, instructions: str, prompt_template: str):
    """全資料を一括投入し、検索ツールを使わずに回答する。"""
    prompt = prompt_template.format(materials=get_all_materials(), question=question)
    print(f"[full-context] 入力{len(prompt):,}文字")
    try:
        with agent.override(tools=[], instructions=instructions):
            return agent.run_sync(prompt, model=model)
    except ModelHTTPError as e:
        print(f"[full-context] APIエラー HTTP {e.status_code}: {e.body}")
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="エージェントを使わず、講義資料の検索だけを実行する")
    parser.add_argument("query", help="調べたい内容")
    args = parser.parse_args()
    for i, result in enumerate(search(args.query), 1):
        print(f"\n{'=' * 60}\n検索結果 {i}\n{'=' * 60}")
        print(f"講義: {result['document_title']}")
        print(f"章: {result['section']}")
        print(f"タイトル: {result['title']}")
        print(f"ページ: {result['page']}")
        print(f"\n{result['content']}")
