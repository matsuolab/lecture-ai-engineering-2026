"""第1回 宿題(発展): チャンク到着の推移(パレート図)とチャンクごとの出力速度(箱ひげ図)を質問別に描く。

使い方(リポジトリのルートで):
    uv run python lectures/01/src/plot_chunks.py lectures/01/results lectures/01/results/measurements.jsonl lectures/01/results/measurements_long.jsonl
入力: measure_llm.py が出力した JSONL を 1 つ以上(chunks は [受信時刻(s), 文字数, 累積出力トークン数])。
出力: 先頭の引数の出力先ディレクトリに chunk_pareto_<質問>.png(モデル別の代表 1 回)と chunk_tps_box_<質問>.png(全チャンク)。
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

STATUS_OK = "ok"
PLOT_QUESTIONS = ("long", "short")
# チャンク間隔がこれ未満だと速度が跳ねるので除く(秒)
MIN_INTERVAL_S = 0.01
BAR_WIDTH_RATIO = 0.006
BAR_COLOR = "tab:blue"
LINE_COLOR = "tab:red"

plt.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "sans-serif"]


def load_ok(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return [r for r in rows if r.get("status") == STATUS_OK and r.get("chunks")]


def chunk_tokens(chunks: list[list]) -> list[tuple[float, int]]:
    """(受信時刻, そのチャンクで増えたトークン数)の列。累積が欠けたチャンクは飛ばす。"""
    out, prev = [], 0
    for t, _chars, cum in chunks:
        if cum is None:
            continue
        out.append((t, cum - prev))
        prev = cum
    return out


def chunk_tps(chunks: list[list]) -> list[float]:
    """隣り合うチャンクの間の出力速度。最初のチャンクは区間を持たないので含めない。"""
    pairs = [(t, cum) for t, _c, cum in chunks if cum is not None]
    return [
        (c1 - c0) / (t1 - t0)
        for (t0, c0), (t1, c1) in zip(pairs, pairs[1:])
        if t1 - t0 >= MIN_INTERVAL_S
    ]


def plot_pareto(by_model: dict[str, list[dict]], question: str, out: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for ax, (model, rows) in zip(axes.flat, sorted(by_model.items())):
        row = rows[-1]  # 代表は入力の最後の成功回(結果で選ばない固定の規則)
        pts = chunk_tokens(row["chunks"])
        times = [t for t, _ in pts]
        deltas = [d for _, d in pts]
        total = sum(deltas)
        cumulative = [sum(deltas[: i + 1]) for i in range(len(deltas))]
        # 到着が偏るモデルでも棒が重ならないよう、幅は区間全体に対する固定の割合にする
        ax.bar(times, deltas, width=(max(times) - min(times)) * BAR_WIDTH_RATIO, color=BAR_COLOR, alpha=0.6)
        ax.set_xlabel("送信からの経過時間 [s]")
        ax.set_ylabel("チャンクごとのトークン数")
        line = ax.twinx()
        line.plot(times, cumulative, color=LINE_COLOR, marker="o", markersize=3)
        line.set_ylim(0, total)
        line.set_ylabel(f"累積出力トークン数(最大 = 総出力 {total})")
        ax.set_title(f"{model}: {len(pts)} チャンク(repeat {row['repeat']})")
    fig.legend(
        handles=[
            Patch(color=BAR_COLOR, alpha=0.6, label="青の棒: そのチャンクで届いたトークン数(左軸)"),
            Line2D([], [], color=LINE_COLOR, marker="o", markersize=3, label="赤の線: 累積出力トークン数(右軸)"),
        ],
        loc="lower center",
        ncol=2,
    )
    fig.suptitle(f"チャンク到着の推移(パレート図): 質問 {question}、モデルごとの代表 1 回")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(out, dpi=150)


def plot_tps_box(by_model: dict[str, list[dict]], question: str, out: Path) -> None:
    models = sorted(by_model)
    data = [[v for r in by_model[m] for v in chunk_tps(r["chunks"])] for m in models]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.boxplot(data, tick_labels=[f"{m}\n(n={len(d)})" for m, d in zip(models, data)])
    ax.set_ylabel("チャンクごとの出力速度 [tokens/s](対数軸)")
    ax.set_yscale("log")
    ax.set_title(f"チャンクごとの出力速度の分布: 質問 {question}、成功した全回(n はチャンク間の区間数)")
    fig.tight_layout()
    fig.savefig(out, dpi=150)


def main() -> None:
    out_dir, paths = Path(sys.argv[1]), [Path(p) for p in sys.argv[2:]]
    rows = [r for p in paths for r in load_ok(p)]
    for question in PLOT_QUESTIONS:
        by_model = defaultdict(list)
        for r in rows:
            if r["question_id"] == question:
                by_model[r["model"]].append(r)
        plot_pareto(by_model, question, out_dir / f"chunk_pareto_{question}.png")
        plot_tps_box(by_model, question, out_dir / f"chunk_tps_box_{question}.png")


if __name__ == "__main__":
    main()
