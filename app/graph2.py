"""第5回 宿題（発展）: 観点ごとに入口を作る Graph 検索。"""
import json
import re
from collections import defaultdict

import sqlite_vec

from app.config import GRAPH_MAX_RESULTS, RAG_DB, RAG_GRAPH, RAG_SOURCE
from app.retrieval import embed_text, load_pages, open_index

MAX_QUERIES = 3      # 観点の最大数
SEEDS_PER_QUERY = 2  # 観点ごとの入口ページ数
SQL_ALL = "SELECT page_id, vec_distance_cosine(embedding, ?) AS d FROM chunks ORDER BY d, page_id LIMIT ?"
SQL_IDS = "SELECT page_id, vec_distance_cosine(embedding, ?) AS d FROM chunks WHERE page_id IN ({})"


def _norm(text):
    return re.sub(r"\s+", "", text).casefold()


def search_graph2(queries: list[str]) -> dict:
    queries = [q.strip() for q in queries if isinstance(q, str) and q.strip()][:MAX_QUERIES]
    if not queries:
        raise ValueError("検索語が空です。")
    pages = {p["page_id"]: p for p in load_pages(RAG_SOURCE)}
    graph = json.loads(RAG_GRAPH.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in graph["nodes"] if n["kind"] == "term" or n["id"] in pages}
    adj = defaultdict(set)
    for e in graph["edges"]:
        a, b = e["source"], e["target"]
        if e["relation"] in ("next_page", "mentions") and a in nodes and b in nodes:
            adj[a].add(b)
            adj[b].add(a)
    vecs = [sqlite_vec.serialize_float32(embed_text(q, "RETRIEVAL_QUERY")) for q in queries]

    with open_index(RAG_DB) as db:
        # 1. 観点ごとの入口
        seeds = {}
        for q, v in zip(queries, vecs):
            rows = db.execute(SQL_ALL, (v, SEEDS_PER_QUERY + len(seeds) + 3)).fetchall()
            new = [r for r in rows if r["page_id"] in pages and r["page_id"] not in seeds]
            for r in new[:SEEDS_PER_QUERY]:
                seeds[r["page_id"]] = {"distance": r["d"], "query": q}
        # 2. 候補：入口の前後ページ + 質問語に一致する用語が出るページ
        via = {}
        for sid in seeds:
            for n in adj[sid]:
                if n in pages and n not in seeds:
                    via.setdefault(n, f"前後ページ（p.{pages[sid]['page']}）")
        qtext = _norm(" ".join(queries))
        for tid, node in nodes.items():
            t = _norm(node["title"])
            if node["kind"] == "term" and len(t) >= 3 and t in qtext:
                for n in adj[tid]:
                    if n in pages and n not in seeds:
                        via.setdefault(n, f"用語「{node['title']}」")
        # 3. どれかの観点に近い順に並べる
        scores = {}
        if via:
            ids = list(via)
            sql = SQL_IDS.format(",".join("?" * len(ids)))
            for v in vecs:
                for r in db.execute(sql, [v, *ids]):
                    scores[r["page_id"]] = min(scores.get(r["page_id"], 9.0), r["d"])

    ranked = sorted(via, key=lambda pid: (scores.get(pid, 9.0), pid))
    limit = max(0, GRAPH_MAX_RESULTS - len(seeds))
    return {
        "queries": queries,
        "seeds": [{**pages[pid], **info} for pid, info in seeds.items()],
        "expanded": [{**pages[pid], "distance": scores.get(pid), "via": via[pid]} for pid in ranked[:limit]],
    }