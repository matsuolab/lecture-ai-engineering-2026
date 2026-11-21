"""第5回宿題(実装): 前後ページが効く質問かを、検索結果だけで判定する。

使い方（リポジトリ直下で）:
    uv run python lectures/05/neighbor_check.py

各質問で search() を1回だけ呼び（埋め込みAPI 1回）、同じ結果に add_neighbors を適用して
「前後なし」と「前後1ページあり」を比べる。LLM は使わない。
need は、答えに必要な根拠ページ（PDFページ番号）。
上位k件(k=1,2,3,5)ごとに、Bが入るか・返したページ数を比べる。
判定: 前後なしで無く、前後ありで初めて入る → "効く"。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.retrieval import add_neighbors, load_pages, search  # noqa: E402

# (質問, 回, 主題のページ A, 答えに必要な隣のページ B)
CASES = [
    ("QLoRAで学習した演習のモデルは、JSONなど形式は直る一方で、何は直らないとされていますか？", 2, 52, 53),
    ("モデル・手法の大別で『既存ツールとの組み合わせ』に挙がっているRAGは、具体的にどういう流れで動きますか？", 1, 48, 49),
    ("人が毎回承認する human-in-the-loop の形にしても、送金や注文のようなツールで起きうる問題は何ですか？", 3, 26, 27),
    ("継続事前学習で知識を足す方法と比べて、FTで小さいモデルに振る舞いを覚えさせると、1講義200問の料金はいくらになりますか？", 2, 48, 49),
    ("事後学習で答え方を直せるのに対して、使うときに考えさせると難問の正答率はどう変わりますか？", 2, 24, 25),
]


def has(rows, lecture, page):
    return any(r["lecture"] == lecture and r["page"] == page for r in rows)


def main() -> None:
    pages = load_pages()
    ks = (1, 2, 3, 5)
    for question, lecture, a, b in CASES:
        hits = search(question)  # RAG_TOP_K件。距離の近い順なので、上から切れば上位k件になる
        order = [f"{h['lecture']}-p{h['page']}" for h in hits]
        rank = next((i + 1 for i, h in enumerate(hits) if h["lecture"] == lecture and h["page"] == b), None)
        print(f"\n質問: {question}")
        print(f"  A=第{lecture}回p.{a} / 必要なB=第{lecture}回p.{b}  (Bの検索順位: {rank or '圏外'})")
        print(f"  上位の並び: {', '.join(order)}")
        print("   k | 前後なし: B有無/ページ数 | 前後あり: B有無/ページ数 | 判定")
        for k in ks:
            plain = add_neighbors(hits[:k], 0, pages)
            wide = add_neighbors(hits[:k], 1, pages)
            p_has, w_has = has(plain, lecture, b), has(wide, lecture, b)
            verdict = "効く" if (not p_has and w_has) else "不要" if p_has else "入らない"
            print(f"  {k:>2} | {'あり' if p_has else 'なし'} / {len(plain):>2}枚          "
                  f"| {'あり' if w_has else 'なし'} / {len(wide):>2}枚          | {verdict}")


if __name__ == "__main__":
    main()
