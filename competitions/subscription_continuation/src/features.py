"""ユーザー単位の特徴量生成。"""
from __future__ import annotations

import numpy as np
import pandas as pd

from clean import DEVICE, DT, EP, MINUTES, PROFILE, SEASON, TITLE, USER

TRIAL_DAYS = 14  # 視聴ログ上の最大期間（初回視聴から最終視聴まで最大 14 日）
SESSION_GAP_MIN = 90  # 視聴開始の間隔がこれを超えたら別セッション

USER_COLS = [
    "職業_大カテゴリ", "職業_小カテゴリ", "性別", "年齢レンジ", "支払い方法", "居住地", "世帯年収レンジ",
    "Q1:新作やおすすめ作品の通知を受け取りますか？", "Q2:現在、他の動画配信サービスを使っていますか？",
    "Q3:サービスを知ったきっかけは？", "Q4:今回登録しようと思った決め手は？",
]
ORDINAL = {
    "年齢レンジ": ["25歳未満", "25歳以上30歳未満", "30歳以上35歳未満", "35歳以上40歳未満",
                "40歳以上45歳未満", "45歳以上50歳未満", "50歳以上65歳未満", "65歳以上"],
    "世帯年収レンジ": ["200万円以下", "200-400万円", "400-600万円", "600-800万円",
                  "800-1000万円", "1000-1500万円", "1500万円以上"],
    "Q1:新作やおすすめ作品の通知を受け取りますか？": ["受け取らない", "重要なものだけ受け取る", "受け取る（推奨）"],
}


def _share(df: pd.DataFrame, col: str, prefix: str, weight: str = MINUTES) -> pd.DataFrame:
    p = df.pivot_table(index=USER, columns=col, values=weight, aggfunc="sum", fill_value=0)
    p = p.div(p.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
    p.columns = [f"{prefix}_{c}" for c in p.columns]
    return p


def user_log_features(log: pd.DataFrame, films: pd.DataFrame) -> pd.DataFrame:
    f = films.set_index(TITLE)
    d = log.copy().sort_values([USER, DT], kind="stable")
    d["cat"] = d[TITLE].map(f["カテゴリ"]).fillna("不明")
    d["weekly"] = d[TITLE].map(f["週次配信"]).fillna(0)
    d["exclusive"] = d[TITLE].map(f["独占配信"]).fillna(0)
    d["n_ep_title"] = d[TITLE].map(f["エピソード数"])
    d["n_season_title"] = d[TITLE].map(f["シーズン数"])

    first = d.groupby(USER)[DT].transform("min")
    d["day"] = (d[DT].dt.normalize() - first.dt.normalize()).dt.days
    d["hour"] = d[DT].dt.hour
    d["wd"] = d[DT].dt.dayofweek
    gap = d.groupby(USER)[DT].diff().dt.total_seconds().div(60)
    d["new_session"] = (gap.isna() | (gap > SESSION_GAP_MIN)).astype(int)
    d["session_id"] = d.groupby(USER)["new_session"].cumsum()

    g = d.groupby(USER)
    F = pd.DataFrame(index=g.size().index)
    F["n_views"] = g.size()
    F["total_min"] = g[MINUTES].sum()
    F["mean_min"] = g[MINUTES].mean()
    F["std_min"] = g[MINUTES].std().fillna(0)
    F["mean_completion"] = g["completion"].mean()
    F["full_watch_rate"] = g["completion"].apply(lambda s: (s >= 0.9).mean())
    F["low_watch_rate"] = g["completion"].apply(lambda s: (s < 0.5).mean())
    F["active_days"] = g["day"].nunique()
    F["n_sessions"] = g["session_id"].max()
    F["views_per_session"] = F["n_views"] / F["n_sessions"]
    F["min_per_active_day"] = F["total_min"] / F["active_days"]
    F["n_titles"] = g[TITLE].nunique()
    F["n_cats"] = g["cat"].nunique()
    F["n_devices"] = g[DEVICE].nunique()
    F["n_profiles"] = g[PROFILE].nunique()
    F["non_main_profile_rate"] = g[PROFILE].apply(lambda s: (s != "USER_1").mean())
    F["first_dom"] = g[DT].min().dt.day
    F["first_wd"] = g[DT].min().dt.dayofweek
    F["last_day"] = g["day"].max()
    F["span_hours"] = (g[DT].max() - g[DT].min()).dt.total_seconds() / 3600
    # トライアル終了（初回視聴日+14日）または観測終了（6/30）までの空白
    obs_end = pd.Timestamp("2025-07-01")
    trial_end = (g[DT].min().dt.normalize() + pd.Timedelta(days=TRIAL_DAYS + 1)).clip(upper=obs_end)
    F["idle_hours_to_end"] = (trial_end - g[DT].max()).dt.total_seconds() / 3600
    F["trial_truncated"] = (g[DT].min().dt.normalize() + pd.Timedelta(days=TRIAL_DAYS + 1) > obs_end).astype(int)

    # 時間推移（KKBox 1位解法の時系列特徴に倣う）
    daily = d.pivot_table(index=USER, columns="day", values=MINUTES, aggfunc="sum", fill_value=0)
    daily = daily.reindex(columns=range(TRIAL_DAYS + 1), fill_value=0)
    for a, b in [(0, 2), (3, 6), (7, 10), (11, 14)]:
        F[f"min_d{a}_{b}"] = daily.loc[:, a:b].sum(axis=1)
    F["late_share"] = (daily.loc[:, 10:].sum(axis=1) / F["total_min"].replace(0, np.nan)).fillna(0)
    F["first3_share"] = (daily.loc[:, :2].sum(axis=1) / F["total_min"].replace(0, np.nan)).fillna(0)
    x = np.arange(daily.shape[1]); xc = x - x.mean()
    F["daily_slope"] = daily.to_numpy() @ xc / (xc @ xc)
    act = (daily > 0).astype(int)
    F["active_last7"] = act.loc[:, 8:].sum(axis=1)
    F["active_first7"] = act.loc[:, :6].sum(axis=1)
    F["max_daily_min"] = daily.max(axis=1)
    # 最長連続視聴日数
    F["max_streak"] = act.apply(lambda r: max((len(s) for s in "".join(map(str, r)).split("0")), default=0), axis=1)
    F["max_views_day"] = d.groupby([USER, "day"]).size().groupby(USER).max()
    F["max_views_session"] = d.groupby([USER, "session_id"]).size().groupby(USER).max()

    # 時間帯・曜日
    F["night_rate"] = g["hour"].apply(lambda s: s.isin([0, 1, 2, 3, 4]).mean())
    F["prime_rate"] = g["hour"].apply(lambda s: s.between(19, 23).mean())
    F["daytime_rate"] = g["hour"].apply(lambda s: s.between(9, 17).mean())
    F["weekend_rate"] = g["wd"].apply(lambda s: (s >= 5).mean())
    F["thu_rate"] = g["wd"].apply(lambda s: (s == 3).mean())

    # 作品属性
    F["weekly_rate"] = g["weekly"].mean()
    F["weekly_views"] = g["weekly"].sum()
    F["exclusive_rate"] = g["exclusive"].mean()
    F["exclusive_views"] = g["exclusive"].sum()
    F["season2plus_views"] = (d[SEASON] > 1).groupby(d[USER]).sum()
    F["multi_season_title_rate"] = (d["n_season_title"] > 1).groupby(d[USER]).mean()

    # ユーザー×タイトル単位の進捗
    ut = d.groupby([USER, TITLE]).agg(
        n=(EP, "size"), max_ep=(EP, "max"), uniq_ep=(EP, "nunique"), n_ep=("n_ep_title", "first"),
        weekly=("weekly", "first"), excl=("exclusive", "first"), last_day=("day", "max"),
    )
    ut["progress"] = (ut["uniq_ep"] / ut["n_ep"]).clip(upper=1)
    ut["finished"] = ((ut["max_ep"] >= ut["n_ep"]) & (ut["n_ep"] > 1)).astype(int)
    ut["series"] = (ut["n_ep"] > 1).astype(int)
    ut["ongoing"] = ((ut["series"] == 1) & (ut["finished"] == 0) & (ut["uniq_ep"] >= 2)).astype(int)
    ut["rewatch"] = ut["n"] - ut["uniq_ep"]
    gu = ut.groupby(level=0)
    F["n_series"] = gu["series"].sum()
    F["n_finished"] = gu["finished"].sum()
    F["n_ongoing"] = gu["ongoing"].sum()
    F["n_ongoing_weekly"] = (ut["ongoing"] * ut["weekly"]).groupby(level=0).sum()
    F["n_weekly_titles"] = gu["weekly"].sum()
    F["n_excl_titles"] = gu["excl"].sum()
    F["mean_progress"] = gu["progress"].mean()
    F["max_progress"] = gu["progress"].max()
    F["max_title_views"] = gu["n"].max()
    F["top_title_share"] = F["max_title_views"] / F["n_views"]
    F["rewatch_views"] = gu["rewatch"].sum()
    F["n_titles_last_days"] = ut[ut["last_day"] >= 10].groupby(level=0).size()
    # 残エピソード（未消化コンテンツ量）
    rem = (ut["n_ep"] - ut["max_ep"]).clip(lower=0) * ut["series"]
    F["remaining_eps"] = rem.groupby(level=0).sum()

    # データ品質（汚れ方自体が記録環境を反映する可能性）
    F["bad_title_rate"] = g["title_raw_bad"].mean()
    F["device_missing_rate"] = g["device_missing"].mean()
    F["ep_missing_rate"] = g["ep_missing"].mean()

    # 構成比
    F = F.join(_share(d, "cat", "cat_min")).join(_share(d, DEVICE, "dev_min"))
    cat_n = d.pivot_table(index=USER, columns="cat", values=MINUTES, aggfunc="size", fill_value=0)
    cat_n.columns = [f"cat_n_{c}" for c in cat_n.columns]
    F = F.join(cat_n)
    F = F.fillna(0)
    F.index.name = USER
    return F


def title_text_features(log: pd.DataFrame, films: pd.DataFrame, n_comp: int = 16, seed: int = 0) -> pd.DataFrame:
    """作品概要の TF-IDF(文字 n-gram) → SVD をユーザーの視聴時間で加重平均。"""
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_extraction.text import TfidfVectorizer

    text = (films["カテゴリ"].fillna("") + " " + films["タイトル名"].fillna("") + " " + films["作品概要"].fillna(""))
    X = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 3), min_df=3, sublinear_tf=True).fit_transform(text)
    emb = TruncatedSVD(n_components=n_comp, random_state=seed).fit_transform(X)
    emb = pd.DataFrame(emb, index=films[TITLE], columns=[f"txt{i}" for i in range(n_comp)])
    d = log[[USER, TITLE, MINUTES]].dropna(subset=[TITLE])
    d = d[d[TITLE].isin(emb.index)]
    W = d.groupby([USER, TITLE])[MINUTES].sum().unstack(fill_value=0)
    W = W.div(W.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
    out = W.to_numpy() @ emb.loc[W.columns].to_numpy()
    return pd.DataFrame(out, index=W.index, columns=emb.columns)


def user_static_features(df: pd.DataFrame) -> pd.DataFrame:
    X = df.set_index(USER)[USER_COLS].copy()
    for c in USER_COLS:
        X[c] = X[c].astype("string").str.strip().fillna("未回答")
    for c, levels in ORDINAL.items():
        X[f"{c}_ord"] = X[c].map({v: i for i, v in enumerate(levels)}).astype(float)
    return X



def _entropy(counts: pd.Series) -> float:
    p = counts / counts.sum()
    return float(-(p * np.log(p)).sum())


def extra_features(log: pd.DataFrame, films: pd.DataFrame) -> pd.DataFrame:
    """検証レポートで効果が報告された切り口（シーズン進行・週次の追いつき・カテゴリ×独占×週次・
    時間帯ルーティン・デバイスの組合せ）。"""
    f = films.set_index(TITLE)
    d = log.dropna(subset=[USER]).copy().sort_values([USER, DT], kind="stable")
    d["cat"] = d[TITLE].map(f["カテゴリ"]).fillna("不明")
    d["weekly"] = d[TITLE].map(f["週次配信"])
    d["excl"] = d[TITLE].map(f["独占配信"])
    d["n_ep_title"] = d[TITLE].map(f["エピソード数"])
    first = d.groupby(USER)[DT].transform("min")
    d["day"] = (d[DT].dt.normalize() - first.dt.normalize()).dt.days
    g = d.groupby(USER)
    F = pd.DataFrame(index=g.size().index)

    # シーズン進行
    F["max_season"] = g[SEASON].max()
    F["season2plus_titles"] = d[d[SEASON] > 1].groupby(USER)[TITLE].nunique()

    # 週次配信: 視聴時点で公開済みの話数 = 6/30 時点の話数 − (視聴日より後〜6/30 の木曜の数)
    end = pd.Timestamp("2025-06-30")
    thu_after = d[DT].dt.normalize().map(
        lambda t: int(((end - t).days + ((t.dayofweek - 3) % 7)) // 7) if t <= end else 0)
    d["avail_ep"] = (d["n_ep_title"] - thu_after).clip(lower=1)
    w = d[d["weekly"] == 1]
    if len(w):
        ut = w.groupby([USER, TITLE]).agg(max_ep=(EP, "max"), avail=("avail_ep", "last"), last_day=("day", "max"))
        ut["caught"] = (ut["max_ep"] >= ut["avail"]).astype(int)
        F["weekly_caught_up"] = ut["caught"].groupby(level=0).sum()
        F["weekly_caught_up_late"] = (ut["caught"] * (ut["last_day"] >= 7)).groupby(level=0).sum()
        # 公開から2日以内の新話視聴（最新話 = 公開済み話数の話を見た回数）
        fresh = (w[EP] >= w["avail_ep"]) & (w[DT].dt.dayofweek.isin([3, 4]))
        F["weekly_fresh_views"] = fresh.groupby(w[USER]).sum()
        F["weekly_thu_early"] = ((w[DT].dt.dayofweek == 3) & (w[DT].dt.hour < 6)).groupby(w[USER]).sum()

    # カテゴリ×独占×週次 の視聴時間シェア
    d["seg"] = d["cat"] + "_" + d["excl"].fillna(-1).astype(int).astype(str) + d["weekly"].fillna(-1).astype(int).astype(str)
    seg = d.pivot_table(index=USER, columns="seg", values=MINUTES, aggfunc="sum", fill_value=0)
    seg = seg.div(seg.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
    seg.columns = [f"seg_{c}" for c in seg.columns]
    F = F.join(seg)

    # 時間帯ルーティン
    F["hour_entropy"] = g["hour" if "hour" in d else DT].apply(lambda s: _entropy(s.dt.hour.value_counts()))
    F["top3_hour_share"] = g[DT].apply(lambda s: s.dt.hour.value_counts().nlargest(3).sum() / len(s))
    F["weekend_night_rate"] = g[DT].apply(lambda s: ((s.dt.dayofweek >= 4) & (s.dt.hour < 5)).mean())

    # デバイスの組合せ
    dev = d.pivot_table(index=USER, columns=DEVICE, values=MINUTES, aggfunc="size", fill_value=0) > 0
    has = lambda c: dev[c] if c in dev else False  # noqa: E731
    F["tv_and_phone"] = (has("TV") & has("Smartphone")).astype(int)
    F["no_tv"] = (~has("TV")).astype(int) if "TV" in dev else 1
    F["cross_device_titles"] = (d.groupby([USER, TITLE])[DEVICE].nunique() >= 2).groupby(level=0).sum()
    F["tv_prime_rate"] = g.apply(lambda x: ((x[DEVICE] == "TV") & x[DT].dt.hour.between(19, 23)).mean())
    F["tv_late_days"] = d[(d[DEVICE] == "TV") & d["day"].between(8, 12)].groupby(USER)["day"].nunique()
    F = F.fillna(0)
    F.index.name = USER
    return F


def event_tokens(log: pd.DataFrame, films: pd.DataFrame) -> pd.Series:
    """各視聴行を「出来事トークン」の文字列にする（袋モデル用）。ユーザーごとに空白区切りで連結。"""
    f = films.set_index(TITLE)
    d = log.dropna(subset=[USER]).copy()
    first = d.groupby(USER)[DT].transform("min")
    day = (d[DT].dt.normalize() - first.dt.normalize()).dt.days
    period = pd.cut(day, [-1, 3, 7, 10, 20], labels=["p0", "p1", "p2", "p3"]).astype(object).fillna("pna").astype(str)
    t = d[TITLE].fillna("unk").astype(str)
    n_ep = d[TITLE].map(f["エピソード数"])
    prog = pd.cut((d[EP] / n_ep).fillna(0), [-np.inf, 0.25, 0.5, 0.99, np.inf], labels=["q1", "q2", "q3", "fin"])
    prog = prog.astype(object).fillna("qna").astype(str)
    cat = d[TITLE].map(f["カテゴリ"]).fillna("unk").astype(str)
    ew = d[TITLE].map(f["独占配信"]).fillna(-1).astype(int).astype(str) + d[TITLE].map(f["週次配信"]).fillna(-1).astype(int).astype(str)
    hour = d[DT].dt.hour
    hb = pd.cut(hour, [-1, 4, 8, 16, 18, 23], labels=["h_night", "h_morn", "h_day", "h_eve", "h_prime"])
    hb = hb.astype(object).fillna("hna").astype(str)
    wk = np.where(d[DT].dt.dayofweek >= 5, "we", "wd")
    dev = d[DEVICE].fillna("Unknown").astype(str)
    season = np.where(d[SEASON] > 1, "s2p", "s1")
    tok = ("T_" + t + " TP_" + t + "_" + prog + " TT_" + t + "_" + period + " C_" + cat + "_" + ew
           + " CP_" + cat + "_" + period + " DP_" + dev + "_" + period + " HW_" + hb + "_" + wk
           + " DH_" + dev + "_" + hb + " PR_" + d[PROFILE].astype(str) + " S_" + season + "_" + cat)
    bad = tok.isna()
    if bad.any():
        raise ValueError(f"トークン生成で欠損が {int(bad.sum())} 行発生しました")
    return tok.groupby(d[USER]).agg(" ".join)

