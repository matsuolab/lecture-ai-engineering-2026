"""LightGBM の正則化候補（事前に固定した少数案）を、提出と同じ平均の形で比較する。

指標: 交差フィット LogLoss（ブレンド重みの楽観を除く）、fold ごとの損失の最大値・標準偏差（安定性）、
      test 予測の広がり（ロジット標準偏差、1%未満/99%超の割合）。
使い方: python src/reg_check.py --split-seeds 0-4 --ext tabpfn,tabfm,limix,ftfm
"""
from __future__ import annotations

import argparse
import copy
import json
import warnings
from pathlib import Path

import numpy as np

import train as T
from external import ExternalScores

warnings.filterwarnings("ignore")

CANDIDATES = {
    "R0_current": {},
    "R1_moderate": dict(num_leaves=15, max_depth=4, min_child_samples=30, reg_lambda=5.0, reg_alpha=0.5,
                        path_smooth=10.0),
    "R2_strong": dict(num_leaves=7, max_depth=3, min_child_samples=50, reg_lambda=20.0, reg_alpha=1.0,
                      path_smooth=30.0, n_estimators=1500),
    # 入れ子検証（外側 seed 1〜2 の 10 fold）で学習側ごとに選ばれたパラメータの中央値（学習率等は幾何平均）
    "R3_nested_consensus": dict(n_estimators=416, learning_rate=0.015, num_leaves=20, max_depth=4, min_child_samples=45,
                                subsample=0.84, colsample_bytree=0.26, reg_lambda=0.13, reg_alpha=0.068,
                                min_data_per_group=54, cat_smooth=18.8, cat_l2=19.7, max_cat_to_onehot=15),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split-seeds", default="0-4")
    ap.add_argument("--ext", default="tabpfn,tabfm,limix,ftfm")
    ap.add_argument("--variant", default="full")
    ap.add_argument("--only", default="")
    ap.add_argument("--out", type=Path, default=Path("output/reg_check.json"))
    args = ap.parse_args()
    T.load_params(Path("config/params.json"))
    base = copy.deepcopy(T.PARAMS["lgb"])
    a, b = (int(v) for v in args.split_seeds.split("-"))
    seeds = list(range(a, b + 1))
    ext = ExternalScores(Path("external"), args.ext.split(",")) if args.ext else None
    X, y, Xte, _, bag = T.build_features(Path("input"), recover_mode=args.variant)
    yv = y.to_numpy()
    res = {}
    names = args.only.split(",") if args.only else list(CANDIDATES)
    for name in names:
        T.PARAMS["lgb"] = dict(base, **CANDIDATES[name])
        oof, test, fl = T.run_cv(X, y, Xte, ["lgb", "lr"], bag=bag, split_seeds=seeds, ext=ext, verbose=False)
        w, ins = T.blend(oof, yv)
        cf = T.crossfit_blend_loss(oof, yv)
        p = np.clip(T.apply_blend(test, w), T.CLIP, 1 - T.CLIP)
        lg = np.log(p / (1 - p))
        f = np.array(fl["lgb"])
        res[name] = dict(crossfit=cf, in_sample=ins, lgb_fold_mean=f.mean(), lgb_fold_max=f.max(), lgb_fold_sd=f.std(),
                         test_logit_sd=float(lg.std()), test_extreme=float(np.mean((p < .01) | (p > .99))),
                         weights=w, fold_losses=f.tolist())
        print(f"{name:12s} 交差フィット {cf:.5f} | LGB fold 平均 {f.mean():.4f} 最大 {f.max():.4f} SD {f.std():.4f} "
              f"| test 広がり {lg.std():.2f} 極端 {res[name]['test_extreme']:.3f}", flush=True)
    args.out.write_text(json.dumps(res, ensure_ascii=False, indent=2, default=float))


if __name__ == "__main__":
    main()
