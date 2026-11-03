# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：素のLLMは、根拠がない回答をそれらしく作り出していた。エージェントでは、根拠のない断定を行わず、用語集にある用語から正しい回答を導けた。
- `--trace` で見えたツール呼び出し（ツール名と引数）：  search_glossary({'query': '3レベル'})
- 1つの質問での LLM 呼び出し回数（`requests`）：2回
- 追加したツールと、docstring に書いた説明：
def make_quiz(lecture: int) -> str:
    """用語の理解を確認するクイズを作る。
    指定された回に関連する用語からランダムに1つ選び、クイズを作る。
    """
    if lecture < 1:
        return "講義回は1から指定してください。"
    terms = [term for term in load_glossary() if term["lecture"] == lecture]
    if not terms:
        return f"第{lecture}回に関連する用語が用語集にありません。"

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
- やったこと：用語を一つだけ入れる　→　まとめて全部入れる　に変更
- 結果：変更前は用語が２つあるとtool_callsが2だったが、変更後は1に減った
- 気づき・疑問：
　　指示の仕方で、ツールの呼び出し回数や結果が変わってくる。
　　平易な日本語で書いてあるものでも、ＡＩは指示として読み取ってくれて便利な反面
　　曖昧さにより思いもよらない動作になる不安や、意図しない指示が混入した場合の危険も感じた。
