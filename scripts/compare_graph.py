"""旧 Graph と graph2 が取得するページを、LLM を使わずに比べる。"""

from app.graph2 import search_graph2
from app.retrieval import search_graph

NEED = {13, 39, 40}  # 根拠として必要なページ（第3回）

old = search_graph("コンパクション セッション メモリ 第3回")
old_pages = [p["page"] for p in old["seeds"]] + [p["page"] for p in old["expanded"]]
print("旧 seeds   :", [p["page"] for p in old["seeds"]])
print("旧 expanded:", [p["page"] for p in old["expanded"]])
print("旧 必要ページ:", sorted(NEED & set(old_pages)), f"{len(NEED & set(old_pages))}/3")
print()
new = search_graph2(["コンパクション", "セッションをまたぐメモリ"])
new_pages = [p["page"] for p in new["seeds"]] + [p["page"] for p in new["expanded"]]
print("新 seeds   :", [(p["page"], p["query"]) for p in new["seeds"]])
print("新 expanded:", [(p["page"], p["via"]) for p in new["expanded"]])
print("新 必要ページ:", sorted(NEED & set(new_pages)), f"{len(NEED & set(new_pages))}/3")