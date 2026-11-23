"""事前学習モデル（EXAONE-Tabular / TabPFN-3 など）を Colab で動かすための入力行列を書き出す。

出力 npz の形式は検証レポートの tabpfn_mix_inputs_*.npz と同じキー:
  X (train 1,419 行 + test 1,414 行, float32, 欠損は NaN), y (train), n_tr, cat_idx (カテゴリ列の位置), columns, user_id
行順は train.csv → sample_submit.csv。カテゴリ列は全行の値から決めた順序コード（正解は使わない）、欠損は NaN。
袋モデルのスコアは fold ごとに作る入れ子の値なので含めない。
使い方: python src/export_fm_inputs.py --recover-mode full --out output/fm_inputs_ours.npz
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import train as T
from features import USER_COLS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recover-mode", default="full")
    ap.add_argument("--out", type=Path, default=Path("output/fm_inputs_ours.npz"))
    args = ap.parse_args()
    X, y, Xte, sub, _ = T.build_features(Path("input"), recover_mode=args.recover_mode, with_bag=False)
    A = pd.concat([X, Xte])
    for c in USER_COLS:
        codes = pd.Categorical(A[c], categories=sorted(A[c].dropna().unique())).codes.astype(float)
        A[c] = np.where(codes < 0, np.nan, codes)
    M = A.astype(float).to_numpy(np.float32)
    if np.isinf(M).any():
        raise ValueError("無限大の値があります")
    if M.shape[0] != len(X) + len(Xte) or not (A.index[len(X):] == sub[T.USER].to_numpy()).all():
        raise ValueError("行順が train → sample_submit になっていません")
    cat_idx = np.array([A.columns.get_loc(c) for c in USER_COLS], dtype=int)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.out, X=M, y=y.to_numpy().astype(int), n_tr=len(X), cat_idx=cat_idx,
                        columns=np.array(A.columns, dtype=object), user_id=np.array(A.index, dtype=object))
    print(f"{args.out}: X {M.shape}, カテゴリ {len(cat_idx)} 列, 欠損率 {np.isnan(M).mean():.4f}")


if __name__ == "__main__":
    main()
