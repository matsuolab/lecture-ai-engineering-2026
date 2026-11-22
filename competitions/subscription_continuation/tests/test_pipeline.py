"""クレンジング・特徴量・ブレンドの単体テスト（合成データ）。

実行: cd competitions/subscription_continuation && python -m pytest tests -q
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from clean import clean_log, recover_title_ids  # noqa: E402
from features import user_log_features  # noqa: E402
from train import apply_blend, blend  # noqa: E402

FILMS = pd.DataFrame({
    "タイトルID": ["anime_001", "jd_001", "jp_movie_001", "intl_movie_002"],
    "タイトル名": ["a", "b", "c", "d"],
    "カテゴリ": ["アニメ", "国内ドラマ", "邦画", "洋画"],
    "週次配信": [1, 0, 0, 0], "独占配信": [0, 1, 0, 0], "シーズン数": [1, 1, 1, 1],
    "エピソード数": [12, 10, 1, 1], "1話当たりの時間(分)": [24.0, 50.0, 120.0, 110.0], "作品概要": ["x"] * 4,
})


def make_log(rows):
    cols = ["日時", "ユーザーID", "プロフィール", "タイトルID", "視聴時間", "視聴シーズンNo", "視聴エピソードNo", "視聴デバイス"]
    df = pd.DataFrame(rows, columns=cols)
    df["日時"] = pd.to_datetime(df["日時"])
    return df


def test_recover_digit_id_from_neighbor():
    log = make_log([
        ("2025-06-01 20:00", "U1", "USER_1", "anime_001", 24, 1, 1, "TV"),
        ("2025-06-01 20:30", "U1", "USER_1", "001", 24, 1, 2, "TV"),  # 接頭辞欠落
        ("2025-06-01 21:00", "U1", "USER_1", np.nan, 24, 1, 3, "TV"),  # 欠損
    ])
    rec = recover_title_ids(log, FILMS)
    assert rec.tolist() == ["anime_001", "anime_001", "anime_001"]


def test_recover_movie_uses_duration_when_no_history():
    log = make_log([("2025-06-01 20:00", "U2", "USER_1", "movie", 115, 1, 1, "TV")])
    # 視聴 115 分は intl_movie(110) の 1.05 倍以内、jp_movie(120) でも整合 → 人気同点なら候補先頭
    assert recover_title_ids(log, FILMS).iloc[0] in {"jp_movie_001", "intl_movie_002"}


def test_unrecoverable_missing_stays_nan():
    log = make_log([("2025-06-01 20:00", "U3", "USER_1", np.nan, 30, 1, 1, "TV")])
    assert pd.isna(recover_title_ids(log, FILMS).iloc[0])


def test_clean_log_seconds_and_imputation():
    log = make_log([
        ("2025-06-01 20:00", "U1", "USER_1", "jd_001", 3000, 1, 1, "TV"),      # 秒 → 50 分
        ("2025-06-01 21:00", "U1", "USER_1", "jd_001", 50, 1, np.nan, None),   # ep → 2, device → TV
        ("2025-06-01 22:00", "U1", "USER_1", "jd_001", np.nan, 1, np.nan, "TV"),  # ep → 3, 時間 → 50
    ])
    c = clean_log(log, FILMS)
    assert c["視聴時間"].tolist() == [50.0, 50.0, 50.0]
    assert c["視聴エピソードNo"].tolist() == [1.0, 2.0, 3.0]
    assert c["視聴デバイス"].tolist() == ["TV", "TV", "TV"]
    assert c["completion"].between(0, 1).all()


def test_user_log_features_shape_and_finite():
    log = make_log([
        ("2025-06-01 20:00", "U1", "USER_1", "anime_001", 24, 1, 1, "TV"),
        ("2025-06-10 20:00", "U1", "USER_2", "anime_001", 24, 1, 12, "Smartphone"),
        ("2025-06-05 08:00", "U2", "USER_1", "jd_001", 10, 1, 1, "PC"),
    ])
    F = user_log_features(clean_log(log, FILMS), FILMS)
    assert set(F.index) == {"U1", "U2"}
    assert np.isfinite(F.to_numpy(dtype=float)).all()
    assert F.loc["U1", "n_finished"] == 1 and F.loc["U1", "n_profiles"] == 2


def test_blend_improves_or_matches_single_model():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 2000)
    a = np.clip(0.5 + (y - 0.5) * 0.4 + rng.normal(0, 0.15, 2000), 0.01, 0.99)
    b = np.clip(0.5 + (y - 0.5) * 0.2 + rng.normal(0, 0.15, 2000), 0.01, 0.99)
    w, loss = blend({"a": a, "b": b}, y)
    from sklearn.metrics import log_loss
    assert loss <= log_loss(y, a) + 1e-9
    p = apply_blend({"a": a, "b": b}, w)
    assert np.all((p > 0) & (p < 1))


def test_clean_log_rejects_bad_datetime():
    log = make_log([("2025-06-01 20:00", "U1", "USER_1", "jd_001", 50, 1, 1, "TV")])
    log["日時"] = ["not a date"]
    with pytest.raises(ValueError):
        clean_log(log, FILMS)


def test_fix_minute_scale_picks_plausible_divisor():
    from clean import fix_minute_scale
    m = pd.Series([240.0, 3000.0, 50.0, 24.0, np.nan])
    d = pd.Series([24.0, 50.0, 50.0, 24.0, 60.0])
    out = fix_minute_scale(m, d)
    assert out.iloc[:4].tolist() == [24.0, 50.0, 50.0, 24.0]  # ×10, 秒(×60), 正常, 正常
    assert np.isnan(out.iloc[4])


def test_clean_log_drops_exact_duplicates():
    row = ("2025-06-01 20:00", "U1", "USER_1", "jd_001", 50, 1, 1, "TV")
    log = make_log([row, row, ("2025-06-01 21:00", "U1", "USER_1", "jd_001", 50, 1, 2, "TV")])
    assert len(clean_log(log, FILMS)) == 2
    assert len(clean_log(log, FILMS, dedupe=False)) == 3


def test_recover_modes():
    log = make_log([
        ("2025-06-01 20:00", "U1", "USER_1", "anime_001", 24, 1, 1, "TV"),
        ("2025-06-05 20:00", "U1", "USER_1", "001", 24, 1, 2, "TV"),  # 近傍なし → 履歴 or 人気で復元
    ])
    assert recover_title_ids(log, FILMS, mode="full").iloc[1] == "anime_001"
    assert pd.isna(recover_title_ids(log, FILMS, mode="neighbor").iloc[1])
    with pytest.raises(ValueError):
        recover_title_ids(log, FILMS, mode="bogus")


def test_event_tokens_and_extra_features_have_no_missing():
    from features import event_tokens, extra_features
    log = make_log([
        ("2025-06-01 20:00", "U1", "USER_1", "anime_001", 24, 1, 40, "TV"),  # 話数が総話数超え
        ("2025-06-02 01:00", "U1", "USER_2", np.nan, 30, 2, np.nan, None),
        ("2025-06-05 08:00", "U2", "USER_1", "jd_001", 10, 1, 1, "PC"),
    ])
    c = clean_log(log, FILMS)
    tok = event_tokens(c, FILMS)
    assert set(tok.index) == {"U1", "U2"} and tok.str.len().gt(0).all()
    E = extra_features(c, FILMS)
    assert np.isfinite(E.to_numpy(dtype=float)).all()
