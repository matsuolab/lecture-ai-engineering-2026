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


def test_default_question_of_lecture1_is_answerable_from_glossary():
    """第1回の既定の質問（app.ask）は、第3回のエージェントが用語集で正しく答えられること。"""
    from app.ask import DEFAULT_QUESTION

    assert "3レベル" in DEFAULT_QUESTION
    hits = json.loads(tools.search_glossary("3レベル"))
    assert hits[0]["term"] == "宿題の3レベル"


def _page(document_id, n):
    return {"page_id": f"{document_id}-p{n:03d}", "document_id": document_id,
            "lecture": int(document_id[3:5]), "page": n, "title": f"p{n}", "content": f"本文{n}"}


PAGES = [_page("lec01-main", n) for n in (1, 2, 3)] + [_page("lec02-main", n) for n in (1, 2, 3, 4, 5)]


def test_add_neighbors_is_noop_when_window_is_zero():
    from app.retrieval import add_neighbors

    hits = [{**PAGES[4], "distance": 0.1}]
    assert add_neighbors(hits, 0, PAGES) == hits


def test_add_neighbors_stays_in_document_and_skips_duplicates():
    from app.retrieval import add_neighbors

    # lec01 の最終ページ、lec02 の p2 と p3（隣どうし）がヒット
    hits = [{**PAGES[2], "distance": 0.1}, {**PAGES[4], "distance": 0.2}, {**PAGES[5], "distance": 0.3}]
    results = add_neighbors(hits, 1, PAGES)
    ids = [r["page_id"] for r in results]

    assert len(ids) == len(set(ids))  # 重複なし
    # lec01-p003 の次は lec02-p001 だが、資料をまたがないので付かない
    assert ids == ["lec01-main-p002", "lec01-main-p003",
                   "lec02-main-p001", "lec02-main-p002", "lec02-main-p003", "lec02-main-p004"]
    by_id = {r["page_id"]: r for r in results}
    # 検索で当たったページは neighbor ではなく search として、距離付きで返る
    assert by_id["lec02-main-p003"]["retrieved_by"] == "search"
    assert by_id["lec02-main-p003"]["distance"] == 0.3
    assert by_id["lec02-main-p004"] == {**PAGES[6], "retrieved_by": "neighbor",
                                        "neighbor_of": "lec02-main-p003"}
    assert "distance" not in by_id["lec01-main-p002"]


def test_search_materials_adds_neighbors(monkeypatch):
    from app import retrieval

    monkeypatch.setattr(retrieval, "search", lambda query: [{**PAGES[4], "distance": 0.1}])
    monkeypatch.setattr(retrieval, "load_pages", lambda *args: PAGES)
    monkeypatch.setattr(retrieval, "RAG_NEIGHBORS", 1)
    results = json.loads(tools.search_materials("LoRA"))["results"]
    assert [(r["page"], r["retrieved_by"]) for r in results] == [(1, "neighbor"), (2, "search"), (3, "neighbor")]
