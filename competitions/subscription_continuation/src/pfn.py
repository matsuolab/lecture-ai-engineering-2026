"""TabPFN（事前学習済み表形式モデル）の入れ子予測を GBDT の特徴量にする（検証レポート v21 の方式）。

学習ユーザーには内側 K-fold の OOF、検証・テストユーザーには学習ユーザー全体で学習した予測を返す。
CPU では1回の学習・予測に約1分かかるため、(seed, fold, 学習ユーザー集合) をキーにディスクへキャッシュし、
同じ分割を使うクレンジング違いの実行で使い回す。
"""
from __future__ import annotations

import hashlib
import os
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

MODEL_PATH = os.environ.get("TABPFN_MODEL_PATH", "/root/models/tabpfn-v2-classifier-v2_default.ckpt")
CACHE_DIR = Path(os.environ.get("TABPFN_CACHE", "output/pfn_cache"))


def pfn_matrix(X: pd.DataFrame, cat_cols: list[str]) -> pd.DataFrame:
    """数値列 + カテゴリ列の one-hot（TabPFN 入力）。"""
    num = X.drop(columns=cat_cols).astype(float)
    cat = pd.get_dummies(X[cat_cols].astype(str)).astype(float)
    return pd.concat([num, cat], axis=1)


def _fit_predict(Ztr, ytr, Zpred, seed, n_estimators):
    from tabpfn import TabPFNClassifier

    if not Path(MODEL_PATH).exists():
        raise FileNotFoundError(f"TabPFN の重みがありません: {MODEL_PATH}")
    m = TabPFNClassifier(model_path=MODEL_PATH, device="cpu", n_estimators=n_estimators,
                         ignore_pretraining_limits=True, random_state=seed)
    m.fit(Ztr, ytr)
    p = np.clip(m.predict_proba(Zpred)[:, 1], 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def nested_pfn_score(Z: pd.DataFrame, y_tr: pd.Series, others: pd.Index, seed: int = 0,
                     n_inner: int = 3, n_estimators: int = 2) -> pd.Series:
    key = hashlib.sha1(("|".join(sorted(y_tr.index)) + f"#{seed}#{n_inner}#{n_estimators}").encode()).hexdigest()
    cache = CACHE_DIR / f"{key}.pkl"
    if cache.exists():
        s = pickle.loads(cache.read_bytes())
        if s.index.isin(others).sum() == len(others):  # 必要な行がそろっていれば再利用
            return s

    Zt = Z.loc[y_tr.index].to_numpy(dtype=np.float32)
    yv = y_tr.to_numpy()
    out = pd.Series(np.nan, index=y_tr.index.append(pd.Index(others)))
    for a, b in StratifiedKFold(n_inner, shuffle=True, random_state=seed).split(Zt, yv):
        out.iloc[b] = _fit_predict(Zt[a], yv[a], Zt[b], seed, n_estimators)
    out.loc[others] = _fit_predict(Zt, yv, Z.loc[others].to_numpy(dtype=np.float32), seed, n_estimators)
    if out.isna().any():
        raise RuntimeError("TabPFN スコアに欠損があります")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(pickle.dumps(out))
    return out
