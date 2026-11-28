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


def test_make_quiz_selects_a_term_from_the_requested_lecture(monkeypatch):
    selected_from = []

    def choose(terms):
        selected_from.extend(terms)
        return terms[0]

    monkeypatch.setattr(tools.random, "choice", choose)
    result = json.loads(tools.make_quiz(2))
    selected = selected_from[0]

    assert selected_from
    assert all(term["lecture"] == 2 for term in selected_from)
    assert result == {
        "question": f"{selected['term']}の意味は？",
        "answer": selected["definition"],
    }


def test_make_quiz_reports_when_lecture_has_no_terms():
    result = json.loads(tools.make_quiz(99))
    assert "error" in result


def test_lecture_summary():
    assert "エージェント" in tools.get_lecture_summary(3)
    assert "まだありません" in tools.get_lecture_summary(99)


def test_default_question_of_lecture1_is_answerable_from_glossary():
    """第1回の既定の質問（app.ask）は、第3回のエージェントが用語集で正しく答えられること。"""
    from app.ask import DEFAULT_QUESTION

    assert "3レベル" in DEFAULT_QUESTION
    hits = json.loads(tools.search_glossary("3レベル"))
    assert hits[0]["term"] == "宿題の3レベル"


def test_find_related_terms_returns_question_terms_and_limit():
    hits = tools.find_related_terms("LoRAとQLoRAの違い", limit=5)
    terms = {hit["term"] for hit in hits}
    assert "LoRA" in terms
    assert "QLoRA" in terms
    assert len(hits) <= 5


def test_find_related_terms_returns_empty_for_blank_question():
    assert tools.find_related_terms("") == []
