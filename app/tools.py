"""Lecture 03: tools for the agent.

Function docstrings and type hints here become the "tool descriptions" presented to the model.
Rewriting descriptions changes whether the model uses a tool and which arguments it supplies.
"""

import json
from functools import cache
from pathlib import Path
from datetime import datetime
import random

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_RESULTS = 3


@cache
def load_glossary() -> list[dict]:
    with open(DATA_DIR / "glossary.json", encoding="utf-8") as f:
        return json.load(f)["terms"]


def _normalize(text: str) -> str:
    return text.casefold().replace(" ", "").replace("　", "")


def _names(entry: dict) -> list[str]:
    return [_normalize(entry["term"]), _normalize(entry["id"])] + [
        _normalize(a) for a in entry["aliases"]
    ]


def search_glossary(query: str) -> str:
    """Search the course glossary and return definitions and the sessions that cover the terms.

    Use before answering about AI engineering terms or words specific to this course (AIE2026).
    Put only one term to look up in query (for example, "LoRA").
    """
    q = _normalize(query)
    if not q:
        return "The search query is empty. Specify one term to look up."
    glossary = load_glossary()

    exact = [e for e in glossary if q in _names(e)]
    # Exclude short names so aliases such as "r" do not match everything
    partial = [
        e for e in glossary
        if e not in exact and any(q in n or (len(n) >= 3 and n in q) for n in _names(e))
    ]
    in_definition = [
        e for e in glossary
        if e not in exact and e not in partial and q in _normalize(e["definition"])
    ]
    hits = (exact + partial + in_definition)[:MAX_RESULTS]

    if not hits:
        return f"The term '{query}' was not found in the glossary."
    return json.dumps(
        [
            {
                "term": e["term"],
                "lecture": e["lecture"],
                "definition": e["definition"],
                "related": e["related"],
            }
            for e in hits
        ],
        ensure_ascii=False,
    )


def get_lecture_summary(lecture: int) -> str:
    """Return key points from the specified session (an integer starting at 1).

    Use when asked about session content or relationships, such as "What will we learn in Lecture 03?".
    """
    path = DATA_DIR / "lectures" / f"{lecture:02d}.md"
    if not path.exists():
        available = sorted(p.stem for p in (DATA_DIR / "lectures").glob("*.md"))
        return f"Key points for Lecture {lecture:02d} are not available yet. Available sessions: {', '.join(available)}"
    return path.read_text(encoding="utf-8")

LOG_PATH = DATA_DIR / "learning_log.md"


def save_learning_log(summary: str) -> str:
    """Save a short note about what the learner studied to their learning log file.

    Use when the user asks to save, record, log, or note down what they learned,
    including phrases like "save a note about it" or "add this to my learning log".
    Do NOT call it unless the user asked for this; never save on your own after
    answering a question. This writes to disk, so a human approves each call.

    Args:
        summary: One or two sentences describing what was learned,
            e.g. "LoRA freezes base weights and trains small adapters (Lecture 02)."
    """
    summary = summary.strip()
    if not summary:
        return "The summary is empty. Nothing was saved."
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"- [{stamp}] {summary}\n")
    return f"Saved to learning log: {summary}"

def make_quiz(lecture: int) -> str:
    """Pick one term from the given lecture and return a review question and its answer.

    Use when the learner asks for a review question, quiz, or practice question,
    e.g. "Give me a review question for Lecture 2". It helps them recall what they
    studied by testing one term at a time.
    Do NOT use it to explain a term (use search_glossary) or to summarize a session
    (use get_lecture_summary).

    After calling it, show the learner ONLY the question. Do not reveal the answer
    until they have tried to answer or ask for it, then compare their reply with it.

    Args:
        lecture: Session number as a plain integer starting at 1 (2, not "02").
    """
    terms = [e for e in load_glossary() if e["lecture"] == lecture]
    if not terms:
        available = sorted({e["lecture"] for e in load_glossary()})
        return (
            f"No glossary terms found for Lecture {lecture}. "
            f"Lectures with terms: {', '.join(str(n) for n in available)}"
        )
    entry = random.choice(terms)
    return json.dumps(
        {"question": f"What does “{entry['term']}” mean?", "answer": entry["definition"]},
        ensure_ascii=False,
    )

