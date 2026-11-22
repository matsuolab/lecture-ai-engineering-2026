"""擬似 test の同じ利用者で、予測の作り方と正則化を対応のある比較で検証する。

学習データを 5 分割し、各分割を擬似 test（hold）として取り分け、残り（dev）で繰り返し分割 CV を回す。
hold の各利用者について次を作り、利用者ごとの損失を比べる（全 1,419 人が 1 回ずつ hold になる）。
  - test 方式: 全 fold モデル（repeats × 5 個）の平均  … 本番の test 予測と同じ
  - CV 方式  : 各 repeat でランダムに割り当てた 1 fold のモデルだけ（repeats 個）の平均 … 本番の OOF と同じ
  - dev の OOF 損失（=手元の CV）も記録
正則化候補（reg_check.CANDIDATES）ごとに同じ分割・同じ乱数で実行する。
使い方: python src/holdout_paired.py --repeats 10 --cands R0_current,R2_strong
"""
from __future__ import annotations

import argparse
import copy
import json
import warnings
from pathlib import Path

import numpy as np
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedKFold

import train as T
from bag import nested_bag_score
from reg_check import CANDIDATES

warnings.filterwarnings("ignore")


def ll(y, p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=10)
    ap.add_argument("--cands", default="R0_current,R2_strong")
    ap.add_argument("--out", type=Path, default=Path("output/holdout_paired.json"))
    args = ap.parse_args()
    T.load_params(Path("config/params.json"))
    base = copy.deepcopy(T.PARAMS["lgb"])
    X, y, Xte, _, (M, idx) = T.build_features(Path("input"))
    X = T.to_category(X, X)
    yv = y.to_numpy()
    cands = args.cands.split(",")
    n = len(X)
    out = {c: dict(test_style=np.zeros(n), cv_style=np.zeros(n), dev_oof_loss=[]) for c in cands}
    rng = np.random.default_rng(0)
    for h, (dev, hold) in enumerate(StratifiedKFold(5, shuffle=True, random_state=99).split(X, y)):
        Xd, yd = X.iloc[dev], y.iloc[dev]
        splits = list(RepeatedStratifiedKFold(n_splits=5, n_repeats=args.repeats, random_state=500 + h).split(Xd, yd))
        assign = rng.integers(0, 5, size=(args.repeats, len(hold)))  # CV 方式で hold 利用者が属する fold
        preds = {c: np.zeros((len(splits), len(hold))) for c in cands}
        oofs = {c: np.zeros(len(dev)) for c in cands}
        for i, (tr, va) in enumerate(splits):
            sc = nested_bag_score(M, idx, yd.iloc[tr], Xd.index[va].append(X.index[hold]), C=20.0, seed=900 + i)
            A = Xd.assign(bag_score=sc.reindex(Xd.index).to_numpy())
            H = X.iloc[hold].assign(bag_score=sc.reindex(X.index[hold]).to_numpy())
            for c in cands:
                T.PARAMS["lgb"] = dict(base, **CANDIDATES[c])
                pv, ph = T.fit_lgb(A.iloc[tr], yd.iloc[tr], A.iloc[va], H, 1000 + i)
                oofs[c][va] += pv / args.repeats
                preds[c][i] = ph
        for c in cands:
            P = preds[c]
            out[c]["test_style"][hold] = P.mean(axis=0)
            cv_p = np.zeros(len(hold))
            for r in range(args.repeats):
                cv_p += P[r * 5 + assign[r], np.arange(len(hold))] / args.repeats
            out[c]["cv_style"][hold] = cv_p
            out[c]["dev_oof_loss"].append(float(ll(yd.to_numpy(), oofs[c]).mean()))
        print(f"holdout{h} 完了", flush=True)
    res = {}
    for c in cands:
        lt, lc = ll(yv, out[c]["test_style"]), ll(yv, out[c]["cv_style"])
        d = lt - lc
        res[c] = dict(test_style=float(lt.mean()), cv_style=float(lc.mean()), dev_cv=float(np.mean(out[c]["dev_oof_loss"])),
                      test_minus_cv=float(d.mean()), se=float(d.std(ddof=1) / np.sqrt(n)))
        print(f"{c:12s} 手元CV(dev OOF) {res[c]['dev_cv']:.4f} | hold: CV方式 {lc.mean():.4f}  test方式 {lt.mean():.4f}  "
              f"(test−CV {d.mean():+.4f} ± {res[c]['se']:.4f})")
    if len(cands) >= 2:
        a, b = cands[0], cands[1]
        d = ll(yv, out[b]["test_style"]) - ll(yv, out[a]["test_style"])
        print(f"{b} − {a}（hold, test方式）: {d.mean():+.4f} ± {d.std(ddof=1) / np.sqrt(n):.4f}")
        res["diff_" + b + "_minus_" + a] = [float(d.mean()), float(d.std(ddof=1) / np.sqrt(n))]
    args.out.write_text(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
