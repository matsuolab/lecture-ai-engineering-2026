"""選択の楽観（ハイパーパラメータ・特徴量・袋モデル C を同じデータで選んだ影響）を入れ子検証で測る。

外側 fold の評価用ユーザーを完全に取り分け、同じ外側 fold で次の2つを比べる。
  A（入れ子）: 学習側だけでハイパーパラメータ・袋モデル C・特徴量群を選び直す → 評価用ユーザーは選択に一切関与しない（偏りなし）
  B（全データ選択）: 全データ（評価用ユーザーを含む）で選んだ現行設定をそのまま使う
B の外側スコアは選択に評価用ユーザーが関わった分だけ有利になりうる。A − B がプラスなら、その大きさが選択の楽観の推定値。

使い方: python src/nested_check.py --outer-seeds 0 --trials 30
"""
from __future__ import annotations

import argparse
import copy
import json
import warnings
from pathlib import Path

import numpy as np
import optuna
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.model_selection import StratifiedKFold, cross_val_predict

import train as T
from bag import nested_bag_score
from external import ExternalScores
from features import USER_COLS

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)
EXTRA_PREFIX = ("max_season", "season2plus_titles", "weekly_", "seg_", "hour_entropy", "top3_hour_share",
                "weekend_night_rate", "tv_and_phone", "no_tv", "cross_device_titles", "tv_prime_rate", "tv_late_days")
C_GRID = [3, 10, 20, 30, 100]


def lgb_space(t):
    return dict(n_estimators=t.suggest_int("n_estimators", 200, 2000, log=True),
                learning_rate=t.suggest_float("learning_rate", 0.005, 0.1, log=True),
                num_leaves=t.suggest_int("num_leaves", 3, 31), max_depth=t.suggest_int("max_depth", 2, 6),
                min_child_samples=t.suggest_int("min_child_samples", 5, 80),
                subsample=t.suggest_float("subsample", 0.5, 1.0),
                colsample_bytree=t.suggest_float("colsample_bytree", 0.1, 0.9),
                reg_lambda=t.suggest_float("reg_lambda", 1e-2, 50, log=True),
                reg_alpha=t.suggest_float("reg_alpha", 1e-3, 10, log=True),
                min_data_per_group=t.suggest_int("min_data_per_group", 10, 100),
                cat_smooth=t.suggest_float("cat_smooth", 1, 50), cat_l2=t.suggest_float("cat_l2", 1, 50),
                max_cat_to_onehot=t.suggest_int("max_cat_to_onehot", 2, 32))


def fit_pred(params, Xa, ya, Xb, seeds):
    T.PARAMS["lgb"] = params
    return np.mean([T.fit_lgb(Xa, ya, Xb, Xb.iloc[:1], s)[0] for s in seeds], axis=0)


def inner_cv(params, X, y, n=5, seed=0, seeds=(0,)):
    oof = np.zeros(len(X))
    for a, b in StratifiedKFold(n, shuffle=True, random_state=seed).split(X, y):
        oof[b] = fit_pred(params, X.iloc[a], y.iloc[a], X.iloc[b], seeds)
    return log_loss(y, np.clip(oof, 1e-6, 1 - 1e-6))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outer-seeds", default="0")
    ap.add_argument("--trials", type=int, default=30)
    ap.add_argument("--ext", default="tabpfn,tabfm,limix,ftfm")
    ap.add_argument("--out", type=Path, default=Path("output/nested_check.json"))
    ap.add_argument("--max-folds", type=int, default=0, help="試運転用: 外側 fold 数の上限")
    args = ap.parse_args()

    T.load_params(Path("config/params.json"))
    GLOBAL = copy.deepcopy(T.PARAMS["lgb"])
    X, y, Xte, _, (M, idx) = T.build_features(Path("input"))
    X = T.to_category(X, pd.concat([X, Xte]))
    ext = ExternalScores(Path("external"), args.ext.split(",")) if args.ext else None
    extra_cols = [c for c in X.columns if c.startswith(EXTRA_PREFIX)]
    pos = pd.Series(np.arange(len(idx)), idx)
    rows = []
    for s in [int(v) for v in args.outer_seeds.split(",")]:
        for k, (tr, va) in enumerate(StratifiedKFold(5, shuffle=True, random_state=s).split(X, y)):
            if args.max_folds and len(rows) >= args.max_folds:
                break
            ytr, yva = y.iloc[tr], y.iloc[va]
            base = X.copy()
            if ext is not None:
                for name, (vtr, vva, _) in ext.fold(s, k, tr, va, len(Xte)).items():
                    col = np.full(len(X), np.nan)
                    col[tr], col[va] = vtr, vva
                    base[f"ext_{name}"] = col

            # --- A: 学習側だけで C を選ぶ（袋 LR 単体の内側 CV）
            Mtr = M[pos.loc[X.index[tr]].to_numpy()]
            c_scores = {}
            for C in C_GRID:
                p = cross_val_predict(LogisticRegression(C=C, max_iter=3000), Mtr, ytr,
                                      cv=StratifiedKFold(5, shuffle=True, random_state=100 + k), method="predict_proba")[:, 1]
                c_scores[C] = log_loss(ytr, p)
            C_sel = min(c_scores, key=c_scores.get)

            def with_bag(C):
                sc = nested_bag_score(M, idx, ytr, X.index[va], C=C, seed=200 + k)
                return base.assign(bag_score=sc.reindex(X.index).to_numpy())

            XA, XB = with_bag(C_sel), with_bag(20.0)
            XA_tr = XA.iloc[tr]

            # --- A: 学習側だけでハイパーパラメータを探索（全特徴量で）
            st = optuna.create_study(sampler=optuna.samplers.TPESampler(seed=k))
            st.optimize(lambda t: inner_cv(dict(lgb_space(t)), XA_tr, ytr, seed=300 + k), n_trials=args.trials)
            P_sel = dict(st.best_params)

            # --- A: 学習側だけで特徴量群（追加特徴量・袋スコア）の有無を選ぶ
            subsets = {
                "all": list(XA.columns),
                "no_extra": [c for c in XA.columns if c not in extra_cols],
                "no_bag": [c for c in XA.columns if c != "bag_score"],
                "no_extra_no_bag": [c for c in XA.columns if c not in extra_cols and c != "bag_score"],
            }
            sub_scores = {n: inner_cv(P_sel, XA_tr[cols], ytr, seed=400 + k) for n, cols in subsets.items()}
            S_sel = min(sub_scores, key=sub_scores.get)
            cols = subsets[S_sel]

            seeds = range(5)
            pA = fit_pred(P_sel, XA_tr[cols], ytr, XA.iloc[va][cols], seeds)
            pB = fit_pred(GLOBAL, XB.iloc[tr], ytr, XB.iloc[va], seeds)
            lA = -(yva.to_numpy() * np.log(np.clip(pA, 1e-6, 1)) + (1 - yva.to_numpy()) * np.log(np.clip(1 - pA, 1e-6, 1)))
            lB = -(yva.to_numpy() * np.log(np.clip(pB, 1e-6, 1)) + (1 - yva.to_numpy()) * np.log(np.clip(1 - pB, 1e-6, 1)))
            rows.append(dict(seed=s, fold=k, C=C_sel, subset=S_sel, inner_best=st.best_value, params=P_sel,
                             outer_A=float(lA.mean()), outer_B=float(lB.mean()), n=len(va),
                             diff_sum=float((lA - lB).sum()), diff_sq=float(((lA - lB) ** 2).sum())))
            print(f"s{s}f{k} C={C_sel} subset={S_sel} inner_best={st.best_value:.4f} "
                  f"outer A(入れ子)={lA.mean():.4f} B(全データ選択)={lB.mean():.4f}", flush=True)

    df = pd.DataFrame(rows)
    n = df.n.sum()
    mA = (df.outer_A * df.n).sum() / n
    mB = (df.outer_B * df.n).sum() / n
    d = df.diff_sum.sum() / n
    se = np.sqrt(df.diff_sq.sum() / n - d ** 2) / np.sqrt(n)
    res = dict(outer_A=mA, outer_B=mB, A_minus_B=d, se=se, folds=rows)
    # 利用者単位の差（他の実行と合算して SE を下げるため保存）
    res["per_user_diff_sum"], res["per_user_diff_sq"], res["n"] = float(df.diff_sum.sum()), float(df.diff_sq.sum()), int(n)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(res, ensure_ascii=False, indent=2, default=float))
    print(f"\nA(入れ子) {mA:.5f}  B(全データ選択) {mB:.5f}  A−B {d:+.5f} ± {se:.5f}")


if __name__ == "__main__":
    main()
