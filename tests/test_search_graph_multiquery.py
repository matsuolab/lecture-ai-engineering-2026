"""Multi-query graph retrieval tests that do not call the embedding API."""

import json

import pytest

from app import retrieval


def test_multiquery_graph_preserves_facet_coverage_and_deduplicates(tmp_path, monkeypatch):
    first_query = "RAGで知識を追加する"
    second_query = "LoRAとQLoRAの違い"
    pages = [
        {"page_id": "p47", "document_id": "lec02-main", "lecture": 2,
         "document_title": "第2回", "section": "知識の追加", "title": "RAG",
         "page": 47, "content": "RAGは知識追加に向く"},
        {"page_id": "p52", "document_id": "lec02-main", "lecture": 2,
         "document_title": "第2回", "section": "学習方法", "title": "LoRA/QLoRA",
         "page": 52, "content": "LoRAとQLoRAの違い"},
        {"page_id": "p48", "document_id": "lec02-main", "lecture": 2,
         "document_title": "第2回", "section": "知識の追加", "title": "RAGの例外",
         "page": 48, "content": "RAGの例外"},
        {"page_id": "p51", "document_id": "lec02-main", "lecture": 2,
         "document_title": "第2回", "section": "学習方法", "title": "PEFT",
         "page": 51, "content": "LoRAは本体を固定する"},
    ]
    graph = {
        "nodes": [
            {"id": "p47", "kind": "page", "title": "RAG"},
            {"id": "p48", "kind": "page", "title": "RAGの例外"},
            {"id": "p51", "kind": "page", "title": "PEFT"},
            {"id": "p52", "kind": "page", "title": "LoRA/QLoRA"},
            {"id": "term:rag", "kind": "term", "title": "RAG"},
            {"id": "term:lora", "kind": "term", "title": "LoRA"},
        ],
        "edges": [
            {"source": "p47", "target": "term:rag", "relation": "mentions"},
            {"source": "term:rag", "target": "p48", "relation": "mentions"},
            {"source": "p52", "target": "term:lora", "relation": "mentions"},
            {"source": "term:lora", "target": "p51", "relation": "mentions"},
        ],
    }
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(graph), encoding="utf-8")
    rankings = {
        first_query: [
            {"page_id": "p47", "distance": 0.1},
            {"page_id": "p52", "distance": 0.2},
        ],
        second_query: [
            {"page_id": "p52", "distance": 0.15},
        ],
    }
    monkeypatch.setattr(retrieval, "load_pages", lambda *_: pages)
    monkeypatch.setattr(retrieval, "RAG_GRAPH", graph_path)
    monkeypatch.setattr(retrieval, "search", lambda query: rankings[query])
    monkeypatch.setattr(retrieval, "GRAPH_START_K", 2)
    monkeypatch.setattr(retrieval, "GRAPH_HOPS", 2)
    monkeypatch.setattr(retrieval, "GRAPH_MAX_RESULTS", 6)

    result = retrieval.search_graph_multiquery([first_query, second_query])

    seed_by_id = {page["page_id"]: page for page in result["seeds"]}
    expanded_by_id = {page["page_id"]: page for page in result["expanded"]}
    assert set(seed_by_id) == {"p47", "p52"}
    assert set(expanded_by_id) == {"p48", "p51"}
    assert set(seed_by_id).isdisjoint(expanded_by_id)
    assert seed_by_id["p52"]["facets"] == [first_query, second_query]
    assert expanded_by_id["p48"]["facets"] == [first_query]
    assert expanded_by_id["p51"]["facets"] == [first_query, second_query]
    assert len(seed_by_id) + len(expanded_by_id) == len(result["seeds"]) + len(result["expanded"])


@pytest.mark.parametrize("queries", [[], [""], ["a", "b", "c", "d"], ["a", None]])
def test_multiquery_graph_rejects_invalid_facets(queries):
    with pytest.raises(ValueError):
        retrieval.search_graph_multiquery(queries)
