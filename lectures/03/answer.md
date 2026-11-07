# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：エージェントは指示に従って用語集を参照しているため、精度の高い回答をだす
- `--trace` で見えたツール呼び出し（ツール名と引数）：search_glossary（ツール名）、引数({'query': 'LoRA'})

- 1つの質問での LLM 呼び出し回数（`requests`）：2回
- 追加したツールと、docstring に書いた説明：
  docstringに書いた内容は"確認問題を求められたら make_quiz を使う"
  追加したツールは、def make_quiz(lecture: int) -> str:
    """指定した回の用語集から確認問題を1問作る。

    利用者が確認問題・復習問題・クイズの出題を求めたときに使う。
    lecture に対象回を整数で渡す。第0回や用語がない回では、用語集に問題を作れる用語がない旨を返す。
    """
    terms = [entry for entry in load_glossary() if entry["lecture"] == lecture]
    if not terms:
        return f"第{lecture}回の確認問題用語が用語集に見つかりませんでした。"

    selected = random.choice(terms)
    return json.dumps(
        {
            "question": f"「{selected['term']}」の意味は？",
            "answer": selected["definition"],
        },
        ensure_ascii=False,
    )

　
## 宿題

- 取り組んだレベル：基礎 / 実装 / 発展
- やったこと：
- 結果：
- 気づき・疑問：
