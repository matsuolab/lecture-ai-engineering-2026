# 第6回 解答

## 宿題

- 取り組んだレベル：基礎 
- やったこと：宿題のSTEP1～4を実施した
- 結果：
　STEP1のツール名：glossary_search_glossary

　STEP3のTOOL CALLの行：[tool call]   glossary_search_glossary({'query': '3レベル'})
[tool return] glossary_search_glossary -> [{"term": "宿題の3レベル", "lecture": 1, "definition": "AIE2026の宿題の構成。「基礎（講義内容の確認）」「実装（自分でコードを書く）」「発展（調査や試行）」の3段階があり、どれか1つに取り組…
[usage] 入力 715 tokens / 出力 182 tokens / モデル応答 2 回

STEP3のTOOL CALLの行：[tool call]   fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
[tool return] fetch_fetch -> Contents of https://modelcontextprotocol.io/:
> ## Documentation Index
> Fetch the complete documentation index at: http…
[usage] 入力 2,228 tokens / 出力 185 tokens / モデル応答 2 回

STEP4のTOOL CALLの行：[tool call]   aws_aws___search_documentation({'search_phrase': 'Amazon S3 バージョニング 概要', 'topics': ['general']})
[tool return] aws_aws___search_documentation -> {'content': {'result': [{'rank_order': 1, 'title': 'querying-aws-s3', 'skill_description': 'Queries S3 object metadata, …
[tool call]   aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'Versioning overview Amazon S3 bucket versions'})
[tool return] aws_aws___search_documentation -> {'content': {'result': [{'rank_order': 1, 'title': 'Amazon S3 FAQs', 'context': '#### What is Versioning?\n\nVersioning …
[usage] 入力 11,463 tokens / 出力 167 tokens / モデル応答 3 回

- 気づき・疑問：だんだんGitの使い方自体には慣れてきた気がする。先生のスライドのjsonコードを書いたり、コマンドを書いたりするのにも慣れてきた。AWSのMCPサーバーにURLで接続する方法も少し理解できた。でも、これをどのように実践の場で活用すればいいのかはまだあまり理解できていない。
