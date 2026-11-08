"""ツールのテスト（LLMもAPIキーも使わない）。"""

import json

from app import tools
from pathlib import Path
from app.tools import save_learning_log, get_pending_topics
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

def test_make_quiz_returns_valid_json_for_lecture_2():
    """
    make_quiz が第2回のデータを持っていて、
    正しい形式の文字列（JSON）を返すか確認する。
    """
    from app.tools import make_quiz
    
    # 実行。本当の動作をシミュレートする
    result = make_quiz(lecture=2)
    
    # JSONとして正しくパースできるか確認
    import json
    data = json.loads(result)
    
    assert "question" in data
    assert "answer" in data
    assert "error" not in data
    assert len(data["question"]) > 0  # 質問が空じゃないこと
    assert len(data["answer"]) > 0     # 回答が空じゃないこと

def test_make_quiz_returns_error_for_non_existent_lecture():
    """
    存在しない回を指定したときに、
    エラーメッセージを含むJSONを正しく返すか確認する。
    """
    from app.tools import make_quiz
    
    # 存在しない第99回を指定
    result = make_quiz(lecture=99)
    
    # JSONとして正しくパースできるか確認
    import json
    data = json.loads(result)
    
    assert "error" in data
    assert "見つかりませんでした" in data["error"]


# テスト用のディレクトリを準備
LOG_DIR = Path("learning_logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

def test_save_learning_log_creates_file(tmp_path, monkeypatch):

    """
    保存ツールを実行した際に、ファイルが実際に作成され、
    中身が正しいか確認する。
    """

    monkeypatch.setattr(tools, "LOG_DIR", tmp_path)
    # 実行
    result = save_learning_log(
        lecture=2,
        term="Transformer",
        understanding="low",
        next_action="再読"
    )
    
    # 1. 成功メッセージが返ってきたか
    assert "ログを保存しました" in result
    
    # 2. ファイルが実際に作られたか確認
    # フォルダ内のjsonファイルが1つ以上あるか
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1

    data = json.loads(files[0].read_text(encoding="utf-8"))
    assert data == {
        "lecture": 2,
        "term": "Transformer",
        "understanding": "low",
        "next_action": "再読",
    }

def test_get_pending_topics_returns_correct_list(tmp_path, monkeypatch):
    

    """
    保存されたデータから、理解度 'low' の項目を正しく抽出できるか確認する。
    """

    monkeypatch.setattr(tools, "LOG_DIR", tmp_path)
    # まず、テスト用のデータを保存する（ファイルが存在しない状態から開始）
    # 既存のファイルを一度消去するなどの前処理は省略し、追加で保存する
    save_learning_log(
        lecture=2, term="LoRA", understanding="low", next_action="練習"
    )
    save_learning_log(
        lecture=3, term="Attention", understanding="high", next_action="完了"
    )

    result = get_pending_topics()

    assert "LoRA" in result
    assert "Attention" not in result
    assert "マスターしました" not in result