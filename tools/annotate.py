"""Lecture 04: an interface for labeling an evaluation set (Streamlit).

Usage:
    uv run --with streamlit==1.66.1 streamlit run tools/annotate.py

`uv run --with` temporarily adds Streamlit to the course environment (without changing pyproject.toml).

- Label: display evaluation cases (data/eval/lec04_cases.jsonl) one at a time and save pass/fail judgments for five criteria
  and an Unsure flag in lectures/04/labels.jsonl
- Compare: check agreement between your labels and the instructor's (lectures/04/reference/labels_instructor.jsonl)
- Author cases (Implementation homework): write questions and expected behavior to create your own evaluation set (data/eval/my_cases.jsonl).
  Generate answers using your agent with `uv run python -m app.judge --generate --cases data/eval/my_cases.jsonl`
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
    "grounding": "Does not contradict glossary entries. States that absent information is not in the glossary instead of making unsupported assertions",
    "scope": "Stays within course learning support. Refuses unrelated questions and requests to ignore instructions",
    "hint": "Provides hints instead of the homework answer itself (passes for questions unrelated to homework)",
    "clarity": "Answers the question directly, concisely, and readably",
    "lecture_mark": "Ends with a Lecture N marker (you will compare this with the code check later)",
}

st.set_page_config(page_title="Lecture 04 Labeling", layout="wide")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def glossary_entries(ids: list[str]) -> list[dict]:
    entries = {e["id"]: e for e in tools.load_glossary()}
    return [entries[i] for i in ids if i in entries]


# ---------------------------------------------------------------- Labeling
def page_label(cases_path: Path, labels_path: Path) -> None:
    cases = read_jsonl(cases_path)
    if not cases:
        st.error(f"No evaluation cases in {rel(cases_path)}")
        return
    labels = load_labels(labels_path) if labels_path.exists() else {}

    if "index" not in st.session_state:
        done = [i for i, c in enumerate(cases) if c["id"] in labels]
        st.session_state.index = min(len(done), len(cases) - 1) if done else 0

    i = st.session_state.index
    case = cases[i]
    st.progress((len(labels)) / len(cases), text=f"Saved {len(labels)} / {len(cases)} cases | Viewing #{case['id']} (case {i + 1})")

    nav1, nav2, nav3 = st.columns([1, 1, 6])
    if nav1.button("← Previous", disabled=i == 0):
        st.session_state.index = i - 1
        st.rerun()
    if nav2.button("Next →", disabled=i >= len(cases) - 1):
        st.session_state.index = i + 1
        st.rerun()

    left, right = st.columns([3, 2])
    with left:
        st.subheader(f"#{case['id']}  {case.get('category', '')}")
        st.markdown("**Question**")
        st.info(case["question"])
        st.markdown("**Answer**")
        st.markdown(case["answer"] or "(No answer yet. Generate one with `app.judge --generate`)")
        st.markdown("**References**")
        ref = case.get("reference", {})
        entries = glossary_entries(ref.get("glossary", []))
        if entries:
            for e in entries:
                st.markdown(f"- **{e['term']}** (Lecture {e['lecture']}): {e['definition']}")
        else:
            st.markdown("- (No glossary entries correspond to this question)")
        st.markdown(f"**Expected behavior**: {ref.get('expected', '(Not specified)')}")

    with right:
        st.subheader("Judgments")
        st.caption("Judge against the references and rubric, rather than your own knowledge. If uncertain, check Unsure and continue")
        current = labels.get(case["id"], {})
        with st.form(key=f"form-{case['id']}"):
            choice = {}
            for key, name in ALL_CRITERIA:
                default = 0 if current.get(key, "pass") == "pass" else 1
                choice[key] = st.radio(
                    f"{name}", ["Pass (T)", "Fail (F)"], index=default, horizontal=True,
                    help=CRITERION_HELP[key], key=f"{case['id']}-{key}",
                )
            unsure = st.checkbox("Unsure (the rubric alone does not resolve this)", value=bool(current.get("unsure_flag", False)))
            note = st.text_input("Note (optional)", value=current.get("note", ""))
            submitted = st.form_submit_button("Save and next", type="primary")
        if submitted:
            labels[case["id"]] = {
                "id": case["id"],
                **{key: ("pass" if choice[key].startswith("Pass") else "fail") for key, _ in ALL_CRITERIA},
                "unsure_flag": unsure,
                "note": note,
            }
            write_jsonl(labels_path, [labels[c["id"]] for c in cases if c["id"] in labels])
            if i < len(cases) - 1:
                st.session_state.index = i + 1
            st.rerun()

    if len(labels) >= len(cases):
        st.success(f"Saved all {len(cases)} cases → {rel(labels_path)}. Next, have an LLM grade them with `uv run python -m app.judge`")
        st.dataframe(
            [{"id": c["id"], **{name: labels[c["id"]][key] for key, name in ALL_CRITERIA},
              "Unsure": labels[c["id"]].get("unsure_flag", False)} for c in cases if c["id"] in labels],
            hide_index=True, use_container_width=True,
        )


# ---------------------------------------------------------------- Comparison
def page_compare(cases_path: Path, labels_path: Path) -> None:
    if not labels_path.exists():
        st.warning("First save your labels on the Label screen")
        return
    if not INSTRUCTOR_LABELS.exists():
        st.warning(f"Instructor labels are missing: {rel(INSTRUCTOR_LABELS)}")
        return
    cases = read_jsonl(cases_path)
    mine, ref = load_labels(labels_path), load_labels(INSTRUCTOR_LABELS)
    ids = [c["id"] for c in cases if c["id"] in mine and c["id"] in ref]
    st.subheader("Agreement between your labels and the instructor's")
    st.caption("The instructor's labels are not an answer key. This comparison illustrates that humans also disagree on some items")
    cols = st.columns(len(ALL_CRITERIA))
    for col, (key, name) in zip(cols, ALL_CRITERIA):
        agree = sum(1 for cid in ids if mine[cid].get(key) == ref[cid].get(key))
        col.metric(name, f"{agree}/{len(ids)}")
    code_agree = sum(1 for cid in ids if mine[cid].get("lecture_mark") == check_lecture_mark(next(c for c in cases if c["id"] == cid)["answer"]))
    st.caption(f"Your Lecture marker labels agree with the code check on {code_agree}/{len(ids)} cases")
    rows = []
    for cid in ids:
        for key, name in ALL_CRITERIA:
            if mine[cid].get(key) != ref[cid].get(key):
                rows.append({"id": cid, "Criterion": name, "You": mine[cid].get(key), "Instructor": ref[cid].get(key),
                             "You marked unsure": mine[cid].get("unsure_flag", False), "Instructor note": ref[cid].get("note", "")})
    st.markdown(f"**Items with different judgments: {len(rows)}**")
    if rows:
        st.dataframe(rows, hide_index=True, use_container_width=True)


# ---------------------------------------------------------------- Authoring cases (Implementation homework)
def page_author(cases_path: Path) -> None:
    st.subheader("Create your own evaluation set (Implementation homework)")
    st.caption("Write questions and expected behavior. Generate answers using your agent with `uv run python -m app.judge --generate --cases "
               f"{rel(cases_path)}`. Include inputs likely to cause failures (edge cases), as well as normal cases")
    existing = read_jsonl(cases_path) if cases_path.exists() else []
    glossary = tools.load_glossary()
    options = {f"{e['term']} (Lecture {e['lecture']})": e["id"] for e in glossary}
    with st.form("author"):
        question = st.text_area("Question", height=80)
        category = st.text_input("Category (for example, normal case, absent term, outside the course)")
        expected = st.text_area("Expected behavior (one or two sentences)", height=80)
        picked = st.multiselect("Referenced glossary entries", list(options))
        submitted = st.form_submit_button("Add", type="primary")
    if submitted:
        if not question.strip() or not expected.strip():
            st.error("Question and expected behavior are required")
        else:
            existing.append({
                "id": f"{len(existing) + 1:02d}", "category": category.strip(),
                "question": question.strip(), "answer": "",
                "reference": {"glossary": [options[p] for p in picked], "expected": expected.strip()},
            })
            write_jsonl(cases_path, existing)
            st.success(f"Added ({len(existing)} cases) → {rel(cases_path)}")
    if existing:
        st.dataframe([{"id": c["id"], "Category": c.get("category", ""), "Question": c["question"],
                       "Has answer": bool(c.get("answer"))} for c in existing], hide_index=True, use_container_width=True)


# ---------------------------------------------------------------- Screen selection
def main() -> None:
    st.markdown("## Lecture 04 Label an Evaluation Set")
    with st.sidebar:
        mode = st.radio("Screen", ["Label", "Compare (with instructor labels)", "Author cases (Implementation homework)"])
        st.divider()
        cases_path = Path(st.text_input("Evaluation set", value=rel(DEFAULT_CASES)))
        labels_path = Path(st.text_input("Label destination", value=rel(DEFAULT_LABELS)))
        my_cases_path = Path(st.text_input("Authored case destination", value=rel(MY_CASES)))
    cases_path = cases_path if cases_path.is_absolute() else ROOT / cases_path
    labels_path = labels_path if labels_path.is_absolute() else ROOT / labels_path
    my_cases_path = my_cases_path if my_cases_path.is_absolute() else ROOT / my_cases_path

    if mode.startswith("Label"):
        page_label(cases_path, labels_path)
    elif mode.startswith("Compare"):
        page_compare(cases_path, labels_path)
    else:
        page_author(my_cases_path)


main()
