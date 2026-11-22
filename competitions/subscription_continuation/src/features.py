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

