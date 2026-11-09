# 第3回 解答

## 演習

- 第1回(素のLLM)とエージェントの回答の違い
  - 同じ質問「AIE2026の講座の宿題にある「3レベル」とは何ですか？」を用いた。第1回のLLMは講座の資料について情報が無いため推測で出力していたが、今回のエージェントは講座の用語集から検索を行い、講座に沿った内容を正しく出力した。
- `--trace` で見えたツール呼び出し(ツール名と引数)
  - エージェントが利用するツールを文脈に合わせて使い分ける変化が見られた。
    - 「3レベル」の質問では、「3レベル」を検索するために、用語集を検索するツール `search_glossary` を使用した。
    - 「LoRAとQLoRAの違いは？」の質問では、同じ `search_glossary` を、検索語「LoRA」と「QLoRA」で1回ずつ、合わせて2回使った。
    - 「第2回の内容から確認問題を1問出して」の質問では、`make_quiz` を、引数「第2回」で1回使った。
- 1つの質問での LLM 呼び出し回数(`requests`)：3つの質問全てで2回だった。
- 追加したツールと、docstring に書いた説明
  - `make_quiz` を作成した。これは、指定した回の用語を用語集から1つランダムに抽出し「○○の意味は？」という問題と答えを返すツールである。モデルへの説明(docstring)には、次の記載を含めた。

```
利用者が確認問題・クイズ・小テストを求めたときに使う。出題するときは答えを伏せて問題だけを見せ、利用者が答えたあとで答え合わせをする。
```

  - LLMに「確認問題を1問出して」と頼むと `make_quiz` が使用され、エージェントは問題を出力した。
  - 用語のない回(第0回など)を指定されたときは、エラーにせず「用語集にありません」と返すようにした。

## 宿題

- 取り組んだレベル：発展(a) ADK で作り直す
- やったこと：
    - 演習で作った学習支援エージェントから、指示やツール(3件)は変更せず、エージェントの作成部分をGoogleのADKを用いて実装した。
      - LLMは `gemini-3.5-flash-lite` を使用した。
    - ADK の標準の実行方法(`adk run`)は回答しか表示しないので、どのツールを使ったか、LLM に何回問い合わせたかは別途計測した。
      - リポジトリの直下で `PYTHONPATH=. uv run --with google-adk adk run adk_agent/glossary_agent` を実行するとツールの使用状況やターン数が出力される。
- 結果：
    - 演習と同じ3つの質問を行った結果、動作は演習で実装したものからあまり変化しなかった。3つの質問とも、ADK 版は演習版とツールの種類・引数が変わらず、LLM のターン数も 2 回だった。
    - 回答は、どちらも用語集の内容と合致し、指示通り最後に関係する回を示した。文面は実行ごとに多少変化した。たとえば確認問題は用語がランダムに選ばれる仕様上、演習版は「過学習」、ADK 版は「PEFT」が出力された。
 
- 気づき・疑問：
    - ADK と演習版で特に指示を変えなかったため、今回 LLM は同じ動作を行った。ただし、ADK版では意図せずプロンプトが増えていることがわかった。
    - Gemini API の応答から得た入力トークン数を以下に示す。ADK 版の方がどの質問でも 124〜135 tokenほど多かった。

    | 質問 | 演習版 | ADK 版 | 差分 |
    |---|---|---|---|
    | 3レベル | 1055 | 1181 | 126 |
    | LoRAとQLoRAの違い | 1468 | 1592 | 124 |
    | 確認問題 | 988 | 1123 | 135 |

    - この差の理由として、ADK が指示文の最後にプロンプトを追加していることがあげられる。内容とその要因となるコードを以下に示す。

```py
@override
async def run_async(
    self, invocation_context: InvocationContext, llm_request: LlmRequest
) -> AsyncGenerator[Event, None]:
  agent = as_llm_agent(invocation_context)
  if getattr(agent, 'mode', None) != AgentMode.SINGLE_TURN:
    si = f'You are an agent. Your internal name is "{agent.name}".'
    if agent.description:
      si += f' The description about you is "{agent.description}".'
    llm_request.append_instructions([si])
```
https://github.com/google/adk-python/blob/v2.14.0/src/google/adk/flows/llm_flows/prompt/_identity.py#L42
