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


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    from types import SimpleNamespace

    from app.ask import MODEL, ask

    class FakeModels:
        def generate_content(self, model, contents):
            assert model == MODEL
            assert contents == "AIE2026とは何ですか?"
            return SimpleNamespace(
                text="AIE2026は講座名です。",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=123,
                    candidates_token_count=45,
                ),
            )

    class FakeClient:
        def __init__(self, api_key):
            self.api_key = api_key
            self.models = FakeModels()

    monkeypatch.setattr("app.ask.get_api_key", lambda: "fake-api-key")
    monkeypatch.setattr("app.ask.genai.Client", FakeClient)

    result = ask("AIE2026とは何ですか?")

    assert result == "AIE2026は講座名です。"
    captured = capsys.readouterr()
    assert "入力トークン" in captured.out
    assert "123" in captured.out
    assert "出力トークン" in captured.out
    assert "45" in captured.out


def test_ask_keeps_history_for_follow_up_questions(monkeypatch):
    from types import SimpleNamespace

    from app.ask import ask

    seen = []

    class FakeModels:
        def generate_content(self, model, contents):
            seen.append(contents)
            return SimpleNamespace(
                text=f"回答: {contents[-1]['parts'][0]['text']}",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=10,
                    candidates_token_count=2,
                ),
            )

    class FakeClient:
        def __init__(self, api_key):
            self.api_key = api_key
            self.models = FakeModels()

    monkeypatch.setattr("app.ask.get_api_key", lambda: "fake-api-key")
    monkeypatch.setattr("app.ask.genai.Client", FakeClient)

    history = [
        {"role": "user", "parts": [{"text": "前の質問"}]},
        {"role": "model", "parts": [{"text": "前の回答"}]},
    ]

    result = ask("次の質問", history=history)

    assert result == "回答: 次の質問"
    assert seen[0][0] == history[0]
    assert seen[0][1] == history[1]
    assert seen[0][-1]["role"] == "user"
    assert seen[0][-1]["parts"][0]["text"] == "次の質問"
