# 第2回 解答

## 演習

- 使ったモデル・設定（`result.json` の `config` から）：Qwen3.5-0.8B, r=16, lr=2e-4, 20 epochs
- 自分で学習を実行したか（`executed_training_myself`）：はい 
- 学習前：`format_rate` =　 9.52% / `content_rate` =　0
- 学習後：`format_rate` =　 100% / `content_rate` =　 90.48%
- 退行した質問： なし
- 学習後に残った失敗と、その型（根拠なしの質問に断定した / 根拠ありの質問に確認要求で逃げた / 形式の崩れ）： 根拠なしの質問に断定した («成績はいつ出ますか», «オフィスアワーは事前予約が必要ですか».)
- 知識を問う質問（セクション 6）の結果（学習前の分類 → 学習後の分類）と気づいたこと：

| Question | Before training | After training|
| --- | --- | --- |
| この講座の最終課題の締切はいつですか | format_error | asserted |
| 担当教員の名前は何ですか | format_error | needs_review |
| 次回の講義のテーマは何ですか | format_error | needs_review |
| 課題の提出期限はいつですか | format_error | asserted |

気づいたこと： The model confidently hallucinated when answering a question about the deadlines for submitting assignments or the final exam. The answer it provided was exactly what it had memorized, but in the context of the actual question asked, it was incorrect.
- 学習で変わったこと・変わらなかったこと：
The format has evolved without regressions, yet the model still confidently gets certain questions wrong.

## 宿題

- 取り組んだレベル：基礎 / 実装 / 発展
### 基礎：LoRAランクの比較: 
I have changed the `lora_r` from 16 to 8. Another settings was unchanged.

| Metric | r=16 | r=8 |
| --- | ---: | ---: |
| Trainable parameters | 6,389,760 | 3,194,880 |
| Final training loss (step 40) | 0.014062 | 0.013375 |
| Training time | 580 s | 376 s |
| format_rate (after training) | 100% | 100% |
| content_rate (after training) | 90.48% | 95.24% |

Reducing the `lora_r` value from 16 to 8 halved the number of trainable parameters and cut training time by approximately 35%. In both configurations, the model achieved 100% compliance with the required JSON format.
Although content accuracy improved from 90.48% to 95.24%, the evaluation was based on only 21 questions—meaning the difference amounts to just a single question. Consequently, it cannot be concluded that a rank of 8 is consistently superior to others.
Moreover, even with a rank of 8, there were instances where the system failed to identify the need for pre-registration confirmation—a point not covered in the FAQ.
These results suggest that while fine-tuning is effective for enforcing JSON formatting and response styles, it is difficult to entirely prevent the generation of unfounded or incorrect answers.

### 実装：医療情報管理システムのFAQによるLoRA学習: 

| Metric | Before training | After training |
| --- | ---: | ---: |
| format_rate | 19.05% | 100% |
| content_rate | 0% | 80.95% |
| both_rate | 0% | 80.95% |

Following the training, all 21 items were output in the correct JSON format. Furthermore, for the 6 questions that lacked supporting data in the FAQ, the system correctly identified all of them as requiring `needs_review=true`.
On the other hand, out of the 15 questions for which answers were available in the FAQ, 4 were incorrectly flagged as requiring further review.
The training process took 364 seconds, with a final recorded error of 0.014994.

How I made the "no basis" (UNGROUNDED) questions: I took my FAQ and thought about what a person would naturally ask next about this project, but what is not written there. For example, the GPU, the final accuracy, the dataset size, the deadline, partner hospitals. I tried to keep them close to the FAQ topics, so the model can't just notice "this is about something else" and refuse. For the test I added 4 more such questions that were not in training, and they are even closer to the FAQ: the weights of the hybrid search, the best tokenizer, the embedding model name, Recall@5. The FAQ mentions hybrid search and tokenizers, but gives no numbers or names. All of them have the same answer: "このFAQには記載がありません。確認が必要です。" and `needs_review=true`.

The 4 mistakes were all on test paraphrases, and 3 of them are yes/no questions ("検索はキーワード方式だけですか", "民間ブログを…利用しますか", "検索精度の評価も研究目的に含まれますか"). The FAQ answers them only indirectly, and in training I didn't have yes/no questions at all, so the model probably decided it's safer to send them to review.

### 発展

| Question type | N | Before training (base) | After training (LoRA) | Glossary search (retrieval) |
| --- | ---: | ---: | ---: | ---: |
| known (term in glossary, same wording as training) | 4 | 0/4 (0%) | 4/4 (100%) | 3/4 (75%) |
| paraphrase (term in glossary, reworded question) | 4 | 2/4 (50%) | 2/4 (50%) | 1/4 (25%) |
| unknown (term not in glossary) | 4 | 0/4 (0%) | 0/4 (0%) | 3/4 (75%) |
| Total | 12 | 2/12 (16.7%) | 6/12 (50.0%) | 7/12 (58.3%) |

学習データ：`glossary_sft.jsonl` 116 件（58 語 × 2 テンプレート）、LoRA r=16、10 epochs、150 steps。学習時間 1089 秒、最終 loss 0.081674（平均 0.669360）。



- 変えた設定やデータ：[基礎](#基礎loraランクの比較)、[実装](#実装医療情報管理システムのfaqによるlora学習)、[発展](#発展) を参照
- 結果（比較表や数字）：[基礎](#基礎loraランクの比較)、[実装](#実装医療情報管理システムのfaqによるlora学習)、[発展](#発展) を参照
- ファインチューニングが向く場面・向かない場面についての考察：

  **Where fine-tuning helped.** It improves the model's adaptation to a specific task:
  - output format: 9.52% → 100% (演習) and 19% → 100% (実装);
  - `needs_review`: all 6 out of 6 questions without an answer in the FAQ were sent to review (実装).

  **Where it did not help.** It does not fully remove wrong answers, especially when the training data is small:
  - unknown terms: 0/4 for LoRA (発展);
  - confident answers to questions that the FAQ does not cover (演習, 基礎);
  - paraphrased questions: only 2/4 (発展).

  Also, after fine-tuning some problems with the model's existing abilities may appear. The training and evaluation sets are small, so it is hard to say what exactly causes them.

  **Comparison with glossary search (retrieval).** On unknown terms retrieval got 3/4 vs 0/4 for LoRA. But on paraphrased questions it got only 1/4: simple search can't find the term if its name is not in the question.

  **Conclusion.** I think fine-tuning is good for a specific small task, for example when the model needs to follow an output format. But when accuracy and relying on existing knowledge are important, it is better to use tools like search or RAG.
