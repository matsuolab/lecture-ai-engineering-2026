"""宿題の比較スクリプトを、APIを呼ばずに最後まで通す（TestModel と固定の検索結果）。"""

import json
import sys

from pydantic_ai.models.test import TestModel

from app import retrieval
from scripts import run_lec05_homework as script


def test_cited_pages_parses_common_forms():
    text = "根拠：第2回・PDF p.52。第3回・PDF p.39, 40。第1回 PDF p.61–62、第2回・p.43"
    assert script.cited_pages(text) == [
        "lec02-main-p052", "lec03-main-p039", "lec03-main-p040",
        "lec01-main-p061", "lec01-main-p062", "lec02-main-p043"]


def test_script_runs_end_to_end_without_api(tmp_path, monkeypatch):
    pages = [p for p in retrieval.load_pages() if p["lecture"] == 3][36:50]

    def fake_search(query):
        return [{**p, "distance": 0.1 * i} for i, p in enumerate(pages[:retrieval.RAG_TOP_K])]

    monkeypatch.setattr(retrieval, "search", fake_search)
    monkeypatch.setattr(script.agent_module, "build_model", lambda: TestModel())
    monkeypatch.setattr(script.time, "sleep", lambda s: None)
    monkeypatch.setattr(sys, "argv", ["x", "--questions", "q2", "--out", str(tmp_path), "--wait", "0"])
    script.main()

    data = json.loads((tmp_path / "homework_runs.json").read_text(encoding="utf-8"))
    runs = {r["mode"]: r for r in data["runs"]}
    assert set(runs) == {"rag", "topk10", "neighbors"}
    assert len(runs["rag"]["retrieved"]) == 5
    assert len(runs["topk10"]["retrieved"]) == 10
    assert len(runs["neighbors"]["retrieved"]) == 7  # 連続する5ページ＋前後1ページずつ
    assert retrieval.RAG_TOP_K == 5  # 終わったら元に戻す
    only = data["retrieval_only"][0]
    assert len(only["rag"]["pages"]) == 5 and len(only["topk10"]["pages"]) == 10
    report = (tmp_path / "homework_report.md").read_text(encoding="utf-8")
    assert "実装：top5＋前後1ページ" in report and "--trace" in report
