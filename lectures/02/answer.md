# 第2回 解答

## 演習

- 使ったモデル・設定（`result.json` の `config` から）：
  `Qwen/Qwen3.5-0.8B`（revision `2fc06364715b967f1860aea9cf38778875588b17`）、量子化なし（32bit）、LoRA（r=16, alpha=32, dropout 0.05）、lr 2e-4、cosine、warmup 6、20 エポック（40 ステップ）、seed 42、貪欲生成（`do_sample: False`）。
  Versions: transformers 5.18.0, peft 0.21.1, trl 1.14.2, torch 2.14.1+cu130（Google Colab, Tesla T4）
- 自分で学習を実行したか（`executed_training_myself`）：**はい**（実行できた範囲：セクション 0〜8 すべて。ノートブック全体を 3 回実行し、3 回とも同じスコアになった）
- 学習前：`format_rate` = **0.095**（2/21） / `content_rate` = **0.000**（0/21）
- 学習後：`format_rate` = **1.000**（21/21） / `content_rate` = **0.905**（19/21）
- 退行した質問：**なし**（`regressed: []`）
- 学習後に残った失敗と、その型：
  2 問とも同じ型 = **根拠なしの質問に、キーワードが重なる FAQ の別項目を当てはめて断定した**。
  - 「成績はいつ出ますか」（正解 `needs_review: true`）→ 提出期限の文「提出期限は 9 月 30 日 23:59（日本時間）です。」を返し `needs_review: false`
  - 「オフィスアワーは事前予約が必要ですか」（正解 `needs_review: true`）→ オフィスアワーの時間の文を返し `needs_review: false`

  The trigger seems to be surface words: 「いつ」→ deadline line, 「オフィスアワー」→ office-hours line.
  The model learned "find the closest FAQ line and copy it", not "check whether the FAQ really answers the question".
  The opposite failure type (escaping a grounded question with "not listed") and format breaks did not occur.
- 知識を問う質問（セクション 6）の結果（学習前の分類 → 学習後の分類）と気づいたこと：

  | 質問 | FAQ にある | 学習前 → 学習後 |
  |---|---|---|
  | この講座の最終課題の締切はいつですか | いいえ | format_error → **asserted**（通常の課題の締切「9 月 30 日 23:59」を返した） |
  | 担当教員の名前は何ですか | いいえ | format_error → needs_review |
  | 次回の講義のテーマは何ですか | いいえ | format_error → needs_review |
  | 課題の提出期限はいつですか（対照） | はい | format_error → asserted（FAQ にあるので正しい） |

  Training turned 2 of 3 unknown questions into the correct "needs review" answer, but the "**final** assignment deadline"
  was answered with a confident, unsupported assertion. It is the same failure type as Section 5: 「締切」 matched the deadline line.
- 学習で変わったこと・変わらなかったこと：
  - **変わった:** 出力形式（format 0.10 → 1.00）と文面。学習後の回答は FAQ の原文をほぼそのまま返すようになった。プロンプトで JSON を指示しても守れなかった形式が、14 件・約 4 分の学習で完全に揃った。
  - **変わらなかった（保証されなかった）:** 「この質問は FAQ に本当に書いてあるか」という判断。FAQ の語とキーワードが重なる根拠なしの質問には、自信を持って間違えた。
  - **再現性:** 同じ seed で 3 回実行し、スコアも残った 2 問も同じだった。
  - **補足（セクション 8、学習なしの 4bit 読み込み）:** 32bit の学習前 format 0.095 / content 0.000 に対し、4bit（NF4）では format **0.667** / content **0.333**。学習していないのに、量子化だけで出力が大きく変わった。今回は良い方向だったが、方向は一定でないとされるので、結論は「4bit が良い」ではなく「量子化で振る舞いが変わる」。だから学習前後の比較は同じ量子化条件で行う必要がある。

## 宿題

- 取り組んだレベル：**発展（準備まで完了、学習と評価は追加予定）**
- 変えた設定やデータ：
  `scripts/make_sft_dataset.py` で講座の用語集から `messages` 形式の Q&A データ **116 件** を作成した
  （例: user「「AIエンジニアリング」とは何ですか？」→ assistant = 用語集の定義。system プロンプトなし）。
  評価用に 3 グループの質問を用意した：用語集にある語（学習とは別の言い回し「〇〇を簡単に説明してください。」）、
  言い回しを変えた質問（別名・くだけた表現）、用語集にない語（実在の AI 用語と架空の講座項目）。
  さらに比較対象として「用語集を検索して答える仕組み（RAG）」も同じ質問で評価する設計にした。
- 結果（比較表や数字）：用語集での学習・評価の結果はこの PR に追加して更新する。
  現時点の数字は上の演習（学習前後、セクション 6、セクション 8）のとおり。
- ファインチューニングが向く場面・向かない場面についての考察：
  - **向く: 振る舞いと形式を揃えること。** わずか 14 件・約 4 分の LoRA で JSON 形式が 2/21 → 21/21 になった。プロンプトだけでは直らなかった。同じ形式の出力を大量に繰り返すなら、安く効果が大きい。
  - **向かない: 知識と「知らないことを知らないと言う」判断。** 学習後も、FAQ に無い質問に似た行をコピーして断定した。学習で身についたのは「答えの見た目」であって、「答えが無いとき」の判断ではない。これは Gekhman et al. (2024) の「ファインチューニングは新しい知識を加えるのが苦手で、自信のある誤りを増やしうる」という指摘と合う。
  - **用語集を検索する仕組みとの比較:**
    - 検索（RAG）のメリット: 用語が増えたり変わったりしても、データを更新するだけで済み、再学習が要らない。検索で見つからなければ「載っていません」と返せる。どの項目を根拠にしたかを示せる。
    - 学習のメリット: 推論時に毎回資料を渡さないのでプロンプトが短く、速く安い。答え方（形式・口調・長さ）を安定させられる。
    - 学習のデメリット: 知識の追加が苦手で、更新のたびに再学習が必要。似た語に引っ張られて断定する（今回の 2 問のような）誤りが残る。
  - **実務での順番:** まずプロンプトと構造化出力、知識は検索（RAG）、それでも直らない振る舞いだけファインチューニング。評価には必ず「答えられない質問」を入れる。形式のスコアだけでは今回の 2 問のような誤りが見えないため。
