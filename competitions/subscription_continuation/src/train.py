"""学習・CV・アンサンブル・提出ファイル生成。

使い方:
    python src/train.py --input input --out output
"""
from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, QuantileTransformer

from bag import bag_matrix, nested_bag_score
from clean import RECOVER_MODES, USER, clean_log, read_csv
from features import (USER_COLS, event_tokens, extra_features, title_text_features, user_log_features,
                      user_static_features)

warnings.filterwarnings("ignore", category=UserWarning)
TARGET = "継続フラグ"
EPS = 1e-6
CLIP = 1e-3  # OOF での悪化は 0.00006 程度。想定外の外れに対する保険


QUALITY_COLS = ["bad_title_rate", "device_missing_rate", "ep_missing_rate"]


def build_features(inp: Path, dedupe: bool = True, extra: bool = True, drop_quality: bool = True,
                   with_bag: bool = True, recover_mode: str = "full"):
    """特徴量行列を作る。返り値: X(train), y, X(test), sample_submit, 袋行列(またはNone)。

    drop_quality: 欠損率などデータ品質の列を除く（検証レポートで継続と無関係: AUC 0.49〜0.53）。
    """
    train, test = read_csv(inp / "train.csv"), read_csv(inp / "test.csv")
    log, films = read_csv(inp / "viewing_log.csv"), read_csv(inp / "films.csv")
    sub = pd.read_csv(inp / "sample_submit.csv", header=None, names=[USER, "p"], encoding="utf-8-sig")

    for name, df in [("train", train), ("test", test)]:
        if df[USER].duplicated().any():
            raise ValueError(f"{name} にユーザーIDの重複があります")
    if set(sub[USER]) != set(test[USER]):
        raise ValueError("sample_submit と test のユーザーIDが一致しません")
    if not set(train[TARGET].unique()) <= {0, 1}:
        raise ValueError("継続フラグに 0/1 以外の値があります")

    clog = clean_log(log, films, dedupe=dedupe, recover_mode=recover_mode)
    users = pd.concat([train.drop(columns=[TARGET]), test], ignore_index=True)
    X = user_static_features(users)
    X = X.join(user_log_features(clog, films)).join(title_text_features(clog, films))
    if extra:
        X = X.join(extra_features(clog, films))
    if drop_quality:
        X = X.drop(columns=QUALITY_COLS)
    num_cols = [c for c in X.columns if c not in USER_COLS]
    X[num_cols] = X[num_cols].fillna(0)  # ログが無いユーザーは 0（現データでは全員ログあり）
    X = X.copy()  # 列追加の繰り返しで断片化したフレームを詰め直す
    y = train.set_index(USER)[TARGET].astype(int)
    bag = None
    if with_bag:
        tok = event_tokens(clog, films).reindex(X.index).fillna("")
        bag = bag_matrix(tok)
    return X.loc[train[USER]], y.loc[train[USER]], X.loc[sub[USER]], sub, bag


# ---------------------------------------------------------------- models
LGB_DEFAULT = dict(n_estimators=600, learning_rate=0.02, num_leaves=7, max_depth=3, min_child_samples=30,
                   subsample=0.8, colsample_bytree=0.5, reg_lambda=5.0, reg_alpha=0.5,
                   cat_smooth=20, min_data_per_group=30)
CAT_DEFAULT = dict(iterations=1200, learning_rate=0.03, depth=4, l2_leaf_reg=10, rsm=0.5, random_strength=1.0)
PARAMS = {"lgb": dict(LGB_DEFAULT), "cat": dict(CAT_DEFAULT)}


def load_params(path: Path) -> None:
    """チューニング済みパラメータ（JSON: {"lgb": {...}, "cat": {...}}）で既定値を上書きする。"""
    if not path.exists():
        print(f"  {path} が無いので既定パラメータを使用")
        return
    cfg = json.loads(path.read_text(encoding="utf-8"))
    unknown = set(cfg) - set(PARAMS)
    if unknown:
        raise ValueError(f"未知のモデル名: {unknown}")
    for k, v in cfg.items():
        PARAMS[k].update(v)
    print(f"  loaded params from {path}")


def fit_lgb(Xtr, ytr, Xva, Xte, seed):
    import lightgbm as lgb
    params = dict(objective="binary", subsample_freq=1, verbose=-1, random_state=seed, n_jobs=4, **PARAMS["lgb"])
    # LightGBM は特殊文字（全角記号など）を含む列名を受け付けないので連番に置換
    names = [f"f{i}" for i in range(Xtr.shape[1])]
    ren = lambda X: X.set_axis(names, axis=1)  # noqa: E731
    m = lgb.LGBMClassifier(**params).fit(ren(Xtr), ytr)
    return m.predict_proba(ren(Xva))[:, 1], m.predict_proba(ren(Xte))[:, 1]


def fit_cat(Xtr, ytr, Xva, Xte, seed):
    from catboost import CatBoostClassifier
    cats = [c for c in Xtr.columns if c in USER_COLS]
    m = CatBoostClassifier(loss_function="Logloss", random_seed=seed, verbose=0, thread_count=4,
                           allow_writing_files=False, **PARAMS["cat"])
    m.fit(Xtr, ytr, cat_features=cats)
    return m.predict_proba(Xva)[:, 1], m.predict_proba(Xte)[:, 1]


def fit_lr(Xtr, ytr, Xva, Xte, seed, C=0.05):
    cats = [c for c in Xtr.columns if c in USER_COLS]
    nums = [c for c in Xtr.columns if c not in cats]
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=10), cats),
        ("num", QuantileTransformer(n_quantiles=200, output_distribution="normal", random_state=seed), nums),
    ])
    m = make_pipeline(pre, LogisticRegression(C=C, max_iter=5000)).fit(Xtr, ytr)
    return m.predict_proba(Xva)[:, 1], m.predict_proba(Xte)[:, 1]


def to_category(X: pd.DataFrame, ref: pd.DataFrame) -> pd.DataFrame:
    X = X.copy()
    for c in USER_COLS:
        X[c] = pd.Categorical(X[c], categories=sorted(ref[c].unique()))
    return X


MODELS = {"lgb": fit_lgb, "cat": fit_cat, "lr": fit_lr}


def run_cv(X, y, Xte, models, n_splits=5, n_repeats=3, seed=42, bag=None, bag_C=1.0, verbose=True):
    """Repeated Stratified K-fold。

    bag=(行列, index) を渡すと、各 fold で袋モデルの入れ子スコア（学習側は内側 OOF）を
    列 bag_score として全モデルの入力に加える（検証レポート v19 の手法）。
    返り値: oof(各 repeat の平均), test 予測(全 fold 平均), fold ごとの損失 {model: [..]}
    """
    allX = pd.concat([X, Xte])
    oof = {k: np.zeros(len(X)) for k in models}
    test = {k: np.zeros(len(Xte)) for k in models}
    fold_loss = {k: [] for k in models}
    rskf = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=seed)
    for i, (tr, va) in enumerate(rskf.split(X, y)):
        A, B = X, Xte
        if bag is not None:
            M, idx = bag
            others = X.index[va].append(Xte.index)
            sc = nested_bag_score(M, idx, y.iloc[tr], others, C=bag_C, seed=seed + i)
            A = X.assign(bag_score=sc.reindex(X.index).to_numpy())
            B = Xte.assign(bag_score=sc.reindex(Xte.index).to_numpy())
            if A["bag_score"].iloc[np.r_[tr, va]].isna().any() or B["bag_score"].isna().any():
                raise RuntimeError("bag_score に欠損があります")
        for k in models:
            if k == "lgb":
                A2, B2 = to_category(A, allX), to_category(B, allX)
            else:
                A2, B2 = A, B
            pv, pt = MODELS[k](A2.iloc[tr], y.iloc[tr], A2.iloc[va], B2, seed + i)
            oof[k][va] += pv / n_repeats
            test[k] += pt / (n_splits * n_repeats)
            fold_loss[k].append(log_loss(y.iloc[va], np.clip(pv, EPS, 1 - EPS)))
    if verbose:
        for k in models:
            print(f"  {k:5s} logloss={log_loss(y, np.clip(oof[k], EPS, 1 - EPS)):.5f} auc={roc_auc_score(y, oof[k]):.4f}")
    return oof, test, fold_loss


def logit(p):
    p = np.clip(p, EPS, 1 - EPS)
    return np.log(p / (1 - p))


def blend(oof: dict, y: np.ndarray):
    """logit 空間での非負重み + 温度/バイアス（Platt）を OOF で最適化。"""
    keys = list(oof)
    L = np.column_stack([logit(oof[k]) for k in keys])

    def loss(w):
        z = L @ np.abs(w[:-1]) + w[-1]
        return log_loss(y, np.clip(1 / (1 + np.exp(-z)), EPS, 1 - EPS))

    w0 = np.r_[np.ones(len(keys)) / len(keys), 0.0]
    res = minimize(loss, w0, method="Nelder-Mead", options=dict(maxiter=5000, xatol=1e-6, fatol=1e-8))
    w = np.r_[np.abs(res.x[:-1]), res.x[-1]]
    return dict(zip(keys + ["bias"], w.tolist())), res.fun


def apply_blend(preds: dict, w: dict):
    z = sum(w[k] * logit(preds[k]) for k in preds) + w["bias"]
    return 1 / (1 + np.exp(-z))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=Path("input"))
    ap.add_argument("--out", type=Path, default=Path("output"))
    ap.add_argument("--models", default="lgb,lr")  # CatBoost はブレンド重みがほぼ 0 のため既定では外す
    ap.add_argument("--repeats", type=int, default=10)
    ap.add_argument("--variants", default=",".join(RECOVER_MODES))
    ap.add_argument("--params", type=Path, default=Path("config/params.json"))
    ap.add_argument("--seed", type=int, default=2025)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    load_params(args.params)
    models = args.models.split(",")
    modes = args.variants.split(",")
    oofs, tests = [], []
    for mode in modes:
        X, y, Xte, sub, bag = build_features(args.input, recover_mode=mode)
        print(f"[{mode}] train={X.shape} test={Xte.shape} pos_rate={y.mean():.4f}")
        o, t, _ = run_cv(X, y, Xte, models, n_repeats=args.repeats, seed=args.seed, bag=bag)
        oofs.append(o)
        tests.append(t)
    # 復元方法の異なるクレンジングごとの予測を logit 平均（復元の不確かさを打ち消す）
    avg = lambda ds, k: 1 / (1 + np.exp(-np.mean([logit(d[k]) for d in ds], axis=0)))  # noqa: E731
    oof = {k: avg(oofs, k) for k in models}
    test = {k: avg(tests, k) for k in models}
    for k in models:
        print(f"  [avg] {k:5s} logloss={log_loss(y, np.clip(oof[k], EPS, 1 - EPS)):.5f}")
    w, cv = blend(oof, y.to_numpy())
    print(f"blend weights={w}\n  blend logloss(OOF, 重み最適化込み)={cv:.5f}")

    p = np.clip(apply_blend(test, w), CLIP, 1 - CLIP)
    if not np.isfinite(p).all():
        raise RuntimeError("予測に非有限値が含まれます")
    out = pd.DataFrame({USER: sub[USER].to_numpy(), "p": p})
    out.to_csv(args.out / "submission.csv", header=False, index=False)
    pd.DataFrame(oof, index=X.index).assign(y=y).to_csv(args.out / "oof.csv")
    json.dump({"weights": w, "cv_blend_logloss": cv}, open(args.out / "cv.json", "w"), ensure_ascii=False, indent=2)
    print(f"saved {args.out/'submission.csv'} rows={len(out)} mean_p={p.mean():.4f}")


if __name__ == "__main__":
    main()
