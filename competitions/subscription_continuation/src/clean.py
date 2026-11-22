"""視聴ログのクレンジング。

観測された汚れ（EDA より）:
- タイトルID: 欠損(NaN)、接頭辞が落ちた数字のみ ("001")、"movie" のみ（jp_movie / intl_movie の判別不可）
- 視聴時間: 一部が秒単位で記録されている（>300 は 1話時間の約60倍）
- 視聴エピソードNo / 視聴デバイス: 欠損
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

USER = "ユーザーID"
TITLE = "タイトルID"
DT = "日時"
MINUTES = "視聴時間"
EP = "視聴エピソードNo"
SEASON = "視聴シーズンNo"
DEVICE = "視聴デバイス"
PROFILE = "プロフィール"

# 1話時間の最大は 180 分。これを大きく超える値は秒単位の記録とみなす
SECONDS_THRESHOLD = 300.0
_PREFIX_RE = re.compile(r"^(.*?)_?(\d+)$")


def read_csv(path) -> pd.DataFrame:
    """BOM 付き UTF-8 を想定して読み込む。列名の前後空白も除去する。"""
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _split_id(tid: str) -> tuple[str, str] | None:
    m = _PREFIX_RE.match(tid)
    return (m.group(1), m.group(2)) if m else None


def _candidates(raw, films_ids: list[str], by_suffix: dict, movie_ids: list[str]) -> list[str]:
    if pd.isna(raw):
        return films_ids
    raw = str(raw).strip()
    if raw.isdigit():
        return by_suffix.get(raw.zfill(3), [])
    if raw == "movie":
        return movie_ids
    return []


def recover_title_ids(log: pd.DataFrame, films: pd.DataFrame, max_gap_hours: float = 6.0) -> pd.Series:
    """壊れたタイトルIDを推定して返す（推定できなければ NaN）。

    優先順位:
      1. 同一ユーザー・前後のレコードのうち候補に含まれ時間的に近いもの（max_gap_hours 以内）
      2. 同一ユーザーが視聴した候補のうち最も視聴回数が多いもの
      3. 候補が数字/movie 由来なら、視聴時間・エピソードNoと整合する候補のうち全体で最も人気のもの
      4. 欠損(NaN)で手掛かりが無ければ NaN のまま
    """
    film_ids = films[TITLE].tolist()
    valid = set(film_ids)
    by_suffix: dict[str, list[str]] = {}
    for t in film_ids:
        sp = _split_id(t)
        if sp:
            by_suffix.setdefault(sp[1], []).append(t)
    movie_ids = [t for t in film_ids if "movie" in t]
    dur = films.set_index(TITLE)["1話当たりの時間(分)"].to_dict()
    n_ep = films.set_index(TITLE)["エピソード数"].to_dict()

    tid = log[TITLE].astype("string")
    is_valid = tid.isin(valid).fillna(False).to_numpy()
    popularity = log.loc[is_valid, TITLE].value_counts().to_dict()

    out = np.array(log[TITLE].where(is_valid, other=np.nan).astype(object).tolist(), dtype=object)
    order = log.sort_values([USER, DT], kind="stable").index.to_numpy()
    pos = {idx: i for i, idx in enumerate(order)}
    users = log[USER].to_numpy()
    times = log[DT].to_numpy()
    raw_ids = np.array(log[TITLE].astype(object).tolist(), dtype=object)
    minutes = log[MINUTES].to_numpy(dtype=float)
    eps = log[EP].to_numpy(dtype=float)
    idx_to_row = {idx: r for r, idx in enumerate(log.index)}

    user_counts = (
        log.loc[is_valid].groupby(USER)[TITLE].value_counts().rename("n").reset_index()
    )
    user_hist: dict[str, dict[str, int]] = {}
    for u, t, n in user_counts.itertuples(index=False):
        user_hist.setdefault(u, {})[t] = n

    gap = np.timedelta64(int(max_gap_hours * 3600), "s")
    bad_rows = np.where(~is_valid)[0]
    for r in bad_rows:
        cands = _candidates(raw_ids[r], film_ids, by_suffix, movie_ids)
        if not cands:
            continue
        cset = set(cands)
        u = users[r]
        p = pos[log.index[r]]
        # 1. 時間的に近い前後レコード（有効IDのみ）
        best, best_gap = None, None
        for step in (-1, 1):
            q = p + step
            while 0 <= q < len(order):
                rr = idx_to_row[order[q]]
                if users[rr] != u:
                    break
                g = abs(times[rr] - times[r])
                if g > gap:
                    break
                if is_valid[rr] and raw_ids[rr] in cset:
                    if best_gap is None or g < best_gap:
                        best, best_gap = raw_ids[rr], g
                    break
                q += step
        if best is not None:
            out[r] = best
            continue
        def consistent(c, tol=1.05):
            m = minutes[r]
            if not np.isnan(m) and m > SECONDS_THRESHOLD:
                m = m / 60.0
            ok_m = np.isnan(m) or m <= dur[c] * tol
            ok_e = np.isnan(eps[r]) or eps[r] <= n_ep[c]
            return ok_m and ok_e

        def closeness(c):
            # 視聴時間が1話時間に近いほど高スコア（多くの視聴は1話を見切っている）
            m = minutes[r]
            if np.isnan(m):
                return 0.0
            if m > SECONDS_THRESHOLD:
                m = m / 60.0
            return -abs(np.log((m + 1) / (dur[c] + 1)))

        # 2. 同一ユーザーの視聴履歴（視聴時間・エピソードと整合する候補を優先）
        hist = user_hist.get(u, {})
        in_hist = [c for c in cands if c in hist]
        if in_hist:
            cons = [c for c in in_hist if consistent(c)] or in_hist
            out[r] = max(cons, key=lambda c: (closeness(c) > -0.15, hist[c], closeness(c)))
            continue
        if pd.isna(raw_ids[r]):
            continue  # 完全欠損で手掛かり無し
        # 3. 視聴時間・エピソードの整合性 + 人気
        cc = [c for c in cands if consistent(c)] or cands
        out[r] = max(cc, key=lambda c: popularity.get(c, 0))
    return pd.Series(out, index=log.index, name=TITLE)


def clean_log(log: pd.DataFrame, films: pd.DataFrame) -> pd.DataFrame:
    log = log.copy()
    log[DT] = pd.to_datetime(log[DT], errors="coerce")
    if log[DT].isna().any():
        raise ValueError(f"日時をパースできない行が {log[DT].isna().sum()} 行あります")
    log[MINUTES] = pd.to_numeric(log[MINUTES], errors="coerce")
    log[EP] = pd.to_numeric(log[EP], errors="coerce")
    log[SEASON] = pd.to_numeric(log[SEASON], errors="coerce").fillna(1)

    log["title_raw_bad"] = (~log[TITLE].isin(set(films[TITLE]))).astype(int)
    log["title_missing"] = log[TITLE].isna().astype(int)
    log[TITLE] = recover_title_ids(log, films)

    # 視聴時間: 秒単位の記録を分に変換
    sec = log[MINUTES] > SECONDS_THRESHOLD
    log.loc[sec, MINUTES] = log.loc[sec, MINUTES] / 60.0
    fdur = log[TITLE].map(films.set_index(TITLE)["1話当たりの時間(分)"])
    # 欠損はタイトルの1話時間、それも無ければ全体中央値
    log[MINUTES] = log[MINUTES].fillna(fdur).fillna(log[MINUTES].median())
    # 1話時間の 1.2 倍で上限クリップ（タイトル不明なら 180 分）
    log[MINUTES] = np.minimum(log[MINUTES], fdur.fillna(150.0) * 1.2).clip(lower=0)
    log["ep_dur"] = fdur
    log["completion"] = (log[MINUTES] / fdur).clip(upper=1.0)

    # デバイス欠損: ユーザーの最頻値
    mode = log.dropna(subset=[DEVICE]).groupby(USER)[DEVICE].agg(lambda s: s.mode().iat[0])
    log["device_missing"] = log[DEVICE].isna().astype(int)
    log[DEVICE] = log[DEVICE].fillna(log[USER].map(mode)).fillna("Unknown")

    # エピソード欠損: 同一ユーザー×タイトル内で直前の既知エピソード + 経過行数
    #   （直前が無ければ直後の既知エピソード - 行数、それも無ければ 1）
    log = log.sort_values([USER, DT], kind="stable")
    key = [log[USER], log[TITLE].fillna("__unknown__")]
    known = log[EP].notna()
    grp_f = known.groupby(key).cumsum()
    off_f = log.groupby(key + [grp_f]).cumcount()
    est_f = log[EP].groupby(key).ffill() + off_f
    rev = log.iloc[::-1]
    key_r = [rev[USER], rev[TITLE].fillna("__unknown__")]
    grp_b = rev[EP].notna().groupby(key_r).cumsum()
    off_b = rev.groupby(key_r + [grp_b]).cumcount()
    est_b = (rev[EP].groupby(key_r).ffill() - off_b).iloc[::-1]
    log["ep_missing"] = (~known).astype(int)
    log[EP] = log[EP].fillna(est_f).fillna(est_b).fillna(1).clip(lower=1)
    return log.sort_index()
