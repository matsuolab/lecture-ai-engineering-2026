"""CV 改善候補（事前に固定）を、提出と同じ形（クレンジング平均 × 分割 seed 平均 × ブレンド）で比較する。

各（クレンジング, モデル）の OOF / test 予測を output/improve_cache/ にキャッシュし、候補の組合せを評価する。
評価は交差フィット（ブレンド重み・校正を別の利用者で決める）予測の LogLoss と、基準との利用者単位の対差 ± SE。
使い方: python src/improve_check.py --split-seeds 0-4
"""
from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import numpy as np

import train as T
from external import ExternalScores

warnings.filterwarnings("ignore")
CACHE = Path("output/improve_cache")


def get(variant, model, seeds, ext, feats):
    f = CACHE / f"{variant}_{model}_s{seeds[0]}-{seeds[-1]}.npz"
    if f.exists():
        d = np.load(f)
        return d["oof"], d["test"]
    X, y, Xte, _, bag = feats(variant)
    oof, test, _ = T.run_cv(X, y, Xte, [model], bag=bag, split_seeds=seeds, ext=ext, verbose=False)
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez(f, oof=oof[model], test=test[model])
    return oof[model], test[model]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split-seeds", default="0-4")
    ap.add_argument("--ext", default="tabpfn,tabfm,limix,ftfm")
    ap.add_argument("--cands", default="C1_production,C2_season_cov,C3_lgb3,C4_catboost")
    ap.add_argument("--out", type=Path, default=Path("output/improve_check.json"))
    args = ap.parse_args()
    T.load_params(Path("config/params.json"))
    a, b = (int(v) for v in args.split_seeds.split("-"))
    seeds = list(range(a, b + 1))
    ext = ExternalScores(Path("external"), args.ext.split(","))
    cache = {}

    def feats(v):
        if v not in cache:
            cache[v] = T.build_features(Path("input"), recover_mode=v)
        return cache[v]

    X0, y, *_ = feats("full")
    yv = y.to_numpy()
    season = (X0["max_season"] > 1).astype(float).to_numpy()
    base_variants = ["full", "no_history", "neighbor"]

    def avg(variants, model):
        zs = [T.logit(get(v, model, seeds, ext, feats)[0]) for v in variants]
        return 1 / (1 + np.exp(-np.mean(zs, axis=0)))

    def evaluate(P):
        p = np.clip(T.crossfit_blend_pred(P, yv), 1e-6, 1 - 1e-6)
        return -(yv * np.log(p) + (1 - yv) * np.log(1 - p))

    base = {"lgb": avg(base_variants, "lgb"), "lr": avg(base_variants, "lr")}
    lb = evaluate(base)
    print(f"B0 基準 {lb.mean():.5f}", flush=True)
    res = {"B0": float(lb.mean())}
    combos = {
        "C1_production": lambda: {"lgb": avg(base_variants + ["production"], "lgb"),
                                  "lr": avg(base_variants + ["production"], "lr")},
        "C2_season_cov": lambda: dict(base, cov_season=season),
        "C3_lgb3": lambda: {"lgb": avg(base_variants, "lgb3"), "lr": base["lr"]},
        "C4_catboost": lambda: dict(base, cat=avg(base_variants, "cat")),
    }
    for name in args.cands.split(","):
        l = evaluate(combos[name]())
        d = l - lb
        res[name] = dict(loss=float(l.mean()), diff=float(d.mean()), se=float(d.std(ddof=1) / np.sqrt(len(d))))
        print(f"{name:14s} {l.mean():.5f}  Δ {d.mean():+.5f} ± {res[name]['se']:.5f}", flush=True)
    args.out.write_text(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
