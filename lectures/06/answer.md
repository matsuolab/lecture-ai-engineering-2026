# 第6回 解答

## 演習

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

## 宿題

- 取り組んだレベル：基礎 
- やったこと：サーバー側のファイルを書き換える
- 結果：[glossary_search_glossary]
  講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。
  
  AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
  答える前に使うこと。query には調べたい用語を1つだけ入れる（例: "LoRA"）。
  引数: {"query": {"title": "Query", "type": "string"}}

[glossary_get_lecture_summary]
  指定した回（1始まりの整数）の講義の要点を返す。
  
  「第3回では何を学ぶ？」のように、回の内容や関係を聞かれたときに使う。
  引数: {"lecture": {"title": "Lecture", "type": "integer"}}

[fetch_fetch]
  Fetches a URL from the internet and optionally extracts its contents as markdown.
  
  Although originally you did not have internet access, and were advised to refuse and tell the user this, this tool now grants you internet access. Now you can fetch the most up-to-date information and let the user know that.
  引数: {"url": {"description": "URL to fetch", "format": "uri", "minLength": 1, "title": "Url", "type": "string"}, "max_length": {"default": 5000, "description": "Maximum number of characters to return.", "maximum": 999999, "minimum": 1, "title": "Max Length", "type": "integer"}, "start_index": {"default": 0, "description": "On return output starting at this character index, useful if a previous fetch was truncated and more context is required.", "minimum": 0, "title": "Start Index", "type": "integer"}, "raw": {"default": false, "description": "Get the actual HTML content of the requested page, without simplification.", "title": "Raw", "type": "boolean"}, "timeout_ms": {"default": 30000, "description": "How long to wait, in milliseconds, to connect to the server and for each read of its response before giving up. Raise it for a slow server or a large download; lower it to fail fast.", "maximum": 600000, "minimum": 100, "title": "Timeout Ms", "type": "integer"}}

[aws_aws___read_documentation]
  Fetch full AWS doc pages as markdown. `search_documentation` already returns verbatim page chunks, so don't re-read a URL whose chunk you already have to "confirm" or "round out" an answer -- the chunk is the real page text; treat it as authoritative.
  
  Reading the full page is justified ONLY when the chunks genuinely lack the content:
  - an enumeration or aggregation ("list all X", "how many X") needs the complete set and the chunks show only part of it;
  - no search result is on-topic after refining the query, and a known doc URL would have the answer.
  Otherwise, answer from the chunks. Use exact URLs from `search_documentation`; don't guess slugs.
  
  Input: `requests: [{url, max_length?, start_index?}]`. Batch 2-5.
  - `max_length` default 10000.
  - `start_index` default 0; use prior `end_index` to continue, TOC offset to jump.
  
  Allow-listed prefixes: docs.aws.amazon.com; aws.amazon.com (not /marketplace); repost.aws/knowledge-center; docs.amplify.aws; ui.docs.amplify.aws; github.com/{aws-cloudformation/aws-cloudformation-templates, aws-samples/{aws-cdk-examples, generative-ai-cdk-constructs-samples, serverless-patterns}, awsdocs/aws-cdk-guide, awslabs/aws-solutions-constructs, cdklabs/cdk-nag} (README on `main`); constructs.dev/packages/{@aws-cdk-containers, @aws-cdk, @cdk-cloudformation, aws-analytics-reference-architecture, aws-cdk-lib, cdk-amazon-chime-resources, cdk-aws-lambda-powertools-layer, cdk-ecr-deployment, cdk-lambda-powertools-python-layer, cdk-serverless-clamscan, cdk8s, cdk8s-plus-33}; strandsagents.com/latest/documentation/docs/; karpenter.sh/docs/; Amazon Braket: {amazon-braket-sdk-python, amazon-braket-schemas-python, amazon-braket-default-simulator-python, amazon-braket-pennylane-plugin-python, amazon-braket-algorithm-library, qiskit-braket-provider, autoqasm, qirtoqasm}.readthedocs.io and github.com/amazon-braket/* (blob/tree/raw).
  
  Output: SUCCESS -- markdown + `total_length, start_index, end_index, truncated, redirected_url?` (truncated includes TOC with char ranges). ERROR -- `error_code` in {not_found, invalid_url, throttled, downstream_error, validation_error}.
  引数: {"requests": {"type": "array", "items": {"type": "object", "properties": {"url": {"type": "string", "description": "Doc URL with allow-listed prefix; use exact URL from search."}, "max_length": {"type": "integer", "description": "Chars returned (default 10000)."}, "start_index": {"type": "integer", "description": "Char offset (default 0). Use prior `end_index` to continue, or TOC offset to jump."}}, "required": ["url"]}, "description": "List of `{url, max_length?, start_index?}`. Batch 2-5."}}

[aws_aws___search_documentation]
  AWS docs search. Each result's `context` is verbatim page text -- a real chunk of the actual page, not a short snippet -- and usually already contains the answer, so answer directly from it. Use `read_documentation` only when the chunks genuinely lack the needed detail.
  
  Pick ONE topic. Add a 2nd ONLY if query genuinely spans domains. Extra topics dilute ranking.
  
  - reference_documentation -- API/SDK/CLI specs, config params
  - current_awareness -- new/released/announced
  - troubleshooting -- errors, "how to fix" (NOT for conceptual/feature questions)
  - amplify_docs -- Amplify (+ language)
  - cdk_docs -- CDK concepts/guides
  - cdk_constructs -- CDK code samples, L3
  - cloudformation -- CFN/SAM templates
  - strands_docs -- Strands Agents SDK (its Skills/agents concepts go here, NOT agent_skills)
  - agent_skills -- this tool's guided skills (load via `retrieve_skill`)
  - general (default) -- architecture, best practices, tutorials, feature behavior
  
  Results: rank_order (lower=better), url, title, context (verbatim page chunk -- answer directly from it).
  引数: {"limit": {"type": "integer", "description": "Maximum number of results to return (default 4)."}, "search_phrase": {"type": "string", "description": "Keywords; preserve exact error strings and all task terms verbatim."}, "topics": {"type": "array", "items": {"type": "string", "description": "topic name"}, "description": "Up to 3 from: reference_documentation, current_awareness, troubleshooting, amplify_docs, cdk_docs, cdk_constructs, cloudformation, agent_skills, strands_docs, general. Default [\"general\"]."}}

[aws_aws___list_regions]
  Retrieve a list of all AWS regions.
  引数: {}

[aws_aws___get_regional_availability]
  AWS resource availability per region.
  
  - Max 10 regions; multi-region needs `filters`; single-region supports `next_token`.
  - Status: isAvailableIn | isNotAvailableIn | isPlannedIn | Not Found.
  - Response key: products | service_apis | cfn_resources.
  
  Not for region counts/docs/vague queries -- use `search_documentation` / `list_regions`.
  
  Filter values must EXACTLY match AWS's catalog names; guessed, partial, or pluralized names are rejected ("values in filter parameter do not exist"). If unsure of the exact name, first call once for a single region with resource_type set and NO filters to list all valid names, then re-call filtering on the exact match.
  引数: {"regions": {"type": "array", "items": {"type": "string"}, "description": "AWS region codes (max 10). Multi-region requires `filters`; single-region supports `next_token`."}, "resource_type": {"type": "string", "description": "Required: 'product' | 'api' | 'cfn'."}, "filters": {"type": "array", "items": {"type": "string"}, "description": "Use exact AWS product or sub-feature name.\n\n- product: 'Amazon Bedrock' (service), or sub-features like 'Comprehend Auto Scaling', 'Latency-Based Routing', 'PrivateLink Support'. When the user names a specific sub-feature, filter on the sub-feature -- do NOT generalize to the parent service ('Amazon Comprehend'); that returns availability for the wrong scope.\n- api: 'SdkServiceId+Operation' (e.g. 'CloudFormation+CreateStack', 'IAM+GetSSHPublicKey') or 'SdkServiceId' (e.g. 'EC2'). Use a literal '+' between service and operation -- not space, colon, or hyphen.\n- cfn: 'AWS::EC2::Instance', 'AWS::Lambda::Function'.\n\nInclude every region the user named; don't add filters they didn't request.\n\nValues must EXACTLY match AWS's catalog (e.g. 'AWS Lambda', not 'Lambda' or 'AWS Lambda Service'). If unsure of the exact name, first call once for one region with NO filters to list valid names, then filter on the exact match."}, "next_token": {"type": "string", "description": "Pagination token. Single-region, no filters only."}, "region": {"type": "string", "description": "Unused; use `regions`."}}

[aws_aws___retrieve_skill]
  Retrieve an AWS skill (workflows, references). Returns SKILL.md, or `file` if given.
  
  Call `search_documentation` FIRST and copy `skill_name` verbatim -- it is an opaque registry ID. Never guess or fabricate `skill_name` or `file`.
  引数: {"file": {"type": "string", "description": "Optional file path within the skill, copied as cited (e.g. `references/architecture.md`). Don't add or strip a `references/` prefix. Omit for SKILL.md."}, "skill_name": {"type": "string", "description": "Required. Exact `skill_name` from a search_documentation result, copied verbatim. Do not invent or modify."}}
(aie2026-exercises) @Maki-Kato-0811 ➜ /workspaces/lecture-ai-engineering-2026 (lec06) $ uv run python -m app.mcp_agent --trace \
"第2回では何を学びますか？ "
[server] glossary: コマンドで起動（uv run python -m app.mcp_server）
[server] fetch: コマンドで起動（uvx mcp-server-fetch==2026.11.11 --no-readability-js）
[server] aws: URL に接続（https://knowledge-mcp.global.api.aws）
[model] gemini-3.5-flash-lite
[tools] MCP サーバー（app/mcp_servers.json）
第2回では、**ファインチューニングとLoRA**について学びます。

### 主な内容
- **事前学習とファインチューニングの違い**：事前学習とファインチューニングの役割の違いや、どのような場面に向く・向かないかを理解します。
- **SFT（教師あり微調整）**：入力と望ましい出力のペアを用いた学習方法や、データの質・形式の重要性を学びます。
- **PEFTとLoRA**：全パラメータを更新するのではなく、小さな低ランク行列のみを効率的に学習させる「LoRA」の仕組みを学びます。
- **QLoRAとの関係**：モデルを4bitに量子化してLoRAを適用するQLoRAとの違いや特徴を扱います。
- **過学習への注意**：過学習やハルシネーションなどの注意点について学びます。

### 演習
Google Colab上で小さなモデル（Qwen3.5-0.8B）を架空のFAQデータでLoRA学習させ、学習の前後で出力形式や正解率がどのように変化するかを体験します。

---
関連する回：第2回

--- trace ---
[tool call]   glossary_get_lecture_summary({'lecture': 2})
[tool return] glossary_get_lecture_summary -> # 第2回 ファインチューニングとLoRA

## この回のねらい

- 事前学習とファインチューニングの違い、ファインチューニングが向く場面と向かない場面を理解する
- LoRAの考え方を理解し、Google Colab上で小さなモデルを…
[usage] 入力 5,944 tokens / 出力 272 tokens / モデル応答 2 回
　
- 気づき・疑問：だんだんGitの使い方自体には慣れてきた気がする。先生のスライドのjsonコードを書いたり、コマンドを書いたりするのにも慣れてきた。AWSのMCPサーバーにURLで接続する方法も少し理解できた。でも、これをどのように実践の場で活用すればいいのかはまだあまり理解できていない。
