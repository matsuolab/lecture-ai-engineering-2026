# 動画配信サブスク 無料トライアル後の継続予測

評価指標: Log Loss（小さいほど良い）

## 実行方法

```bash
cd competitions/subscription_continuation
pip install lightgbm catboost scikit-learn pandas scipy
# input/ に train.csv, test.csv, films.csv, viewing_log.csv, sample_submit.csv を置く（再配布防止のため git 管理外）
python src/train.py                  # → output/submission.csv（ヘッダなし, ID, 確率）
python -m pytest tests -q            # 単体テスト
```

`config/params.json` に Optuna で探索したパラメータが入っている（無ければ既定値で動く）。

## 手法

1. **クレンジング** (`src/clean.py`)
   - タイトルIDの復元: 欠損(約5%)・接頭辞欠落("001")・"movie" を、同一ユーザーの前後レコード → 視聴履歴 → 視聴時間/話数との整合 + 人気 の順で推定。人工的に壊した検証で 数字ID 90% / movie 85% / 完全欠損 49% を復元。
   - 視聴時間: 300 超は秒単位の記録とみなし /60。1話時間の 1.2 倍でクリップ。
   - エピソードNo・デバイス欠損の補完。
2. **特徴量** (`src/features.py`, 約110個)
   - 視聴量・完走率・アクティブ日数・セッション
   - トライアル内の時系列推移（期間別視聴量、日次傾き、後半比率、連続視聴日数、最終視聴から期間終了まで）
   - 作品消化（完走作品数、視聴途中のシリーズ数、週次配信の途中作品、残エピソード数）
   - 週次/独占配信比率、カテゴリ・デバイス構成比、プロフィール数、時間帯・曜日
   - 作品概要の文字 n-gram TF-IDF → SVD をユーザーの視聴時間で加重平均
   - 属性・アンケート（カテゴリ + 順序エンコード）
3. **モデル** (`src/train.py`): LightGBM / CatBoost / ロジスティック回帰 を 5-fold × 3 repeat で学習し、logit 空間で非負重み + バイアスを OOF に最適化してブレンド。最終予測は [0.001, 0.999] にクリップ。

## CV（OOF Log Loss, チューニングとは別の分割 seed=2025）

| モデル | Log Loss | AUC |
|---|---|---|
| LightGBM (tuned) | 0.3016 | 0.936 |
| CatBoost (tuned) | 0.3129 | 0.930 |
| Logistic Regression | 0.3519 | 0.910 |
| **ブレンド** | **0.2973** | |

ベースライン（未チューニング）ブレンド 0.3106、定数予測 約0.63。

不採用: 作品ターゲットエンコーディング（LOO はリークで 0.419、内側 K-fold でも 0.312 と改善なし）、ユーザー×作品行列 SVD（0.314）。
