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


def test_make_quiz_uses_a_term_from_the_requested_lecture(monkeypatch):
    def choose_first(terms):
        assert terms
        assert all(term["lecture"] == 2 for term in terms)
        return terms[0]

    monkeypatch.setattr(tools.random, "choice", choose_first)

    quiz = json.loads(tools.make_quiz(2))

    assert quiz["question"].startswith("次の説明に当てはまる用語は何ですか？")
    assert quiz["answer"] == "事前学習"


def test_make_quiz_reports_when_lecture_has_no_terms():
    assert "第99回" in tools.make_quiz(99)
    assert "用語集にありません" in tools.make_quiz(99)


def test_save_learning_log_appends_to_daily_file(tmp_path, monkeypatch):
    log_dir = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", log_dir)

    saved_path = tools.save_learning_log("  今日学んだこと  ")
    log_files = list(log_dir.glob("*.md"))

    assert len(log_files) == 1
    assert log_files[0].read_text(encoding="utf-8").endswith("今日学んだこと\n\n")
    assert str(log_files[0].relative_to(tmp_path)) in saved_path


def test_save_learning_log_rejects_empty_content(tmp_path, monkeypatch):
    log_dir = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", log_dir)

    try:
        tools.save_learning_log("  ")
    except ValueError as error:
        assert "空" in str(error)
    else:
        raise AssertionError("空の学習記録が保存されました")

    assert not log_dir.exists()


def test_default_question_of_lecture1_is_answerable_from_glossary():
    """第1回の既定の質問（app.ask）は、第3回のエージェントが用語集で正しく答えられること。"""
    from app.ask import DEFAULT_QUESTION

    assert "3レベル" in DEFAULT_QUESTION
    hits = json.loads(tools.search_glossary("3レベル"))
    assert hits[0]["term"] == "宿題の3レベル"
