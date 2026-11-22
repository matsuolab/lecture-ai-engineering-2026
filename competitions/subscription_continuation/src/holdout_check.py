"""評価手順そのものの楽観を測る: 学習データの一部を擬似 test として完全に取り分け、
残りだけで本番と同じ手順（繰り返し分割 CV × 3種クレンジング平均 × ブレンド）を回し、
手元の CV（OOF）と擬似 test の実損失を比べる。

外部の入れ子予測は全 1,419 人の分割で計算されているため、この検証では使わない。
使い方: python src/holdout_check.py --repeats 15
"""
from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import log_loss
from sklearn.model_selection import StratifiedKFold

import train as T
from clean import RECOVER_MODES

warnings.filterwarnings("ignore")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=15)
    ap.add_argument("--holdouts", type=int, default=5)
    ap.add_argument("--out", type=Path, default=Path("output/holdout_check.json"))
    args = ap.parse_args()
    T.load_params(Path("config/params.json"))
    feats = {m: T.build_features(Path("input"), recover_mode=m) for m in RECOVER_MODES}
    X0, y = feats["full"][0], feats["full"][1]
    rows = []
    for h, (dev, hold) in enumerate(StratifiedKFold(5, shuffle=True, random_state=99).split(X0, y)):
        if h >= args.holdouts:
            break
        oofs, tests = [], []
        for m in RECOVER_MODES:
            X, _, _, _, bag = feats[m]
            o, t, _ = T.run_cv(X.iloc[dev], y.iloc[dev], X.iloc[hold], ["lgb", "lr"], n_repeats=args.repeats,
                               seed=7000 + h, bag=bag, verbose=False)
            oofs.append(o)
            tests.append(t)
        avg = lambda ds, k: 1 / (1 + np.exp(-np.mean([T.logit(d[k]) for d in ds], axis=0)))  # noqa: E731
        oof = {k: avg(oofs, k) for k in ["lgb", "lr"]}
        tst = {k: avg(tests, k) for k in ["lgb", "lr"]}
        ydev, yhold = y.iloc[dev].to_numpy(), y.iloc[hold].to_numpy()
        w, cv_in = T.blend(oof, ydev)
        cv_cf = T.crossfit_blend_loss(oof, ydev)
        p = np.clip(T.apply_blend(tst, w), T.CLIP, 1 - T.CLIP)
        hold_ll = log_loss(yhold, p)
        lg = lambda q: np.log(q / (1 - q))  # noqa: E731
        poof = np.clip(T.apply_blend(oof, w), T.CLIP, 1 - T.CLIP)
        rows.append(dict(holdout=h, cv_in=cv_in, cv_crossfit=cv_cf, holdout_ll=hold_ll,
                         lgb_oof=log_loss(ydev, oof["lgb"]), lgb_hold=log_loss(yhold, tst["lgb"]),
                         spread_oof=float(lg(poof).std()), spread_hold=float(lg(p).std())))
        print(f"holdout{h}: CV(重み込み) {cv_in:.4f}  CV(交差フィット) {cv_cf:.4f}  擬似test {hold_ll:.4f}  "
              f"| LGB単体 OOF {rows[-1]['lgb_oof']:.4f} 擬似test {rows[-1]['lgb_hold']:.4f}  "
              f"| 予測の広がり OOF {rows[-1]['spread_oof']:.2f} test {rows[-1]['spread_hold']:.2f}", flush=True)
    df = pd.DataFrame(rows)
    gap = df.holdout_ll - df.cv_crossfit
    print(f"\n平均: CV(交差フィット) {df.cv_crossfit.mean():.4f}  擬似test {df.holdout_ll.mean():.4f}  "
          f"差 {gap.mean():+.4f} ± {gap.std(ddof=1) / np.sqrt(len(gap)):.4f}")
    args.out.write_text(json.dumps(dict(rows=rows, gap_mean=float(gap.mean())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
