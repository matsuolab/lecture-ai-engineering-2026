from app import retrieval


def _page(page_id, document_id, page_number):
    return {
        "page_id": page_id,
        "document_id": document_id,
        "page": page_number,
        "content": f"本文{page_id}",
    }


def test_read_page_returns_neighbors_only_from_same_document(monkeypatch):
    pages = [
        _page("doc1-p1", "doc1", 1),
        _page("doc1-p2", "doc1", 2),
        _page("doc1-p3", "doc1", 3),
        _page("doc2-p1", "doc2", 1),
    ]
    monkeypatch.setattr(retrieval, "load_pages", lambda _: pages)

    result = retrieval.read_page("doc2-p1")

    assert result["page_id"] == "doc2-p1"
    assert result["content"] == "本文doc2-p1"
    assert result["adjacent_pages"] == []


def test_search_with_neighbors_deduplicates_overlapping_context(monkeypatch):
    pages = [
        _page("doc1-p1", "doc1", 1),
        _page("doc1-p2", "doc1", 2),
        _page("doc1-p3", "doc1", 3),
        _page("doc1-p4", "doc1", 4),
        _page("doc2-p1", "doc2", 1),
    ]
    hits = [
        {**pages[1], "distance": 0.1},
        {**pages[2], "distance": 0.2},
    ]
    monkeypatch.setattr(retrieval, "search", lambda _: hits)
    monkeypatch.setattr(retrieval, "load_pages", lambda _: pages)

    results = retrieval.search_with_neighbors("質問")

    assert [result["page_id"] for result in results] == [
        "doc1-p2", "doc1-p1", "doc1-p3", "doc1-p4",
    ]
    assert len({result["page_id"] for result in results}) == len(results)
    assert {result["page_id"] for result in results if result["search_hit"]} == {
        "doc1-p2", "doc1-p3",
    }
    assert results[0]["distance"] == 0.1
    assert results[2]["distance"] == 0.2
    assert all(result["document_id"] == "doc1" for result in results)
