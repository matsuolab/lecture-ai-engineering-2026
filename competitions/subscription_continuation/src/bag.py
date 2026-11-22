"""出来事トークンの袋モデル（対数カウント + L2 ロジスティック回帰）と入れ子 OOF 予測。"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import normalize


def bag_matrix(tokens: pd.Series):
    """ユーザー×トークンの log1p カウント（L2 正規化）。語彙は教師なしなので train+test 共通でよい。"""
    vec = CountVectorizer(token_pattern=r"\S+", lowercase=False, min_df=3)
    X = vec.fit_transform(tokens.to_numpy())
    X.data = np.log1p(X.data)
    return normalize(X), tokens.index


def _fit_predict(X, y, tr, pred_rows, C):
    m = LogisticRegression(C=C, max_iter=3000)
    m.fit(X[tr], y[tr])
    return m.decision_function(X[pred_rows])


def nested_bag_score(X, index: pd.Index, y_tr: pd.Series, others: pd.Index, C: float = 1.0,
                     n_inner: int = 5, seed: int = 0) -> pd.Series:
    """学習ユーザーには内側 K-fold の OOF スコア、その他（検証・テスト）には学習ユーザー全体で学習したスコア。"""
    pos = pd.Series(np.arange(len(index)), index=index)
    tr_rows = pos.loc[y_tr.index].to_numpy()
    yv = y_tr.to_numpy()
    out = pd.Series(np.nan, index=index)
    skf = StratifiedKFold(n_splits=n_inner, shuffle=True, random_state=seed)
    for a, b in skf.split(tr_rows, yv):
        m = LogisticRegression(C=C, max_iter=3000).fit(X[tr_rows[a]], yv[a])
        out.iloc[tr_rows[b]] = m.decision_function(X[tr_rows[b]])
    oth = pos.loc[others].to_numpy()
    m = LogisticRegression(C=C, max_iter=3000).fit(X[tr_rows], yv)
    out.iloc[oth] = m.decision_function(X[oth])
    return out
