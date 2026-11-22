"""第5回 宿題（発展）: Treeの候補文を、章ヘッダー・タイトルを飛ばしたリード文にする。APIは呼ばない。"""

from app import retrieval
from app.retrieval import find_headers, lead_sentence


def _page(n, content, title="タイトル", doc="lec02-main"):
    return {"page_id": f"{doc}-p{n:03d}", "document_id": doc, "title": title, "content": content}


def test_skips_repeated_section_header_and_title():
    pages = [_page(n, f"4/4 　章名\nタイトル{n}\n要点{n}です。続き") for n in range(1, 4)]
    headers = find_headers(pages)
    assert lead_sentence({**pages[0], "title": "タイトル1"}, headers) == "要点1です。続き"


def test_skips_source_line_and_falls_back_to_first_sentence():
    page = _page(1, "タイトル\n出典：論文\n©LAB")
    assert lead_sentence(page, set()) == "タイトル"


def test_long_lead_is_truncated():
    page = _page(1, "タイトル\n" + "あ" * 150)
    lead = lead_sentence(page, set())
    assert lead.endswith("…") and len(lead) == retrieval.LEAD_MAX_CHARS + 1


def test_real_tree_candidates_show_lead(monkeypatch):
    monkeypatch.setattr(retrieval, "TREE_SNIPPET", "lead")
    children = {c["id"]: c["content"] for c in retrieval.browse_tree("lec02-main-s045")["children"]}
    assert children["lec02-main-p052"].startswith("元の重みは固定し")
    children = {c["id"]: c["content"] for c in retrieval.browse_tree("lec03-main-s037")["children"]}
    assert "セッションをまたいで" in children["lec03-main-p039"]


def test_original_mode_keeps_first_sentence(monkeypatch):
    monkeypatch.setattr(retrieval, "TREE_SNIPPET", "first")
    children = {c["id"]: c["content"] for c in retrieval.browse_tree("lec02-main-s045")["children"]}
    assert children["lec02-main-p052"].startswith("4/4")


def test_full_page_content_unchanged():
    node = retrieval.browse_tree("lec02-main-p052")["node"]
    assert node["content"].startswith("4/4") and "4bit" in node["content"]
