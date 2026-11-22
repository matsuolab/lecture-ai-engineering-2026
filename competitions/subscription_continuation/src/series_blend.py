"""手元パイプラインの予測と、検証レポートの系列（series_logits.npz）を交差フィットで混合・評価し、提出ファイルを作る。

使える系列: tabmix / tabmixfm(v44) / fmlmx(v49) / fmlmxft(v52)。
除外: fmlmx_alz（レポートで「検証 fold 自身の分布で尺度合わせ」の漏れが判明し撤回された v51 の系列。OOF が楽観的）、
      notfm_* / ft_*（test 予測が無い）。
手元の予測は improve_check.py のキャッシュ（分割 seed 0-4 と 5-14）を分割数で重み付けして結合する。
使い方: python src/series_blend.py --variants full,no_history,neighbor,production --lgb lgb3
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import train as T

ALLOWED = ["tabmix", "tabmixfm", "fmlmx", "fmlmxft"]
LEAKY = {"fmlmx_alz"}
CACHE = Path("output/improve_cache")


def ours(variants, model):
    """各クレンジングの OOF/test（確率）を seed 範囲で結合し、クレンジング間は logit 平均。"""
    zo, zt = [], []
    for v in variants:
        parts = [(np.load(CACHE / f"{v}_{model}_s0-4.npz"), 5), (np.load(CACHE / f"{v}_{model}_s5-14.npz"), 10)]
        o = sum(d["oof"] * w for d, w in parts) / 15
        t = sum(d["test"] * w for d, w in parts) / 15
        zo.append(T.logit(o))
        zt.append(T.logit(t))
    sig = lambda z: 1 / (1 + np.exp(-z))  # noqa: E731
    return sig(np.mean(zo, axis=0)), sig(np.mean(zt, axis=0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", default="full,no_history,neighbor")
    ap.add_argument("--lgb", default="lgb")
    ap.add_argument("--series", default="fmlmxft", help=f"混ぜる系列（{ALLOWED} から）。空なら手元のみ")
    ap.add_argument("--series-npz", type=Path, default=Path("external/series_logits.npz"))
    ap.add_argument("--base-series", default="fmlmxft", help="対差の基準に使う系列の組（手元+この系列）")
    ap.add_argument("--out", type=Path, default=Path("output/submission_series_blend.csv"))
    args = ap.parse_args()
    variants = args.variants.split(",")
    names = [s for s in args.series.split(",") if s]
    bad = set(names) & LEAKY or set(names) - set(ALLOWED)
    if bad:
        raise ValueError(f"使えない系列: {bad}")

    d = np.load(args.series_npz, allow_pickle=True)
    tr = pd.read_csv("input/train.csv", encoding="utf-8-sig")
    sub = pd.read_csv("input/sample_submit.csv", header=None)
    if not ((d["user_id"][:1419] == tr["ユーザーID"].to_numpy()).all() and (d["user_id"][1419:] == sub[0].to_numpy()).all()):
        raise ValueError("series_logits の利用者順が train/sample_submit と一致しません")
    y = tr["継続フラグ"].to_numpy()
    sig = lambda z: 1 / (1 + np.exp(-z))  # noqa: E731

    def series(name):
        return sig(d[f"{name}_oof"].reshape(-1, 1419).mean(0)), sig(d[f"{name}_test"].reshape(-1, 1414).mean(0))

    lo, to = ours(variants, args.lgb)
    lr_o, lr_t = ours(variants, "lr")

    def build(snames):
        P, Q = {"lgb": lo, "lr": lr_o}, {"lgb": to, "lr": lr_t}
        for s in snames:
            P[s], Q[s] = series(s)
        return P, Q

    def ll(p):
        p = np.clip(p, 1e-6, 1 - 1e-6)
        return -(y * np.log(p) + (1 - y) * np.log(1 - p))

    Pb, _ = build([s for s in args.base_series.split(",") if s])
    lb = ll(T.crossfit_blend_pred(Pb, y))
    P, Q = build(names)
    l = ll(T.crossfit_blend_pred(P, y))
    dlt = l - lb
    w, _ = T.blend(P, y)
    p = np.clip(T.apply_blend(Q, w), T.CLIP, 1 - T.CLIP)
    if not (np.isfinite(p).all() and len(p) == len(sub)):
        raise RuntimeError("予測が不正です")
    pd.DataFrame({0: sub[0], 1: p}).to_csv(args.out, header=False, index=False)
    res = dict(variants=variants, lgb=args.lgb, series=names, crossfit=float(l.mean()), base=float(lb.mean()),
               diff=float(dlt.mean()), se=float(dlt.std(ddof=1) / np.sqrt(len(dlt))), weights=w)
    print(json.dumps(res, ensure_ascii=False))
    args.out.with_suffix(".json").write_text(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
