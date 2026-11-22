- TOP=20
    - gemini-3.5-flash-lite
        - output
        ```text

[model] gemini-3.5-flash-lite
                 pydantic-ai v2.57.0 • Python 3.14.7
      / \
     /   \       agent: target • model: google:gemini-3.5-flash-lite • tools: 1 • capabilities: 0
   /___.___\
  /    |    \    observability: off — see every model and tool call live, with cost
/      |      \    set it up free with Logfire and a GitHub login: https://pydantic.dev/ai-setup.md
`---.._|_..---'    or use any OpenTelemetry backend: https://pydantic.dev/docs/ai/logfire/#otel

                 goes away once observability is on — or PYDANTIC_AI_NO_BANNER=1
RAG_TOP_K: 20
Fine-Tuning（FT）を検討するにあたっては、**「安く速く試せる方法から順に試す」**という判断の順番があります（第2回・PDF p.50）。また、実際にFTへ進むためには**6つのチェックリストすべてにチェックがつくこと**が条件となります（第2回・PDF p.58）。

具体的な順番と条件について、以下のヒントを参考に考えてみてください。

### 1. 試す順番（評価から軽量な手法まで）
1. **まず評価セットを作る**
   - 直ったかどうかを測るための評価用セット（質問と期待する答えの組）がなければ、対策の効果を判断できません（第2回・PDF p.50, 58）。
2. **直したい内容が「知識」か「振る舞い」かを見極める**
   - 新しい事実や資料の内容などの「知識」であれば、FTではなく検索して渡す**RAG**を検討します（第2回・PDF p.46, 50）。
   - 出力形式・口調・手順といった「振る舞い」であれば次のステップに進みます（第2回・PDF p.46）。
3. **プロンプトや形式指定で直らないか試す**
   - 指示や例示、APIの機能（構造化出力など）で直るのであれば、それが最も安く速い解決策になります（第2回・PDF p.50, 53）。
4. **それでも直らない場合にFine-Tuningを検討する**
   - プロンプト等では解決しない、根強い「振る舞い」の課題に対してFTを検討します（第2回・PDF p.50）。

---

### 2. Fine-Tuningに進むための条件（チェックリスト）
以下の6つの条件すべてにチェックが揃ったら、LoRAやQLoRAを用いて小さめのモデルから小さく始めるべきとされています（第2回・PDF p.58）。

1. **学習用とは別の、評価セットがある**（直ったかを測るため）
2. **直したいのは「振る舞い」（形式・口調・手順）であり、「知識」ではない**（知識はFTでは入りにくく誤りが増えるため）
3. **プロンプト・形式指定・RAGでは直らなかった**（安く速く試せる方を先に終えているため）
4. **品質のそろった手本を、数百件以上用意できる**（手本の質が振る舞いを決めるため）
5. **費用対効果が合っている（効果 ＞ FTの費用）**
6. **壊れてほしくない能力も、前後で測る計画がある**（忘却や過剰適合を防ぐため）

まずはご自身が直したい課題が「知識」と「振る舞い」のどちらに該当するか、そして評価セットや手本の準備がどの程度できているかを確認してみてください。

--- trace ---
[tool call]   search_materials({'query': 'Fine-Tuning 検討 順番 条件'})
[tool return] search_materials -> {"results": [{"page_id": "lec02-main-p058", "document_id": "lec02-main", "lecture": 2, "document_title": "基盤モデルの仕組み", "s…
[time] 回答完了まで 7.39 秒（検索・埋め込みを含む）
[usage] 入力 8,199 tokens / 出力 679 tokens / モデル応答 2 回
[cost] 生成APIの推定コスト: $0.004157 USD（埋め込み・索引構築分は含まない）
        ```

    - gemini-3.1-flash-lite
        - output
        ```text

[model] gemini-3.1-flash-lite
                 pydantic-ai v2.57.0 • Python 3.14.7
      / \
     /   \       agent: target • model: google:gemini-3.1-flash-lite • tools: 1 • capabilities: 0
   /___.___\
  /    |    \    observability: off — see every model and tool call live, with cost
/      |      \    set it up free with Logfire and a GitHub login: https://pydantic.dev/ai-setup.md
`---.._|_..---'    or use any OpenTelemetry backend: https://pydantic.dev/docs/ai/logfire/#otel

                 goes away once observability is on — or PYDANTIC_AI_NO_BANNER=1
RAG_TOP_K: 20
Fine-Tuning（FT）を検討する際は、闇雲に試すのではなく、安く速く試せる方法から順に評価を行い、段階的に進めることが推奨されています（第2回・PDF p.50）。

ご質問の「順序」と「進めるべき条件」について、講義資料の内容に基づき回答します。

### 1. 検討・試行の順番
以下の順序で検討し、評価で確かめながら進めます。

1.  **評価セットを作る**：直ったかどうかを判断するために、評価用の問題集を作成します（第2回・PDF p.50, p.61）。
2.  **知識か、振る舞いかを確認する**：
    *   知識の問題であれば、検索して渡す（RAG）手法を優先します（第2回・PDF p.50, p.53）。
    *   振る舞い（形式・口調・手順など）の問題であれば、次へ進みます（第2回・PDF p.20, p.28）。
3.  **プロンプト等で解決できないか試す**：まずはプロンプトやAPIの形式指定などを試し、それで十分であればFTは不要です（第2回・PDF p.50, p.53）。
4.  **Fine-Tuningを検討する**：上記で直らない場合に初めてFTを検討します（第2回・PDF p.50）。

### 2. Fine-Tuningに進むための条件
FTを実施するかどうかは、以下のチェックリストすべてにチェック（✓）が付くことが目安です（第2回・PDF p.58）。

1.  **学習用とは別の、評価セットがある**（直ったかを測るため）
2.  **直したいのは振る舞いである**（知識はFTでは入りにくく、誤りも増えるため）
3.  **プロンプト・形式指定・RAGでは直らなかった**（安く速く試せる方から実施した結果）
4.  **品質のそろった手本を、数百件以上用意できる**（手本の質が振る舞いを決めるため）
5.  **コスト ＜ 効果**（削減額 × 件数などがFTの費用を上回る計画があること）
6.  **壊れてほしくない能力も前後で測る計画がある**（忘却や過剰適合を防ぐため）

---

**ヒント：**
FTに進む際は、いきなり大規模に行うのではなく、LoRAやQLoRAを用いて小さめのモデルから小さく始めることが重要です。また、FTは「コストを下げる（短いプロンプトで済むようにする）」ための手段としても活用できますので、費用対効果の観点も考慮してみてください（第2回・PDF p.49, p.58）。

もし「何をどう測るか」や「手本の質」について詳しく知りたい場合は、評価セットに関する第4回の資料も併せて確認することをお勧めします。

--- trace ---
[tool call]   search_materials({'query': 'Fine-Tuning 検討 順番 条件'})
[tool return] search_materials -> {"results": [{"page_id": "lec02-main-p058", "document_id": "lec02-main", "lecture": 2, "document_title": "基盤モデルの仕組み", "s…
[time] 回答完了まで 5.70 秒（検索・埋め込みを含む）
[usage] 入力 8,199 tokens / 出力 691 tokens / モデル応答 2 回
[cost] 生成APIの推定コスト: $0.003086 USD（埋め込み・索引構築分は含まない）

        ```
- TOP=10
    - gemini-3.5-flash-lite
        - output
        ```text

[model] gemini-3.5-flash-lite
                 pydantic-ai v2.57.0 • Python 3.14.7
      / \
     /   \       agent: target • model: google:gemini-3.5-flash-lite • tools: 1 • capabilities: 0
   /___.___\
  /    |    \    observability: off — see every model and tool call live, with cost
/      |      \    set it up free with Logfire and a GitHub login: https://pydantic.dev/ai-setup.md
`---.._|_..---'    or use any OpenTelemetry backend: https://pydantic.dev/docs/ai/logfire/#otel

                 goes away once observability is on — or PYDANTIC_AI_NO_BANNER=1
RAG_TOP_K: 10
Fine-Tuning（FT）を検討する前にどのような順番で何を試すべきか、また、どういう条件が揃ったらFTに進むべきかについては、講義資料に明確な判断の順番とチェックリストが示されています。

以下のステップと条件を確認しながら進めてみてください。

### 1. 試す順番（安く速く試せる方法から順に）
モデルの出力に不満がある場合、いきなりFine-Tuningを行うのではなく、以下の順番で確認と対策を行います。

1. **まず評価セットを作る**
   - 直ったかどうかを客観的に測るための評価セット（学習用とは別のセット）を準備します。（第2回・PDF p.50, p.58）
2. **直したいのは「知識」か「振る舞い」かを分ける**
   - **知識**（新しい事実や最新の資料など）の場合：FTで覚えさせるのは非効率であり誤りも増えるため、検索して渡す **RAG** などを検討します。（第2回・PDF p.46, p.50）
   - **振る舞い**（出力形式、口調、手順など）の場合：次のステップへ進みます。（第2回・PDF p.46, p.50）
3. **プロンプト（指示・例示）で直るか試す**
   - プロンプトの工夫や形式指定で直る場合は、それが最も安く速い手段となります。（第2回・PDF p.50）
4. **それでも直らない振る舞いがある場合にFine-Tuningを検討する**（第2回・PDF p.50）

---

### 2. Fine-Tuningに進むための条件（チェックリスト）
資料では、以下の**6つの条件すべてにチェック（✓）が付いたら**Fine-Tuningに進むべきだとされています。（第2回・PDF p.58）

1. **学習用とは別の、評価セットがある**
   - 直ったかを測るため。（第2回・PDF p.58）
2. **直したいのは振る舞い（形式・口調・手順）で、知識ではない**
   - 知識はFTで入りにくく、誤りも増えるため。（第2回・PDF p.58）
3. **プロンプト・形式指定・RAGでは直らなかった**
   - より安く速く試せる方法を先に行うため。（第2回・PDF p.58）
4. **品質のそろった手本を、数百件以上用意できる**
   - 手本の質が振る舞いを決めるため。（第2回・PDF p.58）
5. **「削減額 × 件数」または「効果」が、FTの費用（再学習を含む）を上回る**
   - コスト ＜ 効果 の関係を満たすため。（第2回・PDF p.58）
6. **壊れてほしくない能力も、前後で測る計画がある**
   - 忘却や過剰適合が起きるのを防ぐため。（第2回・PDF p.58）

すべてにチェックが付いた場合は、いきなり大規模に行うのではなく、LoRA / QLoRAを用いて小さめのモデルや数百件程度の少なめの手本から小さく始めることが推奨されています。（第2回・PDF p.58）

--- trace ---
[tool call]   search_materials({'query': 'Fine-Tuning 検討 順番 条件'})
[tool return] search_materials -> {"results": [{"page_id": "lec02-main-p058", "document_id": "lec02-main", "lecture": 2, "document_title": "基盤モデルの仕組み", "s…
[time] 回答完了まで 6.98 秒（検索・埋め込みを含む）
[usage] 入力 4,348 tokens / 出力 777 tokens / モデル応答 2 回
[cost] 生成APIの推定コスト: $0.003247 USD（埋め込み・索引構築分は含まない）

        ```
    - gemini-3.1-flash-lite
        ```text

[model] gemini-3.1-flash-lite
                 pydantic-ai v2.57.0 • Python 3.14.7
      / \
     /   \       agent: target • model: google:gemini-3.1-flash-lite • tools: 1 • capabilities: 0
   /___.___\
  /    |    \    observability: off — see every model and tool call live, with cost
/      |      \    set it up free with Logfire and a GitHub login: https://pydantic.dev/ai-setup.md
`---.._|_..---'    or use any OpenTelemetry backend: https://pydantic.dev/docs/ai/logfire/#otel

                 goes away once observability is on — or PYDANTIC_AI_NO_BANNER=1
RAG_TOP_K: 10
Fine-Tuning（FT）の検討にあたっては、闇雲に進めるのではなく、安く速く試せる方法から順に評価を行い、段階を踏んで判断することが推奨されています。

### 検討の順番
以下の順序で「評価」を繰り返しながら、解決策を探ってください。

1.  **評価セットを作る**：直ったかどうかを客観的に測るため、評価用の質問セットを準備します（第2回・PDF p.50, p.61）。
2.  **原因を分ける**：直したい内容が「知識」なのか「振る舞い（形式・口調・手順）」なのかを判断します（第2回・PDF p.50）。
3.  **まずは他の手法を試す**：
    *   **知識に関する問題**：RAG（資料を渡す）や検索を活用します（第2回・PDF p.20, p.50）。
    *   **振る舞いに関する問題**：まずはプロンプトによる指示や例示（few-shot）で改善を試みます（第2回・PDF p.20, p.50）。
4.  **それでも直らない場合**：ここで初めてFine-Tuningの検討に進みます（第2回・PDF p.50）。

---

### Fine-Tuningに進むためのチェックリスト
FTに進む際は、以下の6つの項目すべてにチェックが入る状態である必要があります（第2回・PDF p.58）。

1.  **学習用とは別の評価セットがある**：改善の成否を測るため（第2回・PDF p.58）。
2.  **直したいのは振る舞いである**：知識の追加には不向きであり、誤りも増える可能性があるため（第2回・PDF p.58）。
3.  **プロンプトやRAGでは直らなかった**：より安く速い手段が有効でないことの確認（第2回・PDF p.58）。
4.  **品質のそろった手本を数百件以上用意できる**：手本の質が振る舞いを決定するため（第2回・PDF p.58）。
5.  **コストに対して効果が見合う**：FTの費用（再学習コスト含む）よりも削減額や効果が大きいこと（第2回・PDF p.58）。
6.  **「壊れてほしくない能力」を測る計画がある**：FTによって本来備わっていた能力が失われたり（忘却）、過剰適合が起きたりするリスクへの対策（第2回・PDF p.58）。

**ヒント：**
すべてにチェックが入った場合は、最初から大規模に行うのではなく、LoRA/QLoRAを用いて小さめのモデルから小さく始めることが重要です。その際、FTの前後で同じ評価を行い、直ったものとそうでないものを正確に記録してください（第2回・PDF p.58, p.61）。

--- trace ---
[tool call]   search_materials({'query': 'Fine-Tuning 検討 順番 条件'})
[tool return] search_materials -> {"results": [{"page_id": "lec02-main-p058", "document_id": "lec02-main", "lecture": 2, "document_title": "基盤モデルの仕組み", "s…
[time] 回答完了まで 4.62 秒（検索・埋め込みを含む）
[usage] 入力 4,348 tokens / 出力 676 tokens / モデル応答 2 回
[cost] 生成APIの推定コスト: $0.002101 USD（埋め込み・索引構築分は含まない）


        ```
- TOP=1
    - gemini-3.5-flash-lite
        ```text

[model] gemini-3.5-flash-lite
                 pydantic-ai v2.57.0 • Python 3.14.7
      / \
     /   \       agent: target • model: google:gemini-3.5-flash-lite • tools: 1 • capabilities: 0
   /___.___\
  /    |    \    observability: off — see every model and tool call live, with cost
/      |      \    set it up free with Logfire and a GitHub login: https://pydantic.dev/ai-setup.md
`---.._|_..---'    or use any OpenTelemetry backend: https://pydantic.dev/docs/ai/logfire/#otel

                 goes away once observability is on — or PYDANTIC_AI_NO_BANNER=1
RAG_TOP_K: 1
Fine-Tuning（FT）を検討する前に試すべき順番と、FTに進むための条件（チェックリスト）について、講義資料に以下の通り記載されています。

### 1. Fine-Tuningに進む前に試すべき順番・ステップ
コストが低く手軽に試せる方法から順に検証を行います。
1. **評価セットづくり**（直ったかを測るため、学習用とは別の評価セットを用意する）
2. **プロンプトの工夫・形式指定の調整**
3. **RAG（Retrieval-Augmented Generation）の活用**

（※上記の段階や手法で直らなかった場合に、次のステップとしてFine-Tuningを検討します）
（第2回・PDF p.58）

---

### 2. Fine-Tuningに進むための条件（6つのチェックリスト）
以下の**6つすべてに「✓」が付いたら**、Fine-Tuningに進むべきであるとされています。

1. **学習用とは別の、評価セットがある**
   - 直ったかを測れないと判断できないため。
2. **直したいのは振る舞い（形式・口調・手順）であり、知識ではない**
   - 知識はFTで入りにくく、誤りも増えるため。
3. **プロンプト・形式指定・RAG では直らなかった**
   - 安く速く試せる方から順に行うため。
4. **品質のそろった手本を、数百件以上用意できる**
   - 手本の質が振る舞いを決めるため。
5. **削減額 × 件数、または効果 ＞ FT の費用（再学習も含む）**
   - コストが効果を上回る（コスト ＜ 効果）必要があるため。
6. **壊れてほしくない能力も、前後で測る計画がある**
   - 忘却や過剰適合が起きるため。

1つでも満たされない項目がある場合は、評価セットづくりやプロンプト、RAGの検討に戻るべきとされています。
（第2回・PDF p.58）

--- trace ---
[tool call]   search_materials({'query': 'Fine-Tuning 検討 順番 条件'})
[tool return] search_materials -> {"results": [{"page_id": "lec02-main-p058", "document_id": "lec02-main", "lecture": 2, "document_title": "基盤モデルの仕組み", "s…
[time] 回答完了まで 7.08 秒（検索・埋め込みを含む）
[usage] 入力 1,093 tokens / 出力 485 tokens / モデル応答 2 回
[cost] 生成APIの推定コスト: $0.001540 USD（埋め込み・索引構築分は含まない）


        ```
    - gemini-3.1-flash-lite
        ```text

[model] gemini-3.1-flash-lite
                 pydantic-ai v2.57.0 • Python 3.14.7
      / \
     /   \       agent: target • model: google:gemini-3.1-flash-lite • tools: 1 • capabilities: 0
   /___.___\
  /    |    \    observability: off — see every model and tool call live, with cost
/      |      \    set it up free with Logfire and a GitHub login: https://pydantic.dev/ai-setup.md
`---.._|_..---'    or use any OpenTelemetry backend: https://pydantic.dev/docs/ai/logfire/#otel

                 goes away once observability is on — or PYDANTIC_AI_NO_BANNER=1
RAG_TOP_K: 1
Fine-Tuning（FT）を検討する際は、いきなり実施するのではなく、講義資料で示されているチェックリストに従って段階的に試すことが推奨されています。

第2回講義資料p.58の「Fine-Tuningする前のチェックリスト」によると、**以下の6項目すべてにチェックがつく状態**になったら、FTの実施に進むべきとされています。

### FT検討のチェックリスト（すべて満たす必要がある）

1.  **評価セットの準備**: 学習用とは別に、モデルが改善したかを客観的に測定するための評価セットがあること。
2.  **目的の明確化**: 修正したいのが「知識」ではなく「振る舞い（形式・口調・手順）」であること。（知識はFTで入りにくく、誤情報が増えるリスクがあるため）
3.  **代替手段の検討**: プロンプトエンジニアリング、形式指定、RAGなどの「より安く速く試せる手法」を試したが、解決しなかったこと。
4.  **手本データの品質と量**: 品質のそろった手本データを数百件以上用意できること。（手本の質が振る舞いを決定するため）
5.  **費用対効果**: FTにかかるコスト（再学習費用含む）が、削減額や改善効果を上回っていること。
6.  **能力低下への対策**: FTによって本来維持したい能力が損なわれないよう、前後で能力を測定・監視する計画があること。

### 推奨される検討の順番
もし上記の項目で一つでも「いいえ（✗）」がある場合は、FTには進まず、以下の手順に戻って試すことが推奨されています（第2回・p.58）。

*   **まずは評価セットづくり**: 改善を測る基準を確立する。
*   **プロンプトエンジニアリングの試行**: 指示の出し方を工夫する。
*   **RAGの検討**: 知識の補完が必要であればRAGで対応できないか検討する。

これらを試し、それでも解決しない場合に初めて、LoRA/QLoRAを用いて小さめのモデルからFTを小さく始めるのが良いとされています。

まずは、ご自身の抱えている課題が「知識不足」なのか「振る舞いの問題」なのかを分類し、よりコストの低いプロンプト調整やRAGで解消できないかという視点で検証を進めてみてください。

--- trace ---
[tool call]   search_materials({'query': 'Fine-Tuning 検討 順番 条件'})
[tool return] search_materials -> {"results": [{"page_id": "lec02-main-p058", "document_id": "lec02-main", "lecture": 2, "document_title": "基盤モデルの仕組み", "s…
[time] 回答完了まで 4.62 秒（検索・埋め込みを含む）
[usage] 入力 1,093 tokens / 出力 541 tokens / モデル応答 2 回
[cost] 生成APIの推定コスト: $0.001085 USD（埋め込み・索引構築分は含まない）


        ```
- TOP=5
    - gemini-3.5-flash-lite
        ```text


[model] gemini-3.5-flash-lite
                 pydantic-ai v2.57.0 • Python 3.14.7
      / \
     /   \       agent: target • model: google:gemini-3.5-flash-lite • tools: 1 • capabilities: 0
   /___.___\
  /    |    \    observability: off — see every model and tool call live, with cost
/      |      \    set it up free with Logfire and a GitHub login: https://pydantic.dev/ai-setup.md
`---.._|_..---'    or use any OpenTelemetry backend: https://pydantic.dev/docs/ai/logfire/#otel

                 goes away once observability is on — or PYDANTIC_AI_NO_BANNER=1
RAG_TOP_K: 5
Fine-Tuning（FT）を検討する際には、安く速く試せる方法から順に確かめていく必要があります（第2回・PDF p.50）。

### 1. 試す順番（判断のステップ）
1. **まず評価セットを作る**：直ったかどうかを客観的に測るため、評価セットを最初用意します（第2回・PDF p.50, 58）。
2. **直したい内容を分ける**（知識か、振る舞いか）：
   - **知識**（新しい事実や資料の中身）の場合：検索して渡す（RAG）などを用います（第2回・PDF p.28, 46, 50）。
   - **振る舞い**（出力形式・口調・手順）の場合：次のステップに進みます（第2回・PDF p.28, 46）。
3. **プロンプト（指示・例示）で直るか試す**：プロンプトや形式指定で直る場合は、そちらの方が安く速いため十分と判断します（第2回・PDF p.50）。
4. **それでも直らない振る舞いがある場合**に、はじめてFine-Tuningを検討します（第2回・PDF p.50）。

---

### 2. Fine-Tuningに進むための6つの条件
チェックリストの6つすべてにチェック（✓）が揃ったら、FTに進むべきとされています（第2回・PDF p.58）。

1. **学習用とは別の、評価セットがある**（直ったかを測るため）
2. **直したいのは知識ではなく、振る舞い（形式・口調・手順）である**（知識はFTでは入りにくく、誤りも増えるため）
3. **プロンプト・形式指定・RAGでは直らなかった**（安く速く試せる方を先に試すため）
4. **品質のそろった手本を、数百件以上用意できる**（手本の質が振る舞いを決めるため）
5. **削減額×件数、または効果 ＞ FTの費用（再学習も含む）**（コストよりも効果が上回るため）
6. **壊れてほしくない能力も、前後で測る計画がある**（忘却や過剰適合を防ぐため）

1つでも満たされない項目がある場合は、評価セットづくりやプロンプト、RAGなどの手前に戻って検証することになります（第2回・PDF p.58）。

--- trace ---
[tool call]   search_materials({'query': 'Fine-Tuning 検討 順番 条件'})
[tool return] search_materials -> {"results": [{"page_id": "lec02-main-p058", "document_id": "lec02-main", "lecture": 2, "document_title": "基盤モデルの仕組み", "s…
[time] 回答完了まで 7.27 秒（検索・埋め込みを含む）
[usage] 入力 2,350 tokens / 出力 589 tokens / モデル応答 2 回
[cost] 生成APIの推定コスト: $0.002178 USD（埋め込み・索引構築分は含まない）


        ```
    - gemini-3.1-flash-lite
        ```text


[model] gemini-3.1-flash-lite
                 pydantic-ai v2.57.0 • Python 3.14.7
      / \
     /   \       agent: target • model: google:gemini-3.1-flash-lite • tools: 1 • capabilities: 0
   /___.___\
  /    |    \    observability: off — see every model and tool call live, with cost
/      |      \    set it up free with Logfire and a GitHub login: https://pydantic.dev/ai-setup.md
`---.._|_..---'    or use any OpenTelemetry backend: https://pydantic.dev/docs/ai/logfire/#otel

                 goes away once observability is on — or PYDANTIC_AI_NO_BANNER=1
RAG_TOP_K: 5
Fine-Tuning（FT）の検討にあたっては、いきなり着手するのではなく、まずは「より安く速く試せる方法」から順に実施し、その効果を評価することが重要です。

### 1. 検討の順番
以下の順序で打ち手を試すことが推奨されています。

1.  **評価セットの作成**：直ったかどうかを客観的に測るため、評価セットを用意します（第2回・p.50, p.58）。
2.  **知識か振る舞いかの切り分け**：
    *   知識の問題であれば、検索して渡す（RAG）を検討します（第2回・p.50, p.46）。
    *   形式・口調・手順などの「振る舞い」の問題であれば、次のステップへ進みます（第2回・p.28, p.46）。
3.  **プロンプトによる改善**：指示や例示（プロンプト）で改善できないか試します（第2回・p.50）。
4.  **Fine-Tuningの検討**：上記を試しても直らない振る舞いがある場合に検討します（第2回・p.50）。

---

### 2. 進めるためのチェックリスト
以下の6つの項目すべてにチェックが付いた場合に、初めてFine-Tuningを進めるべきとされています（第2回・p.58）。

1.  **評価セットの存在**：学習用とは別の、評価セットを用意していること。（直ったかを測れないと判断できないため）
2.  **目的の明確化**：直したい対象が「振る舞い（形式・口調・手順）」であること。（知識はFTで入りにくく、誤りも増えるため）
3.  **既存手段の限界**：プロンプト、形式指定、RAGで試したが直らなかったこと。（安く速く試せる方法を優先するため）
4.  **手本の準備**：品質の揃った手本を数百件以上用意できること。（手本の質が振る舞いを決めるため）
5.  **費用対効果**：FTの費用（再学習コスト含む）に対して、期待できる効果や削減額が上回ること。
6.  **能力維持の計画**：FT前後で「壊れてほしくない能力」が維持されているかを測定する計画があること。（忘却や過剰適合が発生するリスクがあるため）

### ヒント
もし上記のチェックリストで一つでも満たせていない項目がある場合は、無理にFTへ進まず、評価セットの整備やプロンプト・RAGの改善に立ち戻るのが良いとされています（第2回・p.58）。

--- trace ---
[tool call]   search_materials({'query': 'Fine-Tuning 検討 順番 条件'})
[tool return] search_materials -> {"results": [{"page_id": "lec02-main-p058", "document_id": "lec02-main", "lecture": 2, "document_title": "基盤モデルの仕組み", "s…
[time] 回答完了まで 4.30 秒（検索・埋め込みを含む）
[usage] 入力 2,350 tokens / 出力 626 tokens / モデル応答 2 回
[cost] 生成APIの推定コスト: $0.001526 USD（埋め込み・索引構築分は含まない）


        ```
