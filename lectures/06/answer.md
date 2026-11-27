# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：
[glossary_search_glossary]
- STEP 2 の [tool call]：
[tool call]   glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]：
[tool call]   fetch_fetch({'url': 'https://docs.aws.amazon.com/ja_jp/AmazonS3/latest/userguide/Versioning.html'})
- STEP 4 の [tool call]：
[tool call]   aws_aws___search_documentation({'search_phrase': 'Amazon S3 バージョニング 概要', 'topics': ['general']})
- 気づき・疑問：
awsのMCPが簡単に使えるようになり、MCPのメリットがよくわかった。
fetchサーバを使うための設定が非常に簡単で驚いた。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：基礎
- やったこと：
get_lecture_summaryを自前のmcpサーバーで公開した。
server.tool()(tools.get_lecture_summary)
を追加する。
- 結果：
[tool call]   glossary_get_lecture_summary({'lecture': 3})
公開したtoolが使えていることが確認できた。
- 気づき・疑問：
自作toolをmcpサーバーで公開することが非常に簡単だと感じた。
一方、mcp_servers.jsonに変更は不要であるので、外部から利用する立場だと、
--list-toolsで取得した説明以上のことはわかりにくいことが分かった。
外部MCPを使うときには注意が必要なことも理解できた。