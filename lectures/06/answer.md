# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：glossary_search_glossary
- STEP 2 の [tool call]：glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]：fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
- STEP 4 の [tool call]：aws_aws___search_documentation({'search_phrase': 'Amazon S3 バージョニング 概要', 'topics': ['general']})
aws_aws___search_documentation({'search_phrase': 'Using versioning Amazon S3 bucket overview', 'topics': ['general']})
[tool call]   aws_aws___search_documentation({'search_phrase': 'Amazon Route 53 features what is', 'topics': ['general']})

- 気づき・疑問：MCPサーバーを通じて、内部のツールや公開されているサーバーや外部で動くサーバーに接続し、回答を取得できることを確認した。特に、外部動くサーバーに追加の質問を投げたところ、日本語で投げた指示をモデルが適宜英訳し、外部サーバーに投げてることが確認できた。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：基礎、実装及び発展
- やったこと：
  基礎では、app/mcy_sever.pyにget_lecture_summaryをMCPから呼び出せるツールとして登録し、一覧に `glossary_get_lecture_summary` が増えたことを確認した後、質問をしてツールが呼ばれることを確認し、最後にテストが全て通ることを確認した。
  実装では、第３回で一度作成したmake_quizがなくなっていたので、再作成した上で、app/mcy_sever.pyにmake_quizをMCPから呼び出せるツールとして登録し、一覧に `glossary_make_quiz` が増えたことを確認した後、質問をしてツールが呼ばれることを確認し、最後にテストが全て通ることを確認した。
  発展では、特に使っているツールがないので、VS Codeについて、AIを使いながら、調べることを確認した。
- 結果：
  実装では、範囲外となる引数（第99回）で質問を投げた場合、以下のようなreturnをモデルにかえし、モデルは、「第99回の用語や講義内容は、現在の用語集には登録されていないようです。そのため、第99回の確認問題を作成することができません。もし他の回（例えば第1回〜第N回など）のクイズや特定の用語の確認問題をご希望でしたら、何回目またはどの用語について知りたいかお知らせください！と正しく返していた。
  [tool return] glossary_make_quiz -> {"error": "第99回の用語は用語集にありません。"}…
　発展では、調べた結果は以下のとおりです。
　|設定を書く場所	|　プロジェクトで作業する場合は、Workspaceの直下に.mcp.jsonを置く
　|コマンドで起動する書き方	|　演習と同じく、 "command" :コマンドを記載する
　|URL で接続する書き方	|　演習と同じく、”url”:エンドポイントのアドレスを記載する
　|有効になる範囲	|　プロジェクト単位もしくは個別PC単位（個人単位）

- 気づき・疑問：エージェントが都度公開しているツールの一覧をサーバーに問い合わせることから、app.mcp_serverにツールを追加し、MCPサーバー側を変更することで、新たなツールが使えるようになることが確認できた。
