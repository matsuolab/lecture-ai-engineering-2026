# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：glossary_search_glossary
- STEP 2 の [tool call]：glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]：fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
- STEP 4 の [tool call]：aws_aws___search_documentation({'search_phrase': 'Amazon S3 バージョニング 概要', 'topics': ['general']})
[tool call]   aws_aws___search_documentation({'search_phrase': 'Using versioning in S3 buckets overview', 'topics': ['general']})
- 気づき・疑問：
MCPを利用すると、エージェント側のPythonコードを変更せず、設定ファイルにサーバーを追加するだけで利用できるツールを増やせることが分かった。
glossary、fetch、AWSの順に追加することで、ツールの数が1個から2個、さらに7個に増えることを確認できた。
fetchは自分のCodespaces内で動作するが、AWSのMCPサーバーは外部で動作しており、URLで接続するという違いが分かった。
AWSのドキュメント検索では、AIが日本語と英語で2回検索してから回答していた。検索キーワードによって取得できる情報が異なることが興味深かった。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：実装
- やったこと：
app/tools.py に make_quiz 関数を追加した。
用語集の glossary.json から指定された講義回の用語を取得し、最大3問の復習クイズと模範解答を作成する機能を実装した。
存在しない講義回を指定した場合は、利用可能な講義回を案内するようにした。
app/mcp_server.py に server.tool()(tools.make_quiz) を追加し、MCPサーバーから利用できるようにした。
tests/test_mcp_server.py に、ツールの公開、正常時、範囲外の動作を確認する3つのテストを追加した。
- 結果：
ツール一覧で glossary_make_quiz が公開され、ツールの合計が7個から8個に増えたことを確認した。
第1回のクイズを作成するように指示すると、AIが以下のツールを呼び出し、3問の復習クイズを作成した。
[tool call]   glossary_make_quiz({'lecture': 1})
存在しない第99回のクイズを作成するように指示した場合も、適切に処理された。
[tool call]   glossary_make_quiz({'lecture': 99})
[tool return] glossary_make_quiz -> 第99回のクイズは作成できません。利用可能な講義回: [1, 2, 3, 4, 6]
AIはツールの戻り値をもとに、利用可能な講義回を案内し、どの回のクイズを作成するか質問した。
MCP関連のテスト結果：9 passed in 7.19s
プロジェクト全体のテスト結果：24 passed in 7.55s
- 気づき・疑問：
自分で作成したPython関数をMCPサーバーに登録することで、エージェント側のコードを変更せずに新しい機能を追加できることが分かった。
docstringや型ヒントが、AIがツールを選択し、適切な引数を指定するための情報になることを理解した。
AIはツールから取得したクイズをそのまま表示するのではなく、復習しやすい問題文に再構成していたことが興味深かった。
範囲外の引数に対して分かりやすいメッセージを返すことで、AIもユーザーに適切な案内ができることが分かった。
テストの作成時に、TestModelがcustom_argsに対応していないというエラーが発生した。利用可能な引数を確認し、FunctionModelを使うことで解決できた。
TestModelとFunctionModelを利用することで、実際のLLMやAPIキーを使わずにMCP経由の動作をテストできることを学んだ。
今後は、クイズの出題順をランダムにしたり、問題数を指定できるようにしたりする機能も実装してみたい。
