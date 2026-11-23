"""新しい事前学習モデルの入れ子予測（colab/fm_nested_colab.py の出力）を加えたときの効果を、最終形で評価する。

1. 単体診断: 新モデルの OOF LogLoss（分割 seed ごとの平均）と、既存の外部予測とのロジット相関（似すぎていれば上積みは小さい）
2. 最終形の比較（分割 seed 0〜14, 4種クレンジング平均, LightGBM + LR + v52 系列, 交差フィット）:
     基準  = 既存の外部予測4本（output/improve_cache の結果を再利用）
     候補  = 4本 + 新モデル（--mode add）または 1 本を置き換え（--mode replace --drop tabpfn）
   利用者単位の対差 ± SE を出し、提出ファイルも書く。
使い方: python src/fm_check.py --new exaone
        python src/fm_check.py --new exaone,tabpfn3
"""
from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import log_loss

import series_blend as SB
import train as T
from external import KNOWN, ExternalScores

warnings.filterwarnings("ignore")
BASE_EXT = ["tabpfn", "tabfm", "limix", "ftfm"]
SEEDS = list(range(15))
VARIANTS = ["full", "no_history", "neighbor", "production"]


def diagnose(names, y):
    ext = ExternalScores(Path("external"), sorted(set(names) | set(BASE_EXT)))
    res = {}
    for name in names:
        lls, cors = [], {b: [] for b in BASE_EXT}
        for s in SEEDS:
            z = {m: np.zeros(len(y)) for m in [name] + BASE_EXT}
            for k in range(5):
                d = ext.data[name]
                va = d[f"s{s}f{k}_va_idx"].astype(int)
                for m in z:
                    dm = ext.data[m]
                    pos = {r: i for i, r in enumerate(dm[f"s{s}f{k}_va_idx"].astype(int))}
                    z[m][va] = [dm[f"s{s}f{k}_va"][pos[r]] for r in va]
            lls.append(log_loss(y, 1 / (1 + np.exp(-z[name]))))
            for b in BASE_EXT:
                cors[b].append(np.corrcoef(z[name], z[b])[0, 1])
        res[name] = dict(oof_logloss=float(np.mean(lls)), logit_corr={b: round(float(np.mean(v)), 3) for b, v in cors.items()})
        print(f"{name}: 単体 OOF LogLoss {res[name]['oof_logloss']:.4f}  既存とのロジット相関 {res[name]['logit_corr']}", flush=True)
    return res


def run_set(ext_names, variants):
    tag = "+".join(ext_names)
    cache = Path("output/fm_cache") / tag
    cache.mkdir(parents=True, exist_ok=True)
    ext = ExternalScores(Path("external"), ext_names)
    zs = {"lgb": ([], []), "lr": ([], [])}
    for v in variants:
        need = [m for m in zs if not (cache / f"{v}_{m}_s0-14.npz").exists()]
        if need:
            X, y, Xte, _, bag = T.build_features(Path("input"), recover_mode=v)
            oof, test, _ = T.run_cv(X, y, Xte, need, bag=bag, split_seeds=SEEDS, ext=ext, verbose=False)
            for m in need:
                np.savez(cache / f"{v}_{m}_s0-14.npz", oof=oof[m], test=test[m])
            print(f"  {tag} {v} 計算済み", flush=True)
        for m in zs:
            dd = np.load(cache / f"{v}_{m}_s0-14.npz")
            zs[m][0].append(T.logit(dd["oof"]))
            zs[m][1].append(T.logit(dd["test"]))
    sig = lambda z: 1 / (1 + np.exp(-np.mean(z, axis=0)))  # noqa: E731
    return {m: (sig(a), sig(b)) for m, (a, b) in zs.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new", required=True, help="追加するモデル（例: exaone,tabpfn3）")
    ap.add_argument("--mode", choices=["add", "replace"], default="add")
    ap.add_argument("--drop", default="tabpfn", help="--mode replace で外す既存モデル")
    ap.add_argument("--diag-only", action="store_true")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    new = [s for s in args.new.split(",") if s]
    unknown = set(new) - set(KNOWN)
    if unknown:
        raise ValueError(f"未知のモデル: {unknown}")
    T.load_params(Path("config/params.json"))
    tr = pd.read_csv("input/train.csv", encoding="utf-8-sig")
    y = tr["継続フラグ"].to_numpy()
    res = dict(diagnose=diagnose(new, y))
    if args.diag_only:
        print(json.dumps(res, ensure_ascii=False))
        return

    cand_ext = BASE_EXT + new if args.mode == "add" else [e for e in BASE_EXT if e != args.drop] + new
    d = np.load("external/series_logits.npz", allow_pickle=True)
    sub = pd.read_csv("input/sample_submit.csv", header=None)
    if not ((d["user_id"][:1419] == tr["ユーザーID"].to_numpy()).all() and (d["user_id"][1419:] == sub[0].to_numpy()).all()):
        raise ValueError("series_logits の利用者順が一致しません")
    sig = lambda z: 1 / (1 + np.exp(-z))  # noqa: E731
    v52 = sig(d["fmlmxft_oof"].reshape(-1, 1419).mean(0)), sig(d["fmlmxft_test"].reshape(-1, 1414).mean(0))

    base = {"lgb": SB.ours(VARIANTS, "lgb"), "lr": SB.ours(VARIANTS, "lr")}   # 既存4本（improve_cache）
    cand = run_set(cand_ext, VARIANTS)

    def ll(p):
        p = np.clip(p, 1e-6, 1 - 1e-6)
        return -(y * np.log(p) + (1 - y) * np.log(1 - p))

    out = {}
    for label, S in [("base", base), ("cand", cand)]:
        P = {"lgb": S["lgb"][0], "lr": S["lr"][0], "fmlmxft": v52[0]}
        Q = {"lgb": S["lgb"][1], "lr": S["lr"][1], "fmlmxft": v52[1]}
        out[label] = (ll(T.crossfit_blend_pred(P, y)), P, Q)
    dl = out["cand"][0] - out["base"][0]
    w, _ = T.blend(out["cand"][1], y)
    p = np.clip(T.apply_blend(out["cand"][2], w), T.CLIP, 1 - T.CLIP)
    if not (np.isfinite(p).all() and len(p) == len(sub)):
        raise RuntimeError("予測が不正です")
    fn = args.out or Path(f"output/submission_fm_{'_'.join(new)}_{args.mode}.csv")
    pd.DataFrame({0: sub[0], 1: p}).to_csv(fn, header=False, index=False)
    res.update(ext=cand_ext, base=float(out["base"][0].mean()), cand=float(out["cand"][0].mean()),
               diff=float(dl.mean()), se=float(dl.std(ddof=1) / np.sqrt(len(dl))), weights=w, submission=str(fn))
    print(f"基準 {res['base']:.5f}  候補 {res['cand']:.5f}  Δ {res['diff']:+.5f} ± {res['se']:.5f}  → {fn}")
    fn.with_suffix(".json").write_text(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
