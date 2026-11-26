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

- 取り組んだレベル：発展
- やったこと：I completed all 3 levels.
In basic level: I publish the function get_lecture_summary by adding server.tool()(tools.get_lecture_summary) to app/mcp_server.py
In implementation level: I add the make_quiz function as an MCP tool in app/mcp_server.py by the code server.tool()(tools.make_quiz). Then I use the question Create a quiz for Lecture 99.
In advanced level: I choose and research the VS code document at https://code.visualstudio.com/docs/agents/reference/mcp-configuration. Then I compare with app/mcp_servers.json and figure out the differences
- 結果：
In basic level: When I ask question What do we learn in Lecture 2, the trace show [tool call] glossary_get_lecture_summary({'lecture': 2}). It returned the lecture 2 summary on fine-tuning and LoRA which the agent use it to answer with the final result is 21 passed in 4.41s
In implementation level: The trace show one call to `glossary_make_quiz` with `{"lecture": 99}`. The tool returned No glossary terms found for Lecture 99 and explain the reasson, then it ask for ask another lecture instead of hallucinate questions.
In advanced level: VS Code use .mcp.json at the workspace root for project settings. For personal configuration shared across workspaces, the default file is ~/.copilot/mcp-config.json. Both use top key mcpServers. The course agent instead reads app/mcp_servers.json. Moreover, the 2 clients describe connections in the similar ways. For a local server, the clients starts a process use command and args. For homework, the glossary server starts with uv run python -m app.mcp_server. For a HTTP server, the client use URL. And the AWS server connected to `https://knowledge-mcp.global.api.aws`
- 気づき・疑問：I realize that the trace was seeing lec02 that show it selected the right tool and pass the lecture number from the question. Moreover, I understand list tool show the tool was available and trace show the agent call it with the requested lecture number and use its result in the answer. Finally, when moving a server definition to another client, I need to check both connection settings and which configuration file the client read.
