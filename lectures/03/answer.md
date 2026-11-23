# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：単に予測して文章を生成するだけでなく検索を挟んで返答を返す。
- `--trace` で見えたツール呼び出し（ツール名と引数）：get_lecture_summary({'lecture': 0})
- 1つの質問での LLM 呼び出し回数（`requests`）：2
- 追加したツールと、docstring に書いた説明：def make_quiz(lecture: int) -> str:
    """指定した回の用語から1つ選び、確認問題と答えを返す。

    「第２回の確認問題を出して」のように、復習用の問題を求められたときに使う
    """
    terms = [term for term in load_glossary() if term["lecture"] == lecture]
    if not terms:
        return f"第{lecture}回の用語が用語集にありません。"

    term = random.choice(terms)
    return json.dumps(
        {
            "question": f"「{term['term']}」の意味は？",
            "answer": term["definition"],
        },
        ensure_ascii=False,
    )


## 宿題

- 取り組んだレベル：基礎 
- やったこと：make_quizで問題、ヒント、答えの順で返すように書き換え、agent.pyのinstructionsに設定した。
- 結果：[model] gemini-3.5-flash-lite
確認問題をお出しします。

**問題：**
「AIエージェント」の意味は？

**ヒント：**
第3回の講義で扱った用語です。関連する用語として agent-loop や tool、harness があります。

**答え：**
LLMが自分で判断してツールを呼び出し、その結果を見てさらに次の行動を決める、というループで目的を達成するシステム。基本構造は「モデル＋ループ＋ツール」。

---
関係する回：第3回

--- trace ---
[tool call]   make_quiz({'lecture': 3})
[tool return] make_quiz -> {"question": "「AIエージェント」の意味は？", "answer": "LLMが自分で判断してツールを呼び出し、その結果を見てさらに次の行動を決める、というループで目的を達成するシステム。基本構造は「モデル＋ループ＋ツール」。…
[usage] RunUsage(cost=Decimal('0.0005967'), details={'text_prompt_tokens': 964}, input_text_tokens=964, input_tokens=964, output_tokens=123, requests=2, tool_calls=1)
make_quizを変更するだけではagentの振る舞いは変わらず、agentのinstructionsを変更することで出力が変化した。
- 気づき・疑問：モデルの出力はツールによって決まるのでもモデルの構造で決まるわけでもない。モデルのInstructionの使用可能なツールの用途があり、出力の形式が定められていてかつ、ツールが必要な情報を返す必要があるのだと感じた。agentの動作の背景がこうなっているのかと初めて知った。
