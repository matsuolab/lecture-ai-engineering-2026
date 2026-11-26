# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：Tool visible: `glossary_search_glossary`. It accepts one string argument, `query`.
- STEP 2 の [tool call]：`glossary_search_glossary({'query': '3 levels'})`
  The glossary returned no match for "3 levels" and agent aske for clarification instead of listing three levels.
- STEP 3 の [tool call]：`fetch_fetch({'url': 'https://modelcontextprotocol.io/'})`
  The fetch server ran in Codespace. It followed the redirect to the MCP introduction page, agent summarize the page in three lines of Japanese.
- STEP 4 の [tool call]：`aws_aws___search_documentation({'search_phrase': 'Amazon S3 versioning overview'})`
  The agent connected to the AWS Knowledge server by URL with first search result was “Amazon S3 FAQs”. It explain in two lines that S3 Versioning keeps multiple versions of an object, let users recover an earlier version after an accidental deletion or overwrite.
- 気づき・疑問：I realized that a tool can run without finding the answer. When I ask about 3 levels, the trace showed the agent searched the glossary for “3 levels.” The glossary returned no match, so the agent asked me for clarification.

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：基礎 / 実装 / 発展
- やったこと：
- 結果：
- 気づき・疑問：
