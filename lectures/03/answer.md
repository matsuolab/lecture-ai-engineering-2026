# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：定義された内容がシンプルになった
- `--trace` で見えたツール呼び出し（ツール名と引数）：search_glossary,引数:LoRAとQLoRA
- 1つの質問での LLM 呼び出し回数（`requests`）：2回
- 追加したツールと、docstring に書いた説明：make_quiz
        """指定した回の用語について、意味を答えるクイズを作る。

        講座用語の確認問題を出したいときに使う。
        lecture には対象の回（1始まりの整数）を指定する。
        """

## 宿題

- 取り組んだレベル：基礎
- やったこと： INSTRUCTIONと、search_glossaryから"答える前に使う"という文言を削除
- 結果：
　　INSTRUCTIONから文言を削除
　　→ [tool return] search_glossaryが消えていない。
　　
　　tools.pyにも"答える前に使う"とあったため、この文言も削除
　　→ [tool return] search_glossaryが消えていない。

　　agent.pyからserch_glossaryを削除
　　→ 回答が変わった。INSTRUCTIONの推測で回答しない、ということに基づき、用語集に登録されていないと回答している。

   (元に戻して) query には調べたい用語をまとめて入れる（例: "LoRA,QLoRA"）に変更する
　　→ tool_callは1回のみ

- 気づき・疑問：
・INSTRUNCTIONの中では、#を利用しても、コメント文にはならず、ただの文字列として扱われ、モデルに渡される。
・docstringの記載を変更しても類似の内容から学習して回答しているのか？
