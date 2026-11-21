# 第5回 解答

## 演習

- 回答モデル（実行時の`[model]`）：
- 比較した質問：
- 対象資料（全文投入と他の方式で範囲が違う点も記録）：

### 各方式の結果

| 方式 | 回答の要点・正しさ | 引用ページと根拠 | 時間（秒） | 入力／出力トークン数 | モデル応答回数 | 生成API推定費用（USD） |
|---|---|---|---|---|---|---|
| 全文投入 | ヒントのみを答える|p.51、p.52|4.13 秒|117,025/168| 1 回|$0.035528 USD| 
| ベクトル検索 |要約の説明|p.51、p.52|2.56 秒|入力 3,028 tokens / 出力 224 tokens |2回 | $0.001468 USD|
| Tree |要約の説明|p52|5.31 秒|入力 9,214 tokens / 出力 324 tokens|5回| $0.003574 USD|
| Graph |要約の説明|p52|2.79 秒|入力 5,771 tokens / 出力 183 tokens|2回|$0.002189 USD|

<!-- 未実行・算定不可の場合は、その旨を書いてください。質問を追加した場合は、質問ごとに表を分けてください。 -->

- 検索だけを実行して見つかったページと、その本文で確認できたこと：p52:タイトル: LoRA と QLoRA ：大きなモデルも GPU 1 台で調整できる
- `--trace`で見えたツール呼び出し（ツール名・引数・回数、Treeでたどった目次など）：browse_tree({})等
- 取得した情報が足りなかった例、取得できたのに回答へ使えなかった例：treeでたどったが、p52しか参照してない
- 今回の用途に採用したい方式と、その理由・比較条件の限界：ベクトル検索：低いトークン数で短い時間
- 気づき・疑問：どのようにツリーはたどっているのか。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：実装
- やったこと（変更したファイル・設定・処理、または設計した取得方法）：
load_pagesの変更前と変更後で比較
変更後
def load_pages(source: Path = RAG_SOURCE) -> list[dict]:
    """資料→章→ページのJSONを、対象資料のページ一覧に変換する。"""
    documents = json.loads(source.read_text(encoding="utf-8"))
    pages = []
    for document in documents:
        if document["id"] not in RAG_DOCUMENT_IDS:
            continue
        for section in document["content"]:
            for page in section["content"]:
                page_number=page["id"][-3:]
                page_name=page["id"][:-4]
                page_number_previous=str(int(page_number)-1)
                page_previous=page_name + page_number_previous
                page_number_subsequent=str(int(page_number)+1)
                page_subsequent=page_name + page_number_subsequent
                pages.append({"page_id": page["id"], "document_id": document["id"],
                              "lecture": int(document["id"][3:5]), "document_title": document["title"],
                              "section": section["section"], "title": page["title"],
                              "page": page["page"], "content": page["content"]})
                pages.append({"page_id": page_previous, "document_id": document["id"],
                              "lecture": int(document["id"][3:5]), "document_title": document["title"],
                              "section": section["section"], "title": page["title"],
                              "page": page["page"], "content": page["content"]})
                pages.append({"page_id": page_subsequent, "document_id": document["id"],
                              "lecture": int(document["id"][3:5]), "document_title": document["title"],
                              "section": section["section"], "title": page["title"],
                              "page": page["page"], "content": page["content"]})
- 比較した質問と、固定した条件（モデル・対象資料など）：
uv run python -m app.agent --graph --trace "$AIE_QUESTION"を質問
質問内容："第2回の説明では、LoRAは何を固定し何を学習しますか？ QLoRAは何を加えますか？"
- 結果（変更前後の回答・根拠、`--trace`の出力、時間・トークン数・生成API推定費用など）：
入力トークン：変化なし
出力トークン:183→154
参照ページ:p52のみ→p51とp52
- 改善した例と、残る失敗・制約：p51も参照するようになった。しかし入力トークンが変化してないため、LLMの回答のばらつきによる可能性もいなめない。
- 気づき・疑問：どのようにページ情報をLLMに渡しているのか
