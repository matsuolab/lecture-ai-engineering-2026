# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：本講座でのレベルの定義を正確に回答している。
- `--trace` で見えたツール呼び出し（ツール名と引数）：
    [tool call]   search_glossary({'query': 'LoRA'})
    [tool call]   search_glossary({'query': 'QLoRA'})
    [tool return] search_glossary -> [{"term": "LoRA", "lecture": 2, "definition": "事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法。学習するパラ…
    [tool return] search_glossary -> [{"term": "QLoRA", "lecture": 2, "definition": "ベースモデルの重みを4ビットなどに量子化してメモリを節約したうえで、LoRAで学習する手法。より大きなモデルを小さなGPUで扱える。本講座の第2…
- 1つの質問での LLM 呼び出し回数（`requests`）：2回
- 追加したツールと、docstring に書いた説明：
    def make_quiz(lecture: int) -> str:
    """指定した回の用語から1つを選び、確認問題と答えを返す。

    「第2回の確認問題を出して」のように、復習用の問題を求められたときに使う。
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

- 取り組んだレベル：実装
- やったこと：app/tools.pyにsave_learning_logを実装、app/agent.pyにsave_learning_logを追加、エージェントの output_type に DeferredToolRequests を追加
　def save_learning_log(topic: str, note: str) -> str:
    """学習の記録をlearning_log/に保存する。

    学習内容を記録したいと利用者が頼んだときに使う。保存前に必ず利用者の確認を得る。
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{datetime.now():%Y%m%d_%H%M%S_%f}_{uuid4().hex}.json"
    path = LOG_DIR / filename
    path.write_text(
        json.dumps({"topic": topic, "note": note}, ensure_ascii=False),
        encoding="utf-8",
    )
    return f"学習記録を保存しました: {path.name}"
　
- 結果：toolは参照して使用されているが、実際にCLIで承認をする前にセッションが切れてしまう
- 気づき・疑問：CLIで承認をする前にセッションが切れてしまうのがなぜか不明
