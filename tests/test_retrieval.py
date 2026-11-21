import json

from app import retrieval


def test_browse_tree_returns_300_character_page_preview_and_full_page(tmp_path, monkeypatch):
    content = "先頭文。二文目。" + "あ" * 500
    source = tmp_path / "lectures.json"
    source.write_text(json.dumps([
        {
            "id": "lec01-main",
            "title": "講義1",
            "content": [{
                "section": "章",
                "content": [{
                    "id": "lec01-main-p001",
                    "title": "ページ1",
                    "page": 1,
                    "content": content,
                }],
            }],
        },
    ], ensure_ascii=False), encoding="utf-8")
    tree = tmp_path / "tree.json"
    tree.write_text(json.dumps({
        "id": "root",
        "kind": "collection",
        "title": "資料",
        "children": [{
            "id": "lec01-main",
            "kind": "document",
            "title": "講義1",
            "children": [{
                "id": "lec01-main-p001",
                "kind": "page",
                "title": "ページ1",
            }],
        }],
    }, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(retrieval, "RAG_SOURCE", source)
    monkeypatch.setattr(retrieval, "RAG_TREE", tree)
    monkeypatch.setattr(retrieval, "RAG_DOCUMENT_IDS", {"lec01-main"})

    preview = retrieval.browse_tree("lec01-main")["children"][0]["content"]
    full_page = retrieval.browse_tree("lec01-main-p001")["node"]["content"]

    assert preview == content[:300]
    assert len(preview) == 300
    assert full_page == content
