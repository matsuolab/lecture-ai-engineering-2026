"""第5回宿題(実装): 前後ページが効く質問かを、検索結果だけで判定する。

使い方（リポジトリ直下で）:
    uv run python lectures/05/neighbor_check.py

各質問で search() を1回だけ呼び（埋め込みAPI 1回）、同じ結果に add_neighbors を適用して
「前後なし」と「前後1ページあり」を比べる。LLM は使わない。
need は、答えに必要な根拠ページ（PDFページ番号）。
判定: ヒットに無く、前後ありで初めて入る → 前後ページが効く質問（"効く"）。
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


def label(lecture: int, page: int) -> str:
    return f"第{lecture}回p.{page}"


def main() -> None:
    pages = load_pages()
    for question, lecture, a, b in CASES:
        hits = search(question)
        plain = add_neighbors(hits, 0, pages)
        wide = add_neighbors(hits, 1, pages)

        def fmt(rows):
            return ", ".join(
                f"{r['lecture']}-p{r['page']}" + ("*" if r["role"] == "neighbor" else "")
                for r in rows
            )

        in_hit = any(r["lecture"] == lecture and r["page"] == b for r in plain)
        in_wide = any(r["lecture"] == lecture and r["page"] == b for r in wide)
        verdict = ("効く" if (not in_hit and in_wide)
                   else "不要(前後なしでも入る)" if in_hit
                   else "前後でも入らない")
        print(f"\n質問: {question}")
        print(f"  A={label(lecture, a)} / 必要なB={label(lecture, b)}")
        print(f"  前後なし : {fmt(plain)}")
        print(f"  前後あり : {fmt(wide)}   (*=neighbor)")
        print(f"  判定     : {verdict}")


if __name__ == "__main__":
    main()
