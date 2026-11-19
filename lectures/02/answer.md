# 第2回 解答

## 演習

- 使ったモデル・設定（`result.json` の `config` から）：Model: Qwen/Qwen3.5-0.8B; revision: 2fc06364715b967f1860aea9cf38778875588b17. Setting: LoRA without quantization, seed 42, 20 training epochs, learning rate 0.0002, 6 warmup steps, LoRA rank 16, LoRA alpha 32, maximum sequence length 512, and maximum output length 96 tokens. Generation used do_sample=False.
- 自分で学習を実行したか（`executed_training_myself`）：はい / いいえ（実行できた範囲：Yes, I executed model loading, pre-training/ post training evaluation, LoRA training, the training completed in 228s, 40 steps and 20 epochs
- 学習前：`format_rate` =　0.095238 (9.52%, 2/21) / `content_rate` =　0.0 (0%,0/21)
- 学習後：`format_rate` =　1.0 (100%, 21/21) / `content_rate` =　0.904762 (90.48%, 19/21)
- 退行した質問：None
- 学習後に残った失敗と、その型（根拠なしの質問に断定した / 根拠ありの質問に確認要求で逃げた / 形式の崩れ）：Two failures remained. For “When will grades be released?”, the model returned the PDF submission-format rule with needs_review: false, although the FAQ did not specify a grade-release date. For “Is an advance booking required for office hours?”, the model returned the office-hour schedule with needs_review: false, although the FAQ did not specify a booking requirement.
- 知識を問う質問（セクション 6）の結果（学習前の分類 → 学習後の分類）と気づいたこと：Final assignment deadline: format_error => asserted. The model reused the ordinary assignment deadline without evidence that it also applied to the final assignment. Instructor’s name: format_error => needs_review. It appropriately requested confirmation. Next lecture’s topic: format_error => needs_review. It appropriately requested confirmation. Ordinary assignment deadline, the supported control: format_error => asserted. It correctly answered using the FAQ. I realized that the original FAQ marked incorrectly the control questions as false because it checked exact-question membership in gold.
- 学習で変わったこと・変わらなかったこと：LoRA improves JSON compliance and reproduce FAQ wording. Answers omitted needs_review before training is followed the required format. The 0% content score reflected missing required fields. The model substituted a related FAQ fact for information that was not provided. Training improved format and measured content accuracy but did not guarantee reliable judgment about whether the FAQ supported an answer.

## 宿題

- 取り組んだレベル：発展
- 変えた設定やデータ： I completed all 3 level. In basic level, I changed "num_train_epochs" from 20 to 10 in config and run again (https://colab.research.google.com/drive/1qLBVZLZnlz0i_chaLmsWpxeOF1whsnbZ). In implementation level, I replaced the FAQ and all grounded, ungrounded, and extra test questions with a fictional marketing-workshop topic, prepared unsupported questions in section 5 and checked these questions in section 6 (https://colab.research.google.com/drive/1sdp3cbcidFHQhGbDEcBjMlo3x6uGgcDL). In advanced level, I add code in codespace uv run python scripts/make_sft_dataset.py > glossary_sft.jsonl and collect 116 messages-format Q&A records from 58 glossary entries. I train first 58 examples and validate other 58 examples. Then, I trained LoRA using these records with remain unchange the original setting in baseline.I increased the generation limit from 96 to 256 tokens and keep it identical before and after evaluation. Before test, I fixed 15 test cases: 6 direct questions, 6 reworded questions and 3 questions about DPO, MoE and BPE (no aliase in the glossary). I used qualitative review rather than the FAQ JSON scorer. Finally, I did the additional part for 4-bit glossary evaluation (https://colab.research.google.com/drive/15guqoHoYa3zG0xsKbPHnue7ln1rBdZCa).
- 結果（比較表や数字）：
    Basic level:
        | Metric | Baseline: 20 epochs | Basic: 10 epochs |
        |---|---:|---:|
        | Training steps | 40 | 20 |
        | Training time | 228 s | 115 s |
        | Last logged training loss | 0.013881 | 0.100523 |
        | Post-training format compliance | 100% | 100% |
        | Post-training content accuracy | 90.48% (19/21) | 90.48% (19/21) |
        Insight: 10 epochs model reduces training time by 49.6%. However the failed questions changed. It incorrectly requested review when asked whether a non-PDF submission was allowed. Equal aggregate scores therefore did not mean identical behavior. But one run is insufficient to establish that 10 epochs is generally as effective as 20.
    Implementation level:
        | Metric | Before | After |
        |---|---:|---:|
        | Format compliance | 9.52% | 100% |
        | Content accuracy | 0% | 100% (21/21) |
        | Evaluation time | 21.6 s | 33.9 s |
        Training took 216 seconds over 40 steps and 20 epochs with training loss: 0.016774. No test failures remained, regression list was empty. In Section 6, the speaker-name and certificate-condition questions changed from `format_error` to `needs_review`. However, the workshop-ending-time question change from `format_error` to `asserted` it answered with the registration deadline and registration-deadline control became a correct supported answer.
        Insight: 100% scored described this particular 21 questions test set. It also did not establish reliable handling of every unsupported question. The separate probe exposed confusion between event's ending time and its registration deadline
    Advanced level:
        The training lasted 374.437s over 160 steps and 20 epochs. Training loss was 0.066899 while mean loss was 0.584874. These are different loss summaries.
        | Evaluation metric: 15 questions | Before | After |
        |---|---:|---:|
        | Total generation time | 161.509 s | 47.022 s |
        | Outputs reaching the 256-token limit | 15/15 | 0/15 |
        | Mean generated tokens, including any generated special tokens | 256 | 56.2 |
        All six direct answers after training reproduced reference definitions verbatim => recall of trained definition is better than establishing broad conceptual understanding. The reworded answer is less reliable. The epoch answer discussed overfitting without defining a complete pass through the data. The quantization answer captured resource savings and possible accuracy loss but omitted the lower-bit weight representation. Other reworded answers mixed relevant points with unclear or unsupported details. Three outside questions still received affirmative explainations after training.
        Insight: The adapter improved direct definition recalls and made output much shorter. The lower generation time coincide with fewer generated tokens => does not establish a higher per-token processing speed. Pre-training outputs reach the length limit, restricts comparison of complete answers. Low training loss and verbatim recall can not guarantee reliable answers to changed wording.
        For 4-bit evaluation:
        | Metric | 32-bit base, before LoRA | 4-bit base, no LoRA |
        |---|---:|---:|
        | Weight memory | 3.01 GB | 0.76 GB |
        | Total generation time, 15 questions | 161.509 s | 277.383 s |
        | Outputs reaching the 256-token limit | 15/15 | 15/15 |
        The reported weight-memory footprint decreased by approximately 74.8%. It run took approximately 1.72 times as long as the 32-bit run. Moreover, outputs changed without additional training.
- ファインチューニングが向く場面・向かない場面についての考察：For me, the experiments suggests that fine-tuning is useful to teach a consistent output format, wording, or response style. In the FAQ baseline, LoRA increase JSON formats compliance from 9.52% to 100%. In the glossary experiment, the model reproduced all six directly requested definitions verbatim and generated much shorter answers. However, fine-tuning can be less reliable with reworded or required recognizing questions that the available information did not support an answer. These results show recalling training examples does not guarantee flexible understanding. I prefer a system that searches the glossary, displays the relevant entry for frequently changing information. Retrieval needs evaluation because it can miss or select the wrong information. Fine-tuning could complement retrieval by improving response format and style.
