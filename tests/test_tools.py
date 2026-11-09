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


def test_default_question_of_lecture1_is_answerable_from_glossary():
    """第1回の既定の質問（app.ask）は、第3回のエージェントが用語集で正しく答えられること。"""
    from app.ask import DEFAULT_QUESTION

    assert "3レベル" in DEFAULT_QUESTION
    hits = json.loads(tools.search_glossary("3レベル"))
    assert hits[0]["term"] == "宿題の3レベル"


# --- 第3回 演習: make_quiz ---

def test_make_quiz_returns_question_and_answer_from_that_lecture():
    quiz = json.loads(tools.make_quiz(2))
    lecture2 = {t["term"]: t["definition"] for t in tools.load_glossary() if t["lecture"] == 2}
    assert quiz["lecture"] == 2
    assert quiz["term"] in lecture2
    assert quiz["term"] in quiz["question"]
    assert quiz["answer"] == lecture2[quiz["term"]]


def test_make_quiz_reports_lecture_without_terms():
    assert "ありません" in tools.make_quiz(99)


# --- 第3回 宿題（実装）: save_learning_log ---

def test_save_learning_log_appends_to_daily_file(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path / "learning_log")
    assert "保存しました" in tools.save_learning_log("LoRA", "低ランク行列だけを学習する")
    assert "保存しました" in tools.save_learning_log("QLoRA", "4bit量子化＋LoRA")
    files = list((tmp_path / "learning_log").glob("*.md"))
    assert len(files) == 1  # 同じ日の記録は1つのファイルに追記される
    text = files[0].read_text(encoding="utf-8")
    assert "LoRA" in text and "4bit量子化＋LoRA" in text
    assert text.count("# 学習の記録") == 1


def test_save_learning_log_rejects_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path / "learning_log")
    assert "指定してください" in tools.save_learning_log("  ", "")
    assert not (tmp_path / "learning_log").exists()
