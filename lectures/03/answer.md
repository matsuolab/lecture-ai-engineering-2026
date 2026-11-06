# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：質問から求められていた正しい回答が返ってきた。
- `--trace` で見えたツール呼び出し（ツール名と引数）：search_glossary{'query': 'LoRA'}{'query': 'QLoRA'}
- 1つの質問での LLM 呼び出し回数（`requests`）：２
- 追加したツールと、docstring に書いた説明：
def make_quiz(lecture: int) -> str:
    """指定した回の用語集から確認問題を1問作り、答えと一緒に返す。

    「第2回の確認問題を出して」のように、講座内容の復習問題が求められたときに使う。
    """
    terms = [entry for entry in load_glossary() if entry["lecture"] == lecture]
    if not terms:
        return f"第{lecture}回の用語集には、確認問題に使える用語がありません。"

    entry = random.choice(terms)
    return json.dumps(
        {
            "question": f"「{entry['term']}」の意味は？",
            "answer": entry["definition"],
        },
        ensure_ascii=False,
    )


## 宿題

- 取り組んだレベル：基礎 
- やったこと：agent.pyのINSTRUCTIONSで「回の概要を説明した後は make_quiz を使って用語確認問題を２問出し、答えは利用者が回答するまで明かさない。」と指示を追加した。
- 結果：第●回の概要を説明してと質問すると概要を説明し、そのあと用語問題を２問出題するようになった。しかし、第●回の内容から確認問題を１問出してと質問すると、追加での出題はなかった。
- 気づき・疑問："第2回の内容を説明した後問題を１問出題して"と質問すると概要を説明した後２問出題された。
　　　　　　　　しかし、"第二回の問題を１問出題してそのあと第二回の概要を説明して"と質問すると問題を１問出題した後、概要を説明し、そのあと問題を１問出題してきた。
