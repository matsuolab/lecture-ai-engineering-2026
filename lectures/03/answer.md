# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：講座の用語集の定義に従って適切に回答している。
- `--trace` で見えたツール呼び出し（ツール名と引数）：search_glossary({'query': 'LoRA'})
- 1つの質問での LLM 呼び出し回数（`requests`）：2
- 追加したツールと、docstring に書いた説明：make_quiz """「第N回の確認問題を出して」と頼まれたときに、用語集から問題と答えを作るために使う。"""

## 宿題

- 取り組んだレベル： 実装 
- やったこと：tools.py に固定の learning_log へ日時ベースのMarkdownファイルを保存する関数を追加し、agent.py では保存前に利用者の承認を求め、承認後に会話履歴を引き継いで処理を再開するよう変更しました。構文チェックと差分チェックは成功し、テストは手動でターミナルで確認しています。
- 結果：どのクイズを確認したかの記録が保持できるようになりました。
- 気づき・疑問：学習の記録がどういう場面で使われるのか明示されていなかったので、やや汎用的に実装し、今回は、クイズを依頼する時に明示的に指示する形式にしましたが、make_quizが呼ばれる場合は、自動的に呼び出すようにするべきだったでしょうか？

(aie2026-exercises) @yonetaro ➜ /workspaces/lecture-ai-engineering-2026 (lec03) $ uv run python -m app.agent --trace "第2回の内容から make_quiz で確認問題を1問作り、問題と答えを save_learning_log で学習記録として保存してください。"
[model] gemini-3.5-flash-lite

--- 保存予定の学習記録 ---
# 学習記録: 第2回 確認問題

## 問題
Hugging Face Hubの意味は？

## 答え
公開されたモデルやデータセットを共有・ダウンロードできるプラットフォーム。オープンウェイトのモデルを入手したり、LoRAアダプタを公開したりするのに使われる。

このツール呼び出しを承認しますか？ [y/N]: y
第2回の内容から作成した確認問題を、学習記録として保存しました。

### 確認問題
**問題:** Hugging Face Hubの意味は？
**答え:** 公開されたモデルやデータセットを共有・ダウンロードできるプラットフォーム。オープンウェイトのモデルを入手したり、LoRAアダプタを公開したりするのに使われる。

関連する回: 第2回

--- trace ---
[tool call]   make_quiz({'lecture': 2})
[tool return] make_quiz -> {"question": "Hugging Face Hubの意味は？", "answer": "公開されたモデルやデータセットを共有・ダウンロードできるプラットフォーム。オープンウェイトのモデルを入手したり、LoRAアダプタを公開したりす…
[tool call]   save_learning_log({'content': '# 学習記録: 第2回 確認問題\n\n## 問題\nHugging Face Hubの意味は？\n\n## 答え\n公開されたモデルやデータセットを共有・ダウンロードできるプラットフォーム。オープンウェイトのモデルを入手したり、LoRAアダプタを公開したりするのに使われる。\n'})
[tool return] save_learning_log -> 学習記録を保存しました: learning_log/20261107_021814_197295.md…
[usage] RunUsage(cost=Decimal('0.0004019'), details={'text_prompt_tokens': 673}, input_text_tokens=673, input_tokens=673, output_tokens=80, requests=1, tool_calls=1)

