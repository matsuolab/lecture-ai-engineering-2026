"""外部で計算した事前学習モデルの入れ子予測（npz）を fold ごとの特徴量として読み込む。

npz の形式（検証レポートのパイプラインと同じ）: キー s{seed}f{k}_{tr_idx,tr,va_idx,va,te}
  - 分割は StratifiedKFold(5, shuffle=True, random_state=seed) を train.csv の行順に適用したもの
  - tr: 学習行の内側 OOF ロジット、va: 検証行、te: test 全行（sample_submit の順）のロジット
読み込み時に分割が手元の分割と一致することを検証し、一致しなければ例外にする。
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

# 名前 → ファイル名の接頭辞（seed 範囲ごとにファイルが分かれている）
KNOWN = {
    "tabpfn": "tabpfn_mix_nested",   # TabPFN（mix 入力 846 列）
    "tabfm": "tabfm_nested",         # TabFM
    "limix": "limix_nested",         # LimiX-2（重みは非商用ライセンス）
    "ftfm": "ftfm_nested",           # FTFM-1（重みは CC BY-NC 4.0）
}


class ExternalScores:
    def __init__(self, directory: Path, names: list[str]):
        self.data: dict[str, dict[str, np.ndarray]] = {}
        for name in names:
            if name not in KNOWN:
                raise ValueError(f"未知の外部モデル: {name}（{list(KNOWN)}）")
            merged: dict[str, np.ndarray] = {}
            files = sorted(Path(directory).glob(f"{KNOWN[name]}_s*-*.npz"))
            if not files:
                raise FileNotFoundError(f"{directory} に {KNOWN[name]}_s*-*.npz がありません")
            for f in files:
                d = np.load(f, allow_pickle=True)
                merged.update({k: d[k] for k in d.files if k.startswith("s") and "f" in k})
            self.data[name] = merged

    def fold(self, seed: int, k: int, tr: np.ndarray, va: np.ndarray, n_test: int) -> dict[str, tuple]:
        """{name: (学習行の値, 検証行の値, test の値)} を手元の行順で返す。"""
        out = {}
        for name, d in self.data.items():
            key = f"s{seed}f{k}"
            if f"{key}_va" not in d:
                raise KeyError(f"{name} に {key} がありません")
            tr_idx, va_idx = d[f"{key}_tr_idx"].astype(int), d[f"{key}_va_idx"].astype(int)
            if not (np.array_equal(np.sort(tr_idx), np.sort(tr)) and np.array_equal(np.sort(va_idx), np.sort(va))):
                raise ValueError(f"{name} {key}: 分割が手元と一致しません")
            pos_tr = {r: i for i, r in enumerate(tr_idx)}
            pos_va = {r: i for i, r in enumerate(va_idx)}
            vtr = np.array([d[f"{key}_tr"][pos_tr[r]] for r in tr], dtype=float)
            vva = np.array([d[f"{key}_va"][pos_va[r]] for r in va], dtype=float)
            vte = np.asarray(d[f"{key}_te"], dtype=float)
            if len(vte) != n_test or not (np.isfinite(vtr).all() and np.isfinite(vva).all() and np.isfinite(vte).all()):
                raise ValueError(f"{name} {key}: 値の形または有限性が不正です")
            out[name] = (vtr, vva, vte)
        return out
