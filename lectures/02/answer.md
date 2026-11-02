# 第2回 解答

## 演習

- 使ったモデル・設定（`result.json` の `config` から）：`Qwen/Qwen3.5-0.8B`（revision=`2fc06364715b967f1860aea9cf38778875588b17`）、LoRA（量子化なし、`r=16`、`alpha=32`、dropout=0.05）、20 エポック、学習率 0.0002、最大系列長 512、seed 42。
- 自分で学習を実行したか（`executed_training_myself`）：はい（学習 40 ステップ、約 229 秒）
- 学習前：`format_rate` = 0.095（2/21） / `content_rate` = 0.000
- 学習後：`format_rate` = 1.000（21/21） / `content_rate` = 0.905（19/21）
- 退行した質問：なし（`regressed: []`）
- 学習後に残った失敗と、その型（根拠なしの質問に断定した / 根拠ありの質問に確認要求で逃げた / 形式の崩れ）：2 問が内容不正解で、どちらも FAQ にない質問に別の FAQ 項目を当てはめて断定する型だった。「成績はいつ出ますか」には提出期限を、「オフィスアワーは事前予約が必要ですか」にはオフィスアワーの時間帯を `needs_review: false` で返した。「いつ」「オフィスアワー」といった表面の語から近い FAQ を選んでおり、FAQ に根拠があるかどうかは判断できていない。形式はすべて正しく、`answer` と `needs_review` のキー欠落もなかった。
- 知識を問う質問（セクション 6）の結果（学習前の分類 → 学習後の分類）と気づいたこと：
  - 「最終課題の締切」（FAQ にない）：形式エラー → `asserted`（「9月30日 23:59」と断定）
  - 「担当教員の名前」（FAQ にない）：形式エラー → `needs_review`（望ましい）
  - 「次回の講義テーマ」（FAQ にない）：形式エラー → `needs_review`（望ましい）
  - 「提出期限」（FAQ にある対照問題）：形式エラー → `asserted`（正しい）

  学習後は形式を守れるようになったが、FAQ にない質問かどうかを常に正しく判断できるようになったわけではない。特に「最終課題の締切」では、質問が似ている FAQ の `deadline` を流用してしまい、根拠のない断定が起きた。
- 学習で変わったこと・変わらなかったこと：LoRA によって JSON の形式遵守と、FAQ にある回答の再現性は大きく改善した。一方、未知の質問に確認を求めるという判断は一貫せず、知識の根拠や検索能力そのものが追加されたわけではない。したがって、ファインチューニングは出力形式や決まった応答パターンの適応には向くが、未知情報の検証には検索・RAG・ルールなどを併用する必要がある。
- 補足：`causal_conv1d` と `flash-linear-attention` の警告は、高速化カーネルがインストールされていないため参照実装にフォールバックしたという意味であり、今回の結果が無効というエラーではない。

## 宿題

- 取り組んだレベル：基礎
- 変えた設定やデータ：FAQ と学習条件は元のままにし、`CONFIG["lora_r"]` だけを 16 から 4、8、32、64 に変えて再学習した。`lora_alpha=32` は固定した。
- 検証に使った追加コード：

  ```python
  import gc, time, torch, pandas as pd
  from peft import LoraConfig
  from trl import SFTTrainer, SFTConfig
  from datasets import Dataset
  from transformers import AutoModelForCausalLM

  # セクション3で読み込んだ学習前モデルは評価済みなので、メモリ節約のため外す
  del model
  gc.collect()
  torch.cuda.empty_cache()

  def to_chat(example):
      return {"messages": build_messages(example) + [{"role": "assistant", "content": example["target"]}]}

  train_ds = Dataset.from_list([to_chat(e) for e in train])
  valid_ds = Dataset.from_list([to_chat(e) for e in valid])

  results = []
  for r in [4, 8, 16, 32, 64]:
      print(f"===== lora_r = {r} =====")
      base = AutoModelForCausalLM.from_pretrained(
          CONFIG["base_model"], revision=CONFIG["revision"], dtype=torch.float32
      ).to(DEVICE)
      base.config.use_cache = False
      lora = LoraConfig(
          r=r,
          lora_alpha=CONFIG["lora_alpha"],  # alpha は 32 に固定（変えるのは r だけ）
          lora_dropout=0.05,
          bias="none",
          task_type="CAUSAL_LM",
          target_modules=[
              "q_proj", "k_proj", "v_proj", "o_proj",
              "gate_proj", "up_proj", "down_proj",
          ],
      )
      sft = SFTConfig(
          output_dir=str(WORK / f"ckpt_r{r}"),
          num_train_epochs=CONFIG["num_train_epochs"],
          per_device_train_batch_size=4,
          gradient_accumulation_steps=2,
          learning_rate=CONFIG["lr"],
          lr_scheduler_type="cosine",
          warmup_steps=CONFIG["warmup_steps"],
          logging_steps=10,
          save_strategy="no",
          max_length=CONFIG["max_seq_len"],
          packing=False,
          report_to="none",
          seed=CONFIG["seed"],
      )
      trainer = SFTTrainer(
          model=base,
          args=sft,
          train_dataset=train_ds,
          eval_dataset=valid_ds,
          peft_config=lora,
          processing_class=tok,
      )
      t0 = time.time()
      trainer.train()
      train_sec = round(time.time() - t0, 1)

      m = trainer.model
      m.config.use_cache = True
      m.eval()
      summary, _ = evaluate(m, f"after_r{r}")
      final_loss = next(
          h["loss"] for h in reversed(trainer.state.log_history) if "loss" in h
      )
      results.append({
          "lora_r": r,
          "format_rate": summary["format_rate"],
          "content_rate": summary["content_rate"],
          "final_loss": final_loss,
          "train_sec": train_sec,
          "steps": trainer.state.global_step,
      })

      del trainer, m, base
      gc.collect()
      torch.cuda.empty_cache()

  df = pd.DataFrame(results)
  display(df)
  (WORK / "lora_r_sweep.json").write_text(
      df.to_json(orient="records", force_ascii=False, indent=2),
      encoding="utf-8",
  )
  ```
- 結果（比較表や数字）：

  | LoRA rank | trainable params（計算値） | format_rate | content_rate | 最終 loss | 学習時間 | steps |
  |---:|---:|---:|---:|---:|---:|---:|
  | 4  | 約 160 万（0.21%） | 1.000 | 0.905（19/21） | 0.013219 | 237.5 秒 | 40 |
  | 8  | 約 319 万（0.42%） | 1.000 | 0.905（19/21） | 0.013252 | 237.9 秒 | 40 |
  | 16 | 約 639 万（0.84%） | 1.000 | 0.905（19/21） | 0.014008 | 238.3 秒 | 40 |
  | 32 | 約 1278 万（1.67%） | 1.000 | 0.905（19/21） | 0.015067 | 238.9 秒 | 40 |
  | 64 | 約 2556 万（3.29%） | 1.000 | 0.857（18/21） | 0.016785 | 241.0 秒 | 40 |

  すべての設定で形式遵守率は 1.000 になり、`r=4`〜`32` は内容正解率も同じ 0.905 だった。`r=64` だけ内容正解率が 0.857 に下がった。学習時間の差は約 3.5 秒で、測定誤差の範囲と考えられる。rank を大きくすると学習可能なパラメータ数は増え、`r=16` の実測値 6,389,760（0.84%）を基準にすると、`r=64` では約 4 倍の 2556 万（3.29%）になる。それでもこの 14 件の小さなデータと 20 エポックの条件では性能向上につながらなかった。

  また、`lora_alpha=32` を固定したため、更新倍率 `alpha/r` は `r=4` で 8、`r=8` で 4、`r=16` で 2、`r=32` で 1、`r=64` で 0.5 と変化した。つまり、r を変えると表現力だけでなく実効的な更新の大きさも変わるため、r の効果だけを純粋に比較した実験ではない。r が大きいほど最終 loss がわずかに高くなったことは、この倍率の変化でも説明できる可能性がある。表の `r=16` は元の学習ではなく、同じ条件をループで再学習した値である。`r=4`〜`32` は失敗した 2 問も同じだったが、`r=64` では「PDF 以外でも出せますか」という FAQ に根拠がある質問に「この FAQ には記載がありません」と `needs_review: true` で返す失敗が 1 問増えた。これは根拠ありの質問に確認要求で逃げる型である。評価が 21 問と少なく、GPU 学習にはわずかな非決定性もあるため、今回だけで `r=64` が常に悪いとは断定できない。
- セクション 8（4bit、学習なし）：`format_rate` は 0.095 から 0.667、`content_rate` は 0.000 から 0.333 に変化した。ただし、根拠のない質問に「なし」「はい」と断定する出力が増え、`"false"` を文字列で返す型崩れもあった。量子化だけでも出力は変わるが、改善方向は一貫しない。
- ファインチューニングが向く場面・向かない場面についての考察：出力 JSON のキーや型、文体、定型的な回答手順を毎回守らせたい場合には向いている。今回も学習前は `missing_key` が多かったが、学習後は 21 問すべてで形式を守れた。一方、学習データにない事実を調べたり、根拠の有無を厳密に判定したりする用途には向かない。今回も FAQ にない「最終課題の締切」を既知の締切と取り違えたため、知識の更新や正確性が必要な場面では、検索・RAG・外部データベース・明示的な検証ルールを組み合わせるべきである。また、`r=4` でも `r=16` と同じ結果だったことから、データ量が少なく目的が形式適応に限られる場合は、rank を大きくしても効果が増えない可能性がある。
