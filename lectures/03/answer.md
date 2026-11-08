# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
エージェントではツール呼び出しにより，用語集の内容に基づいた回答をしていた．その影響もあってか，素のLLMと比べて input tokens が多くなっていたように思う．

- `--trace` で見えたツール呼び出し（ツール名と引数）：
ツール名：search_glossary
引数：{'query': 'AIエージェント'} など

- 1つの質問での LLM 呼び出し回数（`requests`）：
2回

- 追加したツールと、docstring に書いた説明：
まだできてない

## 宿題

- 取り組んだレベル：基礎

- やったこと：
agent に "AIエージェント、ハーネス、Pi の関係を初心者向けに説明してください。" と送る．
このときに，tools.py の設定で，"用語集をまとめて入れる" に変更して比べてみる．

- 結果：
変更前：
    - tool_calls: 3回
    - requests: 2回
    - input_tokens: 1261
    - output_tokens: 555 

変更後：
    - tool_calls: 1回
    - requests: 2回
    - input_tokens: 855
    - output_tokens: 377 

- 気づき・疑問：
変更前は用語を１語ずつ検索したため tool_calls が3回だったが，変更後は1回に減った．
また，requests 回数は変わらず，input_tokens が減っており，コストが下がったのではないかと考えられる．