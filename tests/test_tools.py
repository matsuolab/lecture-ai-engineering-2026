"""ツールのテスト（LLMもAPIキーも使わない）。"""

import json

from app import tools


def test_glossary_ids_are_unique_and_related_links_exist():
    terms = tools.load_glossary()
    ids = [t["id"] for t in terms]
    assert len(ids) == len(set(ids))
    for t in terms:
        for r in t["related"]:
            assert r in ids, f"{t['id']} の related に存在しない id: {r}"


def test_search_finds_term_by_name_and_alias():
    for query in ["LoRA", "lora", "Low-Rank Adaptation"]:
        hits = json.loads(tools.search_glossary(query))
        assert hits[0]["term"] == "LoRA", query


def test_search_finds_course_specific_term():
    hits = json.loads(tools.search_glossary("lecNN-start"))
    assert hits[0]["term"] == "lecNN-start タグ"


def test_search_limits_number_of_results():
    hits = json.loads(tools.search_glossary("エージェント"))
    assert 1 <= len(hits) <= tools.MAX_RESULTS


def test_search_reports_not_found():
    assert "見つかりませんでした" in tools.search_glossary("存在しない用語xyz")


def test_lecture_summary():
    assert "エージェント" in tools.get_lecture_summary(3)
    assert "まだありません" in tools.get_lecture_summary(99)


def test_search_materials_adds_neighbors_without_crossing_document_boundary(monkeypatch):
    hit = {"page_id": "doc-a-2", "document_id": "doc-a", "page": 2, "content": "hit"}
    pages = [
        {"page_id": "doc-a-1", "document_id": "doc-a", "page": 1},
        {"page_id": "doc-a-2", "document_id": "doc-a", "page": 2},
        {"page_id": "doc-a-3", "document_id": "doc-a", "page": 3},
        {"page_id": "doc-b-1", "document_id": "doc-b", "page": 1},
    ]
    search_results = [hit]
    monkeypatch.setattr("app.retrieval.search", lambda query: search_results)
    monkeypatch.setattr("app.retrieval.load_pages", lambda: pages)

    results = json.loads(tools.search_materials("query"))["results"]

    assert [page["page_id"] for page in results] == ["doc-a-2", "doc-a-1", "doc-a-3"]
    assert [page["context"] for page in results] == ["match", "previous", "next"]

    search_results[:] = [pages[2]]
    results = json.loads(tools.search_materials("query"))["results"]
    assert [page["page_id"] for page in results] == ["doc-a-3", "doc-a-2"]


def test_default_question_of_lecture1_is_answerable_from_glossary():
    """第1回の既定の質問（app.ask）は、第3回のエージェントが用語集で正しく答えられること。"""
    from app.ask import DEFAULT_QUESTION

    assert "3レベル" in DEFAULT_QUESTION
    hits = json.loads(tools.search_glossary("3レベル"))
    assert hits[0]["term"] == "宿題の3レベル"
