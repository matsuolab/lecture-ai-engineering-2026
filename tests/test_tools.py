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


def test_make_quiz_reveals_answer_after_yes(monkeypatch, capsys):
    terms = tools.load_glossary()
    expected = next(term for term in terms if term["lecture"] == 3)

    def choose_term(candidates):
        assert all(term["lecture"] == 3 for term in candidates)
        return expected

    monkeypatch.setattr(tools.random, "choice", choose_term)
    monkeypatch.setattr("builtins.input", lambda prompt: " yes ")
    quiz = json.loads(tools.make_quiz(3))
    question = f"「{expected['term']}」とは何ですか？"

    assert quiz == [
        {
            "question": question,
            "answer": expected["definition"],
        }
    ]
    output = capsys.readouterr().out
    assert question in output
    assert expected["definition"] in output


def test_make_quiz_hides_answer_unless_yes_is_entered(monkeypatch):
    expected = next(term for term in tools.load_glossary() if term["lecture"] == 3)
    monkeypatch.setattr(tools.random, "choice", lambda candidates: expected)
    monkeypatch.setattr("builtins.input", lambda prompt: "no")

    quiz = json.loads(tools.make_quiz(3))

    assert quiz == [{"question": f"「{expected['term']}」とは何ですか？"}]


def test_default_question_of_lecture1_is_answerable_from_glossary():
    """第1回の既定の質問（app.ask）は、第3回のエージェントが用語集で正しく答えられること。"""
    from app.ask import DEFAULT_QUESTION

    assert "3レベル" in DEFAULT_QUESTION
    hits = json.loads(tools.search_glossary("3レベル"))
    assert hits[0]["term"] == "宿題の3レベル"
