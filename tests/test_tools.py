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


def test_make_quize_selects_a_term_from_requested_lecture(monkeypatch):
    def choose_lecture_term(terms):
        assert terms
        assert all(term["lecture"] == 2 for term in terms)
        return terms[0]

    monkeypatch.setattr(tools.random, "choice", choose_lecture_term)
    selected = next(term for term in tools.load_glossary() if term["lecture"] == 2)

    quiz = json.loads(tools.make_quize(2))

    assert set(quiz) == {"question", "answer"}
    assert selected["definition"] in quiz["question"]
    assert quiz["answer"] == selected["term"]


def test_make_quize_reports_when_lecture_has_no_terms():
    assert "第99回の用語は用語集にありません" in tools.make_quize(99)


def test_save_learning_log_creates_directory_and_writes_content(tmp_path, monkeypatch):
    log_dir = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", log_dir)

    result = tools.save_learning_log("今日の学び\n- 型ヒント")

    logs = list(log_dir.glob("*.md"))
    assert len(logs) == 1
    assert logs[0].read_text(encoding="utf-8") == "今日の学び\n- 型ヒント\n"
    assert "learning_log/" in result
    assert logs[0].name in result


def test_save_learning_log_rejects_empty_content(tmp_path, monkeypatch):
    log_dir = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", log_dir)

    result = tools.save_learning_log(" \n ")

    assert "空です" in result
    assert not log_dir.exists()


def test_default_question_of_lecture1_is_answerable_from_glossary():
    """第1回の既定の質問（app.ask）は、第3回のエージェントが用語集で正しく答えられること。"""
    from app.ask import DEFAULT_QUESTION

    assert "3レベル" in DEFAULT_QUESTION
    hits = json.loads(tools.search_glossary("3レベル"))
    assert hits[0]["term"] == "宿題の3レベル"
