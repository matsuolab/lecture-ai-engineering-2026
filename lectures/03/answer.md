# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：

- `--trace` で見えたツール呼び出し（ツール名と引数）：
```
$ uv run python -m app.agent --trace " 第2回の内容から確認問題を 1問出して"
[model] gemini-3.5-flash-lite
第2回から確認問題を1問出しますね！

**【確認問題】**
「LoRA」とは何ですか？

---
回答のヒントとして、LoRAは大規模言語モデルなどの効率的なチューニング（PEFT手法）に関わる技術です。ぜひ考えてみてください！

関係する回：第2回

--- trace ---
[tool call]   make_quiz({'lecture': 2})
[tool return] make_quiz -> {"term": "LoRA", "question": "「LoRA」とは何ですか？", "answer": "事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEF…
[usage] RunUsage(cost=Decimal('0.0004903'), details={'text_prompt_tokens': 926}, input_text_tokens=926, input_tokens=926, output_tokens=85, requests=2, tool_calls=1)
```

- 1つの質問での LLM 呼び出し回数（`requests`）：
2回

- 追加したツールと、docstring に書いた説明：

`make_quiz`を追加した
agent.tool_plain(tools.make_quiz)

docstring:
    """指定した回の用語から 1つを選び、
    確認問題と答えを返す。
    「第2回の確認問題を出して」のように、
    復習用の問題を求められたときに使う。
    """

## 宿題

- 取り組んだレベル：実装
- やったこと：
取り組んだ内容の要約をAIを用いて行った：

追加した承認付き学習ログ機能の流れを、ツール定義・エージェント登録・CLI承認・再開処理の順に整理します。


今回追加したのは、**学習ログを保存する前に利用者の承認を求める機能**です。

## 1. `save_learning_log`ツール

`tools.py`に追加した関数です。

- `learning_log/<タイトル>.md`へ学習内容を保存
- タイトルが空の場合は拒否
- パス区切りを含むタイトルも拒否
- 保存先ディレクトリは必要に応じて作成

## 2. 承認が必要なツールとして登録

`agent.py`で、次のように登録しています。

```python
agent.tool_plain(
    tools.save_learning_log,
    requires_approval=True,
)
```

これにより、モデルが保存ツールを呼び出しても、すぐには実行されません。

## 3. `DeferredToolRequests`を利用

`agent.py`では、エージェントの出力型に次の2種類を指定しています。

```python
output_type=[str, DeferredToolRequests]
```

通常は文字列を返しますが、承認が必要なツールが呼ばれた場合は、`DeferredToolRequests`が返ります。

これは次の情報を含みます。

- 呼び出そうとしたツール
- 渡された引数
- ツール呼び出しID

この段階では、まだファイルは保存されていません。

## 4. CLIで利用者に確認

`run_with_approval`が承認処理を担当します。

```text
承認が必要です: save_learning_log(...)
保存してよいですか？ [y/N]:
```

- `y`、`yes`、`はい`の場合：承認
- それ以外の場合：拒否

承認結果は`DeferredToolResults`として作成されます。

```python
deferred_results = result.output.build_results(
    approvals=approvals
)
```

## 5. エージェントを再開

承認結果と元の会話履歴を使い、エージェントを再実行します。

```python
target.run_sync(
    message_history=result.all_messages(),
    deferred_tool_results=deferred_results,
    model=model,
)
```

承認された場合だけ`save_learning_log`が実行され、ログが保存されます。拒否した場合は保存されず、モデルに拒否結果が伝わって最終回答が生成されます。

つまり、処理の流れは次のとおりです。

```text
ユーザーの質問
  ↓
モデルが save_learning_log を呼び出す
  ↓
DeferredToolRequests を返す
  ↓
CLIで利用者に確認
  ↓
承認結果を DeferredToolResults にする
  ↓
エージェントを再開
  ↓
承認時のみファイル保存
```
- 実行結果：
```


- 結果：
以下のように学習ログの保存を促すプロンプトを入力し、 `learning_log`フォルダに保存されたことを確認した
 $ uv run python -m app.agent "今日、Pydantic AIの承認フローを学んだので、学習ログとして保存してください"
[model] gemini-3.5-flash-lite

承認が必要です: save_learning_log({'content': 'Pydantic AIにおける承認フローの仕組みや使い方について学びました。', 'title': 'Pydantic AIの承認フローについて'})
保存してよいですか？ [y/N]: y
Pydantic AIの承認フローに関する学習ログを保存しました。

なお、今回学ばれた「承認フロー」という用語について用語集を確認したところ、該当する用語の登録はありませんでしたが、Pydantic AI（第3回）を用いたエージェント開発の中で重要なトピックとして学ばれたものと思います。

引き続き学習を応援しております！

（関連する回：第3回）
```

- 気づき・疑問：
今回の承認フローはhuman in the loopにあたるものだが、onやout ofにしたときagentの権限の制御をどのように実装するのだろうか