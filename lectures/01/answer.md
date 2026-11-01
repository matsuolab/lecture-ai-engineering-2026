# 第1回 解答

## 演習

- **講座固有の質問**：`AIE2026の講座の宿題にある「3レベル」とは何ですか？`。講座repoの用語集 `data/glossary.json` の `homework-levels` を正解として採用した。
- **用語集との照合**：資料なし・無関係な資料ありでは講座固有情報を「不明」と回答した。関連する定義を与えた場合は具体的な回答が得られた。
- **トークン表示**：API応答から入力・出力・思考・総トークン数を取得し、下記の集計表で比較した。

## 宿題

- **取り組んだレベル**：発展 ＋ Plus α（外部知識による誤答抑制の比較実験）
- **対象モデル**：gemini-3.5-flash-liteとgemini-3.6-flash。合計54回を試行し、44件成功、10件失敗した。
- **仮説**：H1: 講座固有の質問では、関連資料の提供によって正確性が上がり、事実と異なる断定が減る。H2: 追加資料による入力トークン増加はレイテンシと利用枠を圧迫しうる。H3: 無関係な資料を渡しただけでは、関連資料と同等の改善は生じない。
- **比較条件**：①資料なし（baseline）、②無関係なLoRAの定義を付与（irrelevant）、③正解の用語集定義を付与（grounded）。同じ3問を各モデル・各条件で3回ずつ実行する、計54リクエストの計画を作成した。実行順はseed 2026でシャッフルし、単発の独立したリクエストに統一した。
- **実装レベルも実施**：`app/ask.py` にトークン数表示と `--chat` の会話履歴保持機能を実装。単発質問との互換性も維持した。
- **発展の実装**：`scripts/lec01_advanced.py` を作成。API呼び出し時間（`perf_counter`）、入力・出力・思考・総トークン数、失敗時のステータスを個別に記録する。中断後の再開、実行条件のハッシュ記録、CSV/JSONLへの逐次保存、記述統計・ペア差・SVG図を実装した。
- **Plus αの評価**：成功した44回答をAIで一次採点した。完全正答14件、部分正答1件、不明・無回答29件。判定可能な43件で講座固有の誤事実の断定は確認されず、1件は判定保留とした。独立した人手採点は未実施。grounded条件は正解定義を直接与えるオラクル対照であり、RAG検索精度の評価ではない。
- **テスト結果**：APIキーが不要な28件のpytestテストに全件成功（2026-11-01時点、この作成環境）。試験項目は実験計画の重複防止、各条件の作成、欠損したトークン数、レイテンシ計測、失敗時の情報隠蔽、中断再開、設定混在防止、手動採点の保存、SVGエスケープなど。**本テストのモック値はAPI実測結果ではない**。
- **考察**：関連資料によって回答可能性が改善した。一方、資料なしでもモデルは主に「不明」と回答したため、ハルシネーションの減少は実証できなかった。3.6 Flashでは429エラーが9件、503エラーが1件発生し、API利用制約と欠測がモデル間比較を難しくした。
- **残る検証**：AI一次採点の人手確認、設問数の拡大、入力長や思考設定を統制した追試が必要である。API実測は実施済み。

## API実測・評価後の自動追記欄

`uv run python -m scripts.lec01_advanced run` 実行後に自動更新されます。採点後は `uv run python -m scripts.lec01_advanced analyze` で再集計します。

<!-- EXPERIMENT_RESULTS_START -->

# 第1回 発展＋Plus α 実験レポート（自動集計）

## 実験の前提

- 全呼び出しは独立した単発リクエスト。回答に会話履歴は含めない。
- baseline: 資料なし / irrelevant: 無関係なLoRAの定義 / grounded: 対象の正解定義を付加。
- モデルの思考設定は既定値。モデル間の内部推論量が揃うとは限らない。
- latencyはSDK呼び出し全体（SDKの自動リトライを含む）の壁時計時間。
- サンプル数が小さく、下表は**記述統計**。有意差・因果効果は断定しない。
- 正確性はAI一次採点（独立した人手確認は未実施）。スコア2=重要事実が正確、1=一部正しい、0=誤り/不足/不明。
- hallucination=yesは誤った事実を断定した回答。『不明』は誤答でもハルシネーションではない。

## モデル・条件別結果

| モデル | 条件 | 成功/試行 | 平均秒 | 中央値秒 | 標準偏差秒 | 平均入力token | 平均出力token | 平均総token | 平均正確性(0-2) | ハルシネーション率 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gemini-3.5-flash-lite | baseline | 9/9 | 2.68 | 1.14 | 2.66 | 50.0 | 35.7 | 85.7 | 0.00 (n=9) | 0.0% (n=9) |
| gemini-3.5-flash-lite | grounded | 9/9 | 3.18 | 1.16 | 3.38 | 136.7 | 58.6 | 195.2 | 2.00 (n=9) | 0.0% (n=9) |
| gemini-3.5-flash-lite | irrelevant | 9/9 | 2.72 | 1.13 | 3.08 | 152.0 | 31.6 | 183.6 | 0.00 (n=9) | 0.0% (n=9) |
| gemini-3.6-flash | baseline | 5/9 | 4.79 | 4.61 | 1.14 | 50.2 | 52.4 | 773.4 | 0.00 (n=5) | 0.0% (n=4) |
| gemini-3.6-flash | grounded | 6/9 | 4.58 | 4.40 | 1.00 | 136.7 | 54.8 | 786.5 | 1.83 (n=6) | 0.0% (n=6) |
| gemini-3.6-flash | irrelevant | 6/9 | 3.67 | 3.63 | 0.48 | 152.0 | 30.3 | 659.8 | 0.00 (n=6) | 0.0% (n=6) |

## ペア比較（同一モデル・質問・反復の対応差）

| モデル | 差分条件 | レイテンシペア数 | 平均秒差 | 平均総token差 | 正確性差(0-2) |
|---|---|---:|---:|---:|---:|
| gemini-3.5-flash-lite | grounded - baseline | 9 | 0.50 | 109.6 | 2.00 (n=9) |
| gemini-3.5-flash-lite | grounded - irrelevant | 9 | 0.46 | 11.7 | 2.00 (n=9) |
| gemini-3.6-flash | grounded - baseline | 5 | -0.53 | -60.8 | 2.00 (n=5) |
| gemini-3.6-flash | grounded - irrelevant | 6 | 0.91 | 126.7 | 1.83 (n=6) |

## エラー・未完了

| モデル | 質問 | 条件 | 反復 | 状態 | ステータス |
|---|---|---|---:|---|---|
| gemini-3.6-flash | homework-levels | baseline | 2 | error | 503 |
| gemini-3.6-flash | homework-levels | grounded | 3 | error | 429 |
| gemini-3.6-flash | lec-start-tag | irrelevant | 3 | error | 429 |
| gemini-3.6-flash | lec-start-tag | baseline | 3 | error | 429 |
| gemini-3.6-flash | lec-start-tag | grounded | 3 | error | 429 |
| gemini-3.6-flash | default-model | baseline | 3 | error | 429 |
| gemini-3.6-flash | default-model | grounded | 3 | error | 429 |
| gemini-3.6-flash | default-model | irrelevant | 3 | error | 429 |
| gemini-3.6-flash | homework-levels | baseline | 3 | error | 429 |
| gemini-3.6-flash | homework-levels | irrelevant | 3 | error | 429 |

## 評価上の制約

- 陰性対照は文字数・トークン数を厳密に一致させていないため、コンテキスト長の影響を完全には分離できない。
- 質問数と反復数が少ない。設問を増やし、実行順と日を変えた追試が必要。
- grounded条件は正答定義を直接付与するオラクル対照であり、検索精度を含むRAGの評価ではない。
- 出力トークン数と総トークン数は別物。モデルの思考トークンが含まれる可能性がある。
- キー/予算/無料枠/レート制限はプロジェクトとモデルの条件に依存し、1回の実験で一般化できない。

<!-- EXPERIMENT_RESULTS_END -->

## 再現手順

1. `uv run pytest -q` で全テストを確認する。
2. `uv run python -m scripts.lec01_advanced plan` で実験計画とAPI呼び出し回数を確認する。
3. `uv run python -m scripts.lec01_advanced run` で計測する。失敗した呼び出しは結果に記録し、同じコマンドで再開できる。
4. `outputs/lec01_advanced/review.csv` の `accuracy_score`（0/1/2）と `hallucination`（yes/no/unclear）を手動入力する。
5. `uv run python -m scripts.lec01_advanced analyze` で結果を再集計し、このファイルの実測欄を更新する。
6. `outputs/lec01_advanced/comparison.svg` と `summary.md` を確認し、必要な結果だけを提出する。APIキー・個人情報・環境変数の値は記録しない。

※観測結果は今回の実行条件とAI一次採点に限定される。モックテスト値は実測値として扱わない。
