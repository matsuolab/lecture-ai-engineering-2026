"""Adaptive Graph retrieval tests. No external API is used."""

import json
from pathlib import Path

from app import retrieval


def _page(page_id, content, document_id="lec01-main", page_number=1):
    lecture = int(document_id[3:5])
    return {
        "page_id": page_id,
        "document_id": document_id,
        "lecture": lecture,
        "document_title": f"Lecture {lecture}",
        "section": "Section",
        "title": page_id,
        "page": page_number,
        "content": content,
    }


def _run_adaptive(
    monkeypatch,
    tmp_path,
    pages,
    hits,
    edges=(),
    query="LoRAとは？",
    question=None,
    search_calls=None,
):
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(
        json.dumps(
            {
                "nodes": [
                    {"id": page["page_id"], "kind": "page", "title": page["title"]}
                    for page in pages
                ]
                + [
                    {"id": node_id, "kind": "term", "title": node_id}
                    for edge in edges
                    for node_id in edge[:2]
                    if node_id.startswith("term-")
                ],
                "edges": [
                    {"source": source, "target": target, "relation": relation}
                    for source, target, relation in edges
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(retrieval, "load_pages", lambda *_: pages)
    monkeypatch.setattr(retrieval, "RAG_GRAPH", graph_path)
    def search(query_text):
        if search_calls is not None:
            search_calls.append(query_text)
        return hits

    monkeypatch.setattr(retrieval, "search", search)
    return retrieval.search_graph_adaptive(query, question=question)


def test_adaptive_checks_next_vector_seed_before_expanding_graph(monkeypatch, tmp_path):
    first = _page("lec01-main-p001", "LoRAでは元の重みを固定します。")
    second = _page("lec01-main-p002", "QLoRAではさらに元の重みを4bitに量子化します。", page_number=2)
    result = _run_adaptive(
        monkeypatch,
        tmp_path,
        [first, second],
        [
            {"page_id": first["page_id"], "distance": 0.01},
            {"page_id": second["page_id"], "distance": 0.02},
        ],
        query="LoRAは何を固定しますか？QLoRAは何を加えますか？",
    )

    assert [page["page_id"] for page in result["results"]] == [first["page_id"], second["page_id"]]
    assert result["coverage"]["sufficient"]
    assert all(aspect["evidence"] for aspect in result["coverage"]["aspects"])
    assert [aspect["evidence"][0]["page_id"] for aspect in result["coverage"]["aspects"]] == [
        first["page_id"], second["page_id"]
    ]


def test_adaptive_expands_graph_and_deduplicates_reachable_page(monkeypatch, tmp_path):
    first = _page("lec01-main-p001", "Alphaはひとつ目の説明です。")
    second = _page("lec01-main-p002", "Gammaは別の説明ページです。", page_number=2)
    third = _page("lec01-main-p003", "Betaは不足した論点を説明します。", page_number=3)
    result = _run_adaptive(
        monkeypatch,
        tmp_path,
        [first, second, third],
        [
            {"page_id": first["page_id"], "distance": 0.01},
            {"page_id": second["page_id"], "distance": 0.02},
        ],
        [
            (first["page_id"], "term-shared", "mentions"),
            (second["page_id"], "term-shared", "mentions"),
            (third["page_id"], "term-shared", "mentions"),
        ],
        query="Alphaは何ですか？Betaは何ですか？",
    )

    ids = [page["page_id"] for page in result["results"]]
    assert ids.count(third["page_id"]) == 1, result["trace"]
    assert result["coverage"]["sufficient"]
    assert max(page["hops"] for page in result["results"]) <= retrieval.GRAPH_HOPS
    third_result = next(page for page in result["results"] if page["page_id"] == third["page_id"])
    assert third_result["path"] == [
        {"id": first["page_id"], "title": first["title"]},
        {"id": "term-shared", "title": "term-shared"},
        {"id": third["page_id"], "title": third["title"]},
    ]


def test_adaptive_never_crosses_seed_document_boundary(monkeypatch, tmp_path):
    seed = _page("lec01-main-p001", "Alphaはこの資料内の説明です。")
    foreign = _page("lec02-main-p001", "Betaは別資料にある説明です。", "lec02-main")
    result = _run_adaptive(
        monkeypatch,
        tmp_path,
        [seed, foreign],
        [{"page_id": seed["page_id"], "distance": 0.01}],
        [(seed["page_id"], "term-shared", "mentions"), (foreign["page_id"], "term-shared", "mentions")],
    )

    assert [page["page_id"] for page in result["results"]] == [seed["page_id"]]


def test_adaptive_respects_hop_and_result_limits(monkeypatch, tmp_path):
    pages = [
        _page("lec01-main-p001", "Alphaは出発点の説明ページです。"),
        _page("lec01-main-p002", "Betaは近傍にある説明ページです。", page_number=2),
        _page("lec01-main-p003", "Deltaはさらに先にある説明ページです。", page_number=3),
        _page("lec01-main-p004", "Gammaは上限外にある説明ページです。", page_number=4),
    ]
    monkeypatch.setattr(retrieval, "GRAPH_HOPS", 2)
    monkeypatch.setattr(retrieval, "GRAPH_MAX_RESULTS", 2)
    result = _run_adaptive(
        monkeypatch,
        tmp_path,
        pages,
        [{"page_id": pages[0]["page_id"], "distance": 0.01}],
        [
            (pages[0]["page_id"], "term-one", "mentions"),
            ("term-one", pages[1]["page_id"], "mentions"),
            (pages[1]["page_id"], "term-two", "mentions"),
            ("term-two", pages[2]["page_id"], "mentions"),
            (pages[2]["page_id"], "term-three", "mentions"),
            ("term-three", pages[3]["page_id"], "mentions"),
        ],
        query="Alphaは何ですか？Betaは何ですか？Gammaは何ですか？",
    )

    assert [page["page_id"] for page in result["results"]] == [pages[0]["page_id"], pages[1]["page_id"]]
    assert len(result["results"]) <= 2
    assert all(page["hops"] <= 2 for page in result["results"])


def test_adaptive_never_uses_vector_hits_past_rag_top_k(monkeypatch, tmp_path):
    first = _page("lec01-main-p001", "Alphaはこの説明です。")
    second = _page("lec01-main-p002", "Betaは検索上位外の説明です。", page_number=2)
    monkeypatch.setattr(retrieval, "RAG_TOP_K", 1)
    result = _run_adaptive(
        monkeypatch,
        tmp_path,
        [first, second],
        [
            {"page_id": first["page_id"], "distance": 0.01},
            {"page_id": second["page_id"], "distance": 0.02},
        ],
        query="Alphaは何ですか？Betaは何ですか？",
    )

    assert [page["page_id"] for page in result["results"]] == [first["page_id"]]


def test_adaptive_does_not_match_lora_as_substring_of_qlora(monkeypatch, tmp_path):
    only_qlora = _page("lec01-main-p001", "QLoRAは4bit量子化を行う手法です。")
    result = _run_adaptive(
        monkeypatch,
        tmp_path,
        [only_qlora],
        [{"page_id": only_qlora["page_id"], "distance": 0.01}],
        query="LoRAとは何ですか？",
    )

    assert not result["coverage"]["sufficient"]
    assert result["coverage"]["aspects"][0]["evidence"] == []


def test_adaptive_treats_negated_match_as_uncertain_and_continues(monkeypatch, tmp_path):
    negated = _page("lec01-main-p001", "LoRAでは元の重みを固定しません。")
    result = _run_adaptive(
        monkeypatch,
        tmp_path,
        [negated],
        [{"page_id": negated["page_id"], "distance": 0.01}],
        query="LoRAでは重みを固定しますか？",
    )

    assert not result["coverage"]["sufficient"]
    assert result["coverage"]["status"] == "uncertain"
    assert result["coverage"]["aspects"][0]["evidence"][0]["status"] == "ambiguous_negation"
    assert "固定しません" in result["coverage"]["aspects"][0]["evidence"][0]["quote"]


def test_adaptive_reports_both_supporting_and_ambiguous_spans(monkeypatch, tmp_path):
    mixed = _page(
        "lec01-main-p001",
        "LoRAでは元の重みを固定します。LoRAでは元の重みを固定しません。",
    )
    result = _run_adaptive(
        monkeypatch,
        tmp_path,
        [mixed],
        [{"page_id": mixed["page_id"], "distance": 0.01}],
        query="LoRAでは重みを固定しますか？",
    )

    assert not result["coverage"]["sufficient"]
    statuses = {item["status"] for item in result["coverage"]["aspects"][0]["evidence"]}
    assert statuses == {"ambiguous_negation", "lexical_match"}


def test_short_search_query_uses_original_question_for_coverage(monkeypatch, tmp_path):
    all_pages = {page["page_id"]: page for page in retrieval.load_pages()}
    p51 = all_pages["lec02-main-p051"]
    p52 = all_pages["lec02-main-p052"]
    query = "AIE2026 第2回 LoRA QLoRA 固定 学習"
    question = "第2回の説明では、LoRAは何を固定し何を学習しますか？ QLoRAは何を加えますか？"
    searched = []
    result = _run_adaptive(
        monkeypatch,
        tmp_path,
        [p51, p52],
        [{"page_id": p52["page_id"], "distance": 0.01}],
        query=query,
        question=question,
        search_calls=searched,
    )

    assert searched == [query]
    assert [item["aspect"] for item in result["coverage"]["aspects"]] == retrieval._question_aspects(question)
    assert result["coverage"]["sufficient"]
    assert len(result["results"]) == 1
    qlora_evidence = result["coverage"]["aspects"][1]["evidence"][0]
    assert "4bit" in qlora_evidence["quote"]


def test_pre_grounded_lora_coverage_p52_alone_and_p51_plus_p52():
    pages = {page["page_id"]: page for page in retrieval.load_pages()}
    question = "第2回の説明では、LoRAは何を固定し何を学習しますか？ QLoRAは何を加えますか？"
    aspects = retrieval._question_aspects(question)

    p52_only = retrieval._coverage_report(aspects, [pages["lec02-main-p052"]])
    p51_and_p52 = retrieval._coverage_report(
        aspects,
        [pages["lec02-main-p051"], pages["lec02-main-p052"]],
    )

    assert p52_only["sufficient"]
    assert p51_and_p52["sufficient"]


def test_short_query_diagnostics_expose_metadata_term_as_missing():
    pages = {page["page_id"]: page for page in retrieval.load_pages()}
    short_query = "AIE2026 第2回 LoRA QLoRA 固定 学習"
    report = retrieval._coverage_report(
        retrieval._question_aspects(short_query),
        [pages["lec02-main-p051"], pages["lec02-main-p052"]],
    )

    assert not report["sufficient"]
    assert "aie2026" in report["aspects"][0]["missing_terms"]
    assert "missing_entities" in report["aspects"][0]["uncertainty_reasons"]


def test_adaptive_reports_partial_multi_aspect_coverage(monkeypatch, tmp_path):
    lora = _page("lec01-main-p001", "LoRAでは元の重みを固定し、AとBを学習します。")
    result = _run_adaptive(
        monkeypatch,
        tmp_path,
        [lora],
        [{"page_id": lora["page_id"], "distance": 0.01}],
        query="AIE2026 第2回 LoRA QLoRA 固定 学習",
        question="LoRAは何を固定し何を学習しますか？ QLoRAは何を加えますか？",
    )

    assert result["coverage"]["aspects"][0]["sufficient"]
    assert not result["coverage"]["aspects"][1]["sufficient"]
    assert "missing_entities" in result["coverage"]["aspects"][1]["uncertainty_reasons"]


def test_adaptive_rejects_each_graph_candidate_once_across_seeds(monkeypatch, tmp_path):
    first = _page("lec01-main-p001", "Alphaの説明です。")
    second = _page("lec01-main-p002", "Betaの説明です。", page_number=2)
    candidate = _page("lec01-main-p003", "無関係な段落です。", page_number=3)
    result = _run_adaptive(
        monkeypatch,
        tmp_path,
        [first, second, candidate],
        [
            {"page_id": first["page_id"], "distance": 0.01},
            {"page_id": second["page_id"], "distance": 0.02},
        ],
        [
            (first["page_id"], "term-shared", "mentions"),
            (second["page_id"], "term-shared", "mentions"),
            (candidate["page_id"], "term-shared", "mentions"),
        ],
        query="LoRAの重みを固定しますか？",
    )

    rejected = [
        event for event in result["trace"]
        if event["event"] == "candidate_rejected" and event["page_id"] == candidate["page_id"]
    ]
    assert len(rejected) == 1


def test_evaluation_evidence_ids_exist_in_search_materials():
    cases_path = Path(__file__).resolve().parents[1] / "data/eval/lec05_adaptive_graph_cases.jsonl"
    cases = [json.loads(line) for line in cases_path.read_text(encoding="utf-8").splitlines()]
    page_ids = {page["page_id"] for page in retrieval.load_pages()}

    assert len(cases) == 3
    for case in cases:
        evidence = case["gold_evidence"]
        expected_ids = {
            item["page_id"]
            for group in ("required", "useful_support")
            for item in evidence[group]
        }
        expected_ids.update(evidence["known_unneeded"])
        assert expected_ids <= page_ids, case["case_id"]


def test_pre_grounded_required_pages_cover_evaluation_aspects():
    cases_path = Path(__file__).resolve().parents[1] / "data/eval/lec05_adaptive_graph_cases.jsonl"
    cases = [json.loads(line) for line in cases_path.read_text(encoding="utf-8").splitlines()]
    pages = {page["page_id"]: page for page in retrieval.load_pages()}

    for case in cases:
        required_pages = [
            pages[item["page_id"]]
            for item in case["gold_evidence"]["required"]
        ]
        coverage = retrieval._coverage_report(
            retrieval._question_aspects(case["question"]),
            required_pages,
        )
        assert coverage["sufficient"], (case["case_id"], coverage)