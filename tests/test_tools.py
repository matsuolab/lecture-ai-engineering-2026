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


def test_ask_prints_input_and_output_token_usage(monkeypatch, capsys):
    import app.ask as ask_module

    class FakeUsage:
        prompt_token_count = 123
        candidates_token_count = 45

    class FakeResponse:
        text = "回答です"
        usage_metadata = FakeUsage()

    class FakeClient:
        def __init__(self, api_key):
            self.api_key = api_key

        @property
        def models(self):
            return self

        def generate_content(self, model, contents, config):
            assert model == ask_module.MODEL
            assert contents == "質問"
            assert config.temperature == ask_module.TEMPERATURE
            return FakeResponse()

        def close(self):
            pass

    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "dummy-key")

    result = ask_module.ask("質問")
    captured = capsys.readouterr()

    assert result == "回答です"
    assert "[usage] input: 123, output: 45" in captured.out
