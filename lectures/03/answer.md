# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
   素のLLMは一般的な知識をもとに回答するのに対し、 エージェントはツールを利用して講義用の用語集を検索し、 その結果を踏まえて回答を生成する点が異なる。
- `--trace` で見えたツール呼び出し（ツール名と引数）：
  [tool call] search_glossary({'query': 'lec01-start'})
- 1つの質問での LLM 呼び出し回数（`requests`）：
  requests = 2
- 追加したツールと、docstring に書いた説明：
  今回は追加ツールの作成は行わなかった。

## 宿題

- 取り組んだレベル：
  基礎
  
- やったこと：
  app/agent.py の INSTRUCTIONS を変更し、同じ質問に対するエージェントの挙動を比較した。
  
  質問： AIE2026の講座で使う「lec01-startタグ」とは何ですか？

  以下の3パターンで実験を行った。
  １．元のINSTRUCTIONS
  ２．「用語や講座に固有のことを答える前に、必ず search_glossary で用語集を確認する。」を削除
  ３．さらに「回の内容を聞かれたら get_lecture_summary を使う。」を削除

- 結果：
  変更前は
  [tool call] search_glossary({'query':'lec01-start'})
  が実行された。

  「用語や講座に固有のことを答える前に、必ず search_glossary で用語集を確認する。」を削除した後も、
  [tool call] search_glossary({'query':'lec01-start'})
  が実行された。

  さらに「回の内容を聞かれたら get_lecture_summary を使う。」を削除した後も
  [tool call] search_glossary({'query':'lec01-start'})
  が実行された。

  いずれの場合も tool_calls=1 であり、用語集検索が実行された。

  一方で回答内容には違いが見られた。変更前は比較的簡潔な回答だったが、変更後は Git のタグやチェックポイントの可能性について補足説明が追加された。

- 気づき・疑問：
  INSTRUCTIONSを変更しても、モデルは自律的に search_glossary を利用した。
  そのため、エージェントの挙動は INSTRUCTIONS のみで決まるのではなく、モデル自身の推論によっても決定されることが分かった。
  また、ツールの利用回数は変わらなかったが回答内容には変化が見られたため、INSTRUCTIONS はツール利用だけでなく回答の表現方法にも影響を与えることが分かった。