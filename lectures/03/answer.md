# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
  - ただのLLMは一般的な知識以外の質問には答えられないが、エージェントはツールを使って知識を参照できるし、問題作成など事前に定義されたタスクを実行し、その結果を踏まえた回答をすることができる。
  - 例えば「第2回の内容から確認問題を 1問出して」という質問に対する回答は以下のようになる。
    - ただのLLM: 「申し訳ありませんが、**「第2回」がどの教材や講義、あるいはどのテーマを指しているのか情報がありません。**」
    - エージェント: 「事前学習とは何ですか？」

- `--trace` で見えたツール呼び出し（ツール名と引数）：
  - 「第2回の内容から確認問題を 1問出して」という質問に対するツール呼び出しは以下の通り。
    - make_quiz({'lecture': 2})

- 1つの質問での LLM 呼び出し回数（`requests`）：
  - 「第2回の内容から確認問題を 1問出して」という質問の呼び出し回数は2だった（おそらくtool呼び出し前に1回、後に1回）。

- 追加したツールと、docstring に書いた説明：
  - make_quiz(lecture: int) を追加した。指定回の用語をランダムに1つ選び、確認問題と答えをJSON形式で返す。
  - docstringは講義資料のサンプルをそのまま使用した。復習問題を求められたときに呼び出す旨が記載されている。

## 宿題

- 取り組んだレベル：発展
- やったこと：
  - google ADKを用いたエージェント実装
  - instruction, toolsは既存agent（Pydantic AI）用の実装を再利用
  - google ADKでの実装のメイン部分は以下の数行のみ
    ```python
    root_agent = Agent(
        model="gemini-3.5-flash-lite",
        name="glossary_agent",
        instruction=INSTRUCTIONS,
        tools=[
            tools.search_glossary,
            tools.get_lecture_summary,
            tools.make_quiz,
        ],
    )
    ```
  - 既存agentと同じ質問をし、回答とログ（--jsonlで出す）を既存agentのものと比較

- 結果：
  - 既存agentと同じ質問「第2回の内容から確認問題を1問出して」をしたところ、既存agentと同様の、端的に用語を意味を問う質問が返ってきた。
  - ログを見ると、make_quizが呼ばれていることが確認できた。ログ全文を以下に掲載する。
    ```json
    {'author': 'glossary_agent', 'session_id': '5db802bd-e1ca-4b67-982d-0cf95245c101', 'node_path': 'glossary_agent@1', 'id': '130d7771-0389-4c57-ba5a-eb8f98e76b94', 'modelVersion': 'gemini-3.5-flash-lite', 'content': {'parts': [{'functionCall': {'id': 'call_4371507729870439895', 'args': {'lecture': 2}, 'name': 'make_quiz'}, 'thoughtSignature': 'EmAKXgFpFH0Tzshbv-EbMMPtmoVOs9UOvDKRuGNhRuSisl4aKLr6vkIkl6c25xnBSBzGY8RpA_4TCEKV69qtYPaobh8YbIEpMGX5ajrRLSbcBCmAd0REJM9L1KOykHPQ1dA='}], 'role': 'model'}, 'finishReason': 'STOP', 'usageMetadata': {'candidatesTokenCount': 14, 'promptTokenCount': 475, 'promptTokensDetails': [{'modality': 'TEXT', 'tokenCount': 475}], 'totalTokenCount': 489}, 'invocationId': 'e-9116ad2d-09ac-44ba-ba93-4f1a8d6e1d12', 'nodeInfo': {'path': 'glossary_agent@1'}, 'longRunningToolIds': [], 'timestamp': 1794035266.7066486}
    {'author': 'glossary_agent', 'session_id': '5db802bd-e1ca-4b67-982d-0cf95245c101', 'node_path': 'glossary_agent@1', 'id': '328fc331-da3a-40a3-9ad6-8b435c04daa6', 'content': {'parts': [{'functionResponse': {'id': 'call_4371507729870439895', 'name': 'make_quiz', 'response': {'result': '{"question": "ランク（LoRAのr）とは何ですか？", "answer": "LoRAで使う低ランク行列の大きさを決めるハイパーパラメータ。大きいほど表現力が上がるが、学習するパラメータとメモリも増える。"}'}}}], 'role': 'user'}, 'invocationId': 'e-9116ad2d-09ac-44ba-ba93-4f1a8d6e1d12', 'nodeInfo': {'path': 'glossary_agent@1'}, 'timestamp': 1794035266.7167394}
    {'author': 'glossary_agent', 'session_id': '5db802bd-e1ca-4b67-982d-0cf95245c101', 'node_path': 'glossary_agent@1', 'id': '8e23084e-4655-480e-aee6-b407ecedb760', 'modelVersion': 'gemini-3.5-flash-lite', 'content': {'parts': [{'text': '第2回の内容から確認問題を出題します！\n\n**【確認問題】**\nランク（LoRAのr）とは何ですか？\n\n---\n答えが分かったら教えてくださいね。\n（関連する回：第2回）', 'thoughtSignature': 'EmAKXgFpFH0Tih4woEIj7cV2H-J8U2G-baS_VRwMI6neu69yBd_8IVKyF0TpbHFT7T7CQEMt0mXlZt-m0qDotA_kg-1MOjy1HheFFqlwZ-z6qCZE07IUHCDWTP33_Uq5_XQ='}], 'role': 'model'}, 'finishReason': 'STOP', 'usageMetadata': {'candidatesTokenCount': 52, 'promptTokenCount': 555, 'promptTokensDetails': [{'modality': 'TEXT', 'tokenCount': 555}], 'totalTokenCount': 607}, 'invocationId': 'e-9116ad2d-09ac-44ba-ba93-4f1a8d6e1d12', 'nodeInfo': {'path': 'glossary_agent@1'}, 'timestamp': 1794035267.5809002}
    ```

- 気づき・疑問：
  - 今回は数行のinstruction + 3個のtoolというミニマルな構成だったため、ハーネスの違い（Pydantic AI / Google ADK）による違いは顕著に見られなかった。
  - Google ADKでは、モデル・instruction・toolsを数行で宣言するだけでエージェントを定義できた。さらにCLIも標準で提供されており、今回の範囲では独自の実行処理を書く必要がなかった。
  - --traceや--jsonlなどで途中のログを詳細に出すことはデバッグや挙動の詳細を把握する上で不可欠と感じた。