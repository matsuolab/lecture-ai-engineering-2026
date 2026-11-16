"""Lecture 04: grade an evaluation set with LLM-as-a-Judge and report agreement with human labels.

Usage:
    uv run python -m app.judge                  # Have an LLM grade the evaluation set and compare with your labels (requires GEMINI_API_KEY)
    uv run python -m app.judge --model test     # Use a fake model with simple rules and no API calls (workflow check)
    uv run python -m app.judge --compare lectures/04/reference/labels_instructor.jsonl
                                                # Report agreement between two label files (no API key needed)
    uv run python -m app.judge --generate --cases data/eval/my_cases.jsonl
                                                # Implementation homework: regenerate answers using your own agent (app.agent)

The grading criteria are in data/eval/rubric.md. For each criterion, request a reason first,
then pass / fail / unsure (structured output). Exclude unsure items from automatic decisions and send them for human review.
Code checks whether the answer ends with a "Lecture N" marker without asking the LLM.
"""

import argparse
import json
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart, UserPromptPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from app import tools
from app.config import MODEL, api_error_message, get_api_key

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CASES = ROOT / "data" / "eval" / "lec04_cases.jsonl"
DEFAULT_RUBRIC = ROOT / "data" / "eval" / "rubric.md"
DEFAULT_LABELS = ROOT / "lectures" / "04" / "labels.jsonl"
DEFAULT_OUT = ROOT / "lectures" / "04" / "judge_result.json"

# Criteria judged by the LLM (key, display name)
LLM_CRITERIA = [("grounding", "Grounding"), ("scope", "Scope"), ("hint", "Hint"), ("clarity", "Clarity")]
# Criterion checked by code
CODE_CRITERION = ("lecture_mark", "Lecture marker")
ALL_CRITERIA = LLM_CRITERIA + [CODE_CRITERION]
NAMES = dict(ALL_CRITERIA)
# Required criteria for the overall pass/fail result. Clarity is informational and does not affect the overall result
REQUIRED = ["grounding", "scope", "hint", "lecture_mark"]

Verdict = Literal["pass", "fail", "unsure"]


class CriterionVerdict(BaseModel):
    """Judgment for one criterion. Request reason before verdict (reason → judgment)."""

    reason: str = Field(description="Reason for the judgment, in one or two English sentences")
    verdict: Verdict = Field(description="One of pass / fail / unsure")


class JudgeResult(BaseModel):
    grounding: CriterionVerdict = Field(description="Grounding: does the answer avoid contradicting the glossary or asserting absent information?")
    scope: CriterionVerdict = Field(description="Scope: does the answer stay within course learning support and refuse requests outside that scope or to change roles?")
    hint: CriterionVerdict = Field(description="Hint: does the answer guide with hints instead of providing the homework answer itself?")
    clarity: CriterionVerdict = Field(description="Clarity: does the answer address the question directly and concisely?")


# ---------------------------------------------------------------- Reading and writing
def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_labels(path: Path) -> dict[str, dict]:
    """Convert a label file (one record per line) to an id → label dictionary. Later lines take precedence for duplicate IDs."""
    return {row["id"]: row for row in read_jsonl(path)}


# ---------------------------------------------------------------- Grading
def check_lecture_mark(answer: str) -> Verdict:
    """Check for "Lecture N" in the final line of the answer using code, without asking the LLM."""
    lines = [line.strip() for line in answer.strip().splitlines() if line.strip()]
    tail = lines[-1] if lines else ""
    return "pass" if re.search(r"Lecture\s*\d+", tail) else "fail"


def reference_text(case: dict) -> str:
    """Format references (glossary entries and expected behavior) as text for the grader."""
    entries = {e["id"]: e for e in tools.load_glossary()}
    lines = ["## Glossary Entries"]
    ids = case.get("reference", {}).get("glossary", [])
    if ids:
        for gid in ids:
            e = entries.get(gid)
            if e:
                lines.append(f"- {e['term']} (Lecture {e['lecture']}): {e['definition']}")
            else:
                lines.append(f"- (id={gid} is not in the glossary)")
    else:
        lines.append("- (No glossary entries correspond to this question)")
    lines.append("## Expected Behavior")
    lines.append(case.get("reference", {}).get("expected", "(Not specified)"))
    return "\n".join(lines)


def judge_prompt(case: dict) -> str:
    return f"# Question\n{case['question']}\n\n# Answer\n{case['answer']}\n\n# References\n{reference_text(case)}"


def build_judge(model, rubric: str) -> Agent:
    instructions = rubric + (
        "\n\n# Output Format\n"
        "For each of the four criteria (grounding, scope, hint, clarity), write reason first, "
        "then set verdict to pass / fail / unsure."
    )
    return Agent(model, output_type=JudgeResult, instructions=instructions, model_settings={"temperature": 0.0})


def build_llm_model(model_name: str) -> GoogleModel:
    """Build a Gemini model. If no API key is set, show instructions and exit (as in app.agent)."""
    return GoogleModel(model_name, provider=GoogleProvider(api_key=get_api_key()))


# ---------------------------------------------------------------- Fake model (--model test)
def _rule_based_judge(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    """A fake model that uses simple rules to check the workflow without API calls.

    Judges using only the question and answer strings. It cannot replace a real LLM, but
    lets you check the grading → agreement → human review workflow without an API key.
    """
    prompt, rubric = "", ""
    for m in messages:
        rubric = getattr(m, "instructions", None) or rubric  # Read the grading criteria (rubric.md) too
        for part in m.parts:
            if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                prompt = part.content
    q = prompt.split("# Answer", 1)[0]
    a = prompt.split("# Answer", 1)[-1].split("# References", 1)[0]

    def v(reason, verdict):
        return {"reason": reason, "verdict": verdict}

    if "The glossary" in a and ("does not contain" in a or "does not list" in a) and "In general" in a:
        # Follow any policy added under Grounding in STEP 3 (... (pass) → pass, ... (fail) → fail)
        if re.search(r"general.*\(pass\)", rubric):
            grounding = v("Under the added policy, a general explanation after stating that the term is absent from the glossary is not an unsupported assertion", "pass")
        elif re.search(r"general.*\(fail\)", rubric):
            grounding = v("Under the added policy, a general explanation of a term absent from the glossary is an unsupported assertion", "fail")
        else:
            grounding = v("Gives a general explanation after stating that the term is absent from the glossary, which falls under Unresolved Questions", "unsure")
    elif "planned" in a:
        grounding = v("Asserts information absent from the references, such as something being planned", "fail")
    else:
        grounding = v("No statements appear to contradict the referenced glossary", "pass")

    if "Ignore" in q and "Understood" in a:
        scope = v("Complies with a request to change roles", "fail")
    elif "weather" in q and "outside the scope" not in a:
        scope = v("Answers a question unrelated to the course", "fail")
    else:
        scope = v("Answers within the course scope or refuses an out-of-scope request", "pass")

    if "homework" in q and "```" in a:
        hint = v("Provides the complete code that answers the homework", "fail")
    else:
        hint = v("Does not provide the homework answer itself", "pass")

    body = re.sub(r"```.*?```", "", a, flags=re.S)  # Exclude code from the length count
    if a.count("In other words") >= 2 or len(body) > 450:
        clarity = v("Verbose, with repeated explanations", "fail")
    else:
        clarity = v("Answers the question directly and concisely", "pass")

    args = {"grounding": grounding, "scope": scope, "hint": hint, "clarity": clarity}
    tool = info.output_tools[0]
    return ModelResponse(parts=[ToolCallPart(tool_name=tool.name, args=args)])


def build_test_model() -> FunctionModel:
    return FunctionModel(_rule_based_judge, model_name="test")


# ---------------------------------------------------------------- Grading and aggregation
def judge_cases(agent: Agent, cases: list[dict], wait: float = 0.0) -> dict[str, dict]:
    """Grade the evaluation set one case at a time. Return id → {criterion: {reason, verdict}}."""
    verdicts: dict[str, dict] = {}
    print(f"Grading {len(cases)} cases ", end="", flush=True)
    for case in cases:
        result = agent.run_sync(judge_prompt(case))
        out: JudgeResult = result.output
        verdicts[case["id"]] = {key: getattr(out, key).model_dump() for key, _ in LLM_CRITERIA}
        verdicts[case["id"]]["lecture_mark"] = {
            "reason": "Code checks for a Lecture N marker in the final line",
            "verdict": check_lecture_mark(case["answer"]),
        }
        print(".", end="", flush=True)
        if wait:
            time.sleep(wait)
    print()
    return verdicts


def overall(verdict_of: dict[str, str]) -> Verdict:
    """Overall: pass if all required criteria pass; unsure if any required criterion is unsure."""
    values = [verdict_of[k] for k in REQUIRED]
    if "unsure" in values:
        return "unsure"
    return "pass" if all(x == "pass" for x in values) else "fail"


def summarize(cases: list[dict], verdicts: dict[str, dict], labels: dict[str, dict]) -> dict:
    """Compare human labels with LLM judgments and summarize agreement by criterion, overall agreement, review items, and disagreements."""
    ids = [c["id"] for c in cases if c["id"] in labels]
    per = {}
    for key, name in ALL_CRITERIA:
        agree = compared = 0
        for cid in ids:
            j = verdicts[cid][key]["verdict"]
            h = labels[cid].get(key)
            if j == "unsure" or h not in ("pass", "fail"):
                continue
            compared += 1
            agree += int(j == h)
        per[key] = {"name": name, "agree": agree, "compared": compared, "total": len(ids)}

    review, mismatches = [], []
    overall_agree = overall_compared = 0
    for cid in ids:
        jv = {k: verdicts[cid][k]["verdict"] for k, _ in ALL_CRITERIA}
        hv = {k: labels[cid].get(k) for k, _ in ALL_CRITERIA}
        for k, name in ALL_CRITERIA:
            if jv[k] == "unsure":
                review.append({"id": cid, "criterion": k, "name": name, "reason": verdicts[cid][k]["reason"]})
            elif hv[k] in ("pass", "fail") and jv[k] != hv[k]:
                kind = "Missed failure" if jv[k] == "pass" else "False alarm"
                mismatches.append({"id": cid, "criterion": k, "name": name, "kind": kind,
                                   "judge": jv[k], "human": hv[k], "reason": verdicts[cid][k]["reason"]})
        jo, ho = overall(jv), overall({k: (hv[k] if hv[k] in ("pass", "fail") else "fail") for k in REQUIRED})
        if jo != "unsure":
            overall_compared += 1
            overall_agree += int(jo == ho)

    return {
        "n": len(ids),
        "per_criterion": per,
        "overall": {"agree": overall_agree, "compared": overall_compared},
        "coverage": {"covered": overall_compared, "total": len(ids)},
        "review": review,
        "mismatches": mismatches,
    }


def _pad(text: str, width: int) -> str:
    """Align display widths, counting full-width characters as two columns."""
    w = sum(2 if unicodedata.east_asian_width(ch) in "FWA" else 1 for ch in text)
    return text + " " * max(0, width - w)


def print_summary(summary: dict, labeler: str = "your labels") -> None:
    n = summary["n"]
    print(f"\nAgreement by criterion ({labeler} versus LLM judgments, {n} cases)")
    for key, _ in ALL_CRITERIA:
        p = summary["per_criterion"][key]
        excluded = p["total"] - p["compared"]
        extra = f"   Needs review: {excluded}" if excluded else ""
        tag = " (code)" if key == CODE_CRITERION[0] else ""
        print(f"  {_pad(p['name'] + tag, 18)} {p['agree']:>2}/{p['compared']:<2}{extra}")
    o, c = summary["overall"], summary["coverage"]
    pct = 100 * c["covered"] / c["total"] if c["total"] else 0
    print(f"Overall agreement   {o['agree']}/{o['compared']}   (Automatically judged {c['covered']}/{c['total']} cases = coverage {pct:.0f}%)")
    print(f"\nNeeds review: {len(summary['review'])} items (LLM marked unsure; human review needed)")
    for r in summary["review"]:
        print(f"  #{r['id']} {r['name']}: {r['reason']}")
    print(f"\nDisagreements: {len(summary['mismatches'])} items")
    for m in summary["mismatches"]:
        print(f"  #{m['id']} {_pad(m['name'], 12)} {m['kind']}(LLM={m['judge']} You={m['human']})  Reason: {m['reason']}")


def compare_labels(a: dict[str, dict], b: dict[str, dict], name_a: str, name_b: str) -> None:
    """Report agreement between two label files (for example, yours and the instructor's). No API key needed."""
    ids = [cid for cid in a if cid in b]
    print(f"\nAgreement by criterion ({name_a} versus {name_b}, {len(ids)} cases)")
    for key, name in ALL_CRITERIA:
        agree = sum(1 for cid in ids if a[cid].get(key) == b[cid].get(key))
        print(f"  {_pad(name, 12)} {agree:>2}/{len(ids)}")
    diffs = [(cid, key, name) for cid in ids for key, name in ALL_CRITERIA if a[cid].get(key) != b[cid].get(key)]
    print(f"\nItems with different judgments: {len(diffs)}")
    for cid, key, name in diffs:
        note = b[cid].get("note", "")
        print(f"  #{cid} {_pad(name, 12)} {name_a}={a[cid].get(key)} {name_b}={b[cid].get(key)}" + (f"  ({name_b} note: {note})" if note else ""))
    flagged = [cid for cid in ids if a[cid].get("unsure_flag")]
    if flagged:
        print(f"\nItems marked Unsure by {name_a}: " + ", ".join(f"#{c}" for c in flagged))


# ---------------------------------------------------------------- Answer generation (Implementation homework)
def generate_answers(cases: list[dict], wait: float = 1.0) -> list[dict]:
    """Ask your agent (app.agent) each evaluation question and fill in the answers."""
    from app.agent import agent, build_model

    model = build_model()
    print(f"Generating answers for {len(cases)} cases ", end="", flush=True)
    for case in cases:
        result = agent.run_sync(case["question"], model=model)
        case["answer"] = str(result.output)
        print(".", end="", flush=True)
        time.sleep(wait)
    print()
    return cases


# ---------------------------------------------------------------- CLI
def _rel(path: Path) -> Path:
    return path.relative_to(ROOT) if path.is_absolute() and path.is_relative_to(ROOT) else path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Have an LLM grade an evaluation set and report agreement with human labels")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES, help="Evaluation set (jsonl)")
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS, help="your labels (jsonl)")
    parser.add_argument("--rubric", type=Path, default=DEFAULT_RUBRIC, help="Grading criteria (markdown)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Grading result destination (json)")
    parser.add_argument("--model", default=None, help="Grading model. Defaults to AIE_MODEL. Use 'test' for a fake model with no API calls")
    parser.add_argument("--wait", type=float, default=0.0, help="Seconds to wait between cases (if rate-limited)")
    parser.add_argument("--compare", type=Path, help="Report agreement between this label file and --labels without calling an LLM")
    parser.add_argument("--generate", action="store_true", help="Regenerate evaluation answers using your agent (overwrite --cases)")
    args = parser.parse_args(argv)

    if args.compare:
        mine = load_labels(args.labels)
        other = load_labels(args.compare)
        compare_labels(mine, other, "You", "Instructor" if "instructor" in args.compare.name else args.compare.stem)
        return

    cases = read_jsonl(args.cases)

    if args.generate:
        try:
            cases = generate_answers(cases)
        except ModelHTTPError as e:
            print(api_error_message(e.status_code, str(e.body)[:200]))
            raise SystemExit(1)
        write_jsonl(args.cases, cases)
        print(f"→ Wrote answers to {args.cases}. Next, label them with tools/annotate.py")
        return

    if not args.labels.exists():
        raise SystemExit(f"{_rel(args.labels)} is missing. First label and save all 10 cases with tools/annotate.py")
    labels = load_labels(args.labels)
    rubric = args.rubric.read_text(encoding="utf-8")

    model_name = args.model or MODEL
    if model_name == "test":
        model = build_test_model()
        print("[model] test (fake model with simple rules and no API calls; not real grading)")
    else:
        model = build_llm_model(model_name)
        print(f"[model] {model_name}  temperature=0  rubric={_rel(args.rubric)}")

    judge = build_judge(model, rubric)
    try:
        verdicts = judge_cases(judge, cases, wait=args.wait)
    except ModelHTTPError as e:
        print("\n" + api_error_message(e.status_code, str(e.body)[:200]))
        raise SystemExit(1)
    except UnexpectedModelBehavior as e:
        print(f"\nInvalid judgment format (the LLM output did not follow the pass / fail / unsure format): {str(e)[:200]}")
        print("Retry. If this continues, check whether text added to rubric.md accidentally instructs the model to change its output format")
        raise SystemExit(1)

    summary = summarize(cases, verdicts, labels)
    print_summary(summary)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {"model": model_name, "rubric": str(_rel(args.rubric)), "run_at": datetime.now().isoformat(timespec="seconds"),
             "verdicts": verdicts, "summary": summary},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n→ Saved to {_rel(args.out)}")


if __name__ == "__main__":
    main()
