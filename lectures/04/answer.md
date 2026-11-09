第4回: 評価セットのラベル付けと LLM-as-a-Judge の演習・宿題を追加
新しいファイル
- app/judge.py: 評価セットを LLM に採点させ、人のラベルとの一致率・要確認・不一致を出す（--model test で API 無しの動作確認、--compare でラベル同士の比較、--generate で回答の生成）
- tools/annotate.py: ラベル付け・講師ラベルとの比較・作問の画面（Streamlit。uv run --with で一時的に足して動かすので pyproject.toml は変えない）
- .streamlit/config.toml: Codespaces のポート転送で開けるようにする設定
- data/eval/: 評価セット 10 件（lec04_cases.jsonl）と採点の基準（rubric.md）
- lectures/04/: problem.md、answer.md、講師のラベル（reference/）
- data/lectures/04.md、tests/test_judge.py（API キー無しで採点の流れを確認）

変更したファイル（受講生が演習・宿題で編集するファイルは含まない）
- data/glossary.json: 第4回の用語 7 語を配列の末尾に追加、note を更新
- README.md: 構成の説明に第4回の分を追加
