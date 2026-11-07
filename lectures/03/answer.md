# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：推測から、データを参照した断定になり完結な回答になった。
- `--trace` で見えたツール呼び出し（ツール名と引数）：[tool call]   search_glossary、[tool return] search_glossary
- 1つの質問での LLM 呼び出し回数（`requests`）：2
- 追加したツールと、docstring に書いた説明：def make_quiz(lecture: int) -> str:
    """指定した回の用語から1つを選び、確認問題と答えを返す。

    「第2回の確認問題を出して」のように、復習用の問題を求められたときに使う。
    返す文字列は、そのまま利用者に見せられる形式にする。
    """
    glossary = load_glossary()
    terms = [term for term in glossary if term.get("lecture") == lecture]

    if not terms:
        available = sorted({str(t["lecture"]) for t in glossary})
        return (
            f"第{lecture}回に対応する用語は見つかりませんでした。"
            f"用意されている回: {', '.join(available)}"
        )

    term = terms[0]
    question = f"第{lecture}回の用語「{term['term']}」の意味は？"
    answer = f"答え: {term['definition']}"
    return f"{question}\n{answer}"

## 宿題

- 取り組んだレベル：基礎 
- やったこと： def search_glossary(query: str) -> str:を変更
①「"""講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。」→　「"""講座の用語集から用語を検索し、定義と、どの回で扱うかをため口にしたうえで返す。」への変更
②「"""講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。」→　「"""講座の用語集から用語を検索し、定義と、どの回で扱うかをポケモンを例にして返す。"」への変更
③「"""講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。」→　「"""講座の用語集から用語を検索し、定義と、どの回で扱うかを必ずポケモンを例にして返す。"」への変更
- 結果：もとの結果からの回答の変化
①ため口に変わった。
②変わらなかった。
③ピカチュウ（ポケモン）の例を交えた。
- 気づき・疑問：絶対という拘束力がある言葉を入れることで生成される内容が指定した設定に忠実かが変わってくる。しかしため口にして返すことについては絶対という拘束力の強い言葉を使わずとも設定が変更された理由が分からなかった。
