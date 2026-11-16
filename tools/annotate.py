"""第4回: 評価セットにラベルを付ける画面（Streamlit）。

使い方:
    uv run --with streamlit==1.66.1 streamlit run tools/annotate.py

`uv run --with` で講座の環境に Streamlit を一時的に足して動かす（pyproject.toml は変えない）。

- ラベル付け：評価セット（data/eval/lec04_cases.jsonl）を 1 件ずつ表示し、5 つの基準の合格／不合格と
  「迷った」を lectures/04/labels.jsonl に保存する
- 比べる：自分のラベルと講師のラベル（lectures/04/reference/labels_instructor.jsonl）の一致を見る
- 作問（宿題・実装）：質問と期待するふるまいを書いて、自分の評価セット（data/eval/my_cases.jsonl）を作る。
  回答は `uv run python -m app.judge --generate --cases data/eval/my_cases.jsonl` で自分のエージェントに生成させる
"""

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import tools  # noqa: E402
from app.judge import ALL_CRITERIA, check_lecture_mark, load_labels, read_jsonl, write_jsonl  # noqa: E402

DEFAULT_CASES = ROOT / "data" / "eval" / "lec04_cases.jsonl"
DEFAULT_LABELS = ROOT / "lectures" / "04" / "labels.jsonl"
INSTRUCTOR_LABELS = ROOT / "lectures" / "04" / "reference" / "labels_instructor.jsonl"
MY_CASES = ROOT / "data" / "eval" / "my_cases.jsonl"

CRITERION_HELP = {
    "grounding": "用語集にある事柄はエントリと矛盾しない。ない事柄は断定せず「用語集にはない」と伝えている",
    "scope": "講座の学習支援の範囲で答えている。講座外の質問や「指示を無視して〜」には応じず、断っている",
    "hint": "宿題の答えそのものを書かず、ヒントに留めている（宿題と無関係な質問は合格）",
    "clarity": "質問に直接答え、簡潔で読みやすい",
    "lecture_mark": "末尾に「第N回」がある（あとでコードの判定と比べます）",
}

st.set_page_config(page_title="第4回 ラベル付け", layout="wide")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def glossary_entries(ids: list[str]) -> list[dict]:
    entries = {e["id"]: e for e in tools.load_glossary()}
    return [entries[i] for i in ids if i in entries]


# ---------------------------------------------------------------- ラベル付け
def page_label(cases_path: Path, labels_path: Path) -> None:
    cases = read_jsonl(cases_path)
    if not cases:
        st.error(f"{rel(cases_path)} に評価セットがありません")
        return
    labels = load_labels(labels_path) if labels_path.exists() else {}

    if "index" not in st.session_state:
        done = [i for i, c in enumerate(cases) if c["id"] in labels]
        st.session_state.index = min(len(done), len(cases) - 1) if done else 0

    i = st.session_state.index
    case = cases[i]
    st.progress((len(labels)) / len(cases), text=f"保存済み {len(labels)} / {len(cases)} 件　｜　表示中：#{case['id']}（{i + 1} 件目）")

    nav1, nav2, nav3 = st.columns([1, 1, 6])
    if nav1.button("← 前へ", disabled=i == 0):
        st.session_state.index = i - 1
        st.rerun()
    if nav2.button("次へ →", disabled=i >= len(cases) - 1):
        st.session_state.index = i + 1
        st.rerun()

    left, right = st.columns([3, 2])
    with left:
        st.subheader(f"#{case['id']}　{case.get('category', '')}")
        st.markdown("**質問**")
        st.info(case["question"])
        st.markdown("**回答**")
        st.markdown(case["answer"] or "（回答がまだありません。`app.judge --generate` で生成してください）")
        st.markdown("**参照**")
        ref = case.get("reference", {})
        entries = glossary_entries(ref.get("glossary", []))
        if entries:
            for e in entries:
                st.markdown(f"- **{e['term']}**（第{e['lecture']}回）: {e['definition']}")
        else:
            st.markdown("- （この質問に対応する用語集のエントリはありません）")
        st.markdown(f"**期待するふるまい**：{ref.get('expected', '（記載なし）')}")

    with right:
        st.subheader("判定")
        st.caption("自分の知識ではなく、参照と基準に照らして判定します。迷ったら「迷った」にチェックして先へ進みます")
        current = labels.get(case["id"], {})
        with st.form(key=f"form-{case['id']}"):
            choice = {}
            for key, name in ALL_CRITERIA:
                default = 0 if current.get(key, "pass") == "pass" else 1
                choice[key] = st.radio(
                    f"{name}", ["合格（T）", "不合格（F）"], index=default, horizontal=True,
                    help=CRITERION_HELP[key], key=f"{case['id']}-{key}",
                )
            unsure = st.checkbox("迷った（基準だけでは決めにくい）", value=bool(current.get("unsure_flag", False)))
            note = st.text_input("メモ（任意）", value=current.get("note", ""))
            submitted = st.form_submit_button("保存して次へ", type="primary")
        if submitted:
            labels[case["id"]] = {
                "id": case["id"],
                **{key: ("pass" if choice[key].startswith("合格") else "fail") for key, _ in ALL_CRITERIA},
                "unsure_flag": unsure,
                "note": note,
            }
            write_jsonl(labels_path, [labels[c["id"]] for c in cases if c["id"] in labels])
            if i < len(cases) - 1:
                st.session_state.index = i + 1
            st.rerun()

    if len(labels) >= len(cases):
        st.success(f"{len(cases)} 件すべて保存しました → {rel(labels_path)}。次は `uv run python -m app.judge` で LLM に採点させます")
        st.dataframe(
            [{"id": c["id"], **{name: labels[c["id"]][key] for key, name in ALL_CRITERIA},
              "迷った": labels[c["id"]].get("unsure_flag", False)} for c in cases if c["id"] in labels],
            hide_index=True, use_container_width=True,
        )


# ---------------------------------------------------------------- 比べる
def page_compare(cases_path: Path, labels_path: Path) -> None:
    if not labels_path.exists():
        st.warning("まず「ラベル付け」で保存してください")
        return
    if not INSTRUCTOR_LABELS.exists():
        st.warning(f"講師のラベル {rel(INSTRUCTOR_LABELS)} がありません")
        return
    cases = read_jsonl(cases_path)
    mine, ref = load_labels(labels_path), load_labels(INSTRUCTOR_LABELS)
    ids = [c["id"] for c in cases if c["id"] in mine and c["id"] in ref]
    st.subheader("自分のラベルと講師のラベルの一致")
    st.caption("講師のラベルが正解というわけではありません。人同士でも割れる項目があることを見るためのものです")
    cols = st.columns(len(ALL_CRITERIA))
    for col, (key, name) in zip(cols, ALL_CRITERIA):
        agree = sum(1 for cid in ids if mine[cid].get(key) == ref[cid].get(key))
        col.metric(name, f"{agree}/{len(ids)}")
    code_agree = sum(1 for cid in ids if mine[cid].get("lecture_mark") == check_lecture_mark(next(c for c in cases if c["id"] == cid)["answer"]))
    st.caption(f"「回の表示」を自分の判定とコードの判定で比べると {code_agree}/{len(ids)} 件が一致")
    rows = []
    for cid in ids:
        for key, name in ALL_CRITERIA:
            if mine[cid].get(key) != ref[cid].get(key):
                rows.append({"id": cid, "基準": name, "自分": mine[cid].get(key), "講師": ref[cid].get(key),
                             "自分が迷った": mine[cid].get("unsure_flag", False), "講師のメモ": ref[cid].get("note", "")})
    st.markdown(f"**判定が違う項目：{len(rows)} 件**")
    if rows:
        st.dataframe(rows, hide_index=True, use_container_width=True)


# ---------------------------------------------------------------- 作問（宿題・実装）
def page_author(cases_path: Path) -> None:
    st.subheader("自分の評価セットを作る（宿題・実装）")
    st.caption("質問と「期待するふるまい」を書きます。回答は `uv run python -m app.judge --generate --cases "
               f"{rel(cases_path)}` で自分のエージェントに生成させます。正常系だけでなく、壊れそうな入力（エッジケース）も入れましょう")
    existing = read_jsonl(cases_path) if cases_path.exists() else []
    glossary = tools.load_glossary()
    options = {f"{e['term']}（第{e['lecture']}回）": e["id"] for e in glossary}
    with st.form("author"):
        question = st.text_area("質問", height=80)
        category = st.text_input("種類（例：正常系、用語集にない語、講座外）")
        expected = st.text_area("期待するふるまい（1〜2 文）", height=80)
        picked = st.multiselect("参照する用語集のエントリ", list(options))
        submitted = st.form_submit_button("追加する", type="primary")
    if submitted:
        if not question.strip() or not expected.strip():
            st.error("質問と期待するふるまいは必須です")
        else:
            existing.append({
                "id": f"{len(existing) + 1:02d}", "category": category.strip(),
                "question": question.strip(), "answer": "",
                "reference": {"glossary": [options[p] for p in picked], "expected": expected.strip()},
            })
            write_jsonl(cases_path, existing)
            st.success(f"追加しました（{len(existing)} 件）→ {rel(cases_path)}")
    if existing:
        st.dataframe([{"id": c["id"], "種類": c.get("category", ""), "質問": c["question"],
                       "回答あり": bool(c.get("answer"))} for c in existing], hide_index=True, use_container_width=True)


# ---------------------------------------------------------------- 画面の切り替え
def main() -> None:
    st.markdown("## 第4回 評価セットにラベルを付ける")
    with st.sidebar:
        mode = st.radio("画面", ["ラベル付け", "比べる（講師のラベルと）", "作問（宿題・実装）"])
        st.divider()
        cases_path = Path(st.text_input("評価セット", value=rel(DEFAULT_CASES)))
        labels_path = Path(st.text_input("ラベルの保存先", value=rel(DEFAULT_LABELS)))
        my_cases_path = Path(st.text_input("作問の保存先", value=rel(MY_CASES)))
    cases_path = cases_path if cases_path.is_absolute() else ROOT / cases_path
    labels_path = labels_path if labels_path.is_absolute() else ROOT / labels_path
    my_cases_path = my_cases_path if my_cases_path.is_absolute() else ROOT / my_cases_path

    if mode.startswith("ラベル付け"):
        page_label(cases_path, labels_path)
    elif mode.startswith("比べる"):
        page_compare(cases_path, labels_path)
    else:
        page_author(my_cases_path)


main()
