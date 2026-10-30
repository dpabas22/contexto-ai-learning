"""
evaluate_retrieval.py - scores the search methods on eval_queries.json.

Run:  python evaluate_retrieval.py

How it stays honest
* Queries are split into "dev" and "test". The confidence threshold (how sure a method
  must be before it answers instead of saying "not covered") is chosen on dev only.
  The numbers you should quote come from the test split.
* A covered query counts as a hit if ANY acceptable lesson is in the top results.
* A not-covered query is handled correctly only if the method returns nothing.
"""
import json
import time
from pathlib import Path

from lesson_index import build_units
from retrieval import KeywordIndex, lookup, route

BASE = Path(__file__).parent
THRESHOLDS = [round(i * 0.02, 2) for i in range(0, 31)]       # 0.00 ... 0.60
RETRIEVERS = ("lookup", "keyword", "router")


def load_queries(base=BASE):
    with open(Path(base) / "eval_queries.json", "r", encoding="utf-8") as handle:
        return json.load(handle)["queries"]


def run_retriever(name, query, units, index, threshold, k=3):
    """The ids a method returns for one question (at most k)."""
    if name == "lookup":
        found = lookup(query, units)[:k]
    elif name == "keyword":
        found = index.search(query, k=k, min_score=threshold)
    elif name == "router":
        found = route(query, units, index, k=k, min_score=threshold)[1]
    else:
        raise ValueError(name)
    return [unit_id for unit_id, _ in found]


def _mean(values):
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def score(queries, results):
    """results = {query_id: [returned ids]}  ->  dictionary of measurements."""
    covered = [q for q in queries if q["expected"]]
    uncovered = [q for q in queries if not q["expected"]]
    hit1 = _mean(bool(results[q["id"]]) and results[q["id"]][0] in q["expected"] for q in covered)
    hit3 = _mean(any(r in q["expected"] for r in results[q["id"]]) for q in covered)
    false_refusal = _mean(not results[q["id"]] for q in covered)
    correct_refusal = _mean(not results[q["id"]] for q in uncovered)
    by_type = {}
    for kind in sorted({q["type"] for q in covered}):
        group = [q for q in covered if q["type"] == kind]
        by_type[kind] = _mean(any(r in q["expected"] for r in results[q["id"]]) for q in group)
    return {"hit@1": hit1, "hit@3": hit3, "false_refusal": false_refusal,
            "correct_refusal": correct_refusal, "hit@3_by_type": by_type,
            "n_covered": len(covered), "n_uncovered": len(uncovered)}


def balanced(metrics):
    """One number used to pick the threshold: half covered hit@3, half correct refusal."""
    return (metrics["hit@3"] + metrics["correct_refusal"]) / 2


def evaluate_one(name, queries, units, index, threshold):
    start = time.perf_counter()
    results = {q["id"]: run_retriever(name, q["query"], units, index, threshold) for q in queries}
    milliseconds = (time.perf_counter() - start) * 1000 / max(1, len(queries))
    metrics = score(queries, results)
    metrics["ms_per_query"] = milliseconds
    return metrics, results


def choose_threshold(name, dev_queries, units, index):
    """Best threshold on the dev split. Ties go to the more cautious (higher) value."""
    if name == "lookup":
        return 0.0
    best_value, best_threshold = -1.0, 0.0
    for threshold in THRESHOLDS:
        metrics, _ = evaluate_one(name, dev_queries, units, index, threshold)
        value = balanced(metrics)
        if value >= best_value:
            best_value, best_threshold = value, threshold
    return best_threshold


def run_baseline(base=BASE):
    units = build_units(base)
    index = KeywordIndex(units)
    queries = load_queries(base)
    dev = [q for q in queries if q["split"] == "dev"]
    test = [q for q in queries if q["split"] == "test"]
    outcome = {"n_units": len(units), "n_dev": len(dev), "n_test": len(test), "methods": {}}
    for name in RETRIEVERS:
        threshold = choose_threshold(name, dev, units, index)
        test_metrics, test_results = evaluate_one(name, test, units, index, threshold)
        dev_metrics, _ = evaluate_one(name, dev, units, index, threshold)
        outcome["methods"][name] = {
            "threshold": threshold, "test": test_metrics, "dev": dev_metrics,
            "test_results": test_results,
        }
    return outcome


def format_report(outcome):
    lines = [
        "# Baseline retrieval results",
        "",
        f"{outcome['n_units']} lesson units, {outcome['n_dev']} dev queries (threshold choice), "
        f"{outcome['n_test']} test queries (reported below).",
        "",
        "| Method | Threshold | Hit@1 | Hit@3 | False refusals | Correct refusals | ms/query |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, data in outcome["methods"].items():
        m = data["test"]
        lines.append(f"| {name} | {data['threshold']:.2f} | {m['hit@1']:.0%} | {m['hit@3']:.0%} | "
                     f"{m['false_refusal']:.0%} | {m['correct_refusal']:.0%} | {m['ms_per_query']:.2f} |")
    lines += ["", "Hit@3 by query type (test split):", "",
              "| Method | " + " | ".join(sorted(outcome["methods"]["router"]["test"]["hit@3_by_type"])) + " |",
              "|---|" + "---|" * len(outcome["methods"]["router"]["test"]["hit@3_by_type"])]
    for name, data in outcome["methods"].items():
        by_type = data["test"]["hit@3_by_type"]
        lines.append(f"| {name} | " + " | ".join(f"{by_type[k]:.0%}" for k in sorted(by_type)) + " |")
    lines += ["", "The queries and the index hints were written by the same author, so treat these "
                  "numbers as optimistic until real learners' questions are added."]
    return "\n".join(lines)


if __name__ == "__main__":
    report = format_report(run_baseline())
    print(report)
    (BASE / "eval_results_baseline.md").write_text(report + "\n", encoding="utf-8")
