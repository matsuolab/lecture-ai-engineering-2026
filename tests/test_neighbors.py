"""宿題（実装）：検索結果に前後ページを付ける処理のテスト。APIは呼ばない。"""

import json

import pytest
from pydantic_ai.messages import ToolReturnPart
from pydantic_ai.models.test import TestModel

from app import retrieval
from app.agent import NEIGHBOR_TOOL, agent, summarize_pages


def _page(doc: str, page: int) -> dict:
    return {"page_id": f"{doc}-p{page:03d}", "document_id": doc, "lecture": int(doc[3:5]),
            "document_title": doc, "section": "章", "title": f"{doc} p.{page}",
            "page": page, "content": f"{doc} の {page} ページ"}


PAGES = [_page("lec01-main", n) for n in range(1, 4)] + [_page("lec02-main", n) for n in range(1, 6)]


def _hit(doc: str, page: int, distance: float) -> dict:
    return {**_page(doc, page), "distance": distance}


def _ids(results):
    return [(r["page_id"], r["role"]) for r in results]


def test_adds_previous_and_next_page_in_rank_order():
    results = retrieval.add_neighbor_pages([_hit("lec02-main", 3, 0.1)], PAGES)
    assert _ids(results) == [("lec02-main-p002", "neighbor"), ("lec02-main-p003", "hit"),
                             ("lec02-main-p004", "neighbor")]
    assert results[0]["neighbor_of"] == "lec02-main-p003"
    assert results[1]["distance"] == 0.1 and results[1]["rank"] == 1
    assert "distance" not in results[0]


def test_does_not_cross_documents_at_the_edges():
    # lec01 の最終ページの「次」に lec02 の p.1 を付けない
    results = retrieval.add_neighbor_pages([_hit("lec01-main", 3, 0.1), _hit("lec02-main", 1, 0.2)], PAGES)
    assert _ids(results) == [("lec01-main-p002", "neighbor"), ("lec01-main-p003", "hit"),
                             ("lec02-main-p001", "hit"), ("lec02-main-p002", "neighbor")]


def test_no_duplicates_and_hit_wins_over_neighbor():
    # p.3 が1位、p.4 が2位。p.4 は p.3 の「次」として先に入るが、hit として扱う
    hits = [_hit("lec02-main", 3, 0.1), _hit("lec02-main", 4, 0.2)]
    results = retrieval.add_neighbor_pages(hits, PAGES)
    ids = [r["page_id"] for r in results]
    assert len(ids) == len(set(ids))
    assert _ids(results) == [("lec02-main-p002", "neighbor"), ("lec02-main-p003", "hit"),
                             ("lec02-main-p004", "hit"), ("lec02-main-p005", "neighbor")]
    p4 = results[2]
    assert p4["rank"] == 2 and p4["distance"] == 0.2 and "neighbor_of" not in p4


def test_shared_neighbor_is_returned_once():
    hits = [_hit("lec02-main", 2, 0.1), _hit("lec02-main", 4, 0.2)]
    results = retrieval.add_neighbor_pages(hits, PAGES)
    assert [r["page"] for r in results] == [1, 2, 3, 4, 5]
    assert results[2]["neighbor_of"] == "lec02-main-p002"  # 先に付けた hit を記録する


def test_window_zero_keeps_plain_results():
    hits = [_hit("lec02-main", 3, 0.1)]
    assert _ids(retrieval.add_neighbor_pages(hits, PAGES, window=0)) == [("lec02-main-p003", "hit")]
    with pytest.raises(ValueError):
        retrieval.add_neighbor_pages(hits, PAGES, window=-1)


def test_real_materials_neighbors_stay_in_the_same_lecture():
    # 配布の lectures.json でも、第3回 p.39 の前後は第3回 p.38・p.40 になる
    pages = retrieval.load_pages()
    hit = next(p for p in pages if p["page_id"] == "lec03-main-p039")
    results = retrieval.add_neighbor_pages([{**hit, "distance": 0.3}], pages)
    assert [(r["lecture"], r["page"], r["role"]) for r in results] == [
        (3, 38, "neighbor"), (3, 39, "hit"), (3, 40, "neighbor")]


def test_neighbor_tool_keeps_the_same_name_and_reaches_the_model(monkeypatch):
    monkeypatch.setattr("app.retrieval.search", lambda *args, **kwargs: [_hit("lec02-main", 3, 0.1)])
    monkeypatch.setattr("app.retrieval.load_pages", lambda *args, **kwargs: PAGES)
    model = TestModel(call_tools=["search_materials"])
    with agent.override(model=model, tools=[NEIGHBOR_TOOL]):
        result = agent.run_sync("LoRAとは？")
    offered = [t.name for t in model.last_model_request_parameters.function_tools]
    assert offered == ["search_materials"]
    returns = [p for m in result.all_messages() for p in m.parts if isinstance(p, ToolReturnPart)]
    data = json.loads(returns[0].content)
    assert [r["role"] for r in data["results"]] == ["neighbor", "hit", "neighbor"]
    assert summarize_pages(returns[0].content).startswith("3ページ")
    assert "第2回 p.2（前後）" in summarize_pages(returns[0].content)
