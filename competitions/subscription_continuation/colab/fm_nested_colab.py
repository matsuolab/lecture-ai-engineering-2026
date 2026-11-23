# %% [markdown]
# # EXAONE-Tabular / TabPFN-3 / TabPFN-3.5 の入れ子予測（Google Colab, GPU: L4 / A100 推奨）
# 手元パイプライン（src/external.py）がそのまま読める形式の npz を作る。作り方は検証レポートの TabPFN・TabFM・LimiX-2・FTFM-1 と同じ:
#   外側 StratifiedKFold(5, shuffle=True, random_state=seed) の各 fold で
#     - 学習側の内側 5 分割 OOF（random_state=1000+seed）→ "tr"（GBDT の学習行に使う値。評価用の行は一切使わない）
#     - 学習側全体で fit → 検証行 "va" と test 全行 "te"
#   値は継続確率のロジット。
# 1 fold ごとに Drive へ保存するので、切断されても同じセルを再実行すれば続きから再開する。
# 重みのライセンス: EXAONE-Tabular・TabPFN-3/3.5 とも非商用（研究・評価は可）。コンペ規約での使用可否の確認が必要。

# %%
MODEL = "exaone"                 # "exaone" | "tabpfn3" | "tabpfn35"
SRC = "fm_inputs_ours.npz"       # 入力: 手元の特徴量（145列, src/export_fm_inputs.py）または レポートの "tabpfn_mix_inputs_s0-4.npz"（846列）
SEEDS = list(range(15))          # 手元の外部予測と同じ seed 0〜14。まず list(range(5)) で試してもよい（後から増やしても済んだ fold は再計算しない）
USE_DRIVE = True
DRIVE_DIR = "/content/drive/MyDrive/fm_nested"
SMOKE_TEST = False               # True にすると 1 fold・内側なしで動作確認だけ行い、保存しない

# %%
!pip -q install -U huggingface_hub
if MODEL == "exaone":
    !pip -q install "exaonetabular @ git+https://github.com/LGAI-Research/EXAONE-Tabular.git"
else:
    !pip -q install -U tabpfn

# %%
import os, time, hashlib, importlib, json
import numpy as np
import torch
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import log_loss
assert MODEL in ("exaone", "tabpfn3", "tabpfn35"), MODEL
assert torch.cuda.is_available(), "GPU ランタイムにしてください（ランタイム → ランタイムのタイプを変更）"
print("GPU:", torch.cuda.get_device_name(0))
importlib.invalidate_caches()

# HF トークン: TabPFN-3/3.5 は gated（モデルページで利用規約に同意が必要）。Colab の「シークレット」に HF_TOKEN を登録しておく
try:
    from google.colab import userdata
    os.environ.setdefault("HF_TOKEN", userdata.get("HF_TOKEN"))
except Exception as e:
    print("HF_TOKEN をシークレットから読めませんでした（EXAONE は不要, TabPFN-3 は必要）:", type(e).__name__)

WORK = DRIVE_DIR if USE_DRIVE else "/content"
if USE_DRIVE:
    from google.colab import drive
    drive.mount("/content/drive")
os.makedirs(WORK, exist_ok=True)
path = os.path.join(WORK, SRC)
if not os.path.exists(path):
    from google.colab import files
    up = files.upload()
    name = next(k for k in up if k.startswith(SRC.replace(".npz", "")))
    open(path, "wb").write(up[name])
d = np.load(path, allow_pickle=True)
X, y, n = d["X"].astype(np.float32), d["y"].astype(int), int(d["n_tr"])
catM = [int(i) for i in d["cat_idx"]]
assert X.shape[0] == 1419 + 1414 and n == 1419 and len(y) == n and set(np.unique(y)) == {0, 1}, (X.shape, n)
assert not np.isinf(X).any(), "無限大の値があります"
assert all(0 <= i < X.shape[1] for i in catM)
seeds = [int(s) for s in SEEDS]
assert len(set(seeds)) == len(seeds)
Xtr_all, Xte_all = X[:n], X[n:]
FOLDS = {s: list(StratifiedKFold(5, shuffle=True, random_state=s).split(np.zeros(n), y)) for s in seeds}
print("入力", X.shape, "カテゴリ列", len(catM))

# %%
if MODEL == "exaone":
    from exaonetabular import EXAONETabularClassifier, __version__ as PKG_VER
    _EX = EXAONETabularClassifier.from_pretrained(device="cuda:0", seed=0)   # 重みは 1 回だけ読み込み、fit ごとに文脈を差し替える

    def make():
        return _EX
else:
    import tabpfn
    from tabpfn import TabPFNClassifier
    from tabpfn.constants import ModelVersion
    PKG_VER = tabpfn.__version__
    _ver = getattr(ModelVersion, {"tabpfn3": "V3", "tabpfn35": "V3_5"}[MODEL], None)
    assert _ver is not None, f"この tabpfn には {MODEL} がありません。ModelVersion の候補: {[m.name for m in ModelVersion]}"

    def make():
        m = TabPFNClassifier.create_default_for_version(_ver, device="cuda", random_state=0)
        m.set_params(categorical_features_indices=catM)   # カテゴリ列（順序コード）を明示
        return m
print(MODEL, "package", PKG_VER)


def predict(A, ya, Qs):
    """学習行 A, ya で fit し、Qs（行列のリスト）それぞれの継続ロジットを返す。"""
    m = make()
    m.fit(A.copy(), ya.copy())
    assert list(np.asarray(m.classes_)) == [0, 1], m.classes_
    Q = np.vstack(Qs)
    P = np.asarray(m.predict_proba(Q))[:, 1].astype(np.float64)
    assert P.shape == (len(Q),) and np.isfinite(P).all()
    P = np.clip(P, 1e-6, 1 - 1e-6)
    z = np.log(P / (1 - P))
    out, s = [], 0
    for q in Qs:
        out.append(z[s:s + len(q)]); s += len(q)
    torch.cuda.empty_cache()
    return out


# %% 動作確認（任意）: 1 fold の学習側で fit し検証行の LogLoss を表示
if SMOKE_TEST:
    tr, va = FOLDS[seeds[0]][0]
    t0 = time.time()
    zva, = predict(Xtr_all[tr], y[tr], [Xtr_all[va]])
    print(f"smoke: 検証 LogLoss {log_loss(y[va], 1 / (1 + np.exp(-zva))):.4f}  {time.time() - t0:.1f}s")
    raise SystemExit("SMOKE_TEST=False にして本番を実行してください")

# %% 本番: 入れ子予測（再開可能）
tag = hashlib.md5(open(path, "rb").read()).hexdigest()[:8]
PART = os.path.join(WORK, f"partial_{MODEL}_{tag}.npz")
out = dict(np.load(PART, allow_pickle=True)) if os.path.exists(PART) else {}
NF = 5 * len(seeds)
print("済み", sum(k.endswith("_va") for k in out), f"/ {NF} fold", flush=True)
t0 = time.time()
for s in seeds:
    for k in range(5):
        key = f"s{s}f{k}"
        if f"{key}_va" in out:
            continue
        tr, va = FOLDS[s][k][0].astype(int), FOLDS[s][k][1].astype(int)
        assert len(np.intersect1d(tr, va)) == 0 and len(tr) + len(va) == n
        oof = np.full(len(tr), np.nan)
        for a, b in StratifiedKFold(5, shuffle=True, random_state=1000 + s).split(np.zeros(len(tr)), y[tr]):
            oof[b] = predict(Xtr_all[tr[a]], y[tr[a]], [Xtr_all[tr[b]]])[0]
        assert np.isfinite(oof).all()
        zva, zte = predict(Xtr_all[tr], y[tr], [Xtr_all[va], Xte_all])
        out.update({f"{key}_tr_idx": tr, f"{key}_tr": oof, f"{key}_va_idx": va,
                    f"{key}_va": zva.astype(np.float32), f"{key}_te": zte.astype(np.float32)})
        np.savez_compressed(PART + ".tmp.npz", **out); os.replace(PART + ".tmp.npz", PART)
        ll = log_loss(y[va], 1 / (1 + np.exp(-zva)))
        print(f"{key} 完了 検証 LogLoss {ll:.4f}  {sum(kk.endswith('_va') for kk in out)}/{NF}  {time.time() - t0:.0f}s", flush=True)

# %% まとめ: 単体の OOF LogLoss（seed ごと）と保存
done = [s for s in seeds if all(f"s{s}f{k}_va" in out for k in range(5))]
assert len(done) == len(seeds), "未完了の fold があります。上のセルを再実行してください"
lls = []
for s in seeds:
    z = np.zeros(n)
    for k in range(5):
        z[out[f"s{s}f{k}_va_idx"]] = out[f"s{s}f{k}_va"]
    lls.append(log_loss(y, 1 / (1 + np.exp(-z))))
summary = dict(model=MODEL, package=str(PKG_VER), src=SRC, src_md5=tag, seeds=seeds,
               oof_logloss_mean=float(np.mean(lls)), oof_logloss_per_seed=[round(float(v), 5) for v in lls])
print(json.dumps(summary, ensure_ascii=False, indent=1))
fn = os.path.join(WORK, f"{MODEL}_nested_s{seeds[0]}-{seeds[-1]}.npz")
np.savez_compressed(fn, model=MODEL, summary=json.dumps(summary), **out)
from google.colab import files
files.download(fn)
print("完了", fn)
