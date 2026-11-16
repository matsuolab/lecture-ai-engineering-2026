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


def test_make_quiz_returns_a_term_from_the_requested_lecture(monkeypatch):
    terms = [entry for entry in tools.load_glossary() if entry["lecture"] == 2]
    selected = terms[0]
    monkeypatch.setattr(tools.random, "choice", lambda entries: selected)

    quiz = json.loads(tools.make_quiz(2))

    assert quiz == {
        "question": f"「{selected['term']}」の意味は？",
        "answer": selected["definition"],
    }


def test_make_quiz_reports_when_lecture_has_no_terms():
    assert "第0回" in tools.make_quiz(0)
    assert "見つかりませんでした" in tools.make_quiz(0)


def test_save_learning_log_writes_entry(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path)

    result = tools.save_learning_log("今日はRAGを学んだ")

    files = list(tmp_path.glob("*.md"))
    assert len(files) == 1
    assert files[0].read_text(encoding="utf-8") == "今日はRAGを学んだ\n"
    assert files[0].name in result


def test_save_learning_log_does_not_write_empty_entry(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path)

    result = tools.save_learning_log("  \n")

    assert "空" in result
    assert not list(tmp_path.iterdir())


def test_default_question_of_lecture1_is_answerable_from_glossary():
    """第1回の既定の質問（app.ask）は、第3回のエージェントが用語集で正しく答えられること。"""
    from app.ask import DEFAULT_QUESTION

    assert "3レベル" in DEFAULT_QUESTION
    hits = json.loads(tools.search_glossary("3レベル"))
    assert hits[0]["term"] == "宿題の3レベル"
