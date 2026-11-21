import json

from app import retrieval, tools


def _page(doc_id: str, page: int) -> dict:
    return {
        "page_id": f"{doc_id}-p{page:03d}",
        "document_id": doc_id,
        "page": page,
        "content": f"{doc_id} p.{page}の本文",
    }


def _hit(page: dict, distance: float) -> dict:
    return {**page, "distance": distance}


def test_search_with_neighbors(monkeypatch):
    """前後ページを取得し、重複排除・資料境界・元ヒットのdistanceと本文を保持する。"""
    pages = [_page("lec02-main", n) for n in (51, 52, 53)]
    pages.append(_page("lec01-main", 50))

    # p.52(上位ヒット)とp.51(次点ヒット)が検索された状況を再現
    hits = [_hit(pages[1], 0.1), _hit(pages[0], 0.2)]
    monkeypatch.setattr(retrieval, "search", lambda query: hits)
    monkeypatch.setattr(retrieval, "load_pages", lambda: pages)

    results = retrieval.search_with_neighbors("LoRA")

    assert [page["page_id"] for page in results] == [
        "lec02-main-p051",
        "lec02-main-p052",
        "lec02-main-p053",
    ]
    assert [page["content"] for page in results] == [
        "lec02-main p.51の本文",
        "lec02-main p.52の本文",
        "lec02-main p.53の本文",
    ]
    assert results[0]["distance"] == 0.2
    assert results[1]["distance"] == 0.1
    assert "distance" not in results[2]


def test_search_with_neighbors_no_hits(monkeypatch):
    """検索結果が空ならload_pagesを呼ばずに空リストを返す。"""
    monkeypatch.setattr(retrieval, "search", lambda query: [])

    def fail_load_pages():
        raise AssertionError("検索結果が空のときはload_pagesを呼ばない")

    monkeypatch.setattr(retrieval, "load_pages", fail_load_pages)

    assert retrieval.search_with_neighbors("該当なし") == []


def test_search_with_neighbors_first_page_boundary(monkeypatch):
    """資料の先頭ページがヒットしても、別資料の末尾ページや先頭ページを混入しない。"""
    pages = [
        _page("lec01-main", 73),
        _page("lec02-main", 1),
        _page("lec02-main", 2),
    ]
    monkeypatch.setattr(retrieval, "search", lambda query: [_hit(pages[1], 0.15)])
    monkeypatch.setattr(retrieval, "load_pages", lambda: pages)

    results = retrieval.search_with_neighbors("先頭ページ")

    assert [page["page_id"] for page in results] == [
        "lec02-main-p001",
        "lec02-main-p002",
    ]
    assert [page["content"] for page in results] == [
        "lec02-main p.1の本文",
        "lec02-main p.2の本文",
    ]
    assert results[0]["distance"] == 0.15
    assert "distance" not in results[1]


def test_search_with_neighbors_last_page_boundary(monkeypatch):
    """資料の末尾ページがヒットしても、別資料の先頭ページを混入しない。"""
    pages = [
        _page("lec01-main", 72),
        _page("lec01-main", 73),
        _page("lec02-main", 1),
    ]
    monkeypatch.setattr(retrieval, "search", lambda query: [_hit(pages[1], 0.15)])
    monkeypatch.setattr(retrieval, "load_pages", lambda: pages)

    results = retrieval.search_with_neighbors("末尾ページ")

    assert [page["page_id"] for page in results] == [
        "lec01-main-p072",
        "lec01-main-p073",
    ]
    assert [page["content"] for page in results] == [
        "lec01-main p.72の本文",
        "lec01-main p.73の本文",
    ]
    assert "distance" not in results[0]
    assert results[1]["distance"] == 0.15


def test_search_with_neighbors_one_page_gap(monkeypatch):
    """1ページ空きの複数ヒットでも、中間の共有ページを重複させず本文を返す。"""
    pages = [_page("lec02-main", n) for n in (50, 51, 52, 53, 54)]
    hits = [_hit(pages[1], 0.1), _hit(pages[3], 0.2)]
    monkeypatch.setattr(retrieval, "search", lambda query: hits)
    monkeypatch.setattr(retrieval, "load_pages", lambda: pages)

    results = retrieval.search_with_neighbors("LoRAとQLoRA")

    assert [page["page_id"] for page in results] == [
        "lec02-main-p050",
        "lec02-main-p051",
        "lec02-main-p052",
        "lec02-main-p053",
        "lec02-main-p054",
    ]
    assert [page["content"] for page in results] == [
        f"lec02-main p.{n}の本文" for n in (50, 51, 52, 53, 54)
    ]
    assert "distance" not in results[0]
    assert results[1]["distance"] == 0.1
    assert "distance" not in results[2]
    assert results[3]["distance"] == 0.2
    assert "distance" not in results[4]


def test_search_materials_returns_neighbors_and_content(monkeypatch):
    """search_materials経由でも前後ページの本文と引用情報が返る。"""
    pages = [_page("lec02-main", n) for n in (51, 52, 53)]
    monkeypatch.setattr(retrieval, "search", lambda query: [_hit(pages[1], 0.1)])
    monkeypatch.setattr(retrieval, "load_pages", lambda: pages)

    payload = json.loads(tools.search_materials("LoRA"))

    assert [page["page_id"] for page in payload["results"]] == [
        "lec02-main-p051",
        "lec02-main-p052",
        "lec02-main-p053",
    ]
    assert [page["content"] for page in payload["results"]] == [
        "lec02-main p.51の本文",
        "lec02-main p.52の本文",
        "lec02-main p.53の本文",
    ]
